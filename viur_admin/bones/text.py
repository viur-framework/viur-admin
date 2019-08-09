# -*- coding: utf-8 -*-

import html.parser
from typing import Union, Sequence, Any, List, Dict

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings

from viur_admin.bones.base import BaseViewBoneDelegate
from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.bones.string import chooseLang
from viur_admin.event import event
from viur_admin.log import getLogger
from viur_admin.network import RemoteFile, nam
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector
from viur_admin.ui.docEditlinkEditUI import Ui_LinkEdit
from viur_admin.ui.rawtexteditUI import Ui_rawTextEditWindow
from viur_admin.utils import wheelEventFilter, ViurTabBar

logger = getLogger(__name__)


class TextViewBoneDelegate(BaseViewBoneDelegate):
	cantSort = True

	def __init__(
			self,
			modulName: str,
			boneName: str,
			skelStructure: dict,
			*args: Any,
			**kwargs: Any):
		super(TextViewBoneDelegate, self).__init__(modulName, boneName, skelStructure, *args, **kwargs)
		self.skelStructure = skelStructure
		self.boneName = boneName
		self.modulName = modulName

	def displayText(self, value: str, locale: QtCore.QLocale) -> None:
		if "languages" in self.skelStructure[self.boneName]:
			languages = self.skelStructure[self.boneName]["languages"]
		else:
			languages = None
		if languages is not None:
			value = chooseLang(value, languages)

		return super(TextViewBoneDelegate, self).displayText(value, locale)


class RawTextEdit(QtWidgets.QWidget):
	onDataChanged = QtCore.pyqtSignal((object,))

	def __init__(
			self,
			text: str,
			contentType: str = None,
			parent: Union[QtWidgets.QWidget, None] = None):
		super(RawTextEdit, self).__init__(parent)
		self.ui = Ui_rawTextEditWindow()
		self.ui.setupUi(self)
		self.contentType = contentType
		self.ui.textEdit.setText(text)
		self.ui.textEdit.setFocus()
		self.ui.btnSave.released.connect(self.save)

	def save(
			self,
			*args: Any,
			**kwargs: Any) -> None:
		self.onDataChanged.emit(self.ui.textEdit.toPlainText())
		event.emit('popWidget', self)

	def sizeHint(
			self,
			*args: Any,
			**kwargs: Any) -> QtCore.QSize:
		return QtCore.QSize(400, 300)


class ExtendedTextEdit(QtWidgets.QTextEdit):
	def __init__(
			self,
			*args: Any,
			**kwargs: Any):
		super(ExtendedTextEdit, self).__init__(*args, **kwargs)
		self.resourceMapCache: dict[str, Any] = dict()
		self._dragData = None
		self.document().setDefaultStyleSheet(
			"h1 { font-weight: 700; color: #010101 } h2 { font-weight: 600; color: #010101 } h3 { font-weight: 500; color: #010101 }")

	def loadResource(self, resource_type: int, name: QtCore.QUrl) -> Union[QtGui.QImage, None]:
		logger.debug("loadResource: %r, %r", resource_type, name)
		if resource_type == QtGui.QTextDocument.ImageResource:
			name = name.path()
			if name.startswith("/file/download/"):
				name = name[len("/file/download/"):]
			if name in self.resourceMapCache:
				if self.resourceMapCache[name] is not None:
					return QtGui.QImage(self.resourceMapCache[name]["filename"])
			else:
				RemoteFile(name, self.onFileAvaiable)
				self.resourceMapCache[name] = None
		return None

	def onFileAvaiable(self, rFile: QtCore.QFile) -> None:
		size = None
		pic = QtGui.QPixmap(rFile.getFileName())
		size = pic.width(), pic.height()
		self.resourceMapCache[rFile.dlKey] = {
			"filename": rFile.getFileName(),
			"size": size
		}
		self.document().markContentsDirty(0, len(self.document().toPlainText()))

	# self.markContentsDirty( 0, len( self.getText() ) )

	def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
		"""
			Allow resizing inline Images using drag&drop
			Record the start of a potential drag&drop operation
		"""
		cursor = self.cursorForPosition(e.pos())
		txtFormat = cursor.charFormat()
		if txtFormat.objectType() == txtFormat.ImageObject:
			self._dragData = e.x(), e.y()
		super(ExtendedTextEdit, self).mousePressEvent(e)

	def mouseMoveEvent(self, e: QtGui.QMouseEvent) -> None:
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
						if fname in self.resourceMapCache and \
								self.resourceMapCache[fname]["size"] is not None:
							ratio = float(self.resourceMapCache[fname]["size"][0]) / float(
								self.resourceMapCache[fname]["size"][1])
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

	def mouseReleaseEvent(self, e: QtGui.QMouseEvent) -> None:
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

	def __init__(
			self,
			lang: str,
			parent: Union[None, QtWidgets.QWidget] = None):
		super(WebPage, self).__init__(parent)
		self.textToEdit = ""
		self.lang = lang

	@QtCore.pyqtSlot()
	def onEditorLoaded(self) -> None:
		logger.debug('onEditorLoaded called')
		self.sendText.emit(self.textToEdit, self.lang)

	@QtCore.pyqtSlot()
	def getHtmlCode(self) -> None:
		self.requestCode.emit()

	@QtCore.pyqtSlot(str)
	def transmitHtmlCodeToHost(self, data: str) -> None:
		self.receiveCodeCallback.emit(data)


class ExtObj(object):
	pass


class TextEdit(QtWidgets.QMainWindow):
	onDataChanged = QtCore.pyqtSignal((object,))

	def __init__(
			self,
			text: str,
			validHtml: Union[None, dict],
			lang: str,
			parent: Union[None, QtWidgets.QWidget] = None):
		super(TextEdit, self).__init__(parent)
		self.validHtml = validHtml
		self.ui = ExtObj()
		self.ui.centralWidget = QtWidgets.QWidget(self)
		self.setCentralWidget(self.ui.centralWidget)
		self.ui.centralWidget.setLayout(QtWidgets.QVBoxLayout())
		self.ui.textEdit = QWebEngineView()
		self.lang = lang
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
	def onPrepareSave(self) -> None:
		self.handler.getHtmlCode()

	@QtCore.pyqtSlot(str)
	def onFinishSave(self, data: Dict[str, Any]) -> None:
		logger.debug("onFinishSave TODO:: %r", data)
		self.onDataChanged.emit(data)
		event.emit('popWidget', self)

	def getBreadCrumb(self) -> Any:
		return (
			QtCore.QCoreApplication.translate("TextEditBone", "Text edit"),
			QtGui.QIcon(QtGui.QPixmap(":icons/actions/text-edit.png"))
		)


class ClickableWebView(QWebEngineView):
	clicked = QtCore.pyqtSignal()

	def __init__(self, parent: Union[QtWidgets.QWidget, None] = None):
		self.chromeCookieJar = None
		super(ClickableWebView, self).__init__(parent)

	def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
		super(ClickableWebView, self).mousePressEvent(ev)
		self.chromeCookieJar = self.page().profile().cookieStore()
		self.chromeCookieJar.cookieAdded.connect(self.onCookieAdded)
		self.chromeCookieJar.loadAllCookies()
		for cookie in nam.cookieJar().allCookies():
			self.chromeCookieJar.setCookie(cookie)
		self.clicked.emit()

	def onCookieAdded(self, cookie: Any) -> None:
		logger.error("WebWidget.onCookieAdded not yet handled properly: %r", cookie)


class TextEditBone(BoneEditInterface):
	def __init__(
			self,
			modulName: str,
			boneName: str,
			readOnly: bool,
			languages: Sequence[str] = None,
			plaintext: bool = False,
			validHtml: Union[dict, None] = None,
			*args: Any,
			**kwargs: Any):
		super(TextEditBone, self).__init__(modulName, boneName, readOnly)

		self.setLayout(QtWidgets.QVBoxLayout(self))
		self.languages = languages
		self.plaintext = plaintext
		self.validHtml = validHtml
		if self.languages:
			self.languageContainer: Dict[str, QtWidgets.QWidget] = dict()
			self.html: Dict[str, str] = dict()
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
				sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
				webView.setFixedHeight(200)
				webView.setSizePolicy(sizePolicy)
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

	@classmethod
	def fromSkelStructure(
			cls,
			moduleName: str,
			boneName: str,
			skelStructure: dict,
			**kwargs: Any) -> Any:
		readOnly = "readonly" in skelStructure[boneName] and skelStructure[boneName]["readonly"]
		languages = None
		plaintext = False
		validHtml = None
		if boneName in skelStructure:
			if "languages" in skelStructure[boneName]:
				languages = skelStructure[boneName]["languages"]

			if "plaintext" in skelStructure[boneName] and skelStructure[boneName]["plaintext"]:
				plaintext = True

			if "validHtml" in skelStructure[boneName]:
				validHtml = skelStructure[boneName]["validHtml"]

		return cls(
			moduleName,
			boneName,
			readOnly,
			languages=languages,
			plaintext=plaintext,
			validHtml=validHtml,
			**kwargs)

	def onTabLanguageChanged(self, lang: str) -> None:
		if lang in self.languageContainer:
			try:
				self.tabWidget.blockSignals(True)
				self.tabWidget.setCurrentWidget(self.languageContainer[lang])
				self.tabWidget.blockSignals(False)
			except RuntimeError as err:
				pass

	def onTabCurrentChanged(self, idx: int) -> None:
		wdg = self.tabWidget.widget(idx)
		for k, v in self.languageContainer.items():
			if v == wdg:
				event.emit("tabLanguageChanged", k)
				wdg.setFocus()
				return

	def sizeHint(self) -> QtCore.QSize:
		return QtCore.QSize(150, 150)

	def openEditor(self, *args: Any, **kwargs: Any) -> None:
		if self.languages:
			lang = self.languages[self.tabWidget.currentIndex()]
			if self.plaintext:
				editor = RawTextEdit(self.html[lang])
			else:
				if self.validHtml:
					editor = TextEdit(self.html[lang], self.validHtml, lang)
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

	def onSave(self, text: str) -> None:
		if self.languages:
			lang = self.languages[self.tabWidget.currentIndex()]
			self.html[lang] = str(text)
			self.languageContainer[lang].webView.setHtml(text)
		else:
			self.html = str(text)
			self.webView.setHtml(text)

	def unserialize(self, data: dict) -> None:
		if self.boneName not in data:
			return

		if self.languages and isinstance(data[self.boneName], dict):
			for lang in self.languages:
				if lang in data[self.boneName] and data[self.boneName][lang] is not None:
					self.html[lang] = data[self.boneName][lang].replace(
						"target=\"_blank\" href=\"",
						"href=\"!")
				else:
					self.html[lang] = ""
				self.languageContainer[lang].webView.setHtml(self.html[lang])
		elif not self.languages:
			self.html = str(data[self.boneName]).replace("target=\"_blank\" href=\"", "href=\"!") if (
					data and data.get(self.boneName)) else ""
			self.webView.setHtml(self.html)

	def serializeForPost(self) -> Dict[str, Any]:
		if self.languages:
			res = {}
			for lang in self.languages:
				res["%s.%s" % (self.boneName, lang)] = self.html[lang]
			return res
		else:
			return {self.boneName: self.html.replace("href=\"!", "target=\"_blank\" href=\"")}

	def serializeForDocument(self) -> dict:
		return self.serialize()

	def remove(self) -> None:
		pass


def CheckForTextBone(
		moduleName: str,
		boneName: str,
		skelStucture: Dict[str, Any][str, Any]) -> bool:
	return skelStucture[boneName]["type"] == "text"


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForTextBone, TextEditBone)
viewDelegateSelector.insert(2, CheckForTextBone, TextViewBoneDelegate)
