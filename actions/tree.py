# -*- coding: utf-8 -*-
from PySide import QtCore, QtGui
from network import NetworkService
from event import event
from config import conf
from time import sleep, time
import sys, os, os.path
from utils import RegisterQueue, Overlay, loadIcon
from handler.list import ListCoreHandler
from mainwindow import WidgetHandler
from widgets.tree import TreeWidget, TreeItem, DirItem
from widgets.edit import EditWidget
from priorityqueue import protocolWrapperInstanceSelector, actionDelegateSelector

class TreeAddAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( TreeAddAction, self ).__init__(  QtGui.QIcon("icons/actions/add_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "Add entry"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.New )
	
	def onTriggered( self, e ):
		name = QtCore.QCoreApplication.translate("TreeHandler", "Add entry")
		widget = lambda: EditWidget(self.parent().tree.modul, EditWidget.appTree, 0, rootNode=self.parent().tree.currentRootNode, path=self.parent().tree.getPath())
		handler = WidgetHandler( widget, descr=name, icon=QtGui.QIcon("icons/actions/add_small.png") )
		event.emit( QtCore.SIGNAL('stackHandler(PyQt_PyObject)'), handler )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "tree" or modul.startswith("tree.")) and actionName=="add")
		
actionDelegateSelector.insert( 1, TreeAddAction.isSuitableFor, TreeAddAction )

class TreeEditAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( TreeEditAction, self ).__init__(  QtGui.QIcon("icons/actions/edit_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "Edit entry"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )

	def onTriggered( self, e ):
		name = QtCore.QCoreApplication.translate("TreeHandler", "Edit entry")
		entries = []
		for item in self.parent().selectedItems():
			if not isinstance( item, DirItem ):
				entries.append( item.entryData )
		for entry in entries:
			widget = lambda: EditWidget( self.parent().modul, EditWidget.appTree, entry["id"], rootNode=self.parent().currentRootNode, path=self.parent().getPath() )
			handler = WidgetHandler( widget, descr=name, icon=QtGui.QIcon("icons/actions/edit_small.png") )
			handler.stackHandler()

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "tree" or modul.startswith("tree.")) and actionName=="edit")
		
actionDelegateSelector.insert( 1, TreeEditAction.isSuitableFor, TreeEditAction )

class TreeDirUpAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( TreeDirUpAction, self ).__init__(  QtGui.QIcon("icons/actions/folder_back_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "Directory up"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
	
	def onTriggered( self, e ):
		self.parent().path = self.parent().path[ : -1 ]
		self.parent().loadData()

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "tree" or modul.startswith("tree.")) and actionName=="dirup")
		
actionDelegateSelector.insert( 1, TreeDirUpAction.isSuitableFor, TreeDirUpAction )

class TreeMkDirAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( TreeMkDirAction, self ).__init__(  QtGui.QIcon("icons/actions/folder_add_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "New directory"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( "SHIFT+Ctrl+N" )
		self.setShortcutContext( QtCore.Qt.WidgetWithChildrenShortcut )
	
	def onTriggered( self, e ):
		(dirName, okay) = QtGui.QInputDialog.getText( self.parent(), QtCore.QCoreApplication.translate("TreeHandler", "Create directory"), QtCore.QCoreApplication.translate("TreeHandler", "Directory name") )
		if dirName and okay:
			self.parent().tree.mkdir( self.parent().tree.currentRootNode, self.parent().tree.getPath(), dirName )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "tree" or modul.startswith("tree.")) and actionName=="mkdir")
		
actionDelegateSelector.insert( 1, TreeMkDirAction.isSuitableFor, TreeMkDirAction )

class TreeDeleteAction( QtGui.QAction ): 
	def __init__(self, parent, *args, **kwargs ):
		super( TreeDeleteAction, self ).__init__(  QtGui.QIcon("icons/actions/delete_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "Delete"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.Delete )
		self.setShortcutContext( QtCore.Qt.WidgetWithChildrenShortcut )
	
	def onTriggered( self, e ):
		dirs = []
		files = []
		for item in self.parent().selectedItems():
			if isinstance( item, DirItem ):
				dirs.append( item.dirName )
			else:
				files.append( item.entryData )
		if not files and not dirs:
			return
		reqWrap = protocolWrapperInstanceSelector.select( self.parent().modul )
		assert reqWrap is not None
		reqWrap.delete( self.parent().currentRootNode, self.parent().getPath(), [ x["name"] for x in files], dirs )
		#self.parent().delete( self.parent().currentRootNode, self.parent().getPath(), [ x["name"] for x in files], dirs )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "tree" or modul.startswith("tree.")) and actionName=="delete")
		
actionDelegateSelector.insert( 1, TreeDeleteAction.isSuitableFor, TreeDeleteAction )
