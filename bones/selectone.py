#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from event import event
from bones.base import BaseViewBoneDelegate
from priorityqueue import editBoneSelector, viewDelegateSelector, protocolWrapperInstanceSelector

class SelectOneViewBoneDelegate(BaseViewBoneDelegate):
	def displayText(self, value, locale ):
		items = dict( [(str(k), str(v)) for k, v in self.skelStructure[ self.boneName ]["values"].items() ] )
		if str(value) in items.keys():
			return ( items[str(value)])
		else:
			return( value )

class SelectOneEditBone( QtGui.QWidget ):
	def __init__(self, modulName, boneName, readOnly, values, sortBy="keys", *args, **kwargs ):
		super( SelectOneEditBone,  self ).__init__( *args, **kwargs )
		self.modulName = modulName
		self.boneName = boneName
		self.readOnly = readOnly
		self.values = values
		self.layout = QtGui.QVBoxLayout( self ) 
		self.comboBox = QtGui.QComboBox( self )
		self.layout.addWidget( self.comboBox )
		tmpList = values
		if sortBy=="keys":
			tmpList.sort( key=lambda x: x[0] ) #Sort by keys
		else:
			tmpList.sort( key=lambda x: x[1] ) #Values
		self.comboBox.addItems( [x[1] for x in tmpList ] )

	@staticmethod
	def fromSkelStructure( modulName, boneName, skelStructure ):
		readOnly = "readonly" in skelStructure[ boneName ].keys() and skelStructure[ boneName ]["readonly"]
		if "sortBy" in skelStructure[ boneName ].keys():
			sortBy = skelStructure[ boneName ][ "sortBy" ]
		else:
			sortBy = "keys"
		values = list( skelStructure[ boneName ]["values"].items() )
		return( SelectOneEditBone( modulName, boneName, readOnly, values=values, sortBy=sortBy ) )

	def unserialize( self, data ):
		protoWrap = protocolWrapperInstanceSelector.select( self.modulName )
		assert protoWrap is not None
		try: #There might be junk comming from the server
			items = dict( [(str(k), str(v)) for k, v in protoWrap.structure[ self.boneName ]["values"].items() ] )
			if str(data[ self.boneName]) in items.keys():
				self.comboBox.setCurrentIndex( self.comboBox.findText( items[ str(data[ self.boneName]) ] ) )
			else:
				self.comboBox.setCurrentIndex(-1)
		except:
			self.comboBox.setCurrentIndex(-1)

	def serializeForPost(self):
		for key, value in self.values:
			if str(value) == str( self.comboBox.currentText() ):
				return( { self.boneName: str(key) } )
		return( { self.boneName: None } )
		
	def serializeForDocument(self):
		return( self.serialize( ) )


def CheckForSelectOneBone(  modulName, boneName, skelStucture ):
	return( skelStucture[boneName]["type"]=="selectone" )

#Register this Bone in the global queue
editBoneSelector.insert( 2, CheckForSelectOneBone, SelectOneEditBone)
viewDelegateSelector.insert( 2, CheckForSelectOneBone, SelectOneViewBoneDelegate)



