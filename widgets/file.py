# -*- coding: utf-8 -*-
from ui.fileUploadProgressUI import Ui_FileUploadProgress
from ui.fileDownloadProgressUI import Ui_FileDownloadProgress
from PySide import QtCore, QtGui
from utils import Overlay
from network import NetworkService, RemoteFile, RequestGroup
from event import event
from widgets.tree import TreeWidget, TreeItem, TreeListView
from widgets.edit import EditWidget
from mainwindow import WidgetHandler
import os, sys
from config import conf
from priorityqueue import protocolWrapperInstanceSelector


class FileItem( TreeItem ):
	"""
		Displayes a file (including its preview if possible) inside a QListWidget.
	"""
	def __init__( self, data ):
		super( FileItem, self ).__init__( data )
		self.entryData = data
		extension=self.entryData["name"].split(".")[-1].lower()
		if os.path.isfile("icons/filetypes/%s.png"%(extension)):
			icon = QtGui.QIcon("icons/filetypes/%s.png"%(extension))
		else:
			icon = QtGui.QIcon("icons/filetypes/unknown.png")		
		if "meta_mime" in data.keys() and str(data["meta_mime"]).lower().startswith("image"):
			RemoteFile( data["dlkey"], successHandler=self.updateIcon )
	
	def updateIcon(self, remoteFile ):
		pixmap = QtGui.QPixmap()
		pixmap.loadFromData( remoteFile.getFileContents() )
		if( pixmap.isNull() ):
			extension=self.entryData["name"].split(".")[-1].upper()
			if os.path.isfile("icons/filetypes/%s.png"%(extension)):
				icon = QtGui.QIcon("icons/filetypes/%s.png"%(extension))
			else:
				icon = QtGui.QIcon("icons/filetypes/unknown.png")
		else:
			icon = QtGui.QIcon( pixmap.scaled( 64,64 ) )
		self.setIcon( icon )
		self.setToolTip("<img src=\"%s\" width=\"200\" height=\"200\"><br>%s" % ( remoteFile.getFileName(), str( self.entryData["name"] ) ) )

	
	def toURL( self ):
		return( "/file/view/%s/%s" % (self.entryData["dlkey"],self.entryData["name"]))
		

class UploadStatusWidget( QtGui.QWidget ): 
	"""
		Upload files and/or directories from the the local filesystem to the server.
		This one is recursive, it supports uploading of files in subdirectories as well.
		Subdirectories on the server are created as needed.
		The functionality is bound to a widget displaying the current progress.
		If downloading has finished, finished(PyQt_PyObject=self) is emited.
	"""
	
	directorySize = 15 #Letz count an directory as 15 Bytes
	def __init__(self, uploader, *args, **kwargs ):
		"""
			@param files: List of local files or directories (including thier absolute path) which will be uploaded. 
			@type files: List
			@param rootNode: Destination rootNode
			@type rootNode: String
			@param path: Remote destination path, relative to rootNode.
			@type path: String
			@param modul: Modulname to upload to (usually "file")
			@type modul: String
		"""
		super( UploadStatusWidget, self ).__init__( *args, **kwargs )
		self.ui = Ui_FileUploadProgress()
		self.ui.setupUi( self )
		self.uploader = uploader
		self.uploader.uploadProgress.connect( self.onUploadProgress )
		self.uploader.finished.connect( self.onFinished )
		self.ui.btnCancel.released.connect( self.onBtnCancelReleased )
	
	def onBtnCancelReleased(self, *args, **kwargs ):
		self.uploader.cancelUpload()
	
	def onUploadProgress(self, bytesSend, bytesTotal ):
		self.ui.lblProgress.setText( QtCore.QCoreApplication.translate("FileHandler", "Files: %s/%s, Directories: %s/%s, Bytes: %s/%s") % ( self.uploader.statsDone["files"], self.uploader.statsTotal["files"], self.uploader.statsDone["dirs"], self.uploader.statsTotal["dirs"], self.uploader.statsDone["bytes"], self.uploader.statsTotal["bytes"]) )
		self.ui.pbarTotal.setRange( 0, self.uploader.statsTotal["bytes"] )
		self.ui.pbarTotal.setValue(self.uploader.statsDone["bytes"])
		self.ui.pbarFile.setRange( 0, bytesTotal )
		self.ui.pbarFile.setValue( bytesSend )
		
	def askOverwriteFile(self, title, text ):
		res = QtGui.QMessageBox.question( self, title, text,  buttons=QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel )
		if res == QtGui.QMessageBox.Yes:
			return(True)
		elif res == QtGui.QMessageBox.Cancel:
			return( False )
		return( None )
	
	def onFinished( self, req ):
		self.deleteLater()

class DownloadStatusWidget( QtGui.QWidget ): 
	"""
		Download files and/or directories from the server into the local filesystem.
		The functionality is bound to a widget displaying the current progress.
		If downloading has finished, finished(PyQt_PyObject=self) is emited.
	"""
	
	directorySize = 15 #Letz count an directory as 15 Bytes
	def __init__(self, downloader, *args, **kwargs ):
		"""
			@param localTargetDir: Local, existing and absolute destination-path
			@type localTargetDir: String
			@param rootNode: RootNode to download from
			@type rootNode: String
			@param path: Remote path, relative to rootNode.
			@type path: String
			@param files: List of files in the given remote path
			@type files: List
			@param dirs: List of directories in the given remote path
			@type dirs: List
			@param modul: Modulname to download from (usually "file")
			@type modul: String
		"""
		super( DownloadStatusWidget, self ).__init__( *args, **kwargs )
		self.ui = Ui_FileDownloadProgress()
		self.ui.setupUi( self )
		self.downloader = downloader
		self.downloader.downloadProgress.connect( self.onDownloadProgress )
		self.downloader.finished.connect( self.onFinished )
		#self.ui.btnCancel.released.connect( self.onBtnCancelReleased )
	
	def onDownloadProgress(self, bytesDone, bytesTotal ):
		self.ui.pbarTotal.setRange( 0, bytesTotal )
		self.ui.pbarTotal.setValue( bytesDone )

	def onFinished( self, req ):
		self.deleteLater()

class FileListView( TreeListView ):
	
	treeItem = FileItem
	
	def doUpload(self, files, rootNode, path ):
		"""
			Uploads a list of files to the Server and adds them to the given path on the server.
			@param files: List of local filenames including their full, absolute path
			@type files: List
			@param rootNode: RootNode which will recive the uploads
			@type rootNode: String
			@param path: Path (server-side) relative to the given RootNode
			@type path: String
		"""
		if not files:
			return
		protoWrap = protocolWrapperInstanceSelector.select( self.getModul() )
		uploader = protoWrap.upload( files, rootNode, path )
		self.parent().layout().addWidget( UploadStatusWidget( uploader ) )
		#uploader = RecursiveUploader( files, rootNode, path, self.getModul() )
		#self.ui.boxUpload.addWidget( uploader )
		#self.connect( uploader, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.onTransferFinished )
		#self.connect( uploader, QtCore.SIGNAL("failed(PyQt_PyObject)"), self.onTransferFailed )

	def doDownload( self, targetDir, rootNode, path, files, dirs ):
		"""
			Download a list of files and/or directories from the server to the local file-system.
			@param targetDir: Local, existing and absolute path
			@type targetDir: String
			@param rootNode: RootNode to download from
			@type rootNode: String
			@param path: Path relative to the RootNode containing the files and directories which should be downloaded
			@type path: String
			@param files: List of files in this directory which should be downloaded
			@type files: List
			@param dirs: List of directories (in the directory specified by rootNode+path) which should be downloaded
			@type dirs: List
		"""
		protoWrap = protocolWrapperInstanceSelector.select( self.getModul() )
		downloader = protoWrap.download( targetDir, rootNode, path, files, dirs )
		self.parent().layout().addWidget( DownloadStatusWidget( downloader ) )
		#downloader = RecursiveDownloader( targetDir, self.getRootNode(), path, files, dirs, self.getModul() )
		#self.ui.boxUpload.addWidget( downloader )
		#self.connect( downloader, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.onTransferFinished )

	def dropEvent(self, event):
		"""
			Allow Drag&Drop'ing from the local filesystem into our fileview
		"""
		if ( all( [ str(file.toLocalFile()).startswith("file://") or str(file.toLocalFile()).startswith("/") or ( len(str(file.toLocalFile()))>0 and str(file.toLocalFile())[1]==":")  for file in event.mimeData().urls() ] ) ) and len(event.mimeData().urls())>0:
			#Its an upload (files/dirs draged from the local filesystem into our fileview)
			self.doUpload( [file.toLocalFile() for file in event.mimeData().urls()], self.getRootNode(), "/".join(self.getPath()) or "/" )
		else:
			super( FileListView, self ).dropEvent( event )

	def dragEnterEvent( self, event ):
		"""
			Allow Drag&Drop'ing from the local filesystem into our fileview and dragging files out again
			(drag directorys out isnt currently supported)
		"""
		if ( all( [ file.toLocalFile() and (str(file.toLocalFile()).startswith("file://") or str(file.toLocalFile()).startswith("/") or str(file.toLocalFile())[1]==":")  for file in event.mimeData().urls() ] ) ) and len(event.mimeData().urls())>0:
			event.accept()
		else:
			super( FileListView, self ).dragEnterEvent( event )
			print( event.source() )
			if event.source() == self:
				# Its an internal drag&drop - add urls so it works outside, too
				urls = []
				for item in self.selectedItems():
					if isinstance( item, self.treeItem ):
						urls.append( "%s/file/view/%s/%s" % (NetworkService.url[ : -len("/admin")] , item.entryData["dlkey"], item.entryData["name"] ) )
				event.mimeData().setUrls( urls )


class FileWidget( TreeWidget ):
	"""
		Extension for TreeWidget to handle the specialities of files like Up&Downloading.
	"""
	
	treeWidget = FileListView
	
	def __init__( self, *args, **kwargs ):
		super( FileWidget, self ).__init__( actions=["dirup", "mkdir", "upload", "download", "edit", "delete"], *args, **kwargs )

	def doUpload(self, files, rootNode, path ):
		return( self.tree.doUpload( files, rootNode, path ) )

	def doDownload( self, targetDir, rootNode, path, files, dirs ):
		return( self.tree.doDownload( targetDir, rootNode, path, files, dirs ) )



