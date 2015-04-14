#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from event import event
from priorityqueue import editBoneSelector, viewDelegateSelector

class SelectMultiViewBoneDelegate(QtGui.QStyledItemDelegate):
	def __init__(self, modulName, boneName, skelStructure, *args, **kwargs ):
		super( SelectMultiViewBoneDelegate, self ).__init__()
		self.skelStructure = skelStructure
		self.boneName = boneName
		self.modulName=modulName

	def displayText(self, value, locale ):
		boneValues = {str(k): str(v) for k, v in self.skelStructure[ self.boneName ]["values"].items() }
		resStr = ", ".join( [ boneValues[str(x)] for x in value if str(x) in boneValues.keys() ] )
		return( super( SelectMultiViewBoneDelegate, self ).displayText( resStr, locale ) )

class SelectMultiEditBone( QtGui.QWidget ):
	def __init__(self, modulName, boneName, readOnly, values, sortBy="keys", *args, **kwargs ):
		super( SelectMultiEditBone,  self ).__init__(  *args, **kwargs )
		self.modulName = modulName
		self.boneName = boneName
		self.layout = QtGui.QVBoxLayout( self ) 
		self.checkboxes = {}
		tmpList = values
		if sortBy=="keys":
			tmpList.sort( key=lambda x: x[0] ) #Sort by keys
		else:
			tmpList.sort( key=lambda x: x[1] ) #Values
		for key, descr in tmpList:
			cb = QtGui.QCheckBox( descr, self )
			self.layout.addWidget( cb )
			cb.show()
			self.checkboxes[ key ] = cb

	@staticmethod
	def fromSkelStructure( modulName, boneName, skelStructure ):
		readOnly = "readonly" in skelStructure[ boneName ].keys() and skelStructure[ boneName ]["readonly"]
		if "sortBy" in skelStructure[ boneName ].keys():
			sortBy = skelStructure[ boneName ][ "sortBy" ]
		else:
			sortBy = "keys"
		values = list( skelStructure[ boneName ]["values"].items() )
		return( SelectMultiEditBone( modulName, boneName, readOnly, values=values, sortBy=sortBy ) ) 

	def unserialize( self, data ):
		if not self.boneName in data.keys():
			return
		for key, checkbox in self.checkboxes.items():
			checkbox.setChecked( key in data[self.boneName] )

	def serializeForPost(self):
		return( { self.boneName: [ key for key, checkbox in self.checkboxes.items() if checkbox.isChecked() ] } )

	def serializeForDocument(self):
		return( self.serialize( ) )


def CheckForSelectMultiBone(  modulName, boneName, skelStucture ):
	return( skelStucture[boneName]["type"]=="selectmulti" or skelStucture[boneName]["type"].startswith("selectmulti.") )

#Register this Bone in the global queue
editBoneSelector.insert( 2, CheckForSelectMultiBone, SelectMultiEditBone)
viewDelegateSelector.insert( 2, CheckForSelectMultiBone, SelectMultiViewBoneDelegate)
