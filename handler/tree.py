# -*- coding: utf-8 -*-
from ui.treeUI import Ui_Tree
from PyQt4 import QtCore, QtGui, QtNetwork
from network import NetworkService
from event import event
from config import conf
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse
from time import sleep, time
import sys, os, os.path
from utils import RegisterQueue, Overlay
from handler.list import ListCoreHandler
from mainwindow import WidgetHandler
from widgets.tree import TreeWidget, TreeItem, DirItem
from widgets.edit import EditWidget



class TreeList( QtGui.QWidget ):
	treeItem = None #Allow override of these on class level
	dirItem = None
	
	def __init__(self, modul, currentRootNode=None, path=None, *args, **kwargs ):
		super( TreeList, self ).__init__( *args, **kwargs )
		config = conf.serverConfig["modules"][ modul ]
		self.ui = Ui_Tree()
		self.ui.setupUi( self )
		layout = QtGui.QHBoxLayout( self.ui.listWidget )
		self.ui.listWidget.setLayout( layout )
		self.tree = TreeWidget( self.ui.listWidget, modul, currentRootNode, path, treeItem=self.treeItem, dirItem=self.dirItem )
		layout.addWidget( self.tree )
		self.tree.show()
		self.toolBar = QtGui.QToolBar( self )
		self.toolBar.setIconSize( QtCore.QSize( 32, 32 ) )
		self.ui.boxActions.addWidget( self.toolBar )
		queue = RegisterQueue()
		event.emit( QtCore.SIGNAL('requestTreeModulActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), queue, modul, self )
		for item in queue.getAll():
			i = item( self )
			if isinstance( i, QtGui.QAction ):
				self.toolBar.addAction( i )
				self.ui.listWidget.addAction( i )
			else:
				self.toolBar.addWidget( i )
		self.ui.boxActions.addWidget( self.toolBar )
		self.connect( self.tree, QtCore.SIGNAL("itemDoubleClicked(PyQt_PyObject)"), self.on_listWidget_itemDoubleClicked)
		
	def on_btnSearch_released(self, *args, **kwargs):
		self.tree.search( self.ui.editSearch.text() )

	def on_editSearch_returnPressed(self):
		self.tree.search( self.ui.editSearch.text() )
		
	def on_listWidget_itemDoubleClicked(self, item ):
		if( isinstance( item, self.tree.treeItem ) ):
			descr = QtCore.QCoreApplication.translate("TreeWidget", "Edit entry")
			handler = WidgetHandler( lambda: EditWidget(self.tree.modul, EditWidget.appTree, item.data["id"]), descr )
			event.emit( QtCore.SIGNAL('addHandler(PyQt_PyObject)'), handler )


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

class TreeEditAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( TreeEditAction, self ).__init__(  QtGui.QIcon("icons/actions/edit_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "Edit entry"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
	
	def onTriggered( self, e ):
		name = QtCore.QCoreApplication.translate("TreeHandler", "Edit entry")
		entries = []
		for item in self.parent().tree.selectedItems():
			if not isinstance( item, DirItem ):
				entries.append( item.data )
		for entry in entries:
			widget = lambda: EditWidget(self.parent().tree.modul, EditWidget.appTree, entry["id"], rootNode=self.parent().tree.currentRootNode, path=self.parent().tree.getPath())
			handler = WidgetHandler( widget, descr=name, icon=QtGui.QIcon("icons/actions/edit_small.png") )
			event.emit( QtCore.SIGNAL('stackHandler(PyQt_PyObject)'), handler )

class TreeDirUpAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( TreeDirUpAction, self ).__init__(  QtGui.QIcon("icons/actions/folder_back_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "Directory up"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
	
	def onTriggered( self, e ):
		self.parent().tree.path = self.parent().tree.path[ : -1 ]
		self.parent().tree.loadData()

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

class TreeDeleteAction( QtGui.QAction ): 
	def __init__(self, parent, *args, **kwargs ):
		super( TreeDeleteAction, self ).__init__(  QtGui.QIcon("icons/actions/delete_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "Delete"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.Delete )
		self.setShortcutContext( QtCore.Qt.WidgetWithChildrenShortcut )
	
	def onTriggered( self, e ):
		dirs = []
		files = []
		for item in self.parent().tree.selectedItems():
			if isinstance( item, DirItem ):
				dirs.append( item.dirName )
			else:
				files.append( item.data )
		if not files and not dirs:
			return
		self.parent().tree.delete( self.parent().tree.currentRootNode, self.parent().tree.getPath(), [ x["name"] for x in files], dirs )

class TreeBaseHandler( WidgetHandler ):
	def __init__( self, modul, *args, **kwargs ):
		super( TreeBaseHandler, self ).__init__(  lambda: TreeList( modul ), vanishOnClose=False, *args, **kwargs )
		config = conf.serverConfig["modules"][ modul ]
		if config["icon"]:
			lastDot = config["icon"].rfind(".")
			smallIcon = config["icon"][ : lastDot ]+"_small"+config["icon"][ lastDot: ]
			if os.path.isfile( os.path.join( os.getcwd(), smallIcon ) ):
				self.setIcon( 0, QtGui.QIcon( smallIcon ) )
			else:
				self.setIcon( 0, QtGui.QIcon( config["icon"] ) )
		self.setText( 0, config["name"] )


class TreeHandler( QtCore.QObject ):
	"""
	Created automatically to route Events to its handler in this file.png
	Do not create another instance of this!
	"""
	def __init__(self, *args, **kwargs ):
		"""
		Do not instantiate this!
		All parameters are passed to QObject.__init__
		"""
		QtCore.QObject.__init__( self, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('requestTreeModulActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)') ,  self.requestModulListActions )
		self.connect( event, QtCore.SIGNAL('requestModulHandler(PyQt_PyObject,PyQt_PyObject)'), self.requestModulHandler )

	
	def requestModulHandler(self, queue, modul ):
		"""Pushes a L{TreeBaseHandler} onto the queue if handled by "tree"
		
		@type queue: RegisterQueue
		@type modul: string
		@param modul: Name of the modul which should be handled
		"""
		config = conf.serverConfig["modules"][ modul ]
		if( config["handler"]=="tree" ):
			f = lambda: TreeBaseHandler( modul )
			queue.registerHandler( 5, f )
	
	
	def requestModulListActions(self, queue, modul, parent ):
		config = conf.serverConfig["modules"][ modul ]
		if config and config["handler"]=="tree":
			queue.registerHandler( 2, TreeDirUpAction )
			queue.registerHandler( 4, TreeAddAction )
			queue.registerHandler( 4, TreeEditAction )
			queue.registerHandler( 8, TreeMkDirAction )
			queue.registerHandler( 10, TreeDeleteAction )
			

	
	def openList(self, modulName, config ):
		if "name" in config.keys():
			name = config["name"]
		else:
			name = "Liste"
		if "icon" in config.keys():
			icon = config["icon"]
		else:
			icon = None
		event.emit( QtCore.SIGNAL('addHandlerWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), TreeList( modulName, config ), name, icon )

_fileHandler = TreeHandler()


