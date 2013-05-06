# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from event import event
from utils import RegisterQueue, Overlay, formatString
from ui.relationalselectionUI import Ui_relationalSelector
from ui.treeselectorUI import Ui_TreeSelector
from os import path
from bones.relational import RelationalViewBoneDelegate
from widgets.tree import TreeWidget, TreeItem, DirItem
from widgets.selectedEntities import SelectedEntitiesWidget
from priorityqueue import editBoneSelector, viewDelegateSelector

class TreeItemViewBoneDelegate( RelationalViewBoneDelegate ):
	pass

class TreeItemEditBone( QtGui.QWidget ):
	def __init__(self, modulName, boneName, readOnly, destModul, multiple, format="$(name)", *args, **kwargs ):
		super( TreeItemEditBone,  self ).__init__( *args, **kwargs )
		self.modulName = modulName
		self.boneName = boneName
		self.readOnly = readOnly
		self.toModul = destModul
		self.multiple = multiple
		self.format = format
		self.layout = QtGui.QHBoxLayout( self )
		self.addBtn = QtGui.QPushButton( QtCore.QCoreApplication.translate("TreeItemEditBone", "Change selection"), parent=self )
		iconadd = QtGui.QIcon()
		iconadd.addPixmap(QtGui.QPixmap("icons/actions/relationalselect.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.addBtn.setIcon(iconadd)
		self.addBtn.connect( self.addBtn, QtCore.SIGNAL('released()'), self.on_addBtn_released )
		if not self.multiple:
			self.entry = QtGui.QLineEdit( self )
			self.entry.setReadOnly(True)
			self.layout.addWidget( self.entry )
			icon6 = QtGui.QIcon()
			icon6.addPixmap(QtGui.QPixmap("icons/actions/relationaldeselect.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
			self.delBtn = QtGui.QPushButton( "", parent=self )
			self.delBtn.setIcon(icon6)
			self.layout.addWidget( self.addBtn )
			self.layout.addWidget( self.delBtn )
			self.delBtn.connect( self.delBtn, QtCore.SIGNAL('released()'), self.on_delBtn_released )
			self.selection = None
		else:
			self.layout.addWidget( self.addBtn )
			self.selection = []

	@staticmethod
	def fromSkelStructure( modulName, boneName, skelStructure ):
		readOnly = "readonly" in skelStructure[ boneName ].keys() and skelStructure[ boneName ]["readonly"]
		multiple = skelStructure[boneName]["multiple"]
		destModul = skelStructure[ boneName ]["type"].split(".")[1]
		format= "$(name)"
		if "format" in skelStructure[ boneName ].keys():
			format = skelStructure[ boneName ]["format"]
		return( TreeItemEditBone( modulName, boneName, readOnly, multiple=multiple, destModul=destModul, format=format ) )

	def setSelection(self, selection):
		if self.multiple:
			self.selection = selection
		elif len( selection )>0 :
			self.selection = selection[0]
			self.entry.setText( formatString( self.format, {}, self.selection ) ) #FIXME: {} was self.skelStructure
		else:
			self.selection = None
	
	def on_addBtn_released(self, *args, **kwargs ):
		queue = RegisterQueue()
		event.emit( QtCore.SIGNAL('requestTreeItemBoneSelection(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), queue, self.modulName, self.boneName, self.skelStructure, self.selection, self.setSelection )
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
			self.entry.setText( formatString( self.format, {}, data[ self.boneName ] ) ) #FIXME: {} was self.skelStructure

	def serializeForPost(self):
		if self.selection:
			if not self.skelStructure[self.boneName]["multiple"]:
				return( { self.boneName: str( self.selection["id"] ) } )
			else:
				return( { self.boneName: [ str( x["id"] ) for x in self.selection ] } )
		else:
			return( { self.boneName: None } )
	
	def serializeForDocument(self):
		if self.selection:
			if not self.skelStructure[self.boneName]["multiple"]:
				return( str( self.selection ) )
			else:
				return( [ x for x in self.selection ] )
		else:
			return( None )



class BaseTreeItemBoneSelector( QtGui.QWidget ):
	treeItem = None #Allow override of these on class level
	dirItem = None
	
	def __init__(self, modulName, boneName, skelStructure, selection, setSelection, parent=None, widget=None, *args, **kwargs ):
		super( BaseTreeItemBoneSelector, self ).__init__( parent, *args, **kwargs )
		self.modul = skelStructure[ boneName ]["type"].split(".")[1]
		self.boneName = boneName
		self.skelStructure = skelStructure
		self.setSelection = setSelection
		self.multiple = skelStructure[boneName]["multiple"]
		self.ui = Ui_TreeSelector()
		self.ui.setupUi( self )
		if not widget:
			widget = TreeWidget
		self.tree = widget( self.ui.listWidget, self.modul, None, None, treeItem=self.treeItem, dirItem=self.dirItem )
		layout = QtGui.QVBoxLayout( self.ui.listWidget )
		self.toolBar = QtGui.QToolBar( self )
		self.toolBar.setIconSize( QtCore.QSize( 32, 32 ) )
		queue = RegisterQueue()
		event.emit( QtCore.SIGNAL('requestTreeModulActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), queue, self.modul, self )
		for item in queue.getAll():
			i = item( self )
			if isinstance( i, QtGui.QAction ):
				self.toolBar.addAction( i )
				self.ui.listWidget.addAction( i )
			else:
				self.toolBar.addWidget( i )
		layout.addWidget( self.toolBar )
		layout.addWidget( self.tree )
		self.ui.listWidget.setLayout( layout )
		self.tree.show()
		layout = QtGui.QHBoxLayout( self.ui.listSelected )
		self.ui.listSelected.setLayout( layout )
		self.selection = SelectedEntitiesWidget( self, self.modul, selection )
		layout.addWidget( self.selection )
		self.selection.show()
		if not self.multiple:
			self.ui.listSelected.hide()
			self.ui.lblSelected.hide()
			self.ui.btnAddSelected.hide()
		event.emit( QtCore.SIGNAL('stackWidget(PyQt_PyObject)'), self )
		self.connect( self.tree, QtCore.SIGNAL("onItemDoubleClicked(PyQt_PyObject)"), self.on_listWidget_itemDoubleClicked)

	def on_cbRootNode_currentIndexChanged( self, text ): #Fixme: currently disabled
		if not isinstance( text, str ):
			return
		for repo in self.rootNodes:
			if repo["name"] == text:
				self.setRootNode( repo["key"], repo["name"] )
		
	def on_btnSelect_released(self, *args, **kwargs):
		if not self.multiple:
			for item in self.tree.selectedItems():
				if isinstance( item, self.treeItem ):
					self.setSelection( [item.data] )
					event.emit( QtCore.SIGNAL("popWidget(PyQt_PyObject)"), self )
					return
			return
		else:
			self.setSelection( self.selection.get() )
		event.emit( QtCore.SIGNAL("popWidget(PyQt_PyObject)"), self )
	
	def on_listWidget_itemDoubleClicked(self, item):
		if isinstance( item, self.tree.treeItem ):
			if not self.multiple:
				self.setSelection( [item.data] )
				event.emit( QtCore.SIGNAL("popWidget(PyQt_PyObject)"), self )
				return
			else:
				if item.data in self.selection.get():
					return
				self.selection.extend( [item.data] )

	
	def on_btnAddSelected_released(self, *args, **kwargs ):
		items = self.tree.selectedItems()
		for item in items:
			if isinstance( item, self.treeItem ):
				if item.data in self.selection.get():
					continue
				self.selection.extend( [item.data] )

	def onDeleteCurrentSelection( self ):
		items = self.ui.listSelected.selectedItems()
		for item in items:
			self.ui.listSelected.takeItem( self.ui.listSelected.indexFromItem( item ).row() )
			self.selection.remove( item.data )



def CheckForTreeItemBone(  modulName, boneName, skelStucture ):
	return( skelStucture[boneName]["type"].startswith("treeitem.") )

#Register this Bone in the global queue
editBoneSelector.insert( 2, CheckForTreeItemBone, TreeItemEditBone)
viewDelegateSelector.insert( 2, CheckForTreeItemBone, TreeItemViewBoneDelegate)

