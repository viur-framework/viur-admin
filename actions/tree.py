# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from network import NetworkService
from event import event
from config import conf
from time import sleep, time
import sys, os, os.path
from utils import RegisterQueue, Overlay, loadIcon
from handler.list import ListCoreHandler
from mainwindow import WidgetHandler
from widgets.tree import TreeWidget
from widgets.edit import EditWidget
from priorityqueue import protocolWrapperInstanceSelector, actionDelegateSelector

class TreeAddAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( TreeAddAction, self ).__init__(  QtGui.QIcon("icons/actions/add_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "Add entry"), parent )
		self.triggered.connect( self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.New )
	
	def onTriggered( self, e ):
		name = QtCore.QCoreApplication.translate("TreeHandler", "Add entry")
		widget = lambda: EditWidget(self.parent().tree.modul, EditWidget.appTree, 0, rootNode=self.parent().tree.rootNode, path=self.parent().tree.getPath())
		handler = WidgetHandler( widget, descr=name, icon=QtGui.QIcon("icons/actions/add_small.png") )
		event.emit( QtCore.SIGNAL('stackHandler(PyQt_PyObject)'), handler )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "tree" or modul.startswith("tree.")) and actionName=="add")
		
actionDelegateSelector.insert( 1, TreeAddAction.isSuitableFor, TreeAddAction )

class TreeEditAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( TreeEditAction, self ).__init__(  QtGui.QIcon("icons/actions/edit_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "Edit entry"), parent )
		self.parent().currentItemChanged.connect( self.onCurrentItemChanged )
		self.triggered.connect( self.onTriggered )

	def onCurrentItemChanged( self, current, previous ):
		if isinstance( current, self.parent().getLeafItemClass() ): #Its a directory, we cant edit that
			self.setEnabled( False )
		else:
			self.setEnabled( True )

	def onTriggered( self, e ):
		name = QtCore.QCoreApplication.translate("TreeHandler", "Edit entry")
		entries = []
		for item in self.parent().selectedItems():
			if isinstance( item, self.parent().getLeafItemClass() ):
				entries.append( item.entryData )
		for entry in entries:
			if isinstance( item, self.parent().getLeafItemClass() ):
				skelType="leaf"
			else:
				skelType="node"
			widget = lambda: EditWidget( self.parent().modul, EditWidget.appTree, entry["id"], skelType=skelType )
			handler = WidgetHandler( widget, descr=name, icon=QtGui.QIcon("icons/actions/edit_small.png") )
			handler.stackHandler()

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "tree" or modul.startswith("tree.")) and actionName=="edit")
		
actionDelegateSelector.insert( 1, TreeEditAction.isSuitableFor, TreeEditAction )

class TreeDirUpAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( TreeDirUpAction, self ).__init__(  QtGui.QIcon("icons/actions/folder_back_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "Directory up"), parent )
		self.parent().nodeChanged.connect( self.onNodeChanged )
		reqWrap = protocolWrapperInstanceSelector.select( self.parent().modul )
		assert reqWrap is not None
		if self.parent().getNode() in [ x["key"] for x in reqWrap.rootNodes ]:
			self.setEnabled( False )
		self.triggered.connect( self.onTriggered )
	
	def onNodeChanged( self, node ):
		print( "0"*10, node)
		reqWrap = protocolWrapperInstanceSelector.select( self.parent().modul )
		assert reqWrap is not None
		node = reqWrap.getNode( self.parent().getNode() )
		if not node["parentdir"]:
			self.setEnabled( False )
		else:
			self.setEnabled( True )
	
	def onTriggered( self, e ):
		reqWrap = protocolWrapperInstanceSelector.select( self.parent().modul )
		assert reqWrap is not None
		node = reqWrap.getNode( self.parent().getNode() )
		if node:
			print( node )
			if node["parentdir"]:
				self.parent().setNode( node["parentdir"], isInitialCall=True )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "tree" or modul.startswith("tree.")) and actionName=="dirup")
		
actionDelegateSelector.insert( 1, TreeDirUpAction.isSuitableFor, TreeDirUpAction )

class TreeMkDirAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( TreeMkDirAction, self ).__init__(  QtGui.QIcon("icons/actions/folder_add_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "New directory"), parent )
		self.triggered.connect( self.onTriggered )
		self.setShortcut( "SHIFT+Ctrl+N" )
		self.setShortcutContext( QtCore.Qt.WidgetWithChildrenShortcut )
	
	def onTriggered( self, e ):
		(dirName, okay) = QtGui.QInputDialog.getText( self.parent(), QtCore.QCoreApplication.translate("TreeHandler", "Create directory"), QtCore.QCoreApplication.translate("TreeHandler", "Directory name") )
		if dirName and okay:
			reqWrap = protocolWrapperInstanceSelector.select( self.parent().modul )
			assert reqWrap is not None
			reqWrap.mkdir( self.parent().tree.node, dirName )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "tree" or modul.startswith("tree.")) and actionName=="mkdir")
		
actionDelegateSelector.insert( 1, TreeMkDirAction.isSuitableFor, TreeMkDirAction )

class TreeDeleteAction( QtGui.QAction ): 
	def __init__(self, parent, *args, **kwargs ):
		super( TreeDeleteAction, self ).__init__(  QtGui.QIcon("icons/actions/delete_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "Delete"), parent )
		self.triggered.connect( self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.Delete )
		self.setShortcutContext( QtCore.Qt.WidgetWithChildrenShortcut )
	
	def onTriggered( self, e ):
		nodes = []
		leafs = []
		for item in self.parent().selectedItems():
			if isinstance( item, self.parent().getNodeItemClass() ):
				nodes.append( item.entryData["id"] )
			else:
				leafs.append( item.entryData["id"] )
		self.parent().requestDelete( nodes, leafs )
		#self.parent().delete( self.parent().rootNode, self.parent().getPath(), [ x["name"] for x in files], dirs )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "tree" or modul.startswith("tree.")) and actionName=="delete")
		
actionDelegateSelector.insert( 1, TreeDeleteAction.isSuitableFor, TreeDeleteAction )
