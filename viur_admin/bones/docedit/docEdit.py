#!/usr/bin/python3
# -*- coding: utf-8 -*-


import html.parser
import re
import string

from PyQt5 import QtGui, QtCore, QtWebKit, QtWidgets

from viur_admin.ui.docEditUI import Ui_DocEdit
from viur_admin.ui.docEditfileEditUI import Ui_Form
from viur_admin.ui.docEditlinkEditUI import Ui_LinkEdit
from viur_admin.ui.createtableUI import Ui_DialogCreateTable
from viur_admin.event import event
from viur_admin.utils import RegisterQueue, Overlay
from viur_admin.event import event


# from handler.file import FileUploader
from viur_admin.widgets.edit import EditWidget  # FIXME: !!
import urllib.parse, os, os.path, sys
from viur_admin.network import NetworkService
import json

##################### Rich Text Edit #########################
rsrcPath = ":icons/actions/text"


class TextEdit(QtWidgets.QMainWindow):
	def __init__(self, saveCallback, parent=None):
		super(TextEdit, self).__init__(parent)
		self.setWindowIcon(QtWidgets.QIcon('icons/actions/document-edit.png'))
		self.setToolButtonStyle(QtCore.Qt.ToolButtonFollowStyle)
		self.setupEditActions()
		self.setupInsertActions()
		self.setupTextActions()

		self.textEdit = QtWidgets.QTextEdit(self)
		self.textEdit.currentCharFormatChanged.connect(self.currentCharFormatChanged)
		self.textEdit.cursorPositionChanged.connect(self.cursorPositionChanged)

		self.setCentralWidget(self.textEdit)

		# self.layout.addChild( self.textEdit )
		self.textEdit.setFocus()
		self.fontChanged(self.textEdit.font())
		self.colorChanged(self.textEdit.textColor())
		self.alignmentChanged(self.textEdit.alignment())
		self.textEdit.document().modificationChanged.connect(self.setWindowModified)
		self.textEdit.document().undoAvailable.connect(self.actionUndo.setEnabled)
		self.textEdit.document().redoAvailable.connect(self.actionRedo.setEnabled)
		self.setWindowModified(self.textEdit.document().isModified())
		self.actionUndo.setEnabled(self.textEdit.document().isUndoAvailable())
		self.actionRedo.setEnabled(self.textEdit.document().isRedoAvailable())
		self.actionUndo.triggered.connect(self.textEdit.undo)
		self.actionRedo.triggered.connect(self.textEdit.redo)
		self.actionCut.setEnabled(False)
		self.actionCopy.setEnabled(False)
		self.actionCut.triggered.connect(self.textEdit.cut)
		self.actionCopy.triggered.connect(self.textEdit.copy)
		self.actionPaste.triggered.connect(self.textEdit.paste)
		self.textEdit.copyAvailable.connect(self.actionCut.setEnabled)
		self.textEdit.copyAvailable.connect(self.actionCopy.setEnabled)
		QtGui.QApplication.clipboard().dataChanged.connect(self.clipboardDataChanged)
		# self.actionInsertImage.triggered.connect(self.insertImage)
		# self.actionInsertTable.triggered.connect(self.insertTable)
		self.actionInsertLink.triggered.connect(self.insertLink)
		# self.textEdit.contextMenuEvent = self.on_textEdit_contextMenuEvent
		self.textEdit.mousePressEvent = self.on_textEdit_mousePressEvent
		# self.textEdit.loadResource = self.on_textEdit_loadResource
		self.saveCallback = saveCallback
		self.linkEditor = None

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
		href = self.linkEditor.ui.editHref.text()
		cursor = self.textEdit.textCursor()
		block = self.textEdit.document().findBlock(self.linkEditor.fragmentPosition)
		iterator = block.begin()
		foundStart = False
		foundEnd = False
		oldHref = ""
		while (not iterator.atEnd()):
			fragment = iterator.fragment()
			if foundStart:
				foundEnd = True
				if oldHref != fragment.charFormat().anchorHref():
					print("p3")
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

	def on_textEdit_mousePressEvent(self, event):
		if self.linkEditor:
			self.saveLinkEditor()
		QtGui.QTextEdit.mousePressEvent(self.textEdit, event)
		if not self.textEdit.anchorAt(event.pos()):
			if self.linkEditor:
				self.linkEditor.deleteLater()
				self.linkEditor = None
			return
		cursor = self.textEdit.textCursor()
		block = cursor.block()
		iterator = block.begin()
		while (not iterator.atEnd()):
			fragment = iterator.fragment()
			if fragment.charFormat().anchorHref():
				self.openLinkEditor(fragment)
			iterator += 1

	def o2n_textEdit_contextMenuEvent(self, event):
		menu = self.textEdit.createStandardContextMenu()
		if self.textEdit.textCursor().currentTable():
			tableMenu = menu.addMenu(QtCore.QCoreApplication.translate("DocumentEditBone", "Table"))
			insertMenu = tableMenu.addMenu(QtCore.QCoreApplication.translate("DocumentEditBone", "Insert"))
			insertRowBefore = insertMenu.addAction(QtCore.QCoreApplication.translate("DocumentEditBone", "Row before"))
			insertRowAfter = insertMenu.addAction(QtCore.QCoreApplication.translate("DocumentEditBone", "Row after"))
			insertColumBefore = insertMenu.addAction(
				QtCore.QCoreApplication.translate("DocumentEditBone", "Column before"))
			insertColumAfter = insertMenu.addAction(
				QtCore.QCoreApplication.translate("DocumentEditBone", "Column after"))
			removeMenu = tableMenu.addMenu(QtCore.QCoreApplication.translate("DocumentEditBone", "Remove"))
			removeRow = removeMenu.addAction(QtCore.QCoreApplication.translate("DocumentEditBone", "This row"))
			removeColum = removeMenu.addAction(QtCore.QCoreApplication.translate("DocumentEditBone", "This column"))
			# Fixme: Broken atm
			# cellMenu = tableMenu.addMenu("Zelle")
			# mergeRight = cellMenu.addAction("Mit rechter Zelle verschmelzen")
			# mergeBottom = cellMenu.addAction("Mit unterer Zelle verschmelzen")
			# splitRight = cellMenu.addAction("Horizontal trennen")
			# splitBottom = cellMenu.addAction("Vertikal trennen")
			action = menu.exec_(event.globalPos())
			currentTable = self.textEdit.textCursor().currentTable()
			currentCell = currentTable.cellAt(self.textEdit.textCursor())
			if action == insertRowBefore:
				currentTable.insertRows(currentCell.row(), 1)
			elif action == insertRowAfter:
				currentTable.insertRows(currentCell.row() + 1, 1)
			elif action == insertColumBefore:
				currentTable.insertColumns(currentCell.column(), 1)
			elif action == insertColumAfter:
				currentTable.insertColumns(currentCell.column() + 1, 1)
			elif action == removeRow:
				currentTable.removeRows(currentCell.row(), 1)
			elif action == removeColum:
				currentTable.removeColumns(currentCell.column(), 1)
				# elif action == mergeRight:
				#	currentTable.mergeCells( currentCell.row(), currentCell.column(), 0, 1 )
				# elif action == mergeBottom:
				#	currentTable.mergeCells( currentCell.row(), currentCell.column(), 1, 1 )
				# elif action == splitRight:
				#	currentTable.splitCell( currentCell.row(), currentCell.column(), 0, 1 )
				# elif action == splitBottom:
				#	currentTable.splitCell( currentCell.row(), currentCell.column(), 1, 1 )
		else:
			menu.exec_(event.globalPos())

	def setupEditActions(self):
		tb = QtWidgets.QToolBar(self)
		tb.setWindowTitle("Edit Actions")
		self.addToolBar(tb)

		self.actionUndo = QtWidgets.QAction(QtGui.QIcon(':icons/actions/undo.svg'), "&Undo", self,
		                                    shortcut=QtGui.QKeySequence.Undo)
		tb.addAction(self.actionUndo)
		self.actionRedo = QtWidgets.QAction(QtGui.QIcon(':icons/actions/redo.svg'),
		                                    "&Redo", self, priority=QtWidgets.QAction.LowPriority,
		                                    shortcut=QtGui.QKeySequence.Redo)
		tb.addAction(self.actionRedo)

		self.actionCut = QtWidgets.QAction(QtGui.QIcon(":icons/actions/text/cut.png"),
		                                   "Cu&t", self, priority=QtWidgets.QAction.LowPriority,
		                                   shortcut=QtGui.QKeySequence.Cut)
		tb.addAction(self.actionCut)

		self.actionCopy = QtWidgets.QAction(QtGui.QIcon(':icons/actions/text/copy.png'),
		                                    "&Copy", self, priority=QtWidgets.QAction.LowPriority,
		                                    shortcut=QtGui.QKeySequence.Copy)
		tb.addAction(self.actionCopy)
		self.actionPaste = QtWidgets.QAction(QtGui.QIcon(':icons/actions/text/paste.png'),
		                                     "&Paste", self, priority=QtWidgets.QAction.LowPriority,
		                                     shortcut=QtGui.QKeySequence.Paste,
		                                     enabled=(len(QtGui.QApplication.clipboard().text()) != 0))
		tb.addAction(self.actionPaste)

	def setupInsertActions(self):
		tb = QtWidgets.QToolBar(self)
		tb.setWindowTitle("Insert Actions")
		self.addToolBar(tb)


		# self.actionInsertImage = QtWidgets.QAction(QtGui.QIcon(':icons/actions/text/image.png'),"&Image", self)
		# tb.addAction(self.actionInsertImage)

		# self.actionInsertTable = QtWidgets.QAction(QtGui.QIcon(':icons/actions/text/table-add.png'),"&Table", self)
		# tb.addAction(self.actionInsertTable)

		self.actionInsertLink = QtWidgets.QAction(QtGui.QIcon(':icons/actions/text/link.png'), "&Link", self)
		tb.addAction(self.actionInsertLink)

	#		self.actionRedo = QtWidgets.QAction(QtGui.QIcon(':icons/actions/text/redo.png'),
	#				"&Redo", self, priority=QtWidgets.QAction.LowPriority,
	#				shortcut=QtGui.QKeySequence.Redo)
	#		tb.addAction(self.actionRedo)
	#
	#		self.actionCut = QtWidgets.QAction(QtGui.QIcon(':icons/actions/text/cut.png'),
	#				"Cu&t", self, priority=QtWidgets.QAction.LowPriority,
	#				shortcut=QtGui.QKeySequence.Cut)
	#		tb.addAction(self.actionCut)
	#
	#		self.actionCopy = QtWidgets.QAction(QtGui.QIcon(':icons/actions/text/copy.png'),
	#				"&Copy", self, priority=QtWidgets.QAction.LowPriority,
	#				shortcut=QtGui.QKeySequence.Copy)
	#		tb.addAction(self.actionCopy)
	#		self.actionPaste = QtWidgets.QAction(QtGui.QIcon(':icons/actions/text/paste.png'),
	#				"&Paste", self, priority=QtWidgets.QAction.LowPriority,
	#				shortcut=QtGui.QKeySequence.Paste,
	#				enabled=(len(QtGui.QApplication.clipboard().text()) != 0))
	#		tb.addAction(self.actionPaste)

	def setupTextActions(self):
		tb = QtWidgets.QToolBar(self)
		tb.setWindowTitle("Format Actions")
		self.addToolBar(tb)

		self.actionTextBold = QtWidgets.QAction(QtGui.QIcon(':icons/actions/text/bold.png'),
		                                        "&Bold", self, priority=QtWidgets.QAction.LowPriority,
		                                        shortcut=QtCore.Qt.CTRL + QtCore.Qt.Key_B,
		                                        triggered=self.textBold, checkable=True)
		bold = QtGui.QFont()
		bold.setBold(True)
		self.actionTextBold.setFont(bold)
		tb.addAction(self.actionTextBold)

		self.actionTextItalic = QtWidgets.QAction(QtGui.QIcon(':icons/actions/text/italic.png'),
		                                          "&Italic", self, priority=QtWidgets.QAction.LowPriority,
		                                          shortcut=QtCore.Qt.CTRL + QtCore.Qt.Key_I,
		                                          triggered=self.textItalic, checkable=True)
		italic = QtGui.QFont()
		italic.setItalic(True)
		self.actionTextItalic.setFont(italic)
		tb.addAction(self.actionTextItalic)

		self.actionTextUnderline = QtWidgets.QAction(QtGui.QIcon(':icons/actions/text/underline.png'),
		                                             "&Underline", self, priority=QtWidgets.QAction.LowPriority,
		                                             shortcut=QtCore.Qt.CTRL + QtCore.Qt.Key_U,
		                                             triggered=self.textUnderline, checkable=True)
		underline = QtGui.QFont()
		underline.setUnderline(True)
		self.actionTextUnderline.setFont(underline)
		tb.addAction(self.actionTextUnderline)

		grp = QtWidgets.QActionGroup(self, triggered=self.textAlign)

		# Make sure the alignLeft is always left of the alignRight.
		if QtGui.QApplication.isLeftToRight():
			self.actionAlignLeft = QtWidgets.QAction(QtGui.QIcon(':icons/actions/text/alignleft.png'),
			                                         "&Left", grp)
			self.actionAlignCenter = QtWidgets.QAction(QtGui.QIcon(':icons/actions/text/aligncenter.png'),
			                                           "C&enter", grp)
			self.actionAlignRight = QtWidgets.QAction(QtGui.QIcon(':icons/actions/text/alignright.png'),
			                                          "&Right", grp)
		else:
			self.actionAlignRight = QtWidgets.QAction(QtGui.QIcon(':icons/actions/text/alignright.png'),
			                                          "&Right", grp)
			self.actionAlignCenter = QtWidgets.QAction(QtGui.QIcon(':icons/actions/text/aligncenter.png'),
			                                           "C&enter", grp)
			self.actionAlignLeft = QtWidgets.QAction(QtGui.QIcon(':icons/actions/text/alignleft.png'),
			                                         "&Left", grp)

		self.actionAlignJustify = QtWidgets.QAction(QtGui.QIcon(':icons/actions/text/alignjustify.png'),
		                                            "&Justify", grp)

		self.actionAlignLeft.setShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_L)
		self.actionAlignLeft.setCheckable(True)
		self.actionAlignLeft.setPriority(QtWidgets.QAction.LowPriority)

		self.actionAlignCenter.setShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_E)
		self.actionAlignCenter.setCheckable(True)
		self.actionAlignCenter.setPriority(QtWidgets.QAction.LowPriority)

		self.actionAlignRight.setShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_R)
		self.actionAlignRight.setCheckable(True)
		self.actionAlignRight.setPriority(QtWidgets.QAction.LowPriority)

		self.actionAlignJustify.setShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_J)
		self.actionAlignJustify.setCheckable(True)
		self.actionAlignJustify.setPriority(QtWidgets.QAction.LowPriority)

		tb.addActions(grp.actions())

		pix = QtGui.QPixmap(16, 16)
		pix.fill(QtCore.Qt.black)
		self.actionTextColor = QtWidgets.QAction(QtGui.QIcon(pix), "&Color...",
		                                         self, triggered=self.textColor)
		tb.addAction(self.actionTextColor)

		self.addToolBarBreak(QtCore.Qt.TopToolBarArea)
		self.addToolBar(tb)

		self.actionBulletList = QtWidgets.QAction(QtGui.QIcon('icons/actions/text/bullet.png'), "Bullet",
		                                          self,
		                                          triggered=self.onBulletList)
		tb.addAction(self.actionBulletList)

		self.actionNumberedList = QtWidgets.QAction(QtGui.QIcon('icons/actions/text/numbered.png'), "Numbered",
		                                            self,
		                                            triggered=self.onNumberedList)
		tb.addAction(self.actionNumberedList)

	# self.comboFont = QtGui.QFontComboBox(tb)
	# tb.addWidget(self.comboFont)
	# self.comboFont.activated[str].connect(self.textFamily)

	def save(self, *args, **kwargs):
		html = self.textEdit.toHtml()
		start = html.find(">", html.find("<body")) + 1
		html = html[start: html.rfind("</body>")]
		html = html.replace("""text-indent:0px;"></p>""", """text-indent:0px;">&nbsp;</p>""")
		self.saveCallback(html)

	def load(self, html):
		self.textEdit.setHtml(html)

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

	def onBulletList(self, *args, **kwargs):
		cursor = self.textEdit.textCursor()
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
		cursor = self.textEdit.textCursor()
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
		col = QtGui.QColorDialog.getColor(self.textEdit.textColor(), self)
		if not col.isValid():
			return

		fmt = QtGui.QTextCharFormat()
		fmt.setForeground(col)
		self.mergeFormatOnWordOrSelection(fmt)
		self.colorChanged(col)

	def insertImage(self, *args, **kwargs):
		queue = RegisterQueue()
		skelStructure = {"textEdit": {"multiple": False, "type": "treeitem.file"}}
		event.emit(QtCore.SIGNAL(
			'requestTreeItemBoneSelection(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,'
			'PyQt_PyObject)'),
			queue, "file", "textEdit", skelStructure, None, self.setFileSelection)
		self.widget = queue.getBest()()

	def setaSelection(self, selection):
		if (len(selection) == 0):
			return
		file = selection[0]
		cursor = self.textEdit.textCursor()
		document = self.textEdit.document()
		img = QtGui.QImage()
		data = getFileContents(file["dlkey"])  # FIXME: Broken
		img.loadFromData(data)
		document.addResource(document.ImageResource, QtCore.QUrl("/file/view/%s/%s" % (file["dlkey"], file["name"])),
		                     img)
		cursor.insertImage("/file/view/%s/%s" % (file["dlkey"], file["name"]))
		self.textEdit.setTextCursor(cursor)

	def insertTable(self, *args, **kwargs):
		# cursor = self.textEdit.textCursor()
		# cursor.insertTable(5, 7)
		self.widget = CreateTableDialog(self.textEdit.textCursor())

	def insertLink(self, *args, **kwargs):
		(dest, okay) = QtWidgets.QInputDialog.getText(self, "Ziel eingeben", "Bitte das Verknüpfungsziel eigeben")
		if not okay or not dest:
			return
		cursor = self.textEdit.textCursor()
		if not cursor.hasSelection():
			cursor.select(QtGui.QTextCursor.WordUnderCursor)
		txt = cursor.selectedText()
		self.textEdit.insertHtml("<a href=\"%s\" target=\"_blank\">%s</a>" % (dest, txt))

	def textAlign(self, action):
		if action == self.actionAlignLeft:
			self.textEdit.setAlignment(
				QtCore.Qt.AlignLeft | QtCore.Qt.AlignAbsolute)
		elif action == self.actionAlignCenter:
			self.textEdit.setAlignment(QtCore.Qt.AlignHCenter)
		elif action == self.actionAlignRight:
			self.textEdit.setAlignment(
				QtCore.Qt.AlignRight | QtCore.Qt.AlignAbsolute)
		elif action == self.actionAlignJustify:
			self.textEdit.setAlignment(QtCore.Qt.AlignJustify)

	def currentCharFormatChanged(self, format):
		self.fontChanged(format.font())
		self.colorChanged(format.foreground().color())

	def cursorPositionChanged(self):
		self.alignmentChanged(self.textEdit.alignment())

	def clipboardDataChanged(self):
		try:
			self.actionPaste.setEnabled(len(QtGui.QApplication.clipboard().text()) != 0)
		except:
			pass

	def mergeFormatOnWordOrSelection(self, format):
		cursor = self.textEdit.textCursor()
		if not cursor.hasSelection():
			cursor.select(QtGui.QTextCursor.WordUnderCursor)

		cursor.mergeCharFormat(format)
		self.textEdit.mergeCurrentCharFormat(format)

	def fontChanged(self, font):
		# self.comboFont.setCurrentIndex(
		#		self.comboFont.findText(QtGui.QFontInfo(font).family()))
		self.actionTextBold.setChecked(font.bold())
		self.actionTextItalic.setChecked(font.italic())
		self.actionTextUnderline.setChecked(font.underline())

	def colorChanged(self, color):
		pix = QtGui.QPixmap(16, 16)
		pix.fill(color)
		self.actionTextColor.setIcon(QtGui.QIcon(pix))

	def alignmentChanged(self, alignment):
		if alignment & QtCore.Qt.AlignLeft:
			self.actionAlignLeft.setChecked(True)
		elif alignment & QtCore.Qt.AlignHCenter:
			self.actionAlignCenter.setChecked(True)
		elif alignment & QtCore.Qt.AlignRight:
			self.actionAlignRight.setChecked(True)
		elif alignment & QtCore.Qt.AlignJustify:
			self.actionAlignJustify.setChecked(True)


class CreateTableDialog(QtWidgets.QDialog):
	def __init__(self, textCursor, *args, **kwargs):
		super(CreateTableDialog, self).__init__(*args, **kwargs)
		self.ui = Ui_DialogCreateTable()
		self.ui.setupUi(self)
		self.textCursor = textCursor
		self.show()

	def accept(self):
		format = QtGui.QTextTableFormat()
		alignments = [QtCore.Qt.AlignLeft, QtCore.Qt.AlignHCenter, QtCore.Qt.AlignRight]
		format.setAlignment(alignments[self.ui.cbAlignment.currentIndex()])
		self.textCursor.insertTable(self.ui.sboxRows.value(), self.ui.sboxCols.value(), format)
		self.close()


###################### File #####################


class FileEdit(QtWidgets.QWidget):
	loremIpsum = """Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt
    ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea
    rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit
    amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam
    erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren,
    no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr,
    sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et
    accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum
    dolor sit amet.  """
	units = ["%", "px", "em"]

	def __init__(self, saveCallback, attrs, href, *args, **kwargs):
		super(FileEdit, self).__init__(*args, **kwargs)
		self.ui = Ui_Form()
		self.ui.setupUi(self)
		self.fileID = None
		self.fileDlKey = None
		self.fileName = None
		self.attrs = attrs
		self.customURI = False
		self.ui.comboBoxUnits.setCurrentIndex(1)  # Safe Default
		attrs = dict([(k.lower(), v) for (k, v) in attrs])
		if "width" in attrs.keys():
			self.ui.editWidth.setText("".join([x for x in attrs["width"] if x in string.digits]))
			if "%" in attrs["width"]:
				self.ui.comboBoxUnits.setCurrentIndex(0)
			elif "px" in attrs["width"]:
				self.ui.comboBoxUnits.setCurrentIndex(1)
			elif "em" in attrs["width"]:
				self.ui.comboBoxUnits.setCurrentIndex(2)
		if "height" in attrs.keys():
			self.ui.editHeight.setText("".join([x for x in attrs["height"] if x in string.digits]))
			if "%" in attrs["height"]:
				self.ui.comboBoxUnits.setCurrentIndex(0)
			elif "px" in attrs["height"]:
				self.ui.comboBoxUnits.setCurrentIndex(1)
			elif "em" in attrs["height"]:
				self.ui.comboBoxUnits.setCurrentIndex(2)
		if "src" in attrs.keys():
			src = attrs["src"]
			if "/file/view" in src:
				self.fileDlKey = src[src.find("/file/view/") + len("/file/view/"): src.find("/", src.find(
					"/file/view") + 5 + len("/file/view"))]
				self.fileName = src[src.find("/", src.find("/file/view/") + len("/file/view/") + 5) + 1: src.find("?",
				                                                                                                  src.find(
					                                                                                                  "/",
					                                                                                                  src.find(
						                                                                                                  "/file/view/") + len(
						                                                                                                  "/file/view/") + 5))]
				if "?id=" in src:
					self.fileID = src[src.find("?id=") + len("?id="):]
			else:
				self.fileName = src
			self.ui.editFile.setText(self.fileName)
		if "title" in attrs.keys():
			self.ui.editTitle.setText(attrs["title"])
		if "alt" in attrs.keys():
			self.ui.editAlt.setText(attrs["alt"])
		if "align" in attrs.keys():
			self.ui.checkBoxFloat.setChecked(True)
			if attrs["align"] == "left":
				self.ui.comboBoxAlign.setCurrentIndex(0)
			elif attrs["align"] == "center":
				self.ui.comboBoxAlign.setCurrentIndex(1)
			else:
				self.ui.comboBoxAlign.setCurrentIndex(2)
		if "style" in attrs.keys():
			if "margin-left: auto" in attrs["style"].lower() and "margin-right: auto" in attrs["style"].lower():
				self.ui.comboBoxAlign.setCurrentIndex(1)
			elif "margin-right: auto" in attrs["style"].lower():
				self.ui.comboBoxAlign.setCurrentIndex(0)
			elif "margin-left: auto" in attrs["style"].lower():
				self.ui.comboBoxAlign.setCurrentIndex(2)
		if href:
			href = dict([(k.lower(), v) for (k, v) in href])
			if "href" in href.keys():
				if "src" in attrs.keys() and href["href"] == attrs["src"]:
					self.ui.comboBoxHRef.setCurrentIndex(1)
				else:
					self.ui.comboBoxHRef.insertItem(2, href["href"])
					self.ui.comboBoxHRef.setCurrentIndex(2)
			if "target" in href.keys() and href["target"].lower() == "_blank":
				self.ui.checkboxHrefNewWindow.setChecked(True)
		self.saveCallback = saveCallback
		self.updatePreview()

	def on_btnSelectFile_released(self, *args, **kwargs):
		queue = RegisterQueue()
		skelStructure = {"textEdit": {"multiple": False, "type": "treeitem.file"}}
		event.emit(QtCore.SIGNAL(
			'requestTreeItemBoneSelection(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,'
			'PyQt_PyObject)'),
			queue, "file", "textEdit", skelStructure, None, self.setFileSelection)
		self.widget = queue.getBest()()

	def setFileSelection(self, selection):
		if (len(selection) == 0):
			return
		file = selection[0]
		self.fileID = file["id"]
		self.fileDlKey = file["dlkey"]
		self.fileName = file["name"]
		self.ui.editFile.setText(self.fileName)
		self.updatePreview()
		return

	def on_comboBoxHRef_editTextChanged(self, txt):
		self.customURI = True
		self.updatePreview()

	def on_comboBoxHRef_currentIndexChanged(self, txt):
		self.customURI = False
		self.updatePreview()

	def on_comboBoxAlign_currentIndexChanged(self, txt):
		self.updatePreview()

	def on_checkboxHrefNewWindow_stateChanged(self, state):
		self.updatePreview()

	def on_checkBoxFloat_stateChanged(self, state):
		self.updatePreview()

	def on_comboBoxUnits_currentIndexChanged(self, *args, **kwargs):
		self.updatePreview()

	def on_editWidth_textChanged(self, txt):
		self.updatePreview()

	def on_editHeight_textChanged(self, txt):
		self.updatePreview()

	def updatePreview(self):
		attrs, href = self.getAttrs()
		if self.fileDlKey:
			res = "<html><head><base href=\"%s\"></head><body>%s</body></html>"
			body = "<img %s>" % (" ".join(["%s=\"%s\"" % (k, v) for (k, v) in attrs]))
			body += "<br>" + self.loremIpsum
			self.ui.webView.setHtml(res % (NetworkService.url, body))
		else:  # No image selected
			newAttrs = []
			for k, v in attrs:
				if k != "src":
					newAttrs.append((k, v))
				else:
					newAttrs.append((k, os.path.join(os.getcwd(), ":icons/status/missing-image.png")))
			res = "<html><head></head><body>%s</body></html>"
			body = "<img %s>" % (" ".join(["%s=\"%s\"" % (k, v) for (k, v) in newAttrs]))
			body += "<br>" + self.loremIpsum
			srcUrl = QtCore.QUrl.fromLocalFile(os.getcwd())
			self.ui.webView.setHtml(res % (body), srcUrl)

	def getAttrs(self):
		attrs = [("src", "/file/view/%s/%s?id=%s" % (self.fileDlKey, self.fileName, self.fileID)),
		         ("width", "%s%s" % (self.ui.editWidth.text(), self.units[self.ui.comboBoxUnits.currentIndex()])),
		         ("height", "%s%s" % (self.ui.editHeight.text(), self.units[self.ui.comboBoxUnits.currentIndex()])),
		         ("title", self.ui.editTitle.text()),
		         ("alt", self.ui.editAlt.text())]
		attrs = [attr for attr in attrs if attr[1] and attr[1] not in ["px", "%", "em"]]
		if self.ui.checkBoxFloat.isChecked():
			if self.ui.comboBoxAlign.currentIndex() == 0:
				attrs.append(("align", "left"))
			elif self.ui.comboBoxAlign.currentIndex() == 1:
				attrs.append(("align", "center"))
			else:
				attrs.append(("align", "right"))
		else:
			if self.ui.comboBoxAlign.currentIndex() == 0:
				attrs.append(("style", "display: block; margin-right: auto;"))
			elif self.ui.comboBoxAlign.currentIndex() == 1:
				attrs.append(("style", "display: block; margin-left: auto; margin-right: auto;"))
			else:
				attrs.append(("style", "display: block; margin-left: auto;"))
		href = []
		if self.customURI or self.ui.comboBoxHRef.currentIndex() != 0:
			if self.customURI:
				href.append(("href", self.ui.comboBoxHRef.currentText()))
			else:
				if self.ui.comboBoxHRef.currentIndex() == 1:
					href.append(("href", self.ui.editFile.text()))
				else:
					href.append(("href", self.ui.comboBoxHRef.currentText()))
			if self.ui.checkboxHrefNewWindow.isChecked():
				href.append(("target", "_blank"))
		return (attrs, href)

	def save(self):
		attrs, href = self.getAttrs()
		self.saveCallback(attrs, href)


class TableEdit(TextEdit):
	def __init__(self, saveCallback, *args, **kwargs):
		self._origSaveCallback = saveCallback
		super(TableEdit, self).__init__(self.postProcessHtml, *args, **kwargs)

	def load(self, html):
		header, body = self.splitHeader(html)
		super(TableEdit, self).load("<table border=\"2\" cellspacing=\"2\" cellpadding=\"2\" >" + body)

	def postProcessHtml(self, html):
		self._origSaveCallback(html)

	def splitHeader(self, html):
		if "<thead>" in html:
			header = html[: html.find("<thead>") + 7]
			body = html[html.find("<thead>") + 8:]
		else:
			header = html[: html.find("<tr>")]
			body = html[html.find("<tr>"):]
		return (header, body)


class DocumentBlock(QtWidgets.QTreeWidgetItem):
	def __init__(self, name, attrs=[], content="", parent=None, *args, **kwargs):
		super(DocumentBlock, self).__init__(parent, *args, **kwargs)
		self.attrs = attrs
		self.content = content
		self.setText(0, name)


class HtmlBlock(QtWidgets.QTreeWidgetItem):
	def __init__(self, attrs=[], content="", parent=None, *args, **kwargs):
		super(HtmlBlock, self).__init__(*args, **kwargs)
		self.attrs = attrs
		self.content = content

	def isEmpty(self):
		return (False)

	def serialize(self, idx):
		return ("")

	def feed(self, txt):
		self.content += txt

	def init(self):
		pass


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


class TableBlock(HtmlBlock):
	def __init__(self, attrs=[], *args, **kwargs):
		super(TableBlock, self).__init__(attrs, *args, **kwargs)
		self.setText(0, QtCore.QCoreApplication.translate("DocumentEditBone", "Table"))
		self.setIcon(0, QtGui.QIcon(":icons/actions/text/texttypes/table.png"))

	def feed(self, txt):
		# print("Table FEED", txt)
		self.content += txt

	def getEditor(self, parent):
		currentEditor = TableEdit(self.saveChanges)
		currentEditor.load(HtmlSerializer().santinize(self.content))
		return (currentEditor)

	def saveChanges(self, html):
		self.content = html

	def isEmpty(self):
		return (False)

	def serialize(self, idx):
		return (HtmlSerializer().santinize(self.content))

	def init(self):
		currentEditor = TableEdit(self.saveChanges)
		d = CreateTableDialog(currentEditor.textEdit.textCursor())
		d.exec_()
		currentEditor.save()


class TextBlock(HtmlBlock):
	def __init__(self, *args, **kwargs):
		super(TextBlock, self).__init__(*args, **kwargs)
		self.setText(0, QtCore.QCoreApplication.translate("DocumentEditBone", "Text"))
		self.setIcon(0, QtGui.QIcon(":icons/actions/text/texttypes/text.png"))

	def getEditor(self, parent):
		currentEditor = TextEdit(self.saveChanges)
		currentEditor.load(HtmlSerializer().santinize(self.content))
		return (currentEditor)

	def saveChanges(self, html):
		self.content = html.replace("href=\"!", "target=\"_blank\" href=\"")
		caption = HtmlStripper.strip(self.content).strip().replace("\n", " ")[:25]
		if caption:
			self.setText(0, caption)

	def feed(self, txt):
		super(TextBlock, self).feed(txt)
		caption = HtmlStripper.strip(self.content).strip().replace("\n", " ")[:25]
		if caption:
			self.setText(0, caption)

	def isEmpty(self):
		textEdit = QtGui.QTextEdit()
		textEdit.setHtml(self.content)
		return (textEdit.toPlainText().strip() == "")

	def serialize(self, idx):
		return (HtmlSerializer().santinize(self.content))


class ImageBlock(HtmlBlock):
	def __init__(self, attrs, href, *args, **kwargs):
		super(ImageBlock, self).__init__(attrs, *args, **kwargs)
		self.href = href
		self.setText(0, QtCore.QCoreApplication.translate("DocumentEditBone", "Image"))
		self.setIcon(0, QtGui.QIcon(":icons/actions/text/texttypes/image.png"))
		attrDict = dict([(k.lower(), v) for (k, v) in attrs])
		if "title" in attrDict and HtmlStripper.strip(attrDict["title"]).strip().replace("\n", " ")[:25]:
			self.setText(0, HtmlStripper.strip(attrDict["title"]).strip().replace("\n", " ")[:25])
		elif "alt" in attrDict and HtmlStripper.strip(attrDict["alt"]).strip().replace("\n", " ")[:25]:
			self.setText(0, HtmlStripper.strip(attrDict["alt"]).strip().replace("\n", " ")[:25])

	def getEditor(self, parent):
		return (FileEdit(self.save, self.attrs, self.href))

	def save(self, attrs, href):
		self.attrs = attrs
		self.href = href
		attrDict = dict([(k.lower(), v) for (k, v) in attrs])
		if "title" in attrDict and HtmlStripper.strip(attrDict["title"]).strip().replace("\n", " ")[:25]:
			self.setText(0, HtmlStripper.strip(attrDict["title"]).strip().replace("\n", " ")[:25])
		elif "alt" in attrDict and HtmlStripper.strip(attrDict["alt"]).strip().replace("\n", " ")[:25]:
			self.setText(0, HtmlStripper.strip(attrDict["alt"]).strip().replace("\n", " ")[:25])

	def serialize(self, idx):
		imgStr = "<img %s>\n" % (" ".join(["%s=\"%s\"" % (k, v) for (k, v) in self.attrs]))
		if self.href:
			hrefStr = "<a %s>\n" % (" ".join(["%s=\"%s\"" % (k, v) for (k, v) in self.href]))
			return (hrefStr + imgStr + "</a>")
		return (imgStr)


class HeaderBlock(HtmlBlock):
	def __init__(self, caption=None, *args, **kwargs):
		if not caption:
			caption = QtCore.QCoreApplication.translate("DocumentEditBone", "(empty caption)")
		super(HeaderBlock, self).__init__(*args, **kwargs)
		self.setIcon(0, QtGui.QIcon(":icons/actions/text/texttypes/headline.png"))

	def feed(self, txt):
		self.content += HtmlStripper.strip(txt)
		self.setText(0, self.content)

	def serialize(self, idx):
		return ("<h%s>%s</h%s>" % (idx, self.content, idx))

	def getEditor(self, parent):
		currentEditor = QtWebKit.QWebView()
		currentEditor.save = lambda: None
		html = "<html><head><base href=\"%s\"></head><body>%s</body></html>" % (
			NetworkService.url, parent.serialize(self))
		currentEditor.setHtml(html)
		return (currentEditor)

	def doubleClicked(self):
		txt, okay = QtWidgets.QInputDialog.getText(None,
		                                           QtCore.QCoreApplication.translate("DocumentEditBone",
		                                                                             "Change caption"),
		                                           QtCore.QCoreApplication.translate("DocumentEditBone",
		                                                                             "Insert new caption"),
		                                           text=self.content)
		if okay and txt:
			self.content = txt
			self.setText(0, self.content)


class ExtEdit(EditWidget):
	def __init__(self, saveCB, *args, **kwargs):
		super(ExtEdit, self).__init__(*args, **kwargs)
		self.saveCB = saveCB
		self.ui.btnSaveClose.hide()
		self.ui.btnSaveContinue.hide()
		self.ui.btnPreview.hide()
		self.ui.btnReset.hide()

	def reloadData(self, *args, **kwargs):
		pass

	def save(self, *args, **kwargs):
		self.closeOnSuccess = False
		self.overlay.inform(self.overlay.BUSY)
		res = {}
		for key, bone in self.bones.items():
			value = bone.serializeForDocument()
			if value != None:
				res[key] = value
		self.saveCB(res)


class ExtensionBlock(HtmlBlock):
	def __init__(self, ext, data=None, *args, **kwargs):
		super(ExtensionBlock, self).__init__(*args, **kwargs)
		self.data = data or {}
		self.ext = ext
		self.setIcon(0, QtGui.QIcon(":icons/actions/text/../extension.png"))
		self.setText(0, ext["descr"])

	def feed(self, txt):
		assert False, "Should not happen!"

	def serialize(self, idx=None):
		return ("<!--ext:%s %s-->" % (self.ext["name"], json.dumps(self.data)))

	def save(self, data):
		self.data = data
		self.edit = None

	def getEditor(self, parent):
		self.edit = ExtEdit(self.save, "No-Modul", 0)
		self.edit.setData({"structure": self.ext["skel"], "values": self.data})
		return (self.edit)


class Parser(html.parser.HTMLParser):
	blockTags = ('img', 'table', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6')
	from html.entities import entitydefs

	def __init__(self, extensions):
		super(Parser, self).__init__()
		self.openTables = 0
		self.extensions = extensions

	def parseInto(self, inStr, treeWidget):
		self.treeWidget = treeWidget
		self.result = ""
		self.lastCaptionType = [1]
		self.lastHRef = None
		self.currentBlock = TextBlock("txt", "", parent=self.treeWidget)
		self.treeWidget.addTopLevelItem(self.currentBlock)
		self.feed(inStr)
		self.close()
		return (self.currentBlock)

	def handle_data(self, data):
		if not data.strip():
			return
		if self.lastHRef:
			self.result += "<a"
			for k, v in self.lastHRef:
				if k.lower() == "href" and "target" in [x.lower() for x, y in self.lastHRef]:
					v = "!" + v  # Prepend new Window Marker
				self.result += ' %s="%s"' % (k, v)
			self.result += ">"
			self.lastHRef = None
		self.result += data
		self.currentBlock.feed(self.result)
		self.result = ""

	def handle_charref(self, name):
		self.result += "&#%s;" % (name)

	def handle_entityref(self, name):
		if name in self.entitydefs:
			self.result += "&%s;" % (name)

	def addBlockParent(self, item):
		if not self.currentBlock.parent():
			self.treeWidget.addTopLevelItem(item)
		else:
			self.currentBlock.parent().addChild(item)

	def goToParent(self):
		if self.currentBlock.parent():
			self.currentBlock = self.currentBlock.parent()

	def handle_starttag(self, tag, attrs):
		""" Delete all tags except for legal ones """
		self.currentBlock.feed(self.result)
		self.result = ""
		if tag != "a" or self.openTables:
			self.result = "<" + tag
			for k, v in attrs:
				if (k[0:2].lower()) != 'on' and v[0:10].lower() != 'javascript':
					self.result += ' %s="%s"' % (k, v)
			self.result += ">"
		else:
			self.lastHRef = (
				[(k, v) for (k, v) in attrs if k[0:2].lower() != 'on' and v[0:10].lower() != 'javascript'])
		if tag in self.blockTags:
			if tag == "table":
				self.openTables += 1
				tableBlock = TableBlock(attrs)
				self.addBlockParent(tableBlock)
				self.currentBlock = tableBlock
			if self.openTables:
				return
			if tag in ["h%s" % x for x in range(1, 7)]:
				newCaptionType = int(tag[1])

				if newCaptionType > max(self.lastCaptionType):
					newBlock = HeaderBlock(attrs=attrs)
					self.addBlockParent(newBlock)
					self.currentBlock = newBlock
					self.lastCaptionType.append(newCaptionType)
				elif newCaptionType == max(self.lastCaptionType):
					self.goToParent()
					newBlock = HeaderBlock(attrs=attrs)
					self.addBlockParent(newBlock)
					self.currentBlock = newBlock
				else:
					self.goToParent()
					while (newCaptionType < max(self.lastCaptionType)):
						self.goToParent()
						self.lastCaptionType.remove(max(self.lastCaptionType))
					newBlock = HeaderBlock(attrs=attrs)
					self.addBlockParent(newBlock)
					self.currentBlock = newBlock
			elif tag == "img":
				imgBlock = ImageBlock(attrs, self.lastHRef)
				self.lastHRef = None
				imgBlock.feed(self.result)
				self.addBlockParent(imgBlock)
				self.result = ""
				newBlock = TextBlock("txt", "")
				self.addBlockParent(newBlock)
				self.currentBlock = newBlock
			else:
				newBlock = DocumentBlock(tag, attrs, parent=self.currentBlock)
				self.currentBlock.addChild(newBlock)
				self.currentBlock = newBlock

	def handle_endtag(self, tag):
		self.currentBlock.feed(self.result)
		self.result = ""
		self.result += "</%s>" % tag
		if tag == "table":
			self.openTables -= 1
			if not self.openTables:
				newBlock = TextBlock(parent=self)
				self.addBlockParent(newBlock)
				self.currentBlock = newBlock
		elif tag in ["h%s" % x for x in range(1, 7)]:
			if not isinstance(self.currentBlock, HeaderBlock):
				self.result = ""
				return
			newBlock = TextBlock()
			self.currentBlock.addChild(newBlock)
			self.currentBlock = newBlock
		return
		if tag in self.blockTags:
			self.currentBlock.content += self.result
			self.result = ""
			if self.currentBlock.parent():
				self.currentBlock = self.currentBlock.parent()
			else:
				self.currentBlock = DocumentBlock("root", parent=self.treeWidget)
				self.treeWidget.addTopLevelItem(currentBlock)

	def handle_comment(self, txt):
		if txt.strip().upper() == "X-FWS-TEXTBREAK":
			newBlock = TextBlock()
			self.addBlockParent(newBlock)
			self.currentBlock = newBlock
		elif txt.strip().upper().startswith("EXT:"):
			txt = txt.strip()
			extName = txt[4: txt.find(" ")]
			jsonData = txt[txt.find(" ") + 1:]
			data = json.loads(jsonData)
			for ext in self.extensions:
				if ext["name"] == extName:
					newBlock = ExtensionBlock(ext, data)
					self.addBlockParent(newBlock)
					self.currentBlock = newBlock


class HtmlSerializer(html.parser.HTMLParser):
	from html.entities import entitydefs

	attrsMargins = ["margin", "margin-left", "margin-right", "margin-top", "margin-bottom"]
	attrsSpacing = ["spacing", "spacing-left", "spacing-right", "spacing-top", "spacing-bottom"]
	attrsDescr = ["title", "alt"]
	validTags = (
		'font', 'b', 'a', 'i', 'u', 'span', 'div', 'p', 'img', 'ul', 'li', 'acronym', 'h1', 'h2', 'h3', 'h4', 'h5',
		'h6',
		'table', 'tr', 'td', 'th', 'br', 'hr', 'strong')
	validAttrs = {"font": ["color"],
	              "a": ["href", "target"] + attrsDescr,
	              "acronym": ["title"],
	              "div": ["align", "width", "height"] + attrsMargins + attrsSpacing,
	              "p": ["align", "width", "height"] + attrsMargins + attrsSpacing,
	              "span": ["align", "width", "height"] + attrsMargins + attrsSpacing,
	              "img": ["src", "target", "width", "height", "align"] + attrsDescr + attrsMargins + attrsSpacing,
	              "table": ["width", "align", "border", "cellspacing", "cellpadding"] + attrsDescr,
	              "td": ["cellspan", "rowspan", "width", "heigt"] + attrsMargins + attrsSpacing
	              }
	validStyles = ["font-weight", "font-style", "text-decoration", "color", "display"] + attrsMargins + attrsSpacing
	singleTags = ["br", "img", "hr"]

	def __init__(self):
		html.parser.HTMLParser.__init__(self)
		self.result = ""
		self.openTagsList = []
		self.remove_all = False

	def handle_data(self, data):
		if data:
			self.result += data

	def handle_charref(self, name):
		self.result += "&#%s;" % (name)

	def handle_entityref(self, name):
		if name in self.entitydefs:
			self.result += "&%s;" % (name)

	def handle_starttag(self, tag, attrs):
		""" Delete all tags except for legal ones """
		if tag in self.validTags and not self.remove_all:
			self.result = self.result + '<' + tag
			for k, v in attrs:
				if not tag in self.validAttrs.keys() or not k in self.validAttrs[tag]:
					continue
				if k.lower()[0:2] != 'on' and v.lower()[0:10] != 'javascript':
					self.result = '%s %s="%s"' % (self.result, k, v)
			if "style" in [k for (k, v) in attrs]:
				syleRes = {}
				styles = [v for (k, v) in attrs if k == "style"][0].split(";")
				for s in styles:
					style = s[: s.find(":")].strip()
					value = s[s.find(":") + 1:].strip()
					if style in self.validStyles and not any([(x in value) for x in ["\"", ":", ";"]]):
						syleRes[style] = value
				if len(syleRes.keys()):
					self.result += " style=\"%s\"" % "; ".join([("%s: %s" % (k, v)) for (k, v) in syleRes.items()])
			if tag in self.singleTags:
				self.result = self.result + ' />'
			else:
				self.result = self.result + '>'
				self.openTagsList.insert(0, tag)

	def handle_endtag(self, tag):
		if not self.remove_all and tag in self.openTagsList:
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

	def santinize(self, instr, remove_all=False):
		self.result = ""
		self.openTagsList = []
		self.remove_all = remove_all
		self.feed(instr)
		self.close()
		self.cleanup()
		return (self.result)


class EmbeddedImageUploader(QtCore.QObject):
	def __init__(self, *args, **kwargs):
		super(EmbeddedImageUploader, self).__init__(*args, **kwargs)
		self.queue = []
		self.request = None
		self.fileName = None
		self.txt = ""
		self.imgs = []
		self.urlMap = {}

	def imageUrls(self, txt):
		"""
		Returns a list of all Image-URLs in the given string

		@type txt: String
		@param txt: Html-Text
		@returns: [String]
		"""
		res = []
		idx = txt.find("<img ")
		while idx != -1:
			idx = txt.find("src=", idx)
			res.append(urllib.parse.unquote(txt[idx + 5: txt.find("\"", idx + 6)]))
			idx = txt.find("<img ", idx + 7)
		return (res)

	def importHtml(self, fileName):
		"""
		Preprocesses the Html-Text imported and uploads embedded images

		@type fileName: String
		@param fileName: Name of the .html-file
		"""
		self.fileName = fileName
		txt = open(fileName, "rb").read()
		try:
			txt = txt.decode("UTF-8")
		except:  # MS Word
			txt = txt.decode("windows‑1252")
		self.txt = HtmlSerializer().santinize(txt)
		self.imgs = []
		for img in self.imageUrls(txt):
			if not img in self.imgs:
				self.imgs.append(img)
		self.urlMap = {}
		for image in self.imgs:
			fn = os.path.join(os.path.dirname(fileName), image)
			if os.path.isfile(fn) or os.path.isfile(image):
				self.queue.append(image)
		self.uploadNextFile()

	def uploadNextFile(self):
		if not self.queue:
			self.postProcessHtml()
			return
		if self.request:
			self.request.deleteLater
			self.request = None
		fn = self.imgs[-1]
		if not os.path.isfile(fn):
			fn = os.path.join(os.path.dirname(self.fileName), fn)
		self.request = FileUploader(fn)
		self.connect(self.request, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.onUploadFinished)

	def onUploadFinished(self, f):
		image = self.queue.pop()
		self.urlMap[image] = (f[0]["dlkey"], f[0]["name"], f[0]["id"])
		self.uploadNextFile()

	def postProcessHtml(self):
		for k, (dlkey, name, id) in self.urlMap.items():
			self.txt = self.txt.replace(k, "/file/view/%s/%s?id=%s" % (dlkey, name, id))
			if urllib.parse.quote(k) != k:
				self.txt = self.txt.replace(urllib.parse.quote(k), "/file/view/%s/%s?id=%s" % (dlkey, name, id))
		self.emit(QtCore.SIGNAL("finished()"))

	def getHtml(self):
		return (self.txt)


class DocEdit(QtWidgets.QWidget):
	def __init__(self, saveCallback, extensions, *args, **kwargs):
		super(DocEdit, self).__init__(*args, **kwargs)
		self.extensions = extensions
		self.ui = Ui_DocEdit()
		self.ui.setupUi(self)
		self.ui.treeWidget.dropEvent = self.on_treeWidget_dropEvent
		self.currentEditor = None
		self.saveCallback = saveCallback
		self.ui.btnImport.mouseReleaseEvent = self.btnImportPressed
		self.ui.treeWidget.keyPressEvent = self.on_treeWidget_keyPressEvent
		for ext in self.extensions:
			self.ui.cbExtensions.addItem(ext["descr"])
		else:  # We dont have any extensions
			self.ui.boxExtensions.hide()
		event.emit(QtCore.SIGNAL('stackWidget(PyQt_PyObject)'), self)
		self.overlay = Overlay(self)

	def on_treeWidget_keyPressEvent(self, e):
		QtGui.QTreeWidget.keyPressEvent(self.ui.treeWidget, e)
		if e.key() == QtCore.Qt.Key_Delete:
			self.removeBlock(self.ui.treeWidget.currentItem())

	def on_treeWidget_dropEvent(self, event, *args, **kwargs):
		QtGui.QTreeWidget.dropEvent(self.ui.treeWidget, event)
		if self.currentEditor:
			self.currentEditor.save()
			self.currentEditor = None
		self.ui.scrollArea.setWidget(QtWidgets.QWidget())
		self.processDocument()

	def addParent(self, parent, newChild):
		if not parent.parent():
			self.ui.treeWidget.addTopLevelItem(newChild)
		else:
			parent.parent().addChild(newChild)

	def getChildren(self, fromChildren=None):
		res = []
		if not fromChildren:
			idx = 0
			item = self.ui.treeWidget.topLevelItem(idx)
			while item:
				res.append(item)
				idx += 1
				item = self.ui.treeWidget.topLevelItem(idx)
		else:
			idx = 0
			child = fromChildren.child(idx)
			while child:
				res.append(child)
				idx += 1
				child = fromChildren.child(idx)
		return (res)

	def processDocument(self, child=None):
		blocks = self.getChildren(child)

		for b in blocks[:]:
			if len(self.getChildren(b)) > 0:
				if not isinstance(b, HeaderBlock):
					for c in b.takeChildren():
						self.addParent(b, c)
					self.processDocument(b.parent())
				else:
					for c in self.getChildren(b):
						self.processDocument(c)
			self.processDocument(b)
			if b.isEmpty():
				self.removeBlock(b)
		# Remove empty TextBlocks
		if child and child.isEmpty():
			self.removeBlock(child)
		# Join two adjacent TextBlocks
		return
		i = 0
		while i + 1 < len(blocks):
			childA = blocks[i]
			childB = blocks[i + 1]
			if isinstance(childA, TextBlock) and isinstance(childB, TextBlock):
				childA.content += childB.content
				blocks.remove(childB)
				self.removeBlock(childB)
			else:
				i += 1

	def removeBlock(self, block):
		if not block.parent():
			self.ui.treeWidget.takeTopLevelItem(self.ui.treeWidget.indexOfTopLevelItem(block))
		else:
			block.parent().takeChild(block.parent().indexOfChild(block))

	def on_treeWidget_itemSelectionChanged(self):
		items = self.ui.treeWidget.selectedItems()
		if len(items) == 0:
			return
		else:
			item = items[0]
			if self.currentEditor:
				self.currentEditor.save()
			self.currentEditor = item.getEditor(self)
			self.ui.scrollArea.setWidget(self.currentEditor)

	def on_treeWidget_itemDoubleClicked(self, item, colum):
		if not item or not "doubleClicked" in dir(item):
			return
		item.doubleClicked()

	def importHtml(self):
		inFile = QtGui.QFileDialog.getOpenFileName(self, filter="Html-Seite (*.htm *.html)")
		if not inFile:
			return
		self.ui.treeWidget.clear()
		self.ui.scrollArea.setWidget(QtWidgets.QWidget())
		self.currentEditor = None
		self.imageUploader = EmbeddedImageUploader()
		self.connect(self.imageUploader, QtCore.SIGNAL("finished()"), self.setImportedHtml)
		self.overlay.inform(self.overlay.BUSY)
		self.imageUploader.importHtml(inFile)

	def setImportedHtml(self):
		"""
		Starts parsing and displaying of the preprocessed html

		@type html: String
		@param html: Html to display
		"""
		html = self.imageUploader.getHtml()
		self.imageUploader.deleteLater()
		self.imageUploader = None
		Parser(self.extensions).parseInto(html, self.ui.treeWidget)
		self.processDocument()
		self.overlay.clear()

	def btnImportPressed(self, e=None):
		super(QtWidgets.QPushButton, self.ui.btnImport).mouseReleaseEvent(e)
		menu = QtWidgets.QMenu(self)
		importMenu = menu.addMenu("Import")
		exportMenu = menu.addMenu("Export")
		importHtml = importMenu.addAction("HTML")
		exportHtml = exportMenu.addAction("HTML")
		exportPdf = exportMenu.addAction("PDF")
		action = menu.exec_(e.globalPos())
		if action == importHtml:
			self.importHtml()
		elif action == exportHtml:
			self.exportHtml()
		elif action == exportPdf:
			self.exportPdf()

	def exportHtml(self):
		outFile = QtGui.QFileDialog.getSaveFileName(self, filter="Html-Seite (*.htm *.html)")
		if not outFile:
			return
		if not any(outFile.endswith(x) for x in [".htm", "html"]):
			outFile += ".html"
		open(outFile, "w+").write(self.relativeToAbsolutePath(self.serialize()))

	def exportPdf(self):
		outFile = QtGui.QFileDialog.getSaveFileName(self, filter="PDF-Dokumente (*.pdf)")
		if not any(outFile.endswith(x) for x in ["pdf"]):
			outFile += ".pdf"
		if not outFile:
			return
		self.overlay.inform(self.overlay.BUSY)
		self.ww = QtWebKit.QWebView()
		self.connect(self.ww, QtCore.SIGNAL("loadFinished (bool)"), lambda b: self.on_webView_loaded(outFile, b))
		self.ww.setHtml(self.serialize(), QtCore.QUrl(NetworkService.url))

	def on_webView_loaded(self, outFile, b):
		printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
		printer.setOutputFormat(QtGui.QPrinter.PdfFormat)
		printer.setOutputFileName(outFile)
		self.ww.print_(printer)
		self.ww.deleteLater()
		self.ww = None
		self.overlay.clear()

	def relativeToAbsolutePath(self, html):
		"""
		Converts all relative Image-Paths to absolute ones

		@type html: String
		@param html: Html with relative Paths
		@return: String
		"""
		r = html.replace("src=\"/file/view", "src=\"%s/file/view" % NetworkService.url)
		return (r)

	def load(self, file):
		txt = open(file).read()
		Parser(self.extensions).parseInto(txt, self.ui.treeWidget)
		self.processDocument()

	def on_btnSave_released(self):
		if self.currentEditor:
			self.currentEditor.save()
		res = self.serialize()
		self.saveCallback(res)
		event.emit(QtCore.SIGNAL("popWidget(PyQt_PyObject)"), self)

	def serialize(self, block=None, idx=1):
		res = ""
		if block:
			res += block.serialize(idx)
		else:
			idx = 0
		wasTextBlock = False
		for children in self.getChildren(block):
			if isinstance(children, TextBlock):
				if wasTextBlock:
					res += "<span><!-- X-FWS-TEXTBREAK --></span>"
				else:
					wasTextBlock = True
			else:
				wasTextBlock = False
			res += self.serialize(children, idx + 1)
		return (res)

	def unserialize(self, txt):
		self.ui.treeWidget.clear()
		self.currentEditor = None
		self.ui.scrollArea.setWidget(QtWidgets.QWidget())
		Parser(self.extensions).parseInto(txt + " ", self.ui.treeWidget)
		self.processDocument()

	def on_btnNewHeading_released(self, *args, **kwargs):
		txt, okay = QtWidgets.QInputDialog.getText(self,
		                                           QtCore.QCoreApplication.translate("DocumentEditBone", "New caption"),
		                                           QtCore.QCoreApplication.translate("DocumentEditBone",
		                                                                             "Insert new caption"))
		if okay:
			newChild = HeaderBlock()
			newChild.feed(txt)
			self.addNewChild(newChild)

	def on_btnNewText_released(self, *args, **kwargs):
		newChild = TextBlock()
		newChild.feed(QtCore.QCoreApplication.translate("DocumentEditBone", "New text"))
		self.addNewChild(newChild)

	def on_btnNewImage_released(self, *args, **kwargs):
		newChild = ImageBlock([], [])
		self.addNewChild(newChild)

	def on_btnNewTable_released(self, *args, **kwargs):
		newChild = TableBlock()
		newChild.init()
		self.addNewChild(newChild)

	def on_btnAddExtension_released(self, *args, **kwargs):
		for ext in self.extensions:
			if ext["descr"] == self.ui.cbExtensions.currentText():
				newChild = ExtensionBlock(ext)
				newChild.init()
				self.addNewChild(newChild)

	def addNewChild(self, newChild):
		parent = self.ui.treeWidget.currentItem()
		if parent and isinstance(parent, HeaderBlock):
			parent.addChild(newChild)
		else:
			if parent and parent.parent():
				parent.parent().addChild(newChild)
			else:
				self.ui.treeWidget.addTopLevelItem(newChild)
		if self.currentEditor:
			self.currentEditor.save()
		self.currentEditor = newChild.getEditor(self)
		self.ui.scrollArea.setWidget(self.currentEditor)

	def getBreadCrumb(self):
		return (QtCore.QCoreApplication.translate("DocumentEditBone", "Document editor"),
		        QtGui.QIcon(QtGui.QPixmap(":icons/actions/text-edit.png")))
