#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from event import event
from priorityqueue import editBoneSelector, viewDelegateSelector


class BaseViewBoneDelegate(QtGui.QStyledItemDelegate):
	def __init__(self, modulName, boneName, skelStructure, *args, **kwargs ):
		super( BaseViewBoneDelegate, self ).__init__()
		self.skelStructure = skelStructure
		self.boneName = boneName
		self.modulName=modulName


class BaseEditBone( QtGui.QWidget ):
	def getLineEdit(self):
		return (QtGui.QLineEdit( self ))
	
	def setParams(self):
		if self.readOnly:
			self.lineEdit.setReadOnly( True )
		else:
			self.lineEdit.setReadOnly( False )

	def __init__(self, modulName, boneName, readOnly, *args, **kwargs ):
		super( BaseEditBone,  self ).__init__( *args, **kwargs )
		self.boneName = boneName
		self.readOnly = readOnly
		self.layout = QtGui.QHBoxLayout( self ) 
		self.lineEdit = self.getLineEdit()
		self.layout.addWidget( self.lineEdit )
		self.setParams()
		self.lineEdit.show()
		
	@staticmethod
	def fromSkelStructure( modulName, boneName, skelStructure ):
		readOnly = "readonly" in skelStructure[ boneName ].keys() and skelStructure[ boneName ]["readonly"]
		return( BaseEditBone( modulName, boneName, readOnly ) ) 
	
	def unserialize(self, data):
		if self.boneName in data.keys():
			self.lineEdit.setText( str( data[ self.boneName ] ) if data[ self.boneName ] else "" )
	
	def serializeForPost(self):
		return( { self.boneName: self.lineEdit.displayText() } )

	def serializeForDocument(self):
		return( self.serialize( ) )
		

#Register this Bone in the global queue
editBoneSelector.insert( 0, lambda *args, **kwargs: True, BaseEditBone)
viewDelegateSelector.insert( 0, lambda *args, **kwargs: True, BaseViewBoneDelegate)
