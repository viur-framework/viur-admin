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
from widgets.edit import EditWidget
from widgets.file import FileWidget, FileItem
from handler.list import ListCoreHandler
from mainwindow import WidgetHandler
from utils import RegisterQueue
import gc

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
		toolBar = QtGui.QToolBar( self )
		toolBar.setIconSize( QtCore.QSize( 32, 32 ) )
		self.ui.boxActions.addWidget( toolBar )
		queue = RegisterQueue()
		event.emit( QtCore.SIGNAL('requestTreeModulActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), queue, modul, self )
		for item in queue.getAll():
			i = item( self )
			if isinstance( i, QtGui.QAction ):
				toolBar.addAction( i )
				self.ui.listWidget.addAction( i )
			else:
				toolBar.addWidget( i )
		self.connect( self.tree, QtCore.SIGNAL("onItemDoubleClicked(PyQt_PyObject)"), self.on_listWidget_itemDoubleClicked)

	def prepareDeletion(self):
		"""
			Ensure that all our childs have the chance to clean up.
		"""
		self.ui.editSearch.mousePressEvent = None
		self.tree.prepareDeletion()

	def on_listWidget_itemDoubleClicked(self, item ):
		if( isinstance( item, self.tree.treeItem ) ):
			descr = QtCore.QCoreApplication.translate("TreeWidget", "Edit entry")
			widget = EditWidget(self.tree.modul, EditWidget.appTree, item.data["id"])
			handler = WidgetHandler( self.tree.modul, widget )
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


class FileRepoHandler( WidgetHandler ):
	def __init__( self, modul, repo, *args, **kwargs ):
		super( FileRepoHandler, self ).__init__( lambda: FileList( modul, repo["key"] ), vanishOnClose=False, *args, **kwargs )	
		self.repo = repo
		self.setText(0, repo["name"] )

class FileBaseHandler( WidgetHandler ):
	def __init__( self, modul, *args, **kwargs ):
		super( FileBaseHandler, self ).__init__( lambda: FileList( modul ), vanishOnClose=False, *args, **kwargs )
		self.modul = modul
		config = conf.serverConfig["modules"][ modul ]
		if config["icon"]:
			self.setIcon( 0, QtGui.QIcon( config["icon"] ) )
		self.setText( 0, config["name"] )
		self.repos = []
		self.tmpObj = QtGui.QWidget()
		fetchTask = NetworkService.request("/%s/listRootNodes" % modul )
		self.tmpObj.connect( fetchTask, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.setRepos) 
	
	def setRepos( self, fetchTask ):
		data = NetworkService.decode( fetchTask )
		self.tmpObj.deleteLater()
		self.tmpObj = None
		self.repos = data
		if len( self.repos ) > 1:
			for repo in self.repos:
				d = FileRepoHandler( self.modul, repo )
				self.addChild( d )

class FileHandler( QtCore.QObject ):
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('requestModulHandler(PyQt_PyObject,PyQt_PyObject)'), self.requestModulHandler )
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


_fileHandler = FileHandler()


