# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets
from event import event
from utils import RegisterQueue, Overlay
from ui.relationalselectionUI import Ui_relationalSelector
from widgets.tree import TreeWidget
from ui.treeselectorUI import Ui_TreeSelector
from os import path
from bones.relational import RelationalViewBoneDelegate
from priorityqueue import editBoneSelector, viewDelegateSelector

class TreeDirViewBoneDelegate( RelationalViewBoneDelegate ):
	pass



class TreeDirEditBone( QtWidgets.QWidget ):
	def __init__(self, modulName, boneName, readOnly, destModul, multiple=False, format="$(name)", *args, **kwargs ):
		super( TreeDirEditBone,  self ).__init__( *args, **kwargs )
		self.modulName = modulName
		self.boneName = boneName
		self.readOnly = readOnly
		self.toModul = destModul
		self.multiple = multiple
		self.format = format
		self.targetModulStructure = None
		self.layout = QtGui.QHBoxLayout( self )
		self.addBtn = QtGui.QPushButton( "Auswählen", parent=self )
		iconadd = QtGui.QIcon()
		iconadd.addPixmap(QtGui.QPixmap("icons/actions/change_selection.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.addBtn.setIcon(iconadd)
		self.addBtn.released.connect( self.onAddBtnReleased )
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
			self.delBtn.released.connect( self.onDelBtnReleased )
			self.selection = None
		else:
			self.selection = []
		self.overlay = Overlay( self )
		#NetworkService.request( "/%s/list?amount=1" % self.toModul, successHandler=self.onTargetModulStructureAvaiable ) #Fetch the structure of our referenced modul

	@staticmethod
	def fromSkelStructure( modulName, boneName, skelStructure ):
		readOnly = "readonly" in skelStructure[ boneName ].keys() and skelStructure[ boneName ]["readonly"]
		multiple = skelStructure[boneName]["multiple"]
		destModul = skelStructure[ boneName ]["type"].split(".")[1]
		format= "$(name)"
		if "format" in skelStructure[ boneName ].keys():
			format = skelStructure[ boneName ]["format"]
		return( TreeDirEditBone( modulName, boneName, readOnly, multiple=multiple, destModul=destModul, format=format ) )

	def setSelection(self, selection):
		if self.multiple:
			self.selection = selection
		elif len( selection )>0 :
			self.selection = selection[0]
			self.entry.setText( self.selection.split("/",1)[1] )
		else:
			self.selection = None
	
	def onAddBtnReleased(self, *args, **kwargs ):
		queue = RegisterQueue()
		event.emit( QtCore.SIGNAL('requestTreeDirBoneSelection(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), queue, self.modulName, self.boneName, self.skelStructure, self.selection, self.setSelection )
		self.widget = queue.getBest()()

	def onDelBtnReleased(self, *args, **kwargs ):
		if self.multiple:
			self.selection = []
		else:
			self.selection = None
			self.entry.setText("")

	def unserialize( self, data ):
		if not self.boneName in data.keys():
			return
		self.selection = data[ self.boneName ]
		if not self.multiple:
			path = ""
			try:
				repo, path = data[ self.boneName ].split("/",1)
			except:
				pass
			self.entry.setText( path )

	def serializeForPost(self):
		if self.selection:
			if not self.multiple:
				return( { self.boneName: str( self.selection ) } )
			else:
				return( { self.boneName: self.selection } )
		else:
			return( { self.boneName: None } )


class BaseTreeDirBoneSelector( TreeWidget ):
	def __init__(self, modulName, boneName, skelStructure, selection, setSelection,  *args, **kwargs ):
		self.modul = skelStructure[ boneName ]["type"].split(".")[1]
		self.boneName = boneName
		self.skelStructure = skelStructure
		self.selection = selection
		self.setSelection = setSelection
		self.multiple = skelStructure[boneName]["multiple"]
		QtWidgets.QWidget.__init__( self, *args, **kwargs )
		self.ui = Ui_TreeSelector()
		self.ui.setupUi( self )		
		super( BaseTreeDirBoneSelector, self ).__init__( self.modul, {"name":self.boneName,"handler":"treeItem"}, *args, **kwargs )
		self.loadRepositorys()
		self.setAcceptDrops( True )
		if not self.multiple:
			self.ui.listSelected.hide()
			self.ui.lblSelected.hide()
		else:
			if selection:
				for sel in selection:
					self.ui.listSelected.addItem( self.dirItem(sel.split("/",1)[1] ) )
		#self.ui.listSelected.keyPressEvent = self.onListSelectionEvent
		self.show()
		

	def onBtnSelectReleased(self, *args, **kwargs):
		if not self.multiple:
			for item in self.ui.listWidget.selectedItems():
				if isinstance( item, self.dirItem ):
					path = self.currentRepository+"/"+"/".join( self.path+[ item.dirName ] )
					self.setSelection( [path] )
					event.emit( "popWidget", self )
					return
			path = self.currentRepository+"/"+"/".join( self.path )
			self.setSelection( [path] )
		else:
			self.setSelection( self.selection )
		event.emit( "popWidget", self )
	
	def onListSelectionEvent(self, event ):
		if event.key()==QtCore.Qt.Key_Delete:
			items = self.ui.listSelected.selectedItems()
			for item in items:
				path = self.currentRepository+"/"+"/".join( self.path+[ item.dirName ] )
				self.ui.listSelected.takeItem( self.ui.listSelected.indexFromItem( item ).row() )
				self.selection.remove( path )
	
	def onListWidgetItemDoubleClicked(self, item):
		if isinstance( item, self.treeItem ):
			return
		else:
			super( BaseTreeDirBoneSelector, self ).onListWidgetItemDoubleClicked( item )

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


def CheckForTreeDirBone(  modulName, boneName, skelStucture ):
	return( skelStucture[boneName]["type"].startswith("treedir.") )

#Register this Bone in the global queue
editBoneSelector.insert( 2, CheckForTreeDirBone, TreeDirEditBone)
viewDelegateSelector.insert( 2, CheckForTreeDirBone, TreeDirViewBoneDelegate)
