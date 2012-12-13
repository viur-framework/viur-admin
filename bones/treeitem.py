# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from event import event
from utils import RegisterQueue, Overlay, formatString
from ui.relationalselectionUI import Ui_relationalSelector
from handler.tree import TreeList
from ui.treeselectorUI import Ui_TreeSelector
from os import path
from bones.relational import RelationalViewBoneDelegate

class TreeItemViewBoneDelegate( RelationalViewBoneDelegate ):
	pass

class TreeItemEditBone( QtGui.QWidget ):
	def __init__(self, modulName, boneName, skelStructure, *args, **kwargs ):
		super( TreeItemEditBone,  self ).__init__( *args, **kwargs )
		self.skelStructure = skelStructure
		self.modulName = modulName
		self.boneName = boneName
		self.toModul = self.skelStructure[ self.boneName ]["type"].split(".")[1]
		self.format = "$(name)"
		if "format" in skelStructure[ boneName ].keys():
			self.format = skelStructure[ boneName ]["format"]
		self.layout = QtGui.QHBoxLayout( self )
		self.addBtn = QtGui.QPushButton( QtCore.QCoreApplication.translate("TreeItemEditBone", "Select"), parent=self )
		iconadd = QtGui.QIcon()
		iconadd.addPixmap(QtGui.QPixmap("icons/actions/relationalselect.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.addBtn.setIcon(iconadd)
		self.addBtn.connect( self.addBtn, QtCore.SIGNAL('released()'), self.on_addBtn_released )
		self.layout.addWidget( self.addBtn )
		if not skelStructure[boneName]["multiple"]:
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

	def setSelection(self, selection):
		if self.skelStructure[self.boneName]["multiple"]:
			self.selection = selection
		elif len( selection )>0 :
			self.selection = selection[0]
			self.entry.setText( formatString( self.format, self.selection ) )
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
		if not self.skelStructure[self.boneName]["multiple"]:
			self.entry.setText( formatString( self.format, data[ self.boneName ] ) )

	def serialize(self):
		if self.selection:
			if not self.skelStructure[self.boneName]["multiple"]:
				return( str( self.selection["id"] ) )
			else:
				return( [ str( x["id"] ) for x in self.selection ] )
		else:
			return( None )
	
	def serializeForDocument(self):
		if self.selection:
			if not self.skelStructure[self.boneName]["multiple"]:
				return( str( self.selection ) )
			else:
				return( [ x for x in self.selection ] )
		else:
			return( None )

class BaseTreeItemBoneSelector( TreeList ):
	def __init__(self, modulName, boneName, skelStructure, selection, setSelection, parent=None,  *args, **kwargs ):
		self.modul = skelStructure[ boneName ]["type"].split(".")[1]
		self.boneName = boneName
		self.skelStructure = skelStructure
		self.selection = selection
		self.setSelection = setSelection
		self.multiple = skelStructure[boneName]["multiple"]
		QtGui.QWidget.__init__( self, parent )
		self.ui = Ui_TreeSelector()
		self.ui.setupUi( self )
		self.overlay = Overlay( self )
		self.toolBar = QtGui.QToolBar( self.ui.wdgActions )
		self.toolBar.setIconSize( QtCore.QSize( 32, 32 ) )
		super( BaseTreeItemBoneSelector, self ).__init__( self.modul, *args, **kwargs )
		self.ui.boxActions.insertWidget( 0, self.toolBar )
		queue = RegisterQueue()
		event.emit( QtCore.SIGNAL('requestTreeModulActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), queue, self.modul, self )
		for item in queue.getAll():
			i = item( self )
			if isinstance( i, QtGui.QAction ):
				self.toolBar.addAction( i )
				self.ui.listWidget.addAction( i )
			else:
				self.toolBar.addWidget( i )
		self.setAcceptDrops( True )
		#self.clipboard = None  #(str repo,str path, bool doMove, list treeItems, list dirs )
		if not self.multiple:
			self.ui.listSelected.hide()
			self.ui.lblSelected.hide()
			self.ui.btnAddSelected.hide()
		else:
			if selection:
				for sel in selection:
					self.ui.listSelected.addItem( self.treeItem( sel ) )
		#self.ui.listSelected.keyPressEvent = self.on_listSelection_event
		self.delShortcut = QtGui.QShortcut( self.ui.listSelected )
		self.delShortcut.setContext( QtCore.Qt.WidgetWithChildrenShortcut )
		self.delShortcut.setKey( QtGui.QKeySequence.Delete )
		self.connect( self.delShortcut, QtCore.SIGNAL("activated()"), self.onDeleteCurrentSelection )
		event.emit( QtCore.SIGNAL('stackWidget(PyQt_PyObject)'), self )
		
	def onSetDefaultRootNode(self):
		super( BaseTreeItemBoneSelector, self ).onSetDefaultRootNode()
		if self.rootNodes and len( self.rootNodes )>1:
			self.ui.cbRootNode.blockSignals( True )
			self.ui.cbRootNode.show()
			self.ui.cbRootNode.clear()
			for repo in self.rootNodes:
				self.ui.cbRootNode.addItem( repo["name"] )
			self.ui.cbRootNode.setCurrentIndex( 0 )
			self.ui.cbRootNode.blockSignals( False )
		else:
			self.ui.cbRootNode.hide()
	
	def on_cbRootNode_currentIndexChanged( self, text ):
		if not isinstance( text, str ):
			return
		for repo in self.rootNodes:
			if repo["name"] == text:
				self.setRootNode( repo["key"], repo["name"] )
		
	def on_btnSelect_released(self, *args, **kwargs):
		if not self.multiple:
			for item in self.ui.listWidget.selectedItems():
				if isinstance( item, self.treeItem ):
					self.setSelection( [item.data] )
					event.emit( QtCore.SIGNAL("popWidget(PyQt_PyObject)"), self )
					return
			return
		else:
			self.setSelection( self.selection )
		event.emit( QtCore.SIGNAL("popWidget(PyQt_PyObject)"), self )
	
	def on_listWidget_itemDoubleClicked(self, item):
		if isinstance( item, self.treeItem ):
			if not self.multiple:
				self.setSelection( [item.data] )
				event.emit( QtCore.SIGNAL("popWidget(PyQt_PyObject)"), self )
				return
			else:
				if not self.selection:
					self.selection = []
				if item.data in self.selection:
					return
				self.ui.listSelected.addItem( self.treeItem( item.data ) )
				self.selection.append( item.data )
		else:
			super( BaseTreeItemBoneSelector, self ).on_listWidget_itemDoubleClicked( item )
	
	def on_listSelected_itemDoubleClicked(self, item):
		self.ui.listSelected.takeItem( self.ui.listSelected.indexFromItem( item ).row() )
		self.selection.remove( item.data )
	
	def on_btnAddSelected_released(self, *args, **kwargs ):
		items = self.ui.listWidget.selectedItems()
		for item in items:
			if isinstance( item, self.treeItem ):
				if not self.selection:
					self.selection = []
				if item.data in self.selection:
					continue
				self.ui.listSelected.addItem( self.treeItem( item.data ) )
				self.selection.append( item.data )

	def onDeleteCurrentSelection( self ):
		items = self.ui.listSelected.selectedItems()
		for item in items:
			self.ui.listSelected.takeItem( self.ui.listSelected.indexFromItem( item ).row() )
			self.selection.remove( item.data )
	
	def dropEvent(self, event):
		if event.source()==self.ui.listWidget and self.ui.listSelected.childrenRect().contains( self.ui.listSelected.mapFromGlobal( self.mapToGlobal(event.pos()) ) ):
			if not self.selection:
				self.selection = []
			for item in self.ui.listWidget.selectedItems():
				if item.data in self.selection:
					continue
				self.ui.listSelected.addItem( self.treeItem( item.data ) )
				self.selection.append( item.data )
		else:
			super( BaseTreeItemBoneSelector, self ).dropEvent( event )


	def dragEnterEvent(self, event):
		event.accept()


class TreeItemHandler( QtCore.QObject ):
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('requestTreeItemViewDelegate(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.onRequestBoneViewDelegate ) #RegisterObj, ModulName, BoneName, SkelStructure
		self.connect( event, QtCore.SIGNAL('requestBoneEditWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.onRequestBoneEditWidget ) 
		self.connect( event, QtCore.SIGNAL('requestTreeItemBoneSelection(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.RelationalBoneSeletor )
	
	def onRequestBoneViewDelegate(self, registerObject, modulName, boneName, skelStructure):
		if skelStructure[boneName]["type"].startswith("treeitem."):
			registerObject.registerHandler( 10, lambda: TreeItemViewBoneDelegate() )

	def onRequestBoneEditWidget(self, registerObject,  modulName, boneName, skelStructure ):
		if skelStructure[boneName]["type"].startswith("treeitem."):
			registerObject.registerHandler( 10, TreeItemEditBone( modulName, boneName, skelStructure ) )

	def RelationalBoneSeletor(self, registerObject, modulName, boneName, skelStructure, selection, setSelection ):
		if skelStructure[boneName]["type"].startswith("treeitem."):
			registerObject.registerHandler( 10, lambda: BaseTreeItemBoneSelector( modulName, boneName, skelStructure, selection, setSelection ) )

_TreeItemHandler = TreeItemHandler()
