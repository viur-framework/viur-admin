# -*- coding: utf-8 -*-
from ui.fileUploadProgressUI import Ui_FileUploadProgress
from ui.fileDownloadProgressUI import Ui_FileDownloadProgress
from PyQt4 import QtCore, QtGui
from utils import Overlay
from network import NetworkService, RemoteFile, RequestGroup
from event import event
from widgets.tree import TreeWidget, TreeItem
import os, sys

class FileUploader( QtCore.QObject ):
	def __init__(self, fileName, destPath=None, destRepo=None ):
		"""
		Uploads a file to the Server
		
		@type fileName: String
		@param fileName: Full Filename (and Path)
		@type destPath: String
		@param destPath: Target Path on the Server (must exist!)
		@type destRepo: String
		@param destRepo: ID of the target rootNode
		"""
		super( FileUploader, self ).__init__()
		self.fileName = fileName
		self.destPath = destPath
		self.destRepo = destRepo
		self.request = NetworkService.request("/file/getUploadURL")
		self.connect( self.request, QtCore.SIGNAL("finished()"), self.startUpload )
	
	def startUpload(self):
		url = bytes( self.request.readAll() ).decode("UTF8")
		self.request.deleteLater()
		params = {"Filedata": open( self.fileName.encode(sys.getfilesystemencoding()),  "rb" ) }
		if self.destPath and self.destRepo:
			params["path"] = self.destPath.replace( os.sep, "/")
			params["rootNode"] = self.destRepo
		self.request = NetworkService.request( url, params )
		self.connect( self.request, QtCore.SIGNAL("finished()"), self.onFinished )
		self.connect( self.request, QtCore.SIGNAL("uploadProgress (qint64,qint64)"), self.onProgress )
	
	def onFinished(self):
		try:
			data = NetworkService.decode( self.request )
		except:
			self.emit( QtCore.SIGNAL("failed()") )
			return
		finally:
			self.request.deleteLater()
			self.request = None
		self.emit( QtCore.SIGNAL("finished(PyQt_PyObject)"), data )
	
	def onProgress(self, bytesSend, bytesTotal ):
		self.emit( QtCore.SIGNAL("uploadProgress(qint64,qint64)"), bytesSend, bytesTotal )
	
	def abort(self ):
		if self.request:
			self.request.abort()

class FileItem( TreeItem ):

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
		

class RecursiveUploader( QtGui.QWidget ):
	directorySize = 15 #Letz count an directory as 15 Bytes
	def __init__(self, files, rootNode, path, modul, *args, **kwargs ):
		super( RecursiveUploader, self ).__init__( *args, **kwargs )
		self.ui = Ui_FileUploadProgress()
		self.ui.setupUi( self )
		self.rootNode = rootNode
		self.modul = modul
		self.recursionInfo = [ (files, path, {}) ]
		self.request = None
		self.cancel = False
		self.currentFileSize = 0
		self.statsTotal = {	"bytes": 0, 
						"files": 0, 
						"dirs": 0 }
		self.statsDone = {	"bytes": 0, 
						"files": 0, 
						"dirs": 0 }
		for file in files:
			self.addTotalStat( file )
		self.ui.pbarTotal.setRange(0, self.statsTotal["bytes"])
		self.doUploadRecursive()
	
	def on_btnCancel_released(self, *args, **kwargs ):
		self.cancel = True
		if self.request:
			self.request.abort()
	
	def addTotalStat( self, file ):
		if os.path.isdir( file.encode(sys.getfilesystemencoding() ) ):
			self.statsTotal["dirs"] += 1
			self.statsTotal["bytes"] += self.directorySize
			for file in [(file+"/"+x).replace("//","/") for x in os.listdir(file+"/")]:
				self.addTotalStat( file )
		else:
			self.statsTotal["bytes"] += os.stat( file.encode(sys.getfilesystemencoding() ) ).st_size
			self.statsTotal["files"] += 1
		

	def addCacheInformation(self):
		if not self.cancel:
			files, path, cache = self.recursionInfo[ -1 ]
			if not path.endswith( "/" ):
				path += "/"
			cache[ path ] = NetworkService.decode( self.request )
		self.doUploadRecursive()
	
	def doUploadRecursive( self, data=None ):
		"""Uploads a list of Files/Dirs to the Server
		Should only be called by doUpload to prevent raceconditions in which an
		Subdirectory may be uploaded before its parent Direcotry has been created"""
		self.statsDone["bytes"] += self.currentFileSize
		self.currentFileSize = 0
		self.updateStats()
		if self.cancel or len( self.recursionInfo ) == 0:
			self.emit( QtCore.SIGNAL("finished(PyQt_PyObject)"), self )
			if self.request:
				self.request.deleteLater()
				self.request = None
			return
		files, path, cache = self.recursionInfo[ -1 ]
		if not path.endswith( "/" ):
			path += "/"
		if self.request:
			self.request.deleteLater()
			self.request = None
		#Upload the next file / create&process the next subdir
		if len(files)>0:
			file = files[0]
		else: #Were done with this level
			self.recursionInfo.pop() #Remove the last level
			self.doUploadRecursive()
			return
		#Fetch the corresponding directoryentry
		if not path in cache.keys():
			self.request = NetworkService.request("/file/list", {"rootNode":self.rootNode, "path":path })
			self.connect( self.request, QtCore.SIGNAL("finished()"), self.addCacheInformation )
			return
		data = cache[ path ]
		if os.path.isdir( file.encode(sys.getfilesystemencoding() ) ):
			#Check if the Directory exists on the server
			dirname = file.rstrip("/").split("/")[-1]
			if not dirname in data["subdirs"]:
				msg = QtCore.QCoreApplication.translate("FileHandler", "Creating dir %s in %s") % ( dirname, path )
				self.statsDone["dirs"] += 1
				self.currentFileSize = self.directorySize
				self.request = NetworkService.request("/%s/mkDir"% self.modul, {"rootNode": self.rootNode, "path":path, "dirname":dirname} )
				self.connect( self.request, QtCore.SIGNAL("finished()"), self.doUploadRecursive )
				del cache[ path ]
				return
			else:
				files.pop(0) #Were done with this element
				self.recursionInfo.append( ( [(file+"/"+x).replace("//","/") for x in os.listdir(file+"/")], path+dirname, {}  ) )
				self.doUploadRecursive()
				return
		else: #Looks like a file
			if file[ file.rfind("/")+1: ] in [ x["name"] for x in data["entrys"]]: #Filename already exists
				tmp = self.askOverwriteFile(	QtCore.QCoreApplication.translate("FileHandler", "Please confirm"), 
										QtCore.QCoreApplication.translate("FileHandler", "File %s exists in %s. Overwrite?") % (file[ file.rfind("/")+1: ], path) )
				if not tmp: #Dont overwrite
					files.pop(0) #Were done with this element
					self.doUploadRecursive()
					return
			self.currentFileSize = os.stat( file.encode(sys.getfilesystemencoding() ) ).st_size
			self.statsDone["files"] += 1
			self.request = FileUploader( file, path, self.rootNode )
			self.connect( self.request, QtCore.SIGNAL("uploadProgress (qint64,qint64)"), self.onUploadProgress )
			self.connect( self.request, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.doUploadRecursive )
			self.connect( self.request, QtCore.SIGNAL("failed()"), self.onFailed )
			files.pop(0) #Were done with this element

	def onFailed( self, *args, **kwargs ):
		self.emit( QtCore.SIGNAL("failed(PyQt_PyObject)"), self )
		if self.request:
			self.request.deleteLater()
			self.request = None
		return

	def updateStats(self):
		self.ui.lblProgress.setText( QtCore.QCoreApplication.translate("FileHandler", "Files: %s/%s, Directories: %s/%s, Bytes: %s/%s") % ( self.statsDone["files"], self.statsTotal["files"], self.statsDone["dirs"], self.statsTotal["dirs"], self.statsDone["bytes"], self.statsTotal["bytes"]) )
		self.ui.pbarTotal.setValue(self.statsDone["bytes"])
		self.ui.pbarFile.setValue( 0 )
	
	def onUploadProgress(self, bytesSend, bytesTotal ):
		self.ui.pbarFile.setRange( 0, bytesTotal )
		self.ui.pbarFile.setValue( bytesSend )
		
	def askOverwriteFile(self, title, text ):
		res = QtGui.QMessageBox.question( self, title, text,  buttons=QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel )
		if res == QtGui.QMessageBox.Yes:
			return(True)
		elif res == QtGui.QMessageBox.Cancel:
			return( False )
		return( None )

class RecursiveDownloader( QtGui.QWidget ):
	directorySize = 15 #Letz count an directory as 15 Bytes
	def __init__(self, localTargetDir, rootNode, path, files, dirs, modul, *args, **kwargs ):
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
				self.request.deleteLater()
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
	def __init__( self, *args, **kwargs ):
		super( FileWidget, self ).__init__( *args, **kwargs )
		self.startDrag = False

	def doUpload(self, files, rootNode, path ):
		if not files:
			return
		uploader = RecursiveUploader( files, rootNode, path, self.modul )
		self.ui.boxUpload.addWidget( uploader )
		self.connect( uploader, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.onTransferFinished )
		self.connect( uploader, QtCore.SIGNAL("failed(PyQt_PyObject)"), self.onTransferFailed )
	
	def onTransferFinished(self, task):
		self.flushCache( task.rootNode )
		self.loadData()
		task.deleteLater()
	
	def onTransferFailed(self, task):
		QtGui.QMessageBox.information( self, QtCore.QCoreApplication.translate("FileHandler", "Error during upload") , QtCore.QCoreApplication.translate("FileHandler", "There was an error uploading your files")  )
		self.flushCache( task.rootNode )
		self.reloadData()
		task.deleteLater()

	def download( self, targetDir, currentRootNode, path, files, dirs ):
		downloader = RecursiveDownloader( targetDir, self.currentRootNode, path, files, dirs, self.modul )
		self.ui.boxUpload.addWidget( downloader )
		self.connect( downloader, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.onTransferFinished )

	def dropEvent(self, event):
		if ( all( [ str(file.toLocalFile()).startswith("file://") or str(file.toLocalFile()).startswith("/") or ( len(str(file.toLocalFile()))>0 and str(file.toLocalFile())[1]==":")  for file in event.mimeData().urls() ] ) ) and len(event.mimeData().urls())>0:
			self.doUpload( [file.toLocalFile() for file in event.mimeData().urls()], self.currentRootNode, self.getPath() )
		else:
			super( FileWidget, self ).dropEvent( event )

	def dragEnterEvent( self, event ):
		if ( all( [ file.toLocalFile() and (str(file.toLocalFile()).startswith("file://") or str(file.toLocalFile()).startswith("/") or str(file.toLocalFile())[1]==":")  for file in event.mimeData().urls() ] ) ) and len(event.mimeData().urls())>0:
			event.accept()
		else:
			super( FileWidget, self ).dragEnterEvent( event )

	def on_listWidget_customContextMenuRequested(self, point ):
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
				widget = Edit(self.modul, item.data["id"])
				handler = EditHandler( self.modul, widget )
				event.emit( QtCore.SIGNAL('addHandler(PyQt_PyObject)'), handler )
		else:
			actionPaste = menu.addAction( QtCore.QCoreApplication.translate("FileHandler", "Insert") )
			selection = menu.exec_( self.ui.listWidget.mapToGlobal( point ) )
			if( selection==actionPaste and self.clipboard ):
				# self.ui.listWidget.currentItem() ):
				self.copy( self.clipboard, self.currentRootNode, self.getPath() )

