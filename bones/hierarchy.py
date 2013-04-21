# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from event import event
from utils import RegisterQueue
from ui.relationalselectionUI import Ui_relationalSelector
from handler.hierarchy import HierarchyList
from ui.hierarchySelectorUI import Ui_HierarchySelector
from widgets.hierarchy import HierarchyWidget, HierarchyItem
from widgets.selectedEntities import SelectedEntitiesWidget
from os import path

def formatBoneDescr( data ):
	if data and "name" in data.keys():
		return( str( data["name"] ) )
	else:
		return( "" )

class HierarchyEditBone( QtGui.QWidget ):
	def __init__(self, modulName, boneName, skelStructure, *args, **kwargs ):
		super( HierarchyEditBone,  self ).__init__( *args, **kwargs )
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
		if not self.skelStructure[self.boneName]["multiple"]:
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



class BaseHierarchyBoneSelector( QtGui.QWidget ):
	
	class SelectionItem(QtGui.QListWidgetItem):
		def __init__( self, data ):
			if isinstance( data, dict ) and "name" in data:
				name = str( data["name"] )
			else:
				name = " - "
			super( BaseHierarchyBoneSelector.SelectionItem, self ).__init__( QtGui.QIcon("icons/filetypes/unknown.png"), str( name ) )
			self.data = data

	def __init__(self, modulName, boneName, skelStructure, selection, setSelection, parent=None,  *args, **kwargs ):
		super( BaseHierarchyBoneSelector, self ).__init__( parent, *args, **kwargs )
		self.modul = skelStructure[ boneName ]["type"].split(".")[1]
		self.boneName = boneName
		self.skelStructure = skelStructure
		self.setSelection = setSelection
		self.multiple = skelStructure[boneName]["multiple"]
		self.ui = Ui_HierarchySelector()
		self.ui.setupUi( self )		
		layout = QtGui.QHBoxLayout( self.ui.hierarchyWidget )
		self.ui.hierarchyWidget.setLayout( layout )
		self.hierarchy = HierarchyWidget( self.ui.hierarchyWidget, self.modul )
		layout.addWidget( self.hierarchy )
		layout = QtGui.QHBoxLayout( self.ui.listSelected )
		self.ui.listSelected.setLayout( layout )
		#parent, modul, selection=None, treeItem=None, dragSource=None,
		self.selection = SelectedEntitiesWidget( self, self.modul, selection )
		layout.addWidget( self.selection )
		self.selection.show()
		#self.ui.treeWidget.addChild( self.hierarchy )
		self.hierarchy.show()
		#self.clipboard = None  #(str repo,str path, bool doMove, list Hierarchys, list dirs )
		if not self.multiple:
			self.ui.listSelected.hide()
			self.ui.lblSelected.hide()
		self.ui.listSelected.keyPressEvent = self.on_listSelection_event
		event.emit( QtCore.SIGNAL('stackWidget(PyQt_PyObject)'), self )
		self.connect( self.hierarchy, QtCore.SIGNAL("onItemDoubleClicked(PyQt_PyObject)"), self.on_treeWidget_itemDoubleClicked )
		
	
	def on_cbRepository_currentIndexChanged( self, text ):
		if not isinstance( text, str ):
			return
		for repo in self.repositorys:
			if repo["name"] == text:
				self.setRepository( repo["key"], repo["name"] )
		
	def on_btnSelect_released(self, *args, **kwargs):
		if not self.multiple:
			for item in self.ui.listWidget.selectedItems():
				if isinstance( item, self.Hierarchy ):
					self.setSelection( [item.data] )
					event.emit( QtCore.SIGNAL("popWidget(PyQt_PyObject)"), self )
					return
			return
		else:
			self.setSelection( self.selection.get() )
		event.emit( QtCore.SIGNAL("popWidget(PyQt_PyObject)"), self )
	
	def on_treeWidget_itemDoubleClicked(self, item):
		if not self.multiple:
			self.setSelection( [item] )
			event.emit( QtCore.SIGNAL("popWidget(PyQt_PyObject)"), self )
			return
		else:
			self.selection.extend( [item] )

	def on_listSelection_event(self, event ):
		if event.key()==QtCore.Qt.Key_Delete:
			items = self.ui.listSelected.selectedItems()
			for item in items:
				self.ui.listSelected.takeItem( self.ui.listSelected.indexFromItem( item ).row() )
				self.selection.remove( item.data )
	
class HierarchyHandler( QtCore.QObject ):
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		#self.connect( event, QtCore.SIGNAL('requestHierarchyViewDelegate(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.onRequestBoneViewDelegate ) #RegisterObj, ModulName, BoneName, SkelStructure
		self.connect( event, QtCore.SIGNAL('requestBoneEditWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.onRequestBoneEditWidget ) 
		self.connect( event, QtCore.SIGNAL('requestHierarchyBoneSelection(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.RelationalBoneSeletor )
	
	# Fixme: sad
	#def onRequestBoneViewDelegate(self, registerObject, modulName, boneName, skelStructure):
	#	if skelStructure[boneName]["type"].startswith("hierarchy."):
	#		registerObject.registerHandler( 10, lambda: HierarchyViewBoneDelegate() )

	def onRequestBoneEditWidget(self, registerObject,  modulName, boneName, skelStructure ):
		if skelStructure[boneName]["type"].startswith("hierarchy."):
			registerObject.registerHandler( 10, HierarchyEditBone( modulName, boneName, skelStructure ) )

	def RelationalBoneSeletor(self, registerObject, modulName, boneName, skelStructure, selection, setSelection ):
		if skelStructure[boneName]["type"].startswith("hierarchy."):
			registerObject.registerHandler( 10, lambda: BaseHierarchyBoneSelector( modulName, boneName, skelStructure, selection, setSelection ) )

_HierarchyHandler = HierarchyHandler()
