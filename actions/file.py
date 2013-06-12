# -*- coding: utf-8 -*-
from ui.treeUI import Ui_Tree
from PyQt4 import QtCore, QtGui
from network import NetworkService, RemoteFile
from event import event
from config import conf
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse
from time import sleep, time
import sys, os
from widgets.file import FileWidget
from handler.list import ListCoreHandler
from utils import RegisterQueue, loadIcon
from priorityqueue import protocolWrapperInstanceSelector, actionDelegateSelector


class FileUploadAction( QtGui.QAction ): 
	def __init__(self, parent, *args, **kwargs ):
		super( FileUploadAction, self ).__init__(  QtGui.QIcon("icons/actions/upload_small.png"), QtCore.QCoreApplication.translate("FileHandler", "Upload files"), parent )
		self.triggered.connect( self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.New )
	
	def onTriggered( self, e ):
		files = QtGui.QFileDialog.getOpenFileNames()[0] #PySIDE FIX!!!
		self.parent().doUpload( files, self.parent().getNode() )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "tree.file" or modul.startswith("tree.file.")) and actionName=="upload")

actionDelegateSelector.insert( 3, FileUploadAction.isSuitableFor, FileUploadAction )

class FileDownloadAction( QtGui.QAction ): 
	def __init__(self, parent, *args, **kwargs ):
		super( FileDownloadAction, self ).__init__(  QtGui.QIcon("icons/actions/download_small.png"), QtCore.QCoreApplication.translate("FileHandler", "Download files"), parent )
		self.triggered.connect( self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.Save )
	
	def onTriggered( self, e ):
		dirs = []
		files = []
		for item in self.parent().selectedItems():
			if isinstance( item, self.parent().getNodeItemClass() ):
				dirs.append( item.dirName )
			else:
				files.append( item.entryData )
		if not files and not dirs:
			return
		targetDir = QtGui.QFileDialog.getExistingDirectory( self.parentWidget() )
		if not targetDir:
			return
		self.parent().doDownload( targetDir, self.parent().rootNode, self.parent().getPath(), files, dirs )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "tree.file" or modul.startswith("tree.file.")) and actionName=="download")

actionDelegateSelector.insert( 3, FileDownloadAction.isSuitableFor, FileDownloadAction )
