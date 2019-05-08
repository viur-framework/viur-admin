# -*- coding: utf-8 -*-

from viur_admin.log import getLogger

logger = getLogger(__name__)

import html.parser

from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings

from viur_admin.bones.base import BaseViewBoneDelegate
from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.bones.string import chooseLang
from viur_admin.event import event
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector
from viur_admin.ui.rawtexteditUI import Ui_rawTextEditWindow
from viur_admin.network import RemoteFile, nam
from viur_admin.ui.docEditlinkEditUI import Ui_LinkEdit
from html.entities import entitydefs
from viur_admin.utils import wheelEventFilter, ViurTabBar


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


class ExtObj(object):
	pass


class HtmlSerializer(html.parser.HTMLParser):  # html.parser.HTMLParser
	def __init__(self, validHtml=None):
		global _defaultTags
		html.parser.HTMLParser.__init__(self)
		self.result = ""
		self.openTagsList = []
		self.validHtml = validHtml

	def handle_data(self, data):
		if data:
			self.result += data

	def handle_charref(self, name):
		self.result += "&#%s;" % (name)

	def handle_entityref(self, name):  # FIXME
		if name in entitydefs.keys():
			self.result += "&%s;" % (name)

	def handle_starttag(self, tag, attrs):
		""" Delete all tags except for legal ones """
		if self.validHtml and tag in self.validHtml["validTags"]:
			self.result = self.result + '<' + tag
			for k, v in attrs:
				if not tag in self.validHtml["validAttrs"].keys() or not k in \
				                                                         self.validHtml["validAttrs"][tag]:
					continue
				if k.lower()[0:2] != 'on' and v.lower()[0:10] != 'javascript':
					self.result = '%s %s="%s"' % (self.result, k, v)
			if "style" in [k for (k, v) in attrs]:
				syleRes = {}
				styles = [v for (k, v) in attrs if k == "style"][0].split(";")
				for s in styles:
					style = s[: s.find(":")].strip()
					value = s[s.find(":") + 1:].strip()
					if style in self.validHtml["validStyles"] and not any(
							[(x in value) for x in ["\"", ":", ";"]]):
						syleRes[style] = value
				if len(syleRes.keys()):
					self.result += " style=\"%s\"" % "; ".join(
						[("%s: %s" % (k, v)) for (k, v) in syleRes.items()])
			if tag in self.validHtml["singleTags"]:
				self.result = self.result + ' />'
			else:
				self.result = self.result + '>'
				self.openTagsList.insert(0, tag)

	def handle_endtag(self, tag):
		if self.validHtml and tag in self.openTagsList:
			for endTag in self.openTagsList[
			              :]:  # Close all currently open Tags until we reach the current one
				self.result = "%s</%s>" % (self.result, endTag)
				self.openTagsList.remove(endTag)
				if endTag == tag:
					break

	def cleanup(self):  # FIXME: vertauschte tags
		""" Append missing closing tags """
		for tag in self.openTagsList:
			endTag = '</%s>' % tag
			self.result += endTag

	def santinize(self, instr):
		self.result = ""
		self.openTagsList = []
		self.feed(instr)
		self.close()
		self.cleanup()
		return (self.result)


### Copy&Paste: End

class ExtendedTextEdit(QtWidgets.QTextEdit):
	def __init__(self, *args, **kwargs):
		super(ExtendedTextEdit, self).__init__(*args, **kwargs)
		self.ressourceMapCache = {}
		self._dragData = None
		self.document().setDefaultStyleSheet(
			"h1 { font-weight: 700; color: #010101 } h2 { font-weight: 600; color: #010101 } h3 { font-weight: 500; color: #010101 }")

	def loadResource(self, rType, name):
		if rType == QtGui.QTextDocument.ImageResource:
			name = name.path()
			if name.startswith("/file/download/"):
				name = name[len("/file/download/"):]
			if name in self.ressourceMapCache.keys():
				if self.ressourceMapCache[name] is not None:
					return (QtGui.QImage(self.ressourceMapCache[name]["filename"]))
			else:
				RemoteFile(name, self.onFileAvaiable)
				self.ressourceMapCache[name] = None
		return (None)

	def onFileAvaiable(self, rFile):
		size = None
		pic = QtGui.QPixmap(rFile.getFileName())
		size = pic.width(), pic.height()
		self.ressourceMapCache[rFile.dlKey] = {"filename": rFile.getFileName(),
		                                       "size": size
		                                       }
		self.document().markContentsDirty(0, len(self.document().toPlainText()))

	# self.markContentsDirty( 0, len( self.getText() ) )

	def mousePressEvent(self, e):
		"""
			Allow resizing inline Images using drag&drop
			Record the start of a potential drag&drop operation
		"""
		cursor = self.cursorForPosition(e.pos())
		txtFormat = cursor.charFormat()
		if txtFormat.objectType() == txtFormat.ImageObject:
			self._dragData = e.x(), e.y()
		super(ExtendedTextEdit, self).mousePressEvent(e)

	def mouseMoveEvent(self, e):
		"""
			Allow resizing inline Images using drag&drop
			Do the actual work and resize the image
		"""
		if self._dragData:
			dx = e.x() - self._dragData[0]
			dy = e.y() - self._dragData[1]
			self._dragData = e.x(), e.y()
			currentBlock = self.textCursor().block()
			it = currentBlock.begin()
			while not it.atEnd():
				fragment = it.fragment()
				if fragment.isValid():
					if fragment.charFormat().isImageFormat():
						newImageFormat = fragment.charFormat().toImageFormat()
						fname = newImageFormat.name()
						if fname.startswith("/file/download/"):
							fname = fname[len("/file/download/"):]
						if fname in self.ressourceMapCache.keys() and \
								self.ressourceMapCache[fname]["size"] is not None:
							ratio = float(self.ressourceMapCache[fname]["size"][0]) / float(
								self.ressourceMapCache[fname]["size"][1])
							newX = max(50, newImageFormat.width() + dx)
							newY = max(50, newImageFormat.height() + dy)
							newX = min(newX, newY * ratio)
							newY = newX / ratio
							newImageFormat.setWidth(newX)
							newImageFormat.setHeight(newY)
						else:
							newImageFormat.setWidth(max(50, newImageFormat.width() + dx))
							newImageFormat.setHeight(max(50, newImageFormat.height() + dy))
						if newImageFormat.isValid():
							helper = self.textCursor()
							helper.setPosition(fragment.position())
							helper.setPosition(fragment.position() + fragment.length(),
							                   helper.KeepAnchor)
							helper.setCharFormat(newImageFormat)
				it += 1
		super(ExtendedTextEdit, self).mouseMoveEvent(e)

	def mouseReleaseEvent(self, e):
		"""
			Allow resizing inline Images using drag&drop
			Destroy our recording of the potential start-drag position.
		"""
		self._dragData = None
		super(ExtendedTextEdit, self).mouseReleaseEvent(e)


class WebPage(QtCore.QObject):
	sendText = QtCore.pyqtSignal((str))
	requestCode = QtCore.pyqtSignal()
	receiveCodeCallback = QtCore.pyqtSignal((str))

	def __init__(self, parent=None):
		super(WebPage, self).__init__(parent)
		self.textToEdit = ""

	@QtCore.pyqtSlot()
	def onEditorLoaded(self):
		logger.debug('onEditorLoaded called')
		self.sendText.emit(self.textToEdit)

	@QtCore.pyqtSlot()
	def getHtmlCode(self):
		self.requestCode.emit()

	@QtCore.pyqtSlot(str)
	def transmitHtmlCodeToHost(self, data):
		self.receiveCodeCallback.emit(data)


class TextEdit(QtWidgets.QMainWindow):
	onDataChanged = QtCore.pyqtSignal((object,))

	def __init__(self, text, validHtml, parent=None):
		super(TextEdit, self).__init__(parent)
		self.validHtml = validHtml
		self.serializer = HtmlSerializer(validHtml)
		self.ui = ExtObj()
		self.ui.centralWidget = QtWidgets.QWidget(self)
		self.setCentralWidget(self.ui.centralWidget)
		self.ui.centralWidget.setLayout(QtWidgets.QVBoxLayout())
		self.ui.textEdit = QWebEngineView()
		settings = self.ui.textEdit.settings()
		settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
		settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
		settings.setDefaultTextEncoding("utf-8")
		settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
		settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
		settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
		settings.setUnknownUrlSchemePolicy(QWebEngineSettings.AllowAllUnknownUrlSchemes)
		self.channel = QWebChannel()
		self.handler = WebPage(self)
		self.handler.textToEdit = text
		self.channel.registerObject('handler', self.handler)
		self.ui.textEdit.page().setWebChannel(self.channel)
		self.ui.centralWidget.layout().addWidget(self.ui.textEdit)
		self.ui.btnSave = QtWidgets.QPushButton(QtGui.QIcon(":icons/actions/accept.svg"),
		                                        QtCore.QCoreApplication.translate("TextEdit", "Apply"),
		                                        self.ui.centralWidget)
		self.ui.centralWidget.layout().addWidget(self.ui.btnSave)
		self.ui.btnSave.released.connect(self.onPrepareSave)
		self.handler.receiveCodeCallback.connect(self.onFinishSave)
		self.linkEditor = None
		self.setToolButtonStyle(QtCore.Qt.ToolButtonFollowStyle)
		self.ui.textEdit.setFocus()
		# self.ui.textEdit.setHtml(open("/home/stefan/IdeaProjects/viur_admin/viur_admin/htmleditor/index.html").read())
		self.ui.textEdit.setUrl(QtCore.QUrl("qrc:/htmleditor/index.html"))
		logger.debug("text to edit: %r", text)

	@QtCore.pyqtSlot()
	def onPrepareSave(self):
		self.handler.getHtmlCode()

	@QtCore.pyqtSlot(str)
	def onFinishSave(self, data):
		self.onDataChanged.emit(data)
		event.emit('popWidget', self)

	def onTextEditInsertFromMimeData(self, source):
		QtWidgets.QTextEdit.insertFromMimeData(self.ui.textEdit, source)
		html = self.ui.textEdit.toHtml()
		start = html.find(">", html.find("<body")) + 1
		html = html[start: html.rfind("</body>")]
		html = html.replace("""text-indent:0px;"></p>""", """text-indent:0px;">&nbsp;</p>""")
		self.ui.textEdit.setText(self.serializer.santinize(html))

	def openLinkEditor(self, fragment):
		if self.linkEditor:
			self.linkEditor.deleteLater()

		self.linkEditor = QtWidgets.QDockWidget(
			QtCore.QCoreApplication.translate("DocumentEditBone", "Edit link"), self)
		self.linkEditor.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)
		self.linkEditor.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
		self.linkEditor.cWidget = QtWidgets.QWidget()
		self.linkEditor.ui = Ui_LinkEdit()
		self.linkEditor.ui.setupUi(self.linkEditor.cWidget)
		self.linkEditor.setWidget(self.linkEditor.cWidget)
		self.linkEditor.fragmentPosition = fragment.position()
		href = fragment.charFormat().anchorHref()
		self.linkEditor.ui.editHref.setText(href.strip("!"))
		if href.startswith("!"):
			self.linkEditor.ui.checkBoxNewWindow.setChecked(True)
		self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.linkEditor)

	def saveLinkEditor(self):
		self.ui.textEdit.blockSignals(True)
		href = self.linkEditor.ui.editHref.text()
		cursor = self.ui.textEdit.textCursor()
		block = self.ui.textEdit.document().findBlock(self.linkEditor.fragmentPosition)
		iterator = block.begin()
		foundStart = False
		foundEnd = False
		oldHref = ""
		while (not iterator.atEnd()):
			fragment = iterator.fragment()
			if foundStart:
				foundEnd = True
				if oldHref != fragment.charFormat().anchorHref():
					newPos = fragment.position()
					while (cursor.position() < newPos):
						cursor.movePosition(QtGui.QTextCursor.NextCharacter,
						                    QtGui.QTextCursor.KeepAnchor)
					break
			elif fragment.contains(self.linkEditor.fragmentPosition):
				cursor.setPosition(fragment.position())
				foundStart = True
				oldHref = fragment.charFormat().anchorHref()
			iterator += 1
		if foundStart and not foundEnd:  # This is only this block
			cursor.select(cursor.BlockUnderCursor)
		if not href:
			cursor.insertHtml(cursor.selectedText())
		else:
			if self.linkEditor.ui.checkBoxNewWindow.isChecked():
				linkTxt = "<a href=\"!%s\">%s</a>"
			else:
				linkTxt = "<a href=\"%s\">%s</a>"
			cursor.insertHtml(linkTxt % (self.linkEditor.ui.editHref.text(), cursor.selectedText()))
		self.ui.textEdit.blockSignals(False)

	def getBreadCrumb(self):
		return (QtCore.QCoreApplication.translate("TextEditBone", "Text edit"),
		        QtGui.QIcon(QtGui.QPixmap(":icons/actions/text-edit.png")))

	# def onBtnSaveReleased(self):
	# 	print(self.ui.textEdit.toHtml())
	# 	self.save()




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
	               "img": ["src", "target", "width", "height",
	                       "align"] + _attrsDescr + _attrsMargins + _attrsSpacing,
	               "table": ["width", "align", "border", "cellspacing", "cellpadding"] + _attrsDescr,
	               "td": ["cellspan", "rowspan", "width", "heigt"] + _attrsMargins + _attrsSpacing
	               },
	"validStyles": ["font-weight", "font-style", "text-decoration", "color", "display"],
	# List of CSS-Directives we allow
	"singleTags": ["br", "img", "hr"]  # List of tags, which dont have a corresponding end tag
}
del _attrsDescr, _attrsSpacing, _attrsMargins


class ClickableWebView(QWebEngineView):
	clicked = QtCore.pyqtSignal()

	def mousePressEvent(self, ev):
		super(ClickableWebView, self).mousePressEvent(ev)
		self.chromeCookieJar = self.page().profile().cookieStore()
		self.chromeCookieJar.cookieAdded.connect(self.onCookieAdded)
		self.chromeCookieJar.loadAllCookies()
		for cookie in nam.cookieJar().allCookies():
			self.chromeCookieJar.setCookie(cookie)
		self.clicked.emit()

	def onCookieAdded(self, cookie):
		logger.error("WebWidget.onCookieAdded not yet handled properly: %r", cookie)


class TextEditBone(BoneEditInterface):
	def __init__(self, modulName, boneName, readOnly, languages=None, plaintext=False, validHtml=None,
	             editWidget=None,
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
			self.tabWidget.setTabBar(ViurTabBar())
			self.tabWidget.blockSignals(True)
			self.tabWidget.currentChanged.connect(self.onTabCurrentChanged)
			event.connectWithPriority("tabLanguageChanged", self.onTabLanguageChanged, event.lowPriority)
			self.layout().addWidget(self.tabWidget)
			for lang in self.languages:
				self.html[lang] = ""
				container = QtWidgets.QWidget()
				container.setLayout(QtWidgets.QVBoxLayout(container))
				self.languageContainer[lang] = container
				btn = QtWidgets.QPushButton(
					QtCore.QCoreApplication.translate("TextEditBone", "Open editor"), self)
				iconbtn = QtGui.QIcon()
				iconbtn.addPixmap(QtGui.QPixmap(":icons/actions/text-edit.svg"), QtGui.QIcon.Normal,
				                  QtGui.QIcon.Off)
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
			btn = QtWidgets.QPushButton(QtCore.QCoreApplication.translate("TextEditBone", "Open editor"),
			                            self)
			iconbtn = QtGui.QIcon()
			iconbtn.addPixmap(QtGui.QPixmap(":icons/actions/text-edit.svg"), QtGui.QIcon.Normal,
			                  QtGui.QIcon.Off)
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
		self.installEventFilter(wheelEventFilter)

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
			TextEditBone(modulName, boneName, readOnly, languages=languages, plaintext=plaintext,
			             validHtml=validHtml,
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
					editor = TextEdit(self.html[lang], self.validHtml)
				else:
					editor = RawTextEdit(self.html[lang])
		else:
			if self.plaintext:
				editor = RawTextEdit(self.html)
			else:
				if self.validHtml:
					editor = TextEdit(self.html, self.validHtml)
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
					self.html[lang] = data[self.boneName][lang].replace("target=\"_blank\" href=\"",
					                                                    "href=\"!")
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
