# -*- coding: utf-8 -*-
from PySide import QtCore, QtGui
from event import event
from utils import RegisterQueue
from ui.relationalselectionUI import Ui_relationalSelector
from handler.tree import TreeList
from ui.treeselectorUI import Ui_TreeSelector
from os import path
from bones.relational import RelationalViewBoneDelegate

class TreeDirViewBoneDelegate( RelationalViewBoneDelegate ):
	pass



class TreeDirEditBone( QtGui.QWidget ):
	def __init__(self, modulName, boneName, skelStructure, *args, **kwargs ):
		super( TreeDirEditBone,  self ).__init__( *args, **kwargs )
		self.skelStructure = skelStructure
		self.modulName = modulName
		self.boneName = boneName
		self.toModul = self.skelStructure[ self.boneName ]["type"].split(".")[1]
		self.layout = QtGui.QHBoxLayout( self )
		self.addBtn = QtGui.QPushButton( "Auswählen", parent=self )
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
			self.entry.setText( self.selection.split("/",1)[1] )
		else:
			self.selection = None
	
	def on_addBtn_released(self, *args, **kwargs ):
		queue = RegisterQueue()
		event.emit( QtCore.SIGNAL('requestTreeDirBoneSelection(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), queue, self.modulName, self.boneName, self.skelStructure, self.selection, self.setSelection )
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
			path = ""
			try:
				repo, path = data[ self.boneName ].split("/",1)
			except:
				pass
			self.entry.setText( path )

	def serializeForPost(self):
		if self.selection:
			if not self.skelStructure[self.boneName]["multiple"]:
				return( { self.boneName: str( self.selection ) } )
			else:
				return( { self.boneName: self.selection } )
		else:
			return( { self.boneName: None } )


class BaseTreeDirBoneSelector( TreeList ):
	def __init__(self, modulName, boneName, skelStructure, selection, setSelection,  *args, **kwargs ):
		self.modul = skelStructure[ boneName ]["type"].split(".")[1]
		self.boneName = boneName
		self.skelStructure = skelStructure
		self.selection = selection
		self.setSelection = setSelection
		self.multiple = skelStructure[boneName]["multiple"]
		QtGui.QWidget.__init__( self, *args, **kwargs )
		self.ui = Ui_TreeSelector()
		self.ui.setupUi( self )		
		super( BaseTreeDirBoneSelector, self ).__init__( self.modul, {"name":self.boneName,"handler":"treeItem"}, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('reloadlist(PyQt_PyObject)'),self.doReloadData )
		self.loadRepositorys()
		self.setAcceptDrops( True )
		if not self.multiple:
			self.ui.listSelected.hide()
			self.ui.lblSelected.hide()
		else:
			if selection:
				for sel in selection:
					self.ui.listSelected.addItem( self.dirItem(sel.split("/",1)[1] ) )
		self.ui.listSelected.keyPressEvent = self.on_listSelection_event
		self.show()
		

	def on_btnSelect_released(self, *args, **kwargs):
		if not self.multiple:
			for item in self.ui.listWidget.selectedItems():
				if isinstance( item, self.dirItem ):
					path = self.currentRepository+"/"+"/".join( self.path+[ item.dirName ] )
					self.setSelection( [path] )
					event.emit( QtCore.SIGNAL("popWidget(PyQt_PyObject)"), self )
					return
			path = self.currentRepository+"/"+"/".join( self.path )
			self.setSelection( [path] )
		else:
			self.setSelection( self.selection )
		event.emit( QtCore.SIGNAL("popWidget(PyQt_PyObject)"), self )
	
	def on_listSelection_event(self, event ):
		if event.key()==QtCore.Qt.Key_Delete:
			items = self.ui.listSelected.selectedItems()
			for item in items:
				path = self.currentRepository+"/"+"/".join( self.path+[ item.dirName ] )
				self.ui.listSelected.takeItem( self.ui.listSelected.indexFromItem( item ).row() )
				self.selection.remove( path )
	
	def on_listWidget_itemDoubleClicked(self, item):
		if isinstance( item, self.treeItem ):
			return
		else:
			super( BaseTreeDirBoneSelector, self ).on_listWidget_itemDoubleClicked( item )

	def dropEvent(self, event):
		if event.source()==self.ui.listWidget and self.ui.listSelected.childrenRect().contains( self.ui.listSelected.mapFromGlobal( self.mapToGlobal(event.pos()) ) ):
			for item in self.ui.listWidget.selectedItems():
				path = self.currentRepository+"/"+"/".join( self.path+[ item.dirName ] )
				if path in self.selection:
					continue
				self.ui.listSelected.addItem( self.dirItem( path.split("/",1)[1] ) )
				self.selection.append( path )
		else:
			super( BaseTreeDirBoneSelector, self ).dropEvent( event )


	def dragEnterEvent(self, event):
		event.accept()


class TreeDirHandler( QtCore.QObject ):
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('requestTreeDirViewDelegate(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.onRequestBoneViewDelegate ) #RegisterObj, ModulName, BoneName, SkelStructure
		self.connect( event, QtCore.SIGNAL('requestBoneEditWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.onRequestBoneEditWidget ) 
		self.connect( event, QtCore.SIGNAL('requestTreeDirBoneSelection(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.RelationalBoneSeletor )
	
	def onRequestBoneViewDelegate(self, registerObject, modulName, boneName, skelStructure):
		if skelStructure[boneName]["type"].startswith("treedir."):
			registerObject.registerHandler( 10, lambda: TreeDirViewBoneDelegate() )

	def onRequestBoneEditWidget(self, registerObject,  modulName, boneName, skelStructure ):
		if skelStructure[boneName]["type"].startswith("treedir."):
			registerObject.registerHandler( 10, TreeDirEditBone( modulName, boneName, skelStructure ) )

	def RelationalBoneSeletor(self, registerObject, modulName, boneName, skelStructure, selection, setSelection ):
		if skelStructure[boneName]["type"].startswith("treedir."):
			registerObject.registerHandler( 10, lambda: BaseTreeDirBoneSelector( modulName, boneName, skelStructure, selection, setSelection ) )

_TreeDirHandler = TreeDirHandler()
