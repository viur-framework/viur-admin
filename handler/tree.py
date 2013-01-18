from ui.treeUI import Ui_Tree
from PyQt4 import QtCore, QtGui, QtNetwork
from network import NetworkService
from event import event
from config import conf
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse
from time import sleep, time
import sys, os, os.path
from handler.edit import Edit, EditHandler
from utils import RegisterQueue, Overlay
from handler.list import ListCoreHandler
from widgets.tree import TreeWidget, TreeItem, DirItem



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
		self.connect( self.tree, QtCore.SIGNAL("itemDoubleClicked(PyQt_PyObject)"), self.on_listWidget_itemDoubleClicked)
		
	def on_btnSearch_released(self, *args, **kwargs):
		self.path = None
		self.loadData( filter={"rootNode":self.currentRootNode, "path": "",  "serach": self.ui.editSearch.text() }  )
		
	def on_listWidget_itemDoubleClicked(self, item ):
		if( isinstance( item, self.tree.treeItem ) ):
			descr = QtCore.QCoreApplication.translate("TreeWidget", "Edit entry")
			widget = Edit(self.tree.modul, item.data["id"])
			handler = EditHandler( self.tree.modul, widget )
			event.emit( QtCore.SIGNAL('addHandler(PyQt_PyObject)'), handler )


class TreeEdit( Edit ):
	def __init__( self, modul, id=0, rootNode="", path="", *args, **kwargs ):
		self.rootNode = rootNode
		self.path = path
		super( TreeEdit, self ).__init__( modul, id, *args, **kwargs )
	
	def reloadData(self):
		if self.id: #We are in Edit-Mode
			self.request = NetworkService.request("/%s/edit/%s" % ( self.modul, self.id ), {"rootNode": self.rootNode, "path": self.path }, successHandler=self.setData )
		else:
			self.request = NetworkService.request("/%s/add/" % ( self.modul ), {"rootNode": self.rootNode, "path": self.path }, successHandler=self.setData )

	def save(self, data ):
		data.update( {"rootNode": self.rootNode, "path": self.path } )
		if self.id:
			self.request = NetworkService.request("/%s/edit/%s" % ( self.modul, self.id ), data, secure=True, successHandler=self.onSaveResult )
		else:
			self.request = NetworkService.request("/%s/add/" % ( self.modul ), data, secure=True, successHandler=self.onSaveResult )

	def emitEntryChanged( self, modul ):
		event.emit( QtCore.SIGNAL('dataChanged(PyQt_PyObject,PyQt_PyObject)'), modul, self )
	

class TreeAddAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( TreeAddAction, self ).__init__(  QtGui.QIcon("icons/actions/add_icon_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "Add entry"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.New )
	
	def onTriggered( self, e ):
		config = conf.serverConfig["modules"][ self.parent().tree.modul ]
		if "name" in config.keys():
			name = QtCore.QCoreApplication.translate("TreeHandler", "Add entry: %s") % config["name"]
		else:
			name = QtCore.QCoreApplication.translate("TreeHandler", "Add entry")
		widget = TreeEdit(self.parent().tree.modul, 0, rootNode=self.parent().tree.currentRootNode, path=self.parent().tree.getPath())
		handler = EditHandler( self.parentWidget().tree.modul, widget )
		event.emit( QtCore.SIGNAL('addHandler(PyQt_PyObject)'), handler )


class TreeDirUpAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( TreeDirUpAction, self ).__init__(  QtGui.QIcon("icons/actions/folder_back_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "Directory up"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
	
	def onTriggered( self, e ):
		self.parent().tree.path = self.parent().tree.path[ : -1 ]
		self.parent().tree.reloadData()

class TreeMkDirAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( TreeMkDirAction, self ).__init__(  QtGui.QIcon("icons/actions/folder_add_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "New directory"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( "SHIFT+Ctrl+N" )
		self.setShortcutContext( QtCore.Qt.WidgetWithChildrenShortcut )
	
	def onTriggered( self, e ):
		(dirName, okay) = QtGui.QInputDialog.getText( self.parent(), QtCore.QCoreApplication.translate("TreeHandler", "Create directory"), QtCore.QCoreApplication.translate("TreeHandler", "Directory name") )
		if dirName and okay:
			self.parent().tree.mkdir( self.parent().tree.modul, self.parent().tree.currentRootNode, self.parent().tree.getPath(), dirName )

class TreeDeleteAction( QtGui.QAction ): 
	def __init__(self, parent, *args, **kwargs ):
		super( TreeDeleteAction, self ).__init__(  QtGui.QIcon("icons/actions/delete_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "Delete"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.Delete )
		self.setShortcutContext( QtCore.Qt.WidgetWithChildrenShortcut )
	
	def onTriggered( self, e ):
		dirs = []
		files = []
		for item in self.parent().ui.listWidget.selectedItems():
			if isinstance( item, DirItem ):
				dirs.append( item.dirName )
			else:
				files.append( item.data )
		if not files and not dirs:
			return
		self.parent().delete( self.parent().currentRootNode, self.parent().getPath(), [ x["name"] for x in files], dirs )

class TreeBaseHandler( ListCoreHandler ):
	def __init__( self, modul, *args, **kwargs ):
		super( TreeBaseHandler, self ).__init__( modul, *args, **kwargs )
		config = conf.serverConfig["modules"][ modul ]
		if config["icon"]:
			lastDot = config["icon"].rfind(".")
			smallIcon = config["icon"][ : lastDot ]+"_small"+config["icon"][ lastDot: ]
			if os.path.isfile( os.path.join( os.getcwd(), smallIcon ) ):
				self.setIcon( 0, QtGui.QIcon( smallIcon ) )
			else:
				self.setIcon( 0, QtGui.QIcon( config["icon"] ) )
		self.setText( 0, config["name"] )

	def clicked( self ):
		if not self.widgets:
			self.addWidget( TreeList( self.modul ) )
		else:
			self.focus()

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


