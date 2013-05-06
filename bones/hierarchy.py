# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from event import event
from utils import RegisterQueue
from ui.relationalselectionUI import Ui_relationalSelector
from ui.hierarchySelectorUI import Ui_HierarchySelector
from widgets.hierarchy import HierarchyWidget, HierarchyItem
from widgets.selectedEntities import SelectedEntitiesWidget
from os import path
from priorityqueue import editBoneSelector, viewDelegateSelector

def formatBoneDescr( data ):
	if data and "name" in data.keys():
		return( str( data["name"] ) )
	else:
		return( "" )

class HierarchyEditBone( QtGui.QWidget ):
	def __init__(self, modulName, boneName, readOnly, destModul, multiple, format="$(name)", *args, **kwargs ):
		super( HierarchyEditBone,  self ).__init__( *args, **kwargs )
		self.modulName = modulName
		self.boneName = boneName
		self.toModul = destModul
		self.readOnly = readOnly
		self.multiple = multiple
		self.format = format
		self.layout = QtGui.QHBoxLayout( self )
		self.addBtn = QtGui.QPushButton( "Auswählen", parent=self )
		iconadd = QtGui.QIcon()
		iconadd.addPixmap(QtGui.QPixmap("icons/actions/relationalselect.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.addBtn.setIcon(iconadd)
		self.addBtn.connect( self.addBtn, QtCore.SIGNAL('released()'), self.on_addBtn_released )
		self.layout.addWidget( self.addBtn )
		if not self.multiple:
			self.entry = QtGui.QLineEdit( self )
			self.entry.setReadOnly(True)
			self.layout.addWidget( self.entry )
			icon6 = QtGui.QIcon()
			icon6.addPixmap(QtGui.QPixmap("icons/actions/relationaldeselect.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
			self.delBtn = QtGui.QPushButton( "", parent=self )
			self.delBtn.setIcon(icon6)
			self.layout.addWidget( self.delBtn )
			self.delBtn.connect( self.delBtn, QtCore.SIGNAL('released()'), self.on_delBtn_released )
			self.selection = None
		else:
			self.selection = []
			
	@staticmethod
	def fromSkelStructure( modulName, boneName, skelStructure ):
		readOnly = "readonly" in skelStructure[ boneName ].keys() and skelStructure[ boneName ]["readonly"]
		multiple = skelStructure[boneName]["multiple"]
		destModul = skelStructure[ boneName ]["type"].split(".")[1]
		format= "$(name)"
		if "format" in skelStructure[ boneName ].keys():
			format = skelStructure[ boneName ]["format"]
		return( HierarchyEditBone( modulName, boneName, readOnly, multiple=multiple, destModul=destModul, format=format ) )

	def setSelection(self, selection):
		if self.skelStructure[self.boneName]["multiple"]:
			self.selection = selection
		elif len( selection )>0 :
			self.selection = selection[0]
			self.entry.setText( formatBoneDescr( self.selection ) )
		else:
			self.selection = None
	
	def on_addBtn_released(self, *args, **kwargs ):
		queue = RegisterQueue()
		event.emit( QtCore.SIGNAL('requestHierarchyBoneSelection(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), queue, self.modulName, self.boneName, self.skelStructure, self.selection, self.setSelection )
		self.widget = queue.getBest()()

	def on_delBtn_released(self, *args, **kwargs ):
		if self.skelStructure[ self.boneName ]["multiple"]:
			self.selection = []
		else:
			self.selection = None
			self.entry.setText("")

	def unserialize( self, data ):
		if not self.boneName in data.keys():
			return
		self.selection = data[ self.boneName ]
		if not self.multiple:
			self.entry.setText( formatBoneDescr( data[ self.boneName ] ) )

	def serializeForPost(self):
		if self.selection:
			if not self.skelStructure[self.boneName]["multiple"]:
				return( { self.boneName: str( self.selection["id"] ) } )
			else:
				return( { self.boneName: [ str( x["id"] ) for x in self.selection ] } )
		else:
			return( {} )
	
	def serializeForDocument(self):
		if self.selection:
			if not self.skelStructure[self.boneName]["multiple"]:
				return( str( self.selection ) )
			else:
				return( [ x for x in self.selection ] )
		else:
			return( None )




def CheckForHierarchyBone(  modulName, boneName, skelStucture ):
	return( skelStucture[boneName]["type"].startswith("hierarchy.") )

#Register this Bone in the global queue
editBoneSelector.insert( 2, CheckForHierarchyBone, HierarchyEditBone)

