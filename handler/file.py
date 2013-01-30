# -*- coding: utf-8 -*-
from ui.treeUI import Ui_Tree
from PyQt4 import QtCore, QtGui
from network import NetworkService, RemoteFile
from event import event
from config import conf
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse
from time import sleep, time
import sys, os
from handler.tree import TreeDirUpAction, TreeMkDirAction, TreeDeleteAction,  TreeItem, DirItem

from widgets.file import FileWidget, FileItem
from handler.list import ListCoreHandler
from utils import RegisterQueue

class FileList( QtGui.QWidget ):
	treeItem = FileItem
	dirItem = None
	
	def __init__(self, modul, currentRootNode=None, path=None, *args, **kwargs ):
		super( FileList, self ).__init__( *args, **kwargs )
		config = conf.serverConfig["modules"][ modul ]
		self.ui = Ui_Tree()
		self.ui.setupUi( self )
		layout = QtGui.QHBoxLayout( self.ui.listWidget )
		self.ui.listWidget.setLayout( layout )
		self.tree = FileWidget( self.ui.listWidget, modul, currentRootNode, path, treeItem=self.treeItem, dirItem=self.dirItem )
		layout.addWidget( self.tree )
		self.tree.show()
		self.ui.editSearch.mousePressEvent = self.on_editSearch_clicked
		self.toolBar = QtGui.QToolBar( self )
		self.toolBar.setIconSize( QtCore.QSize( 32, 32 ) )
		self.ui.boxActions.addWidget( self.toolBar )
		queue = RegisterQueue()
		event.emit( QtCore.SIGNAL('requestTreeModulActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), queue, modul, self )
		print("Event emited")
		for item in queue.getAll():
			i = item( self )
			if isinstance( i, QtGui.QAction ):
				self.toolBar.addAction( i )
				self.ui.listWidget.addAction( i )
			else:
				self.toolBar.addWidget( i )
		self.ui.boxActions.addWidget( self.toolBar )
		self.connect( self.tree, QtCore.SIGNAL("itemDoubleClicked(PyQt_PyObject)"), self.on_listWidget_itemDoubleClicked)
		
	def on_listWidget_itemDoubleClicked(self, item ):
		if( isinstance( item, self.tree.treeItem ) ):
			descr = QtCore.QCoreApplication.translate("TreeWidget", "Edit entry")
			widget = Edit(self.modul, item.data["id"])
			handler = EditHandler( self.modul, widget )
			event.emit( QtCore.SIGNAL('addHandler(PyQt_PyObject)'), handler )

	def on_editSearch_clicked(self, *args, **kwargs):
		if self.ui.editSearch.text()==QtCore.QCoreApplication.translate("ListHandler", "Search") :
			self.ui.editSearch.setText("")

	def on_btnSearch_released(self, *args, **kwargs):
		self.tree.search( self.ui.editSearch.text() )

	def on_editSearch_returnPressed(self):
		self.tree.search( self.ui.editSearch.text() )

class FileUploadAction( QtGui.QAction ): 
	def __init__(self, parent, *args, **kwargs ):
		super( FileUploadAction, self ).__init__(  QtGui.QIcon("icons/actions/upload_small.png"), QtCore.QCoreApplication.translate("FileHandler", "Upload files"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.New )
	
	def onTriggered( self, e ):
		files = QtGui.QFileDialog.getOpenFileNames()
		self.parent().tree.doUpload( files, self.parent().tree.currentRootNode, self.parent().tree.getPath() )


class FileDownloadAction( QtGui.QAction ): 
	def __init__(self, parent, *args, **kwargs ):
		super( FileDownloadAction, self ).__init__(  QtGui.QIcon("icons/actions/download_small.png"), QtCore.QCoreApplication.translate("FileHandler", "Download files"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.Save )
	
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
		targetDir = QtGui.QFileDialog.getExistingDirectory( self.parentWidget() )
		if not targetDir:
			return
		self.parent().tree.download( targetDir, self.parent().tree.currentRootNode, self.parent().tree.getPath(), files, dirs )


class FileRepoHandler( ListCoreHandler ):
	def __init__( self, modul, repo, *args, **kwargs ):
		super( FileRepoHandler, self ).__init__( modul, *args, **kwargs )	
		self.repo = repo
		self.setText(0, repo["name"] )

	def clicked( self ):
		if not self.widgets:
			self.addWidget( FileList( self.modul, self.repo["key"] ) )
		else:
			self.focus()

class FileBaseHandler( ListCoreHandler ):
	def __init__( self, modul, *args, **kwargs ):
		super( FileBaseHandler, self ).__init__( modul, *args, **kwargs )
		config = conf.serverConfig["modules"][ modul ]
		if config["icon"]:
			self.setIcon( 0, QtGui.QIcon( config["icon"] ) )
		self.setText( 0, config["name"] )
		self.repos = []
		self.tmpObj = QtGui.QWidget()
		self.fetchTask = NetworkService.request("/%s/listRootNodes" % self.modul )
		self.tmpObj.connect(self.fetchTask, QtCore.SIGNAL("finished()"), self.setRepos) 
	
	def setRepos( self ):
		data = NetworkService.decode( self.fetchTask )
		self.fetchTask.deleteLater()
		self.fetchTask = None
		self.tmpObj.deleteLater()
		self.tmpObj = None
		self.repos = data
		if len( self.repos ) > 1:
			for repo in self.repos:
				d = FileRepoHandler( self.modul, repo )
				self.addChild( d )
	
	def clicked( self ):
		if not self.widgets:
			self.addWidget( FileList( self.modul ) )
		else:
			self.focus()

class FileHandler( QtCore.QObject ):
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('requestModulHandler(PyQt_PyObject,PyQt_PyObject)'), self.requestModulHandler )
		self.connect( event, QtCore.SIGNAL('modulHandlerInitializion(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.initWidgetItem )
		self.connect( event, QtCore.SIGNAL('requestTreeModulActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)') ,  self.requestModulListActions )

	def requestModulListActions(self, queue, modul, parent ):
		config = conf.serverConfig["modules"][ modul ]
		if config and config["handler"]=="tree.file":
			queue.registerHandler( 1, TreeDirUpAction )
			queue.registerHandler( 2, FileUploadAction )
			queue.registerHandler( 3, FileDownloadAction )
			queue.registerHandler( 4, TreeMkDirAction )
			queue.registerHandler( 5, TreeDeleteAction )
			
			
	def requestModulHandler(self, queue, modul ):
		config = conf.serverConfig["modules"][ modul ]
		if( config["handler"]=="tree.file" ):
			f = lambda: FileBaseHandler( modul )
			queue.registerHandler( 5, f )

	def initWidgetItem(self, queue, modulName, config ):
		if( modulName!="file"):
			return
		listOpener = lambda *args, **kwargs: self.openList( modulName, config )
		contextHandler = lambda *args, **kwargs: None 
		if not "icon" in config.keys():
			config["icon"]="icons/conesofticons/ihre_idee.png"
		res= {"name":config["name"], "icon":config["icon"], "functions":[
				{"name":"Meine Dateien", "icon":config["icon"], "handler":listOpener, "contextHandler":contextHandler }
			], "defaulthandler":listOpener }
		queue.registerHandler(10,res)
	
	def openList(self, modulName, config ):
		event.emit( QtCore.SIGNAL('addHandlerWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), FileList( modulName, config ), "Liste", None ) 

_fileHandler = FileHandler()


