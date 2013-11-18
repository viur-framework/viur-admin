# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from event import event
from bones.base import BaseViewBoneDelegate
from config import conf
from priorityqueue import editBoneSelector, viewDelegateSelector
from html.parser import HTMLParser

def unescapeHtml( html ):
	if 1:
		return( HTMLParser.unescape(HTMLParser, html) )
	else: #except:
		return( html )

def chooseLang( value, prefs ):
	"""
		Tries to select the best language for the current user.
		Value is the dictionary of lang -> text recived from the server,
		prefs the list of languages (in order of preference) for that bone.
	"""
	if not isinstance( value, dict ):
		return( value )
	try:
		lang = conf.adminConfig["language"]
	except:
		lang = ""
	if lang in value.keys() and value[ lang ]:
		return( value[ lang ] )
	for lang in prefs:
		if lang in value.keys():
			if value[ lang ]:
				return( value[ lang ] )
	return( None )

class StringViewBoneDelegate( BaseViewBoneDelegate ):
	def displayText(self, value, locale ):
		if self.boneName in self.skelStructure.keys():
			if "multiple" in self.skelStructure[ self.boneName ].keys():
				multiple = self.skelStructure[ self.boneName ]["multiple"]
			else:
				multiple = False
			if "languages" in self.skelStructure[ self.boneName ].keys():
				languages = self.skelStructure[ self.boneName ]["languages"]
			else:
				languages = None
			if multiple and languages:
				try:
					value = ", ".join( chooseLang( value, languages ) )
				except:
					value = ""
			elif multiple and not languages:
				value = ", ".join( value )
			elif not multiple and languages:
				value = chooseLang( value, languages )
			else: #Not multiple nor languages
				pass
		return( super(StringViewBoneDelegate, self).displayText( str(value), locale ) )

class Tag( QtGui.QWidget ):
	def __init__( self, tag, editMode, *args, **kwargs ):
		super( Tag,  self ).__init__( *args, **kwargs )
		self.setLayout( QtGui.QHBoxLayout( self ) )
		self.tag = tag
		self.lblDisplay = QtGui.QLabel( tag, self )
		self.editField = QtGui.QLineEdit( tag, self )
		self.btnDelete = QtGui.QPushButton( "Löschen", self )
		self.layout().addWidget( self.lblDisplay )
		self.layout().addWidget( self.editField )
		self.layout().addWidget( self.btnDelete )
		if editMode:
			self.lblDisplay.hide()
			self.editField.show()
		else:
			self.lblDisplay.show()
			self.editField.hide()
		self.editField.editingFinished.connect( self.onEditingFinished )
		self.btnDelete.released.connect( self.deleteLater )
		self.lblDisplay.mousePressEvent = self.onEdit
	
	def onEdit( self, *args, **kwargs ):
		self.lblDisplay.hide()
		self.editField.show()
		self.editField.setFocus()
	
	def onEditingFinished( self, *args, **kwargs ):
		self.tag = self.editField.text()
		self.lblDisplay.setText( str( self.tag ) )
		self.lblDisplay.show()
		self.editField.hide()

class StringEditBone( QtGui.QWidget ):
	def __init__(self, modulName, boneName, readOnly, multiple=False, languages=None, *args, **kwargs ):
		super( StringEditBone,  self ).__init__( *args, **kwargs )
		self.modulName = modulName
		self.boneName = boneName
		self.readOnly = readOnly
		self.multiple = multiple
		self.languages = languages
		self.boneName = boneName
		if self.languages and self.multiple: #FIXME: Multiple and readOnly...
			self.setLayout( QtGui.QVBoxLayout( self ) )
			self.tabWidget = QtGui.QTabWidget( self )
			self.tabWidget.blockSignals(True)
			self.tabWidget.currentChanged.connect( self.onTabCurrentChanged )
			event.connectWithPriority( "tabLanguageChanged", self.onTabLanguageChanged, event.lowPriority )
			self.layout().addWidget( self.tabWidget )
			self.langEdits = {}
			for lang in self.languages:
				container = QtGui.QWidget()
				self.langEdits[ lang ] = container
				container.setLayout( QtGui.QVBoxLayout(container) ) 
				self.tabWidget.addTab( container, lang )
				btnAdd = QtGui.QPushButton( "Hinzufügen", self )
				container.layout().addWidget( btnAdd )
				def genLambda( lang ):
					return lambda *args, **kwargs: self.genTag("",True,lang)
				btnAdd.released.connect( genLambda( lang ) ) #FIXME: Lambda..
			self.tabWidget.blockSignals(False)
			self.tabWidget.show()
		elif self.languages and not self.multiple:
			self.setLayout( QtGui.QVBoxLayout( self ) )
			self.tabWidget = QtGui.QTabWidget( self )
			self.tabWidget.blockSignals(True)
			self.tabWidget.currentChanged.connect( self.onTabCurrentChanged )
			event.connectWithPriority( "tabLanguageChanged", self.onTabLanguageChanged, event.lowPriority )
			self.layout().addWidget( self.tabWidget )
			self.langEdits = {}
			for lang in self.languages:
				edit = QtGui.QLineEdit()
				edit.setReadOnly( self.readOnly )
				self.langEdits[ lang ] = edit
				self.tabWidget.addTab( edit, lang )
			self.tabWidget.blockSignals(False)
		elif not self.languages and self.multiple:
			self.setLayout( QtGui.QVBoxLayout( self ) )
			self.btnAdd = QtGui.QPushButton( "Hinzufügen", self )
			self.layout().addWidget( self.btnAdd )
			self.btnAdd.released.connect( lambda *args, **kwargs: self.genTag("",True) ) #FIXME: Lambda
			self.btnAdd.show()
		else: #not languages and not multiple:
			self.setLayout( QtGui.QVBoxLayout( self ) )
			self.lineEdit = QtGui.QLineEdit( self )
			self.layout().addWidget( self.lineEdit )
			self.lineEdit.show()
			self.lineEdit.setReadOnly( self.readOnly )

	@staticmethod
	def fromSkelStructure( modulName, boneName, skelStructure ):
		readOnly = "readonly" in skelStructure[ boneName ].keys() and skelStructure[ boneName ]["readonly"]
		if boneName in skelStructure.keys():
			if "multiple" in skelStructure[ boneName ].keys():
				multiple = skelStructure[ boneName ]["multiple"]
			else:
				multiple = False
			if "languages" in skelStructure[ boneName ].keys():
				languages = skelStructure[ boneName ]["languages"]
			else:
				languages = None
		return( StringEditBone( modulName, boneName, readOnly, multiple=multiple, languages=languages ) ) 

	def onTabLanguageChanged(self, lang):
		if lang in self.langEdits.keys():
			self.tabWidget.blockSignals(True)
			self.tabWidget.setCurrentWidget( self.langEdits[ lang ] )
			self.tabWidget.blockSignals(False)
	
	def onTabCurrentChanged( self, idx ):
		wdg = self.tabWidget.widget( idx )
		for k, v in self.langEdits.items():
			if v == wdg:
				event.emit( "tabLanguageChanged", k )
				wdg.setFocus()
				return

	def unserialize( self, data ):
		if not self.boneName in data.keys():
			return
		data = data[ self.boneName ]
		if not data:
			return
		if self.languages and self.multiple:
			assert isinstance(data,dict)
			for lang in self.languages:
				if lang in data.keys():
					val = data[ lang ]
					if isinstance( val, str ):
						self.genTag( unescapeHtml(val), lang=lang )
					elif isinstance( val, list ):
						for v in val:
							self.genTag( unescapeHtml(v), lang=lang )
		elif self.languages and not self.multiple:
			assert isinstance(data,dict)
			for lang in self.languages:
				if lang in data.keys():
					self.langEdits[ lang ].setText( unescapeHtml(str(data[ lang ])) )
		elif not self.languages and self.multiple:
			if isinstance( data,list ):
				for tagStr in data:
					self.genTag( unescapeHtml(tagStr) )
			else:
				self.genTag( unescapeHtml(data) )
		elif not self.languages and not self.multiple:
			self.lineEdit.setText( unescapeHtml(str( data )) )
		else: 
			pass

	def serializeForPost(self):
		res = {}
		if self.languages and self.multiple:
			for lang in self.languages:
				res[ "%s.%s" % (self.boneName, lang ) ] = []
				for child in self.langEdits[ lang ].children():
					if isinstance( child, Tag ):
						res[ "%s.%s" % (self.boneName, lang ) ].append( child.tag )
		elif not self.languages and self.multiple:
			res[ self.boneName ] = []
			for child in self.children():
				if isinstance( child, Tag ):
					res[ self.boneName ].append( child.tag )
		elif self.languages and not self.multiple:
			for lang in self.languages:
				txt = self.langEdits[ lang ].text()
				if txt:
					res[ "%s.%s" % (self.boneName, lang) ] = txt
		elif not self.languages and not self.multiple:
			res[ self.boneName ] = self.lineEdit.text()
		return( res )

	def serializeForDocument(self):
		return( self.serialize( ) )

	def genTag( self, tag, editMode=False, lang=None ):
		if lang is not None:
			self.langEdits[ lang ].layout().addWidget( Tag( tag, editMode ) )
		else:
			self.layout().addWidget( Tag( tag, editMode ) )


def CheckForStringBone(  modulName, boneName, skelStucture ):
	return( skelStucture[boneName]["type"]=="str" )

#Register this Bone in the global queue
editBoneSelector.insert( 2, CheckForStringBone, StringEditBone)
viewDelegateSelector.insert( 2, CheckForStringBone, StringViewBoneDelegate)


