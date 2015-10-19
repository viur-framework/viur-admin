# -*- coding: utf-8 -*-
import html.parser

from html.entities import entitydefs

from PyQt5 import QtCore, QtGui, QtWidgets, QtWebKitWidgets

from viur_admin.event import event
from viur_admin.ui.rawtexteditUI import Ui_rawTextEditWindow
from viur_admin.ui.docEditlinkEditUI import Ui_LinkEdit
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector
from viur_admin.bones.file import FileBoneSelector
from viur_admin.bones.string import chooseLang
from viur_admin.bones.base import BaseViewBoneDelegate
from viur_admin.network import RemoteFile

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


class DocumentToHtml:
	"""
		Helper class which serializes a QDocument to *clean* html.
		Sadly, the default .toHtml() function produces lots of inline style (ie blue links)
		which arent appropriate in this case.
	"""

	headingMap = {87: 1,  # Font-weight of 700 (87) is a H1
	              75: 2,
	              62: 3
	              }

	def __init__(self):
		super(DocumentToHtml, self).__init__()
		self.res = ""
		self.openTags = []

	def serializeDocument(self, doc):
		"""
			Serializes the given QtDocument to clean html.
		"""
		self.res = ""
		self.openTags = []
		block = doc.firstBlock()
		while (block.isValid()):
			print("Processing block %s" % block.blockNumber())
			self.processBlock(block, doc)
			block = block.next()
		# Close any tag thats still open
		for t in self.openTags[:: -1]:
			self.res += "</%s>" % t[0]
		return (self.res)

	def processBlock(self, block, document):
		"""
			Processes one Block at a time
		"""
		if not self.isTagOpen("ul") and not self.isTagOpen("ol"):
			# Each block<=>paragraph (unless we have a list)
			alignment = ""
			if block.blockFormat().alignment() & QtCore.Qt.AlignRight:
				alignment = "right"
			elif block.blockFormat().alignment() & QtCore.Qt.AlignHCenter:
				alignment = "center"
			if alignment:
				self.openTag("p", tagArgs={"align": alignment})
			else:
				self.openTag("p")
		else:
			self.openTag("li")
		# Check if we need to open a list
		if block.textList() is not None:
			# Ensure ul, ol and li made it into the result
			if block.textList().itemNumber(block) == 0:
				if block.textList().format().style() in [QtGui.QTextListFormat.ListDisc,
				                                         QtGui.QTextListFormat.ListCircle,
				                                         QtGui.QTextListFormat.ListSquare]:
					self.openTag("ul")
				else:
					self.openTag("ol")
				self.openTag("li")
		fragmentIter = block.begin()
		while (not fragmentIter.atEnd()):
			fragment = fragmentIter.fragment()
			self.processFragment(fragment, block, document)
			fragmentIter += 1
		if block.textList() is not None:
			# Check if we need to close a list
			if block.textList().itemNumber(block) == block.textList().count() - 1:  # This was the last one
				self.closeTag("li")
				self.closeTag(("ul", "ol"))
		if not self.isTagOpen("ul") and not self.isTagOpen("ol"):
			# Each block<=>paragraph (unless we have a list)
			self.closeTag("p")
		else:
			self.closeTag("li")

	def processFragment(self, fragment, block, document):
		"""
			Processes one fragment in block "block" from
			document "document".
		"""
		print("ProcessFragment")
		txtFormat = fragment.charFormat()
		if txtFormat.objectType() == txtFormat.ImageObject:
			# FIXME: Why isnt txtFormat an instance of QtGui.QTextImageFormat in this case?
			imgSrc = txtFormat.property(txtFormat.ImageName)
			imgWidth = int(txtFormat.property(txtFormat.ImageWidth))
			imgHeight = int(txtFormat.property(txtFormat.ImageHeight))
			self.res += "<img src=\"%s\"" % imgSrc
			if imgWidth != -2 and imgWidth is not None:
				self.res += " width=\"%s\"" % imgWidth
			if imgHeight != -2 and imgHeight is not None:
				self.res += " height=\"%s\"" % imgHeight
			self.res += " />"
			return
		elif txtFormat.objectType() == txtFormat.TableObject:  # txtFormat.isTableFormat():
			txtFormat = txtFormat.toTableFormat()
			self.res += "<table>"
			for row in range(0, txtFormat.rows()):
				self.res += "<tr>"
				for col in range(0, txtFormat.columns()):
					cell = txtFormat.cellAt(row, col)
					# Prevent messing up row/col spans
					if cell.row() != row or cell.column() != col:
						continue
					self.res += "<td>"
			print("TABLE")
		# Check for hrefs
		if self.isTagOpen("a") and not txtFormat.anchorHref():  # This a has been closed recently
			self.closeTag("a")
		elif self.isTagOpen("a") and self.getLastInternalInfo("a") != txtFormat.anchorHref():  # The href has changed
			self.closeTag("a")
			self.openTag("a", tagArgs={"href": txtFormat.anchorHref()}, internalInfo=txtFormat.anchorHref())
		elif txtFormat.anchorHref():
			self.openTag("a", tagArgs={"href": txtFormat.anchorHref()}, internalInfo=txtFormat.anchorHref())
		if not self.isTagOpen("a"):  # Dont apply QTs style to hrefs
			# Check closing tags
			# Check for <i>
			if not txtFormat.fontItalic() and self.isTagOpen("i"):
				self.closeTag("i")
			# Check for <u>
			if not txtFormat.fontUnderline() and self.isTagOpen("u"):
				self.closeTag("u")
			# Check for <strong>
			if not txtFormat.font().bold() and self.isTagOpen("strong"):
				self.closeTag("strong")
			if txtFormat.fontWeight() in self.headingMap.keys() and self.isTagOpen(("h1", "h2", "h3")):
				self.closeTag(("h1", "h2", "h3"))
			# Check for opening tags
			# Check for <i>
			color = txtFormat.foreground().color().toRgb()
			if txtFormat.fontWeight() in self.headingMap.keys() and all(
					[x == 1 for x in [color.red(), color.blue(), color.green()]]):
				self.openTag("h%s" % self.headingMap[txtFormat.fontWeight()])
			else:
				if txtFormat.fontItalic() and not self.isTagOpen("i"):
					self.openTag("i")
				# Check for <u>
				if txtFormat.fontUnderline() and not self.isTagOpen("u"):
					self.openTag("u")
				# Check for <strong>
				if txtFormat.font().bold() and not self.isTagOpen("strong"):
					self.openTag("strong")
				# Check for font color
				color = txtFormat.foreground().color().toRgb()
				colorStr = self.colorToHtml(color)
				if color.red() or color.green() or color.blue():  # It's not black
					if not self.isTagOpen("font") or self.getLastInternalInfo("font") != colorStr:
						self.openTag("font", tagArgs={"color": colorStr}, internalInfo=colorStr)
				elif self.isTagOpen("font") and self.getLastInternalInfo(
						"font") != colorStr:  # Its black and doesn't equal the last open color
					self.openTag("font", tagArgs={"color": colorStr}, internalInfo=colorStr)
		self.res += fragment.text()

	def colorToHtml(self, color):
		"""
			Returns an html-representation of the given QColor
		"""
		colorStrRed = hex(color.red())[2:]
		if len(colorStrRed) == 1:
			colorStrRed = "0" + colorStrRed
		colorStrGreen = hex(color.green())[2:]
		if len(colorStrGreen) == 1:
			colorStrGreen = "0" + colorStrGreen
		colorStrBlue = hex(color.blue())[2:]
		if len(colorStrBlue) == 1:
			colorStrBlue = "0" + colorStrBlue
		return ("#%s%s%s" % (colorStrRed, colorStrGreen, colorStrBlue))

	def openTag(self, tag, tagArgs=None, internalInfo=None, hasClosingTag=True):
		"""
			Opens a new tag named tag.
			args is a string of additional params
		"""
		print("open tag %s" % tag)
		strArgs = ""
		if tagArgs is not None:
			strArgs = " ".join(["%s=\"%s\"" % (k, v) for k, v in tagArgs.items()])
		if strArgs:
			self.res += "<%s %s>" % (tag, strArgs)
		else:
			self.res += "<%s>" % tag
		self.openTags.append((tag, internalInfo))

	def isTagOpen(self, tag):
		"""
			Returns true, if the given html tag is currently opened.
		"""
		if isinstance(tag, tuple):
			return (any([t in [x[0] for x in self.openTags] for t in tag]))
		return (tag in [x[0] for x in self.openTags])

	def closeTag(self, tag):
		"""
			Recursively closes all tags until we reach tag.
			"tag" is also closed.
			If tag is a tuple, it closes the first tag found matching one element in that tuple
		"""
		print("Closing %s" % str(tag))
		assert self.isTagOpen(tag)
		deletedTags = 0
		for t in self.openTags[:: -1]:
			deletedTags += 1
			self.res += "</%s>" % t[0]
			if (isinstance(tag, str) and t[0] == tag) or (isinstance(tag, tuple) and t[0] in tag):
				break
		self.openTags = self.openTags[: -deletedTags]

	def getLastInternalInfo(self, tag):
		"""
			Returns the internal information stored with this tag.
			If this tag is open multiple times, the last one is returned.
		"""
		assert self.isTagOpen(tag)
		for t in self.openTags[:: -1]:
			if t[0] == tag:
				return (t[1])


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
						if fname in self.ressourceMapCache.keys() and self.ressourceMapCache[fname]["size"] is not None:
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
							helper.setPosition(fragment.position() + fragment.length(), helper.KeepAnchor)
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


class ExtObj(object):
	pass


class TextEdit(QtWidgets.QMainWindow):
	onDataChanged = QtCore.pyqtSignal((object,))

	def __init__(self, text, validHtml, parent=None):
		super(TextEdit, self).__init__(parent)
		self.validHtml = validHtml
		self.serializer = HtmlSerializer(validHtml)
		self.ui = ExtObj()  # Ui_textEditWindow()
		# self.ui.setupUi( self )
		self.ui.centralWidget = QtWidgets.QWidget(self)
		self.setCentralWidget(self.ui.centralWidget)
		self.ui.centralWidget.setLayout(QtWidgets.QVBoxLayout())
		self.ui.textEdit = ExtendedTextEdit(self.ui.centralWidget)
		self.ui.centralWidget.layout().addWidget(self.ui.textEdit)
		self.ui.btnSave = QtWidgets.QPushButton(QtGui.QIcon(":icons/actions/accept.svg"),
		                                        QtCore.QCoreApplication.translate("TextEdit", "Apply"),
		                                        self.ui.centralWidget)
		self.ui.centralWidget.layout().addWidget(self.ui.btnSave)
		self.linkEditor = None
		self.setToolButtonStyle(QtCore.Qt.ToolButtonFollowStyle)
		self.setupEditActions()
		self.setupInsertActions()
		self.setupTextActions()
		self.ui.textEdit.currentCharFormatChanged.connect(self.currentCharFormatChanged)
		self.ui.textEdit.cursorPositionChanged.connect(self.cursorPositionChanged)
		self.ui.textEdit.setFocus()
		self.fontChanged(self.ui.textEdit.font())
		self.colorChanged(self.ui.textEdit.textColor())
		self.alignmentChanged(self.ui.textEdit.alignment())
		self.ui.textEdit.document().undoAvailable.connect(self.actionUndo.setEnabled)
		self.ui.textEdit.document().redoAvailable.connect(self.actionRedo.setEnabled)
		self.actionUndo.setEnabled(self.ui.textEdit.document().isUndoAvailable())
		self.actionRedo.setEnabled(self.ui.textEdit.document().isRedoAvailable())
		self.actionUndo.triggered.connect(self.ui.textEdit.undo)
		self.actionRedo.triggered.connect(self.ui.textEdit.redo)
		self.actionCut.setEnabled(False)
		self.actionCopy.setEnabled(False)
		self.actionCut.triggered.connect(self.ui.textEdit.cut)
		self.actionCopy.triggered.connect(self.ui.textEdit.copy)
		self.actionPaste.triggered.connect(self.ui.textEdit.paste)
		self.ui.textEdit.copyAvailable.connect(self.actionCut.setEnabled)
		self.ui.textEdit.copyAvailable.connect(self.actionCopy.setEnabled)
		QtWidgets.QApplication.clipboard().dataChanged.connect(self.clipboardDataChanged)
		self.ui.textEdit.setHtml(text)
		# self.saveCallback = saveCallback
		self.ui.btnSave.released.connect(self.onBtnSaveReleased)

	# self.ui.textEdit.mousePressEvent = self.on_textEdit_mousePressEvent  # FIXME: !!!
	# self.ui.textEdit.insertFromMimeData = self.on_textEdit_insertFromMimeData # FIXME: !!!


	def onTextEditInsertFromMimeData(self, source):
		QtGui.QTextEdit.insertFromMimeData(self.ui.textEdit, source)
		html = self.ui.textEdit.toHtml()
		start = html.find(">", html.find("<body")) + 1
		html = html[start: html.rfind("</body>")]
		html = html.replace("""text-indent:0px;"></p>""", """text-indent:0px;">&nbsp;</p>""")
		self.ui.textEdit.setText(self.serializer.santinize(html))

	def openLinkEditor(self, fragment):
		if self.linkEditor:
			self.linkEditor.deleteLater()

		self.linkEditor = QtGui.QDockWidget(QtCore.QCoreApplication.translate("DocumentEditBone", "Edit link"), self)
		self.linkEditor.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)
		self.linkEditor.setFeatures(QtGui.QDockWidget.NoDockWidgetFeatures)
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
						cursor.movePosition(QtGui.QTextCursor.NextCharacter, QtGui.QTextCursor.KeepAnchor)
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
		        QtGui.QIcon(QtGui.QPixmap(":icons/actions/text-edit.svg")))

	def setupEditActions(self):
		tb = QtWidgets.QToolBar(self)
		tb.setWindowTitle("Edit Actions")
		self.addToolBar(tb)

		self.actionUndo = QtWidgets.QAction(QtGui.QIcon(":icons/actions/undo.svg"), "&Undo", self,
		                                    shortcut=QtGui.QKeySequence.Undo)
		tb.addAction(self.actionUndo)
		self.actionRedo = QtWidgets.QAction(QtGui.QIcon(":icons/actions/redo.svg"),
		                                    "&Redo", self, priority=QtWidgets.QAction.LowPriority,
		                                    shortcut=QtGui.QKeySequence.Redo)
		tb.addAction(self.actionRedo)

		self.actionCut = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/cut.png"),
		                                   "Cu&t", self, priority=QtWidgets.QAction.LowPriority,
		                                   shortcut=QtGui.QKeySequence.Cut)
		tb.addAction(self.actionCut)

		self.actionCopy = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/copy.png"),
		                                    "&Copy", self, priority=QtWidgets.QAction.LowPriority,
		                                    shortcut=QtGui.QKeySequence.Copy)
		tb.addAction(self.actionCopy)
		self.actionPaste = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/paste.png"),
		                                     "&Paste", self, priority=QtWidgets.QAction.LowPriority,
		                                     shortcut=QtGui.QKeySequence.Paste,
		                                     enabled=(len(QtWidgets.QApplication.clipboard().text()) != 0))
		tb.addAction(self.actionPaste)

	def setupInsertActions(self):
		if "a" in self.validHtml["validTags"] or "img" in self.validHtml["validTags"]:
			tb = QtWidgets.QToolBar(self)
			tb.setWindowTitle("Insert Actions")
			self.addToolBar(tb)
		if "a" in self.validHtml["validTags"]:
			self.actionInsertLink = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/link.png"), "&Link", self)
			tb.addAction(self.actionInsertLink)
			self.actionInsertLink.triggered.connect(self.insertLink)
		if "img" in self.validHtml["validTags"]:
			self.actionInsertImage = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/image_add.png"), "&Image", self)
			tb.addAction(self.actionInsertImage)
			self.actionInsertImage.triggered.connect(self.insertImage)

		if any([x in self.validHtml["validTags"] for x in ["h1", "h2", "h3"]]):
			tb = QtWidgets.QToolBar(self)
			tb.setWindowTitle("Insert Actions")
			self.addToolBar(tb)

		if "h1" in self.validHtml["validTags"]:
			self.actionInsertH1 = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/headline1.svg"), "&H1", self)
			tb.addAction(self.actionInsertH1)
			self.actionInsertH1.triggered.connect(self.insertH1)

		if "h2" in self.validHtml["validTags"]:
			self.actionInsertH2 = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/headline2.svg"), "&H2", self)
			tb.addAction(self.actionInsertH2)
			self.actionInsertH2.triggered.connect(self.insertH2)

		if "h3" in self.validHtml["validTags"]:
			self.actionInsertH3 = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/headline3.svg"), "&H3", self)
			tb.addAction(self.actionInsertH3)
			self.actionInsertH3.triggered.connect(self.insertH3)

		self.actionClearFormat = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/clear-format.png"), "&Clear", self)
		tb.addAction(self.actionClearFormat)
		self.actionClearFormat.triggered.connect(self.clearFormat)

	# self.actionInsertTable = QtWidgets.QAction(QtGui.QIcon(rsrcPath + '/link.png'),"&Table", self)
	# tb.addAction(self.actionInsertTable)
	# self.actionInsertTable.triggered.connect(self.insertTable)


	def setupTextActions(self):
		tb = QtWidgets.QToolBar(self)
		tb.setWindowTitle("Format Actions")
		self.addToolBar(tb)
		if "b" in self.validHtml["validTags"]:
			self.actionTextBold = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/bold.png"),
			                                        "&Bold", self, priority=QtWidgets.QAction.LowPriority,
			                                        shortcut=QtCore.Qt.CTRL + QtCore.Qt.Key_B,
			                                        triggered=self.textBold, checkable=True)
			bold = QtGui.QFont()
			bold.setBold(True)
			self.actionTextBold.setFont(bold)
			tb.addAction(self.actionTextBold)

		if "i" in self.validHtml["validTags"]:
			self.actionTextItalic = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/italic.png"),
			                                          "&Italic", self, priority=QtWidgets.QAction.LowPriority,
			                                          shortcut=QtCore.Qt.CTRL + QtCore.Qt.Key_I,
			                                          triggered=self.textItalic, checkable=True)
			italic = QtGui.QFont()
			italic.setItalic(True)
			self.actionTextItalic.setFont(italic)
			tb.addAction(self.actionTextItalic)

		if "u" in self.validHtml["validTags"]:
			self.actionTextUnderline = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/underline.png"),
			                                             "&Underline", self, priority=QtWidgets.QAction.LowPriority,
			                                             shortcut=QtCore.Qt.CTRL + QtCore.Qt.Key_U,
			                                             triggered=self.textUnderline, checkable=True)
			underline = QtGui.QFont()
			underline.setUnderline(True)
			self.actionTextUnderline.setFont(underline)
			tb.addAction(self.actionTextUnderline)

		if "p" in self.validHtml["validAttrs"].keys() and "align" in self.validHtml["validAttrs"]["p"]:
			grp = QtWidgets.QActionGroup(self)
			grp.triggered.connect(self.textAlign)
			# Make sure the alignLeft is always left of the alignRight.
			if QtWidgets.QApplication.isLeftToRight():
				self.actionAlignLeft = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/alignleft.png"),
				                                         "&Left", grp)
				self.actionAlignCenter = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/aligncenter.png"),
				                                           "C&enter", grp)
				self.actionAlignRight = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/alignright.png"),
				                                          "&Right", grp)
			else:
				self.actionAlignRight = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/alignright.png"),
				                                          "&Right", grp)
				self.actionAlignCenter = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/aligncenter.png"),
				                                           "C&enter", grp)
				self.actionAlignLeft = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/alignleft.png"),
				                                         "&Left", grp)

			self.actionAlignLeft.setShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_L)
			self.actionAlignLeft.setCheckable(True)
			self.actionAlignLeft.setPriority(QtWidgets.QAction.LowPriority)

			self.actionAlignCenter.setShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_E)
			self.actionAlignCenter.setCheckable(True)
			self.actionAlignCenter.setPriority(QtWidgets.QAction.LowPriority)

			self.actionAlignRight.setShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_R)
			self.actionAlignRight.setCheckable(True)
			self.actionAlignRight.setPriority(QtWidgets.QAction.LowPriority)

			tb.addActions(grp.actions())

		if "font" in self.validHtml["validAttrs"].keys() and "color" in self.validHtml["validAttrs"]["font"]:
			pix = QtGui.QPixmap(16, 16)
			pix.fill(QtCore.Qt.black)
			self.actionTextColor = QtWidgets.QAction(QtGui.QIcon(pix), "&Color...",
			                                         self, triggered=self.textColor)
			tb.addAction(self.actionTextColor)

		if "ul" in self.validHtml["validTags"]:
			self.actionBulletList = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/bullet.png"), "Bullet",
			                                          self,
			                                          triggered=self.onBulletList)
			tb.addAction(self.actionBulletList)

		if "ol" in self.validHtml["validTags"]:
			self.actionNumberedList = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/numbered.png"), "Numbered",
			                                            self,
			                                            triggered=self.onNumberedList)
			tb.addAction(self.actionNumberedList)

	def save(self, *args, **kwargs):
		html = DocumentToHtml().serializeDocument(self.ui.textEdit.document())
		print(html)
		self.onDataChanged.emit(html)
		event.emit("popWidget", self)

	def textBold(self):
		fmt = QtGui.QTextCharFormat()
		fmt.setFontWeight(self.actionTextBold.isChecked() and QtGui.QFont.Bold or QtGui.QFont.Normal)
		self.mergeFormatOnWordOrSelection(fmt)

	def textUnderline(self):
		fmt = QtGui.QTextCharFormat()
		fmt.setFontUnderline(self.actionTextUnderline.isChecked())
		self.mergeFormatOnWordOrSelection(fmt)

	def textItalic(self):
		fmt = QtGui.QTextCharFormat()
		fmt.setFontItalic(self.actionTextItalic.isChecked())
		self.mergeFormatOnWordOrSelection(fmt)

	def textFamily(self, family):
		fmt = QtGui.QTextCharFormat()
		fmt.setFontFamily(family)
		self.mergeFormatOnWordOrSelection(fmt)

	def textSize(self, pointSize):
		pointSize = float(pointSize)
		if pointSize > 0:
			fmt = QtGui.QTextCharFormat()
			fmt.setFontPointSize(pointSize)
			self.mergeFormatOnWordOrSelection(fmt)

	def onBulletList(self, *args, **kwargs):
		cursor = self.ui.textEdit.textCursor()
		style = QtGui.QTextListFormat.ListDisc
		cursor.beginEditBlock()
		blockFmt = cursor.blockFormat()
		listFmt = QtGui.QTextListFormat()
		if cursor.currentList():
			listFmt = cursor.currentList().format()
			listFmt.setIndent(listFmt.indent() + 1)
		else:
			listFmt.setIndent(blockFmt.indent() + 1)
			blockFmt.setIndent(0)
			cursor.setBlockFormat(blockFmt)
		listFmt.setStyle(style)
		cursor.createList(listFmt)
		cursor.endEditBlock()

	def onNumberedList(self, *args, **kwargs):
		cursor = self.ui.textEdit.textCursor()
		style = QtGui.QTextListFormat.ListDecimal
		cursor.beginEditBlock()
		blockFmt = cursor.blockFormat()
		listFmt = QtGui.QTextListFormat()
		if cursor.currentList():
			listFmt = cursor.currentList().format()
			listFmt.setIndent(listFmt.indent() + 1)
		else:
			listFmt.setIndent(blockFmt.indent() + 1)
			blockFmt.setIndent(0)
			cursor.setBlockFormat(blockFmt)
		listFmt.setStyle(style)
		cursor.createList(listFmt)
		cursor.endEditBlock()

	def textColor(self):
		col = QtGui.QColorDialog.getColor(self.ui.textEdit.textColor(), self)
		if not col.isValid():
			return

		fmt = QtGui.QTextCharFormat()
		fmt.setForeground(col)
		self.mergeFormatOnWordOrSelection(fmt)
		self.colorChanged(col)

	def insertLink(self, *args, **kwargs):
		(dest, okay) = QtGui.QInputDialog.getText(self,
		                                          QtCore.QCoreApplication.translate("TextEditBone", "Specify target"),
		                                          QtCore.QCoreApplication.translate("TextEditBone", "Link target:"))
		if not okay or not dest:
			return
		cursor = self.ui.textEdit.textCursor()
		if not cursor.hasSelection():
			cursor.select(QtGui.QTextCursor.WordUnderCursor)
		txt = cursor.selectedText()
		self.ui.textEdit.insertHtml("<a href=\"%s\" target=\"_blank\">%s</a>" % (dest, txt))

	def insertHeading(self, lvl):
		assert 0 < lvl < 7
		cursor = self.ui.textEdit.textCursor()
		if not cursor.hasSelection():
			cursor.select(QtGui.QTextCursor.WordUnderCursor)
		txt = cursor.selectedText()
		cursor.insertHtml(
			"<h%s>%s</h%s> " % (lvl, txt, lvl))  # The tailing whitespace is nessesary to reset the style afterwards

	def insertH1(self, *args, **kwargs):
		self.insertHeading(1)

	def insertH2(self, *args, **kwargs):
		self.insertHeading(2)

	def insertH3(self, *args, **kwargs):
		self.insertHeading(3)

	def insertImage(self, *args, **kwargs):
		d = FileBoneSelector("-", "file", False, "file", None)
		d.selectionChanged.connect(self.onFileSelected)

	def insertTable(self, *args, **kwargs):
		cursor = self.ui.textEdit.textCursor()
		cursor.insertHtml(
			"<br /><table border=\"1\"><thead><tr><td>a</td><td>b</td></tr></thead><tr><td>c</td><td>d</td></tr><tr><td>e</td><td>f</td></tr></table><br />")

	def onFileSelected(self, selection):
		if selection:
			w, h = 50, 50
			try:
				tmp = RemoteFile(selection[0]["dlkey"])
				fname = tmp.getFileName()
				if fname:  # Seems this is allready cached
					pic = QtGui.QPixmap(fname)
					w, h = pic.width(), pic.height()
			except:
				pass
			cursor = self.ui.textEdit.textCursor()  # width=\"75\" height=\"50\"
			cursor.insertHtml("<img src=\"/file/download/%s\" width=\"%s\" height=\"%s\" >" % (
				selection[0]["dlkey"], w, h))  # selection[0]["id"],

	def textAlign(self, action):
		if action == self.actionAlignLeft:
			self.ui.textEdit.setAlignment(
				QtCore.Qt.AlignLeft | QtCore.Qt.AlignAbsolute)
		elif action == self.actionAlignCenter:
			self.ui.textEdit.setAlignment(QtCore.Qt.AlignHCenter)
		elif action == self.actionAlignRight:
			self.ui.textEdit.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignAbsolute)

	def currentCharFormatChanged(self, format):
		self.fontChanged(format.font())
		print(format.fontWeight())
		self.colorChanged(format.foreground().color())

	def cursorPositionChanged(self):
		self.alignmentChanged(self.ui.textEdit.alignment())
		cursor = self.ui.textEdit.textCursor()
		block = cursor.block()
		iterator = block.begin()
		while (not iterator.atEnd()):
			fragment = iterator.fragment()
			if fragment.position() + fragment.length() < cursor.position():
				iterator += 1
				continue
			if fragment.charFormat().anchorHref():
				if self.linkEditor:
					if self.linkEditor.fragmentPosition == fragment.position():  # The editor for this link is allready open
						return
					self.saveLinkEditor()
				self.openLinkEditor(fragment)
			elif self.linkEditor:
				self.saveLinkEditor()
				self.linkEditor.deleteLater()
				self.linkEditor = None
			break

	def clipboardDataChanged(self):
		if "actionPaste" in dir(self):
			self.actionPaste.setEnabled(len(QtWidgets.QApplication.clipboard().text()) != 0)

	def mergeFormatOnWordOrSelection(self, format):
		cursor = self.ui.textEdit.textCursor()
		if not cursor.hasSelection():
			cursor.select(QtGui.QTextCursor.WordUnderCursor)
		cursor.mergeCharFormat(format)

		self.ui.textEdit.mergeCurrentCharFormat(format)

	def fontChanged(self, font):
		if "actionTextBold" in dir(self):
			self.actionTextBold.setChecked(font.bold())
		if "actionTextItalic" in dir(self):
			self.actionTextItalic.setChecked(font.italic())
		if "actionTextUnderline" in dir(self):
			self.actionTextUnderline.setChecked(font.underline())

	def clearFormat(self, *args, **kwargs):
		"""
			Clears headings etc. applied the the current selection.
			FIXME: Bad hack...
		"""
		cursorpos = self.ui.textEdit.textCursor().position()
		fmt = QtGui.QTextCharFormat()
		fmt.setFontWeight(QtGui.QFont.Normal)
		fmt.setFontUnderline(False)
		fmt.setFontItalic(False)
		fmt.setForeground(QtGui.QColor("black"))
		fmt.setFont(QtGui.QFont("Courier", 9))
		self.mergeFormatOnWordOrSelection(fmt)
		block = self.ui.textEdit.document().begin()
		while (block.isValid()):
			if block.contains(cursorpos):
				cursor = QtGui.QTextCursor(block)
				fmt = block.blockFormat()
				fmt.setTopMargin(0)
				fmt.setBottomMargin(0)
				cursor.setBlockFormat(QtGui.QTextBlockFormat())
				break
			block = block.next()
		self.ui.textEdit.setHtml(DocumentToHtml().serializeDocument(
			self.ui.textEdit.document()))  # Ive no cloue how to to this cleanly without reloading the whole text

	def colorChanged(self, color):
		if "actionTextColor" in dir(self):
			pix = QtGui.QPixmap(16, 16)
			pix.fill(color)
			self.actionTextColor.setIcon(QtGui.QIcon(pix))

	def alignmentChanged(self, alignment):
		if alignment & QtCore.Qt.AlignLeft:
			if "actionAlignLeft" in dir(self):
				self.actionAlignLeft.setChecked(True)
		elif alignment & QtCore.Qt.AlignHCenter:
			if "actionAlignCenter" in dir(self):
				self.actionAlignCenter.setChecked(True)
		elif alignment & QtCore.Qt.AlignRight:
			if "actionAlignRight" in dir(self):
				self.actionAlignRight.setChecked(True)

	def onBtnSaveReleased(self):
		print(self.ui.textEdit.toHtml())
		self.save()

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
				if not tag in self.validHtml["validAttrs"].keys() or not k in self.validHtml["validAttrs"][tag]:
					continue
				if k.lower()[0:2] != 'on' and v.lower()[0:10] != 'javascript':
					self.result = '%s %s="%s"' % (self.result, k, v)
			if "style" in [k for (k, v) in attrs]:
				syleRes = {}
				styles = [v for (k, v) in attrs if k == "style"][0].split(";")
				for s in styles:
					style = s[: s.find(":")].strip()
					value = s[s.find(":") + 1:].strip()
					if style in self.validHtml["validStyles"] and not any([(x in value) for x in ["\"", ":", ";"]]):
						syleRes[style] = value
				if len(syleRes.keys()):
					self.result += " style=\"%s\"" % "; ".join([("%s: %s" % (k, v)) for (k, v) in syleRes.items()])
			if tag in self.validHtml["singleTags"]:
				self.result = self.result + ' />'
			else:
				self.result = self.result + '>'
				self.openTagsList.insert(0, tag)

	def handle_endtag(self, tag):
		if self.validHtml and tag in self.openTagsList:
			for endTag in self.openTagsList[:]:  # Close all currently open Tags until we reach the current one
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

class ClickableWebView(QtWebKitWidgets.QWebView):
	clicked = QtCore.pyqtSignal()

	def mousePressEvent(self, ev):
		super(ClickableWebView, self).mousePressEvent(ev)
		self.clicked.emit()


class TextEditBone(QtWidgets.QWidget):
	def __init__(self, modulName, boneName, readOnly, languages=None, plaintext=False, validHtml=None, editWidget=None, *args, **kwargs):
		super(TextEditBone, self).__init__(*args, **kwargs)
		self.editWidget = editWidget
		self.modulName = modulName
		self.boneName = boneName
		self.readOnly = readOnly
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
			TextEditBone(modulName, boneName, readOnly, languages=languages, plaintext=plaintext, validHtml=validHtml, **kwargs))

	def onTabLanguageChanged(self, lang):
		if lang in self.languageContainer.keys():
			self.tabWidget.blockSignals(True)
			self.tabWidget.setCurrentWidget(self.languageContainer[lang])
			self.tabWidget.blockSignals(False)

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
		if not self.boneName in data.keys():
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
