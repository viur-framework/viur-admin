# -*- coding: utf-8 -*-
from ui.treeUI import Ui_Tree
from PySide import QtCore, QtGui
from network import NetworkService, RemoteFile
from event import event
from config import conf
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse
from time import sleep, time
import sys, os
from handler.tree import TreeItem, DirItem
from widgets.edit import EditWidget
from widgets.file import FileWidget, FileItem
from handler.list import ListCoreHandler
from mainwindow import WidgetHandler
from utils import RegisterQueue, loadIcon
import gc


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
		super( FileRepoHandler, self ).__init__( lambda: FileWidget( modul, repo["key"] ), vanishOnClose=False, *args, **kwargs )	
		self.repo = repo
		self.setText(0, repo["name"] )

class FileBaseHandler( WidgetHandler ):
	def __init__( self, modul, *args, **kwargs ):
		super( FileBaseHandler, self ).__init__( lambda: FileWidget( modul ), vanishOnClose=False, *args, **kwargs )
		self.modul = modul
		config = conf.serverConfig["modules"][ modul ]
		if config["icon"]:
			self.setIcon( 0, loadIcon( config["icon"] ) )
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
		event.connectWithPriority( 'requestModulHandler', self.requestModulHandler, event.lowPriority )
			
			
	def requestModulHandler(self, queue, modul ):
		config = conf.serverConfig["modules"][ modul ]
		if( config["handler"]=="tree.file" ):
			f = lambda: FileBaseHandler( modul )
			queue.registerHandler( 5, f )


_fileHandler = FileHandler()


