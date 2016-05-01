# -*- coding: utf-8 -*-
import html.parser

from PyQt5 import QtCore, QtGui, QtWidgets, QtWebKitWidgets

from viur_admin.bones.base import BaseViewBoneDelegate
from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.bones.string import chooseLang
from viur_admin.event import event
from viur_admin.mkdown_edit.mk_editor import MkEditor
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector
from viur_admin.ui.rawtexteditUI import Ui_rawTextEditWindow


class HtmlStripper(html.parser.HTMLParser):
	def __init__(self):
		super(HtmlStripper, self).__init__()
		self.cleanData = []

	def handle_data(self, data):
		self.cleanData.append(data)

	def getData(self):
		return ''.join(self.cleanData)

	@staticmethod
	def strip(txt):
		s = HtmlStripper()
		s.feed(txt)
		return (s.getData())


class TextViewBoneDelegate(BaseViewBoneDelegate):
	cantSort = True

	def __init__(self, modulName, boneName, skelStructure, *args, **kwargs):
		super(TextViewBoneDelegate, self).__init__(modulName, boneName, skelStructure, *args, **kwargs)
		self.skelStructure = skelStructure
		self.boneName = boneName
		self.modulName = modulName

	def displayText(self, value, locale):
		if "languages" in self.skelStructure[self.boneName].keys():
			languages = self.skelStructure[self.boneName]["languages"]
		else:
			languages = None
		if languages is not None:
			value = chooseLang(value, languages)
		if value:
			value = HtmlStripper.strip(value)
		return (super(TextViewBoneDelegate, self).displayText(value, locale))


class RawTextEdit(QtWidgets.QWidget):
	onDataChanged = QtCore.pyqtSignal((object,))

	def __init__(self, text, contentType=None, parent=None):
		super(RawTextEdit, self).__init__(parent)
		self.ui = Ui_rawTextEditWindow()
		self.ui.setupUi(self)
		self.contentType = contentType
		self.ui.textEdit.setText(text)
		self.ui.textEdit.setFocus()
		self.ui.btnSave.released.connect(self.save)

	def save(self, *args, **kwargs):
		self.onDataChanged.emit(self.ui.textEdit.toPlainText())
		event.emit('popWidget', self)

	def sizeHint(self, *args, **kwargs):
		return (QtCore.QSize(400, 300))


### Copy&Paste from server/bones/textBone.py

_attrsMargins = ["margin", "margin-left", "margin-right", "margin-top", "margin-bottom"]
_attrsSpacing = ["spacing", "spacing-left", "spacing-right", "spacing-top", "spacing-bottom"]
_attrsDescr = ["title", "alt"]
_defaultTags = {
	"validTags": ['font', 'b', 'a', 'i', 'u', 'span', 'div', 'p', 'img', 'ol', 'ul', 'li', 'acronym',
	              # List of HTML-Tags which are valid
	              'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'tr', 'td', 'th', 'br', 'hr', 'strong'],
	"validAttrs": {"font": ["color"],
	               # Mapping of valid parameters for each tag (if a tag is not listed here: no parameters allowed)
	               "a": ["href", "target"] + _attrsDescr,
	               "acronym": ["title"],
	               "div": ["align", "width", "height"] + _attrsMargins + _attrsSpacing,
	               "p": ["align", "width", "height"] + _attrsMargins + _attrsSpacing,
	               "span": ["align", "width", "height"] + _attrsMargins + _attrsSpacing,
	               "img": ["src", "target", "width", "height", "align"] + _attrsDescr + _attrsMargins + _attrsSpacing,
	               "table": ["width", "align", "border", "cellspacing", "cellpadding"] + _attrsDescr,
	               "td": ["cellspan", "rowspan", "width", "heigt"] + _attrsMargins + _attrsSpacing
	               },
	"validStyles": ["font-weight", "font-style", "text-decoration", "color", "display"],
	# List of CSS-Directives we allow
	"singleTags": ["br", "img", "hr"]  # List of tags, which dont have a corresponding end tag
}
del _attrsDescr, _attrsSpacing, _attrsMargins


class ClickableWebView(QtWebKitWidgets.QWebView):
	clicked = QtCore.pyqtSignal()

	def mousePressEvent(self, ev):
		super(ClickableWebView, self).mousePressEvent(ev)
		self.clicked.emit()


class TextEditBone(BoneEditInterface):
	def __init__(self, modulName, boneName, readOnly, languages=None, plaintext=False, validHtml=None, editWidget=None,
	             *args, **kwargs):
		super(TextEditBone, self).__init__(modulName, boneName, readOnly, editWidget)

		self.setLayout(QtWidgets.QVBoxLayout(self))
		self.languages = languages
		self.plaintext = plaintext
		self.validHtml = validHtml
		if self.languages:
			self.languageContainer = {}
			self.html = {}
			self.tabWidget = QtWidgets.QTabWidget(self)
			self.tabWidget.blockSignals(True)
			self.tabWidget.currentChanged.connect(self.onTabCurrentChanged)
			event.connectWithPriority("tabLanguageChanged", self.onTabLanguageChanged, event.lowPriority)
			self.layout().addWidget(self.tabWidget)
			for lang in self.languages:
				self.html[lang] = ""
				container = QtWidgets.QWidget()
				container.setLayout(QtWidgets.QVBoxLayout(container))
				self.languageContainer[lang] = container
				btn = QtWidgets.QPushButton(QtCore.QCoreApplication.translate("TextEditBone", "Open editor"), self)
				iconbtn = QtGui.QIcon()
				iconbtn.addPixmap(QtGui.QPixmap(":icons/actions/text-edit.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
				btn.setIcon(iconbtn)
				btn.released.connect(self.openEditor)
				btn.lang = lang
				webView = ClickableWebView(self)
				webView.clicked.connect(self.openEditor)
				container.webView = webView
				container.layout().addWidget(webView)
				container.layout().addWidget(btn)
				self.tabWidget.addTab(container, lang)
			self.tabWidget.blockSignals(False)
			self.tabWidget.show()
		else:
			btn = QtWidgets.QPushButton(QtCore.QCoreApplication.translate("TextEditBone", "Open editor"), self)
			iconbtn = QtGui.QIcon()
			iconbtn.addPixmap(QtGui.QPixmap("icons/actions/text-edit.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
			btn.setIcon(iconbtn)
			btn.lang = None
			btn.released.connect(self.openEditor)
			self.webView = ClickableWebView(self)
			self.webView.clicked.connect(self.openEditor)
			self.layout().addWidget(self.webView)
			self.layout().addWidget(btn)
			self.html = ""
		self.setSizePolicy(
				QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred))

	@staticmethod
	def fromSkelStructure(modulName, boneName, skelStructure, **kwargs):
		readOnly = "readonly" in skelStructure[boneName].keys() and skelStructure[boneName]["readonly"]
		if boneName in skelStructure.keys():
			if "languages" in skelStructure[boneName].keys():
				languages = skelStructure[boneName]["languages"]
			else:
				languages = None
			if "plaintext" in skelStructure[boneName].keys() and skelStructure[boneName]["plaintext"]:
				plaintext = True
			else:
				plaintext = False
			if "validHtml" in skelStructure[boneName].keys():
				validHtml = skelStructure[boneName]["validHtml"]
			else:
				validHtml = None
		return (
			TextEditBone(modulName, boneName, readOnly, languages=languages, plaintext=plaintext, validHtml=validHtml,
			             **kwargs))

	def onTabLanguageChanged(self, lang):
		if lang in self.languageContainer.keys():
			try:
				self.tabWidget.blockSignals(True)
				self.tabWidget.setCurrentWidget(self.languageContainer[lang])
				self.tabWidget.blockSignals(False)
			except RuntimeError as err:
				pass

	def onTabCurrentChanged(self, idx):
		wdg = self.tabWidget.widget(idx)
		for k, v in self.languageContainer.items():
			if v == wdg:
				event.emit("tabLanguageChanged", k)
				wdg.setFocus()
				return

	def sizeHint(self):
		return (QtCore.QSize(150, 150))

	def openEditor(self, *args, **kwargs):
		if self.languages:
			lang = self.languages[self.tabWidget.currentIndex()]
			if self.plaintext:
				editor = RawTextEdit(self.html[lang])
			else:
				if self.validHtml:
					editor = MkEditor(self.html[lang])
				else:
					editor = RawTextEdit(self.html[lang])
		else:
			if self.plaintext:
				editor = RawTextEdit(self.html)
			else:
				if self.validHtml:
					editor = MkEditor(self.html)
				else:
					editor = RawTextEdit(self.html)
		editor.onDataChanged.connect(self.onSave)
		event.emit("stackWidget", editor)

	def onSave(self, text):
		if self.languages:
			lang = self.languages[self.tabWidget.currentIndex()]
			self.html[lang] = str(text)
			self.languageContainer[lang].webView.setHtml(text)
		else:
			self.html = str(text)
			self.webView.setHtml(text)

	def unserialize(self, data):
		if self.boneName not in data.keys():
			return
		if self.languages and isinstance(data[self.boneName], dict):
			for lang in self.languages:
				if lang in data[self.boneName].keys() and data[self.boneName][lang] is not None:
					self.html[lang] = data[self.boneName][lang].replace("target=\"_blank\" href=\"", "href=\"!")
				else:
					self.html[lang] = ""
				self.languageContainer[lang].webView.setHtml(self.html[lang])
		elif not self.languages:
			self.html = str(data[self.boneName]).replace("target=\"_blank\" href=\"", "href=\"!") if (
				data and data.get(self.boneName)) else ""
			self.webView.setHtml(self.html)

	def serializeForPost(self):
		if self.languages:
			res = {}
			for lang in self.languages:
				res["%s.%s" % (self.boneName, lang)] = self.html[lang]
			return (res)
		else:
			return ({self.boneName: self.html.replace("href=\"!", "target=\"_blank\" href=\"")})

	def serializeForDocument(self):
		return (self.serialize())

	def remove(self):
		pass


def CheckForTextBone(modulName, boneName, skelStucture):
	return (skelStucture[boneName]["type"] == "text")


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForTextBone, TextEditBone)
viewDelegateSelector.insert(2, CheckForTextBone, TextViewBoneDelegate)
