# -*- coding: utf-8 -*-
from ui.fileUploadProgressUI import Ui_FileUploadProgress
from ui.fileDownloadProgressUI import Ui_FileDownloadProgress
from PySide import QtCore, QtGui
from utils import Overlay
from network import NetworkService, RemoteFile, RequestGroup
from event import event
from widgets.tree import TreeWidget, TreeItem
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
		self.data = data
		extension=self.data["name"].split(".")[-1].lower()
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
			extension=self.data["name"].split(".")[-1].upper()
			if os.path.isfile("icons/filetypes/%s.png"%(extension)):
				icon = QtGui.QIcon("icons/filetypes/%s.png"%(extension))
			else:
				icon = QtGui.QIcon("icons/filetypes/unknown.png")
		else:
			icon = QtGui.QIcon( pixmap.scaled( 128,128 ) )
		self.setIcon( icon )
		self.setToolTip("<img src=\"%s\" width=\"200\" height=\"200\"><br>%s" % ( remoteFile.getFileName(), str( self.data["name"] ) ) )

	
	def toURL( self ):
		return( "/file/view/%s/%s" % (self.data["dlkey"],self.data["name"]))
		

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
	
	def on_btnCancel_released(self, *args, **kwargs ):
		self.cancel = True
		if self.request:
			self.request.abort()
	
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

class RecursiveDownloader( QtGui.QWidget ):  #OBSOLETE!!
	"""
		Download files and/or directories from the server into the local filesystem.
		The functionality is bound to a widget displaying the current progress.
		If downloading has finished, finished(PyQt_PyObject=self) is emited.
	"""
	
	directorySize = 15 #Letz count an directory as 15 Bytes
	def __init__(self, localTargetDir, rootNode, path, files, dirs, modul, *args, **kwargs ):
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
		super( RecursiveDownloader, self ).__init__( *args, **kwargs )
		self.ui = Ui_FileDownloadProgress()
		self.ui.setupUi( self )
		self.localTargetDir = localTargetDir
		self.rootNode = rootNode
		self.modul = modul
		self.recursionInfo = [ (files, dirs, path, localTargetDir) ]
		self.request = None
		self.cancel = False
		self.doDownloadRecursive()
	
	
	def doDownloadRecursive( self ):
		if self.cancel or len( self.recursionInfo ) == 0:
			self.emit( QtCore.SIGNAL("finished(PyQt_PyObject)"), self )
			if self.request:
				self.request = None
			return
		files, dirs,  path, localTargetDir = self.recursionInfo[ -1 ]
		if not os.path.exists( localTargetDir ):
			os.mkdir( localTargetDir )
		if len( files ) > 0:
			file = files.pop()
			self.ui.lblProgress.setText( QtCore.QCoreApplication.translate("FileHandler", "Downloading: %s") % file["name"] )
			self.ui.pbarTotal.setValue( 0 )
			dlkey = "/file/view/%s/file.dat" % file["dlkey"]
			self.request = NetworkService.request( dlkey )
			self.connect( self.request, QtCore.SIGNAL("downloadProgress (qint64,qint64)"), self.onDownloadProgress )
			self.lastFileInfo = file["name"],localTargetDir
			self.connect( self.request, QtCore.SIGNAL("finished()"), self.saveFile  )
		elif len( dirs ) > 0:
			dir = dirs.pop()
			self.request = NetworkService.request("/%s/list" % self.modul, {"rootNode":self.rootNode, "path":"%s/%s" % (path, dir)} )
			self.lastDirInfo = path, localTargetDir, dir
			self.connect( self.request, QtCore.SIGNAL("finished()"), self.onDirList  )
		else: # Were done with this recursion
			self.recursionInfo.pop()
			self.doDownloadRecursive()

	
	def onDirList( self ):
		oldPath, oldTargetDir, dirName = self.lastDirInfo
		data = NetworkService.decode( self.request )
		self.recursionInfo.append( (data["entrys"], data["subdirs"], "%s/%s" % (oldPath, dirName), os.path.join(oldTargetDir, dirName) ) )
		self.doDownloadRecursive()
	
	def saveFile( self ):
		name, targetDir = self.lastFileInfo
		fh = open( os.path.join( targetDir, name), "wb+" )
		fh.write( self.request.readAll() )
		self.doDownloadRecursive()

	def onDownloadProgress(self, bytesDone, bytesTotal ):
		self.ui.pbarTotal.setRange( 0, bytesTotal )
		self.ui.pbarTotal.setValue( bytesDone )


class FileWidget( TreeWidget ):
	"""
		Extension for TreeWidget to handle the specialities of files like Up&Downloading.
	"""
	
	def __init__( self, *args, **kwargs ):
		super( FileWidget, self ).__init__( *args, **kwargs )
		self.startDrag = False
		self.setAcceptDrops( True )

	def onTransferFinished(self, task):
		self.flushCache( task.rootNode )
		self.loadData()
		task.deleteLater()
	
	def onTransferFailed(self, task):
		QtGui.QMessageBox.information( self, QtCore.QCoreApplication.translate("FileHandler", "Error during upload") , QtCore.QCoreApplication.translate("FileHandler", "There was an error uploading your files")  )
		self.flushCache( task.rootNode )
		self.loadData()
		task.deleteLater()

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
		print("upl")
		if not files:
			print("err1")
			return
		print("doupl")
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		uploader = protoWrap.upload( files, rootNode, path )
		self.layout().addWidget( UploadStatusWidget( uploader ) )
		#uploader = RecursiveUploader( files, rootNode, path, self.modul )
		#self.ui.boxUpload.addWidget( uploader )
		#self.connect( uploader, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.onTransferFinished )
		#self.connect( uploader, QtCore.SIGNAL("failed(PyQt_PyObject)"), self.onTransferFailed )

	def download( self, targetDir, currentRootNode, path, files, dirs ):
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
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		protoWrap.download( targetDir, currentRootNode, path, files, dirs )
		
		#downloader = RecursiveDownloader( targetDir, self.currentRootNode, path, files, dirs, self.modul )
		#self.ui.boxUpload.addWidget( downloader )
		#self.connect( downloader, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.onTransferFinished )

	def dropEvent(self, event):
		print("p1")
		if ( all( [ str(file.toLocalFile()).startswith("file://") or str(file.toLocalFile()).startswith("/") or ( len(str(file.toLocalFile()))>0 and str(file.toLocalFile())[1]==":")  for file in event.mimeData().urls() ] ) ) and len(event.mimeData().urls())>0:
			print("aa11")
			self.doUpload( [file.toLocalFile() for file in event.mimeData().urls()], self.currentRootNode, self.getPath() )
		else:
			print("aa22")
			super( FileWidget, self ).dropEvent( event )

	def dragEnterEvent( self, event ):
		print("p2")
		if ( all( [ file.toLocalFile() and (str(file.toLocalFile()).startswith("file://") or str(file.toLocalFile()).startswith("/") or str(file.toLocalFile())[1]==":")  for file in event.mimeData().urls() ] ) ) and len(event.mimeData().urls())>0:
			print("x2222")
			event.accept()
		else:
			print("y2222")
			super( FileWidget, self ).dragEnterEvent( event )

	def on_listWidget_customContextMenuRequested(self, point ):
		"""
			Provides the default context-menu for this modul.
		"""
		#FIXME: Copy&Paste from tree.py
		menu = QtGui.QMenu( self )
		if self.ui.listWidget.itemAt(point):
			dirs = []
			files = []
			for item in self.ui.listWidget.selectedItems():
				if isinstance( item, self.dirItem ):
					dirs.append( item.dirName )
				else:
					files.append( item.data )
			if len( files )+len( dirs ) == 1:
				actionRename = menu.addAction( QtCore.QCoreApplication.translate("FileHandler", "Rename") )
			else: 
				actionRename = "-unset-"
			if not dirs and len( files ) == 1:
				actionEdit = menu.addAction( QtCore.QCoreApplication.translate("FileHandler", "Edit") )
			else:
				actionEdit = "-unset-"
			menu.addSeparator ()
			actionCopy = menu.addAction( QtCore.QCoreApplication.translate("FileHandler", "Copy") )
			actionMove = menu.addAction( QtCore.QCoreApplication.translate("FileHandler", "Cut") )
			actionDelete = menu.addAction( QtCore.QCoreApplication.translate("FileHandler", "Delete") )
			menu.addSeparator ()
			actionDownload = menu.addAction( "Herunterladen" )
			selection = menu.exec_( self.ui.listWidget.mapToGlobal( point ) )
			if( selection==actionRename and self.ui.listWidget.currentItem() ):
				item = self.ui.listWidget.currentItem()
				if isinstance( item, self.dirItem ):
					oldName = item.dirName
				else:
					oldName = item.data["name"]
				newName, okay = QtGui.QInputDialog.getText( 	self, 
														QtCore.QCoreApplication.translate("FileHandler", "Rename"),
														QtCore.QCoreApplication.translate("FileHandler", "New name"),
														text=oldName )
				if okay:
					self.rename( self.currentRootNode, self.getPath(), oldName, newName )
			elif selection == actionCopy or selection == actionMove:
				doMove = (selection==actionMove)
				self.clipboard = ( self.currentRootNode, self.getPath(), doMove, [ x["name"] for x in files] , dirs )
			elif selection == actionDelete:
				self.delete( self.currentRootNode, self.getPath(), [ x["name"] for x in files], dirs )
			elif selection == actionDownload:
				targetDir = QtGui.QFileDialog.getExistingDirectory( self )
				if not targetDir:
					return
				self.download( targetDir, self.currentRootNode, self.getPath(), files, dirs )
			elif selection == actionEdit:
				descr = "Bearbeiten"
				widget = EditWidget(self.modul, EditWidget.appTree, item.data["id"])
				handler = WidgetHandler( self.modul, widget )
				event.emit( QtCore.SIGNAL('addHandler(PyQt_PyObject)'), handler )
		else:
			actionPaste = menu.addAction( QtCore.QCoreApplication.translate("FileHandler", "Insert") )
			selection = menu.exec_( self.ui.listWidget.mapToGlobal( point ) )
			if( selection==actionPaste and self.clipboard ):
				# self.ui.listWidget.currentItem() ):
				self.copy( self.clipboard, self.currentRootNode, self.getPath() )

