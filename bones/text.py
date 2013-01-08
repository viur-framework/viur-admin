from PyQt4 import QtCore, QtGui, QtWebKit, Qsci
from PyQt4.Qsci import QsciScintilla, QsciLexerHTML
import sys
from event import event
from utils import RegisterQueue
from ui.texteditUI import Ui_textEditWindow
from ui.rawtexteditUI import Ui_rawTextEditWindow
import html.parser
from ui.docEditlinkEditUI import Ui_LinkEdit

rsrcPath = "icons/actions/text"


class HtmlStripper( html.parser.HTMLParser ):
	def __init__(self):
		super( HtmlStripper, self ).__init__()
		self.cleanData = []
	
	def handle_data(self, data):
		self.cleanData.append( data )
	
	def getData(self):
		return ''.join(self.cleanData)
	
	@staticmethod
	def strip( txt ):
		s = HtmlStripper()
		s.feed( txt )
		return( s.getData() )


class TextViewBoneDelegate(QtGui.QStyledItemDelegate):
	cantSort=True
	def __init__(self, registerObject, modulName, boneName, skelStructure, *args, **kwargs ):
		super( QtGui.QStyledItemDelegate,self ).__init__()
		self.skelStructure = skelStructure
		self.boneName = boneName
		self.modulName=modulName
	
	def displayText(self, value, locale ):
		if value:
			value = HtmlStripper.strip( value )
		return( super( TextViewBoneDelegate, self ).displayText( value, locale ) )
		


class RawTextEdit(QtGui.QMainWindow):
	def __init__(self,  saveCallback, text, contentType=None, parent=None):
		super(RawTextEdit, self).__init__(parent)
		self.ui = Ui_rawTextEditWindow()
		self.ui.setupUi( self )
		self.contentType = contentType
		self.ui.textEdit.setUtf8( True )
		if contentType=="text/html":
			self.ui.textEdit.setLexer(QsciLexerHTML())
		self.ui.textEdit.setFolding(QsciScintilla.BoxedTreeFoldStyle, 2)
		self.ui.textEdit.setText( text )
		self.ui.textEdit.setAutoCompletionSource( QsciScintilla.AcsAll )
		self.ui.textEdit.setAutoCompletionThreshold( 1 )
		#self.ui.textEdit.setWrapMode(QsciScintilla.WrapWord )
		self.ui.textEdit.setFocus()
		self.saveCallback = saveCallback

	def save(self, *args, **kwargs ):
		self.saveCallback( self.ui.textEdit.text() )
		event.emit( QtCore.SIGNAL('popWidget(PyQt_PyObject)'), self )
	
	def sizeHint( self, *args, **kwargs ):
		return( QtCore.QSize( 400, 300 ) )
		
	def on_btnSave_released( self ):
		self.save()



class TextEdit(QtGui.QMainWindow):
	def __init__(self,  saveCallback, text, validHtml, parent=None):
		super(TextEdit, self).__init__(parent)
		self.validHtml = validHtml
		self.serializer = HtmlSerializer( validHtml )
		self.ui = Ui_textEditWindow()
		self.ui.setupUi( self )
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
		QtGui.QApplication.clipboard().dataChanged.connect(self.clipboardDataChanged)
		self.actionInsertLink.triggered.connect(self.insertLink)
		self.ui.textEdit.setHtml( text )
		self.saveCallback = saveCallback
		self.linkEditor = None
		self.ui.textEdit.mousePressEvent = self.on_textEdit_mousePressEvent
		self.ui.textEdit.insertFromMimeData = self.on_textEdit_insertFromMimeData
		

	def on_textEdit_insertFromMimeData(self, source):
		QtGui.QTextEdit.insertFromMimeData( self.ui.textEdit, source )
		html = self.ui.textEdit.toHtml()
		start = html.find(">", html.find("<body") )+1
		html = html[ start : html.rfind("</body>") ]
		html = html.replace("""text-indent:0px;"></p>""", """text-indent:0px;">&nbsp;</p>""")
		print( html )
		self.ui.textEdit.setText( self.serializer.santinize( html ) )
	
	def openLinkEditor(self, fragment):
		if self.linkEditor:
			self.linkEditor.deleteLater()
		self.linkEditor = QtGui.QDockWidget( QtCore.QCoreApplication.translate("DocumentEditBone", "Edit link"), self )
		self.linkEditor.setAllowedAreas( QtCore.Qt.BottomDockWidgetArea )
		self.linkEditor.setFeatures( QtGui.QDockWidget.NoDockWidgetFeatures )
		self.linkEditor.cWidget = QtGui.QWidget()
		self.linkEditor.ui = Ui_LinkEdit()
		self.linkEditor.ui.setupUi( self.linkEditor.cWidget )
		self.linkEditor.setWidget( self.linkEditor.cWidget )
		self.linkEditor.fragmentPosition = fragment.position()
		href =  fragment.charFormat().anchorHref()
		self.linkEditor.ui.editHref.setText( href.strip("!") )
		if href.startswith("!"):
			self.linkEditor.ui.checkBoxNewWindow.setChecked(True) 
		self.addDockWidget( QtCore.Qt.BottomDockWidgetArea, self.linkEditor)


	def saveLinkEditor(self):
		href = self.linkEditor.ui.editHref.text()
		cursor = self.ui.textEdit.textCursor()
		block = self.ui.textEdit.document().findBlock( self.linkEditor.fragmentPosition )
		iterator = block.begin()
		foundStart = False
		foundEnd = False
		oldHref = ""
		while( not iterator.atEnd() ):
			fragment = iterator.fragment()
			if foundStart:
				foundEnd = True
				if oldHref!=fragment.charFormat().anchorHref():
					newPos = fragment.position()
					while( cursor.position() < newPos ):
						cursor.movePosition( QtGui.QTextCursor.NextCharacter, QtGui.QTextCursor.KeepAnchor )
					break
			elif fragment.contains( self.linkEditor.fragmentPosition ):
				cursor.setPosition( fragment.position() )
				foundStart = True
				oldHref=fragment.charFormat().anchorHref()
			iterator += 1
		if foundStart and not foundEnd: #This is only this block
			cursor.select( cursor.BlockUnderCursor )
		if not href:
			cursor.insertHtml( cursor.selectedText() )
		else:
			if self.linkEditor.ui.checkBoxNewWindow.isChecked():
				linkTxt = "<a href=\"!%s\">%s</a>"
			else:
				linkTxt = "<a href=\"%s\">%s</a>"
			cursor.insertHtml(  linkTxt % (self.linkEditor.ui.editHref.text(),  cursor.selectedText() ) )

	def on_textEdit_mousePressEvent(self, event):
		if self.linkEditor:
			self.saveLinkEditor()
		QtGui.QTextEdit.mousePressEvent(self.ui.textEdit, event)
		if not self.ui.textEdit.anchorAt( event.pos() ):
			if self.linkEditor:
				self.linkEditor.deleteLater()
				self.linkEditor = None
			return
		cursor = self.ui.textEdit.textCursor()
		block = cursor.block()
		iterator = block.begin()
		while( not iterator.atEnd() ):
			fragment = iterator.fragment()
			if fragment.charFormat().anchorHref():
				self.openLinkEditor( fragment )
			iterator += 1

	def getBreadCrumb( self ):
		return( QtCore.QCoreApplication.translate("TextEditBone", "Text edit"), QtGui.QIcon( QtGui.QPixmap( "icons/actions/text-edit.png" ) ) )

	def setupEditActions(self):
		tb = QtGui.QToolBar(self)
		tb.setWindowTitle("Edit Actions")
		self.addToolBar(tb)


		self.actionUndo = QtGui.QAction(QtGui.QIcon(rsrcPath + '/../undo_small.png'),"&Undo", self, shortcut=QtGui.QKeySequence.Undo)
		tb.addAction(self.actionUndo)
		self.actionRedo = QtGui.QAction(QtGui.QIcon(rsrcPath + '/../redo_small.png'),
				"&Redo", self, priority=QtGui.QAction.LowPriority,
				shortcut=QtGui.QKeySequence.Redo)
		tb.addAction(self.actionRedo)

		self.actionCut = QtGui.QAction(QtGui.QIcon(rsrcPath + '/cut.png'),
				"Cu&t", self, priority=QtGui.QAction.LowPriority,
				shortcut=QtGui.QKeySequence.Cut)
		tb.addAction(self.actionCut)

		self.actionCopy = QtGui.QAction(QtGui.QIcon(rsrcPath + '/copy.png'),
				"&Copy", self, priority=QtGui.QAction.LowPriority,
				shortcut=QtGui.QKeySequence.Copy)
		tb.addAction(self.actionCopy)
		self.actionPaste = QtGui.QAction(QtGui.QIcon(rsrcPath + '/paste.png'),
				"&Paste", self, priority=QtGui.QAction.LowPriority,
				shortcut=QtGui.QKeySequence.Paste,
				enabled=(len(QtGui.QApplication.clipboard().text()) != 0))
		tb.addAction(self.actionPaste)
		
	def setupInsertActions(self):
		if "a" in self.validHtml["validTags"]:
			tb = QtGui.QToolBar(self)
			tb.setWindowTitle("Insert Actions")
			self.addToolBar(tb)
			self.actionInsertLink = QtGui.QAction(QtGui.QIcon(rsrcPath + '/link.png'),"&Link", self)
			tb.addAction(self.actionInsertLink)

	def setupTextActions(self):
		tb = QtGui.QToolBar(self)
		tb.setWindowTitle("Format Actions")
		self.addToolBar(tb)
		if "b" in self.validHtml["validTags"]:
			self.actionTextBold = QtGui.QAction(QtGui.QIcon(rsrcPath + '/bold.png'),
					"&Bold", self, priority=QtGui.QAction.LowPriority,
					shortcut=QtCore.Qt.CTRL + QtCore.Qt.Key_B,
					triggered=self.textBold, checkable=True)
			bold = QtGui.QFont()
			bold.setBold(True)
			self.actionTextBold.setFont(bold)
			tb.addAction(self.actionTextBold)

		if "i" in self.validHtml["validTags"]:
			self.actionTextItalic = QtGui.QAction(QtGui.QIcon(rsrcPath + '/italic.png'),
					"&Italic", self, priority=QtGui.QAction.LowPriority,
					shortcut=QtCore.Qt.CTRL + QtCore.Qt.Key_I,
					triggered=self.textItalic, checkable=True)
			italic = QtGui.QFont()
			italic.setItalic(True)
			self.actionTextItalic.setFont(italic)
			tb.addAction(self.actionTextItalic)
		
		if "u" in self.validHtml["validTags"]:
			self.actionTextUnderline = QtGui.QAction(QtGui.QIcon(rsrcPath + '/underline.png'),
					"&Underline", self, priority=QtGui.QAction.LowPriority,
					shortcut=QtCore.Qt.CTRL + QtCore.Qt.Key_U,
					triggered=self.textUnderline, checkable=True)
			underline = QtGui.QFont()
			underline.setUnderline(True)
			self.actionTextUnderline.setFont(underline)
			tb.addAction(self.actionTextUnderline)

		if "p" in self.validHtml["validAttrs"].keys() and "align" in self.validHtml["validAttrs"]["p"]:
			grp = QtGui.QActionGroup(self, triggered=self.textAlign)
			# Make sure the alignLeft is always left of the alignRight.
			if QtGui.QApplication.isLeftToRight():
				self.actionAlignLeft = QtGui.QAction(QtGui.QIcon(rsrcPath + '/alignleft.png'),
						"&Left", grp)
				self.actionAlignCenter = QtGui.QAction(QtGui.QIcon(rsrcPath + '/aligncenter.png'),
						"C&enter", grp)
				self.actionAlignRight = QtGui.QAction(QtGui.QIcon(rsrcPath + '/alignright.png'),
						"&Right", grp)
			else:
				self.actionAlignRight = QtGui.QAction(QtGui.QIcon(rsrcPath + '/alignright.png'),
						"&Right", grp)
				self.actionAlignCenter = QtGui.QAction(QtGui.QIcon(rsrcPath + '/aligncenter.png'),
						"C&enter", grp)
				self.actionAlignLeft = QtGui.QAction(QtGui.QIcon(rsrcPath + '/alignleft.png'),
						"&Left", grp)

			self.actionAlignJustify = QtGui.QAction(QtGui.QIcon(rsrcPath + '/alignjustify.png'),
					"&Justify", grp)

			self.actionAlignLeft.setShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_L)
			self.actionAlignLeft.setCheckable(True)
			self.actionAlignLeft.setPriority(QtGui.QAction.LowPriority)

			self.actionAlignCenter.setShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_E)
			self.actionAlignCenter.setCheckable(True)
			self.actionAlignCenter.setPriority(QtGui.QAction.LowPriority)

			self.actionAlignRight.setShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_R)
			self.actionAlignRight.setCheckable(True)
			self.actionAlignRight.setPriority(QtGui.QAction.LowPriority)

			self.actionAlignJustify.setShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_J)
			self.actionAlignJustify.setCheckable(True)
			self.actionAlignJustify.setPriority(QtGui.QAction.LowPriority)

			tb.addActions(grp.actions())

		if "font" in self.validHtml["validAttrs"].keys() and "color" in self.validHtml["validAttrs"]["font"]:
			pix = QtGui.QPixmap(16, 16)
			pix.fill(QtCore.Qt.black)
			self.actionTextColor = QtGui.QAction(QtGui.QIcon(pix), "&Color...",
					self, triggered=self.textColor)
			tb.addAction(self.actionTextColor)
	
		if "ul" in self.validHtml["validTags"]:
			self.actionBulletList = QtGui.QAction(	QtGui.QIcon('icons/actions/text/bullet.png'), "Bullet",
											self,
											triggered=self.onBulletList)
			tb.addAction(self.actionBulletList)
		
		if "ol" in self.validHtml["validTags"]:
			self.actionNumberedList = QtGui.QAction(	QtGui.QIcon('icons/actions/text/numbered.png'), "Numbered",
												self,
												triggered=self.onNumberedList)
			tb.addAction(self.actionNumberedList)

	def save(self, *args, **kwargs):
		html = self.ui.textEdit.toHtml()
		start = html.find(">", html.find("<body") )+1
		html = html[ start : html.rfind("</body>") ]
		html = html.replace("""text-indent:0px;"></p>""", """text-indent:0px;">&nbsp;</p>""")
		self.saveCallback( html )
		event.emit( QtCore.SIGNAL("popWidget(PyQt_PyObject)"), self )


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
			listFmt.setIndent( listFmt.indent() + 1)
		else:
			listFmt.setIndent(blockFmt.indent() + 1)
			blockFmt.setIndent(0)
			cursor.setBlockFormat(blockFmt)
		listFmt.setStyle(style)
		cursor.createList(listFmt)
		cursor.endEditBlock()


	def onNumberedList(self, *args, **kwargs ):
		cursor = self.ui.textEdit.textCursor()
		style = QtGui.QTextListFormat.ListDecimal
		cursor.beginEditBlock()
		blockFmt = cursor.blockFormat()
		listFmt = QtGui.QTextListFormat()
		if cursor.currentList():
			listFmt = cursor.currentList().format()
			listFmt.setIndent( listFmt.indent() + 1)
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


	def insertLink( self, *args, **kwargs ):
		(dest, okay) = QtGui.QInputDialog.getText( self, QtCore.QCoreApplication.translate("TextEditBone", "Specify target"), QtCore.QCoreApplication.translate("TextEditBone", "Link target:") )
		if not okay or not dest:
			return
		cursor = self.ui.textEdit.textCursor()
		if not cursor.hasSelection():
			cursor.select(QtGui.QTextCursor.WordUnderCursor)
		txt = cursor.selectedText()
		self.ui.textEdit.insertHtml( "<a href=\"%s\" target=\"_blank\">%s</a>" % (dest, txt))

	def textAlign(self, action):
		if action == self.actionAlignLeft:
			self.ui.textEdit.setAlignment(
					QtCore.Qt.AlignLeft | QtCore.Qt.AlignAbsolute)
		elif action == self.actionAlignCenter:
			self.ui.textEdit.setAlignment(QtCore.Qt.AlignHCenter)
		elif action == self.actionAlignRight:
			self.ui.textEdit.setAlignment(
					QtCore.Qt.AlignRight | QtCore.Qt.AlignAbsolute)
		elif action == self.actionAlignJustify:
			self.ui.textEdit.setAlignment(QtCore.Qt.AlignJustify)

	def currentCharFormatChanged(self, format):
		self.fontChanged(format.font())
		self.colorChanged(format.foreground().color())

	def cursorPositionChanged(self):
		self.alignmentChanged(self.ui.textEdit.alignment())

	def clipboardDataChanged(self):
		if "actionPaste" in dir( self ):
			self.actionPaste.setEnabled( len(QtGui.QApplication.clipboard().text()) != 0 )

	def mergeFormatOnWordOrSelection(self, format):
		cursor = self.ui.textEdit.textCursor()
		if not cursor.hasSelection():
			cursor.select(QtGui.QTextCursor.WordUnderCursor)
		cursor.mergeCharFormat(format)
		self.ui.textEdit.mergeCurrentCharFormat(format)

	def fontChanged(self, font):
		if "actionTextBold" in dir(self ):
			self.actionTextBold.setChecked(font.bold())
		if "actionTextItalic" in dir(self ):
			self.actionTextItalic.setChecked(font.italic())
		if "actionTextUnderline" in dir(self ):
			self.actionTextUnderline.setChecked(font.underline())

	def colorChanged(self, color):
		if "actionTextColor" in dir( self ):
			pix = QtGui.QPixmap(16, 16)
			pix.fill(color)
			self.actionTextColor.setIcon(QtGui.QIcon(pix))

	def alignmentChanged(self, alignment):
		if alignment & QtCore.Qt.AlignLeft:
			if "actionAlignLeft" in dir( self ):
				self.actionAlignLeft.setChecked(True)
		elif alignment & QtCore.Qt.AlignHCenter:
			if "actionAlignCenter" in dir( self ):
				self.actionAlignCenter.setChecked(True)
		elif alignment & QtCore.Qt.AlignRight:
			if "actionAlignRight" in dir( self ):
				self.actionAlignRight.setChecked(True)
		elif alignment & QtCore.Qt.AlignJustify:
			if "actionAlignJustify" in dir( self ):
				self.actionAlignJustify.setChecked(True)
	
	def on_btnSave_released( self ):
		self.save()

### Copy&Paste from server/bones/textBone.py

_attrsMargins = ["margin","margin-left","margin-right","margin-top","margin-bottom"]
_attrsSpacing = ["spacing","spacing-left","spacing-right","spacing-top","spacing-bottom"]
_attrsDescr = ["title","alt"]
_defaultTags = {
	"validTags": [	'font','b', 'a', 'i', 'u', 'span', 'div','p', 'img', 'ol', 'ul','li','acronym', #List of HTML-Tags which are valid
				'h1','h2','h3','h4','h5','h6', 'table', 'tr', 'td', 'th', 'br', 'hr', 'strong'], 
	"validAttrs": {	"font": ["color"], #Mapping of valid parameters for each tag (if a tag is not listed here: no parameters allowed)
					"a": ["href","target"]+_attrsDescr,
					"acronym": ["title"],
					"div": ["align","width","height"]+_attrsMargins+_attrsSpacing,
					"p":["align","width","height"]+_attrsMargins+_attrsSpacing,
					"span":["align","width","height"]+_attrsMargins+_attrsSpacing,
					"img":[ "src","target", "width","height", "align" ]+_attrsDescr+_attrsMargins+_attrsSpacing,
					"table": [ "width","align", "border", "cellspacing", "cellpadding" ]+_attrsDescr,
					"td" : [ "cellspan", "rowspan", "width", "heigt" ]+_attrsMargins+_attrsSpacing
				}, 
	"validStyles": ["font-weight","font-style","text-decoration","color", "display"], #List of CSS-Directives we allow
	"singleTags": ["br","img", "hr"] # List of tags, which dont have a corresponding end tag
}
del _attrsDescr, _attrsSpacing, _attrsMargins


class HtmlSerializer( html.parser.HTMLParser ): #html.parser.HTMLParser
	def __init__(self, validHtml=None ):
		global _defaultTags
		html.parser.HTMLParser.__init__(self)
		self.result = ""
		self.openTagsList = [] 
		self.validHtml = validHtml

	def handle_data(self, data):
		if data:
			self.result += data

	def handle_charref(self, name):
		self.result += "&#%s;" % ( name )

	def handle_entityref(self, name): #FIXME
		if name in htmlentitydefs.entitydefs.keys(): 
			self.result += "&%s;" % ( name )

	def handle_starttag(self, tag, attrs):
		""" Delete all tags except for legal ones """
		if self.validHtml and tag in self.validHtml["validTags"]:
			self.result = self.result + '<' + tag
			for k, v in attrs:
				if not tag in self.validHtml["validAttrs"].keys() or not k in self.validHtml["validAttrs"][ tag ]:
					continue					
				if k.lower()[0:2] != 'on' and v.lower()[0:10] != 'javascript':
					self.result = '%s %s="%s"' % (self.result, k, v)
			if "style" in [ k for (k,v) in attrs ]:
				syleRes = {}
				styles = [ v for (k,v) in attrs if k=="style"][0].split(";")
				for s in styles:
					style = s[ : s.find(":") ].strip()
					value = s[ s.find(":")+1 : ].strip()
					if style in self.validHtml["validStyles"] and not any( [(x in value) for x in ["\"",":",";"]] ):
						syleRes[ style ] = value
				if len( syleRes.keys() ):
					self.result += " style=\"%s\"" % "; ".join( [("%s: %s" % (k,v)) for (k,v) in syleRes.items()] )
			if tag in self.validHtml["singleTags"]:
				self.result = self.result + ' />'
			else:
				self.result = self.result + '>'
				self.openTagsList.insert( 0, tag)    

	def handle_endtag(self, tag):
		if self.validHtml and tag in self.openTagsList:
			for endTag in self.openTagsList[ : ]: #Close all currently open Tags until we reach the current one
				self.result = "%s</%s>" % (self.result, endTag)
				self.openTagsList.remove( endTag)
				if endTag==tag:
					break

	def cleanup(self): #FIXME: vertauschte tags
		""" Append missing closing tags """
		for tag in self.openTagsList:
			endTag = '</%s>' % tag
			self.result += endTag 
	
	def santinize( self, instr ):
		self.result = ""
		self.openTagsList = [] 
		self.feed( instr )
		self.close()
		self.cleanup()
		return( self.result )

### Copy&Paste: End


class TextEditBone( QtGui.QWidget ):
	def __init__(self, modulName, boneName, skelStructure, *args, **kwargs ):
		super( TextEditBone,  self ).__init__( *args, **kwargs )
		self.skelStructure = skelStructure
		self.boneName = boneName
		self.layout = QtGui.QVBoxLayout( self ) 
		self.btn = QtGui.QPushButton( QtCore.QCoreApplication.translate("TextEditBone", "Open editor"), self )
		iconbtn = QtGui.QIcon()
		iconbtn.addPixmap(QtGui.QPixmap("icons/actions/text-edit_small.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.btn.setIcon(iconbtn)
		self.btn.connect( self.btn, QtCore.SIGNAL("released()"), self.openEditor )
		self.webView = QtWebKit.QWebView(self)
		self.webView.mousePressEvent = self.openEditor
		self.layout.addWidget( self.webView )
		self.layout.addWidget( self.btn )
		self.setSizePolicy( QtGui.QSizePolicy( QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Preferred ) )
		self.html = ""
		self.editor = None

	def sizeHint(self):
		return( QtCore.QSize( 150, 150 ) )

	def openEditor(self, *args, **kwargs ):
		global _defaultTags
		if "plaintext" in self.skelStructure[self.boneName].keys() and self.skelStructure[self.boneName]["plaintext"]:
			editor = RawTextEdit( self.onSave, self.html )
		elif self.skelStructure[self.boneName]["params"] and "plaintext" in self.skelStructure[self.boneName]["params"].keys(): #FIXME:!
			editor = RawTextEdit( self.onSave, self.html, contentType=self.skelStructure[self.boneName]["params"]["plaintext"] )
		elif "validHtml" in self.skelStructure[self.boneName].keys():
			if self.skelStructure[self.boneName]["validHtml"]:
				editor = TextEdit( self.onSave, self.html, self.skelStructure[self.boneName]["validHtml"] )
			else:
				editor = RawTextEdit( self.onSave, self.html )
		else:
			editor = TextEdit( self.onSave, self.html, _defaultTags )
		event.emit( QtCore.SIGNAL('stackWidget(PyQt_PyObject)'), editor )

	def onSave(self, text ):
		self.html = str(text)
		self.webView.setHtml (text)
	
	def unserialize( self, data ):
		if not self.boneName in data.keys():
			return
		self.html = data[ self.boneName ].replace( "target=\"_blank\" href=\"", "href=\"!" ) if data else ""
		self.webView.setHtml (self.html)

	def serialize(self):
		return( self.html.replace("href=\"!", "target=\"_blank\" href=\"" ) )

	def serializeForDocument(self):
		return( self.serialize( ) )

	def remove( self ):
		pass

class TextHandler( QtCore.QObject ):
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('requestBoneViewDelegate(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.onRequestBoneViewDelegate ) #RegisterObj, ModulName, BoneName, SkelStructure
		self.connect( event, QtCore.SIGNAL('requestBoneEditWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.onRequestBoneEditWidget ) 
		
	
	def onRequestBoneViewDelegate(self, registerObject, modulName, boneName, skelStucture):
		if skelStucture[boneName]["type"]=="text":
			registerObject.registerHandler( 5, lambda: TextViewBoneDelegate( registerObject, modulName, boneName, skelStucture ) )

	def onRequestBoneEditWidget(self, registerObject,  modulName, boneName, skelStucture ):
		if skelStucture[boneName]["type"]=="text":
			registerObject.registerHandler( 10, TextEditBone( modulName, boneName, skelStucture ) )

_textHandler = TextHandler()

