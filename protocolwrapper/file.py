#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide import QtCore
from network import NetworkService, RequestGroup
from time import time
import weakref
from priorityqueue import protocolWrapperClassSelector, protocolWrapperInstanceSelector
from protocolwrapper.tree import TreeWrapper
import os, sys
from config import conf

ignorePatterns = [	#List of patterns of filenames/directories, which wont get uploaded
			lambda x: x.startswith("."),  #All files/dirs starting with a dot (".")
			lambda x: x.lower()=="thumbs.db",  #Thumbs.DB,
			lambda x: x.startswith("~") or x.endswith("~") #Temp files (ususally starts/ends with ~)
		]


class FileUploader( QtCore.QObject ):
	uploadProgress = QtCore.Signal( (int,int) )
	finished = QtCore.Signal( dict )
	failed = QtCore.Signal( )
	
	def __init__(self, fileName, destPath=None, destRepo=None, *args, **kwargs ):
		"""
		Uploads a file to the Server
		
		@type fileName: String
		@param fileName: Full Filename (and Path)
		@type destPath: String
		@param destPath: Target Path on the Server (must exist!)
		@type destRepo: String
		@param destRepo: ID of the target rootNode
		"""
		super( FileUploader, self ).__init__( *args, **kwargs )
		self.fileName = fileName
		self.destPath = destPath
		self.destRepo = destRepo
		NetworkService.request("/file/getUploadURL", successHandler=self.startUpload )
	
	def startUpload(self, req):
		print("xxx")
		url = req.readAll().data().decode("UTF-8")
		print(url)
		params = {"Filedata": open( self.fileName.encode(sys.getfilesystemencoding()),  "rb" ) }
		if self.destPath and self.destRepo:
			params["path"] = self.destPath.replace( os.sep, "/")
			params["rootNode"] = self.destRepo
		req = NetworkService.request( url, params, finishedHandler=self.onFinished )
		req.uploadProgress.connect( self.onProgress )
		#self.connect( req, QtCore.SIGNAL("uploadProgress (qint64,qint64)"), self.onProgress )
		
	
	def onFinished(self, req):
		try:
			data = NetworkService.decode( req )
		except:
			self.failed.emit()
			#self.emit( QtCore.SIGNAL("failed()") )
			return
		self.finished.emit( data )
		#self.emit( QtCore.SIGNAL("finished(PyQt_PyObject)"), data )
	
	def onProgress(self, req, bytesSend, bytesTotal ):
		self.uploadProgress.emit( bytesSend, bytesTotal )
		#self.emit( QtCore.SIGNAL("uploadProgress(qint64,qint64)"), bytesSend, bytesTotal )
	
	def abort(self ):
		if self.request:
			self.request.abort()

class RecursiveUploader( QtCore.QObject ):
	"""
		Upload files and/or directories from the the local filesystem to the server.
		This one is recursive, it supports uploading of files in subdirectories as well.
		Subdirectories on the server are created as needed.
		The functionality is bound to a widget displaying the current progress.
		If downloading has finished, finished(PyQt_PyObject=self) is emited.
	"""
	
	directorySize = 15 #Letz count an directory as 15 Bytes
	finished = QtCore.Signal( QtCore.QObject )
	failed = QtCore.Signal( QtCore.QObject )
	uploadProgress = QtCore.Signal( (int,int) )
	
	
	def __init__(self, files, rootNode, path, modul, *args, **kwargs ):
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
		super( RecursiveUploader, self ).__init__( *args, **kwargs )
		self.rootNode = rootNode
		self.modul = modul
		self.recursionInfo = [ ( [x for x in files if conf.cmdLineOpts.noignore or not any( [pattern(x) for pattern in ignorePatterns] ) ] , path, {}) ]
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
		#self.ui.pbarTotal.setRange(0, self.statsTotal["bytes"])
		self.doUploadRecursive()
	
	def cancelUpload(self, *args, **kwargs ):
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
		

	def addCacheInformation( self, req ):
		if not self.cancel:
			files, path, cache = self.recursionInfo[ -1 ]
			if not path.endswith( "/" ):
				path += "/"
			cache[ path ] = NetworkService.decode( req )
		self.doUploadRecursive()
	
	def doUploadRecursive( self, data=None ):
		"""
			Uploads a list of Files/Dirs to the Server
			Should only be called by doUpload to prevent raceconditions in which an
			Subdirectory may be uploaded before its parent Direcotry has been created.
		"""
		self.statsDone["bytes"] += self.currentFileSize
		self.currentFileSize = 0
		self.updateStats()
		if self.cancel or len( self.recursionInfo ) == 0:
			self.finished.emit( self )
			#self.emit( QtCore.SIGNAL("finished(PyQt_PyObject)"), self )
			if self.request:
				self.request = None
			return
		files, path, cache = self.recursionInfo[ -1 ]
		if not path.endswith( "/" ):
			path += "/"
		if self.request:
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
			NetworkService.request("/file/list", {"rootNode":self.rootNode, "path":path }, finishedHandler=self.addCacheInformation )
			#self.connect( self.request, QtCore.SIGNAL("finished()"), self.addCacheInformation )
			return
		data = cache[ path ]
		if os.path.isdir( file.encode(sys.getfilesystemencoding() ) ):
			#Check if the Directory exists on the server
			dirname = file.rstrip("/").split("/")[-1]
			if not dirname in data["subdirs"]:
				msg = QtCore.QCoreApplication.translate("FileHandler", "Creating dir %s in %s") % ( dirname, path )
				self.statsDone["dirs"] += 1
				self.currentFileSize = self.directorySize
				request = NetworkService.request("/%s/mkDir"% self.modul, {"rootNode": self.rootNode, "path":path, "dirname":dirname}, finishedHandler=self.doUploadRecursive )
				del cache[ path ]
				return
			else:
				files.pop(0) #Were done with this element
				self.recursionInfo.append( ( [(file+"/"+x).replace("//","/") for x in os.listdir(file+"/") if conf.cmdLineOpts.noignore or not any( [pattern(x) for pattern in ignorePatterns] ) ], path+dirname, {}  ) )
				self.doUploadRecursive()
				return
		else: #Looks like a file
			if file[ file.rfind("/")+1: ] in [ x["name"] for x in data["entrys"]]: #Filename already exists
				tmp = self.askOverwriteFile(	QtCore.QCoreApplication.translate("FileHandler", "Please confirm"), 
								QtCore.QCoreApplication.translate("FileHandler", "File %s exists in %s. Overwrite?") % (file[ file.rfind("/")+1: ], path) )
				if tmp is None: #Dont overwrite
					files.pop(0) #Were done with this element
					self.doUploadRecursive()
					return
				elif tmp is False: #Abort
					self.cancel = True
					self.doUploadRecursive()
					return
			self.currentFileSize = os.stat( file.encode(sys.getfilesystemencoding() ) ).st_size
			self.statsDone["files"] += 1
			request = FileUploader( file, path, self.rootNode, parent=self )
			request.uploadProgress.connect( self.onUploadProgress )
			request.finished.connect( self.doUploadRecursive )
			request.failed.connect( self.onFailed )
			files.pop(0) #Were done with this element

	def onFailed( self, *args, **kwargs ):
		self.failed.emit( self )
		#self.emit( QtCore.SIGNAL("failed(PyQt_PyObject)"), self )
		if self.request:
			self.request = None
		return

	def updateStats(self):
		return
		#self.ui.lblProgress.setText( QtCore.QCoreApplication.translate("FileHandler", "Files: %s/%s, Directories: %s/%s, Bytes: %s/%s") % ( self.statsDone["files"], self.statsTotal["files"], self.statsDone["dirs"], self.statsTotal["dirs"], self.statsDone["bytes"], self.statsTotal["bytes"]) )
		#self.ui.pbarTotal.setValue(self.statsDone["bytes"])
		#self.ui.pbarFile.setValue( 0 )
	
	def onUploadProgress(self, bytesSend, bytesTotal ):
		self.uploadProgress.emit( bytesSend, bytesTotal )
		#self.ui.pbarFile.setRange( 0, bytesTotal )
		#self.ui.pbarFile.setValue( bytesSend )
		
	def askOverwriteFile(self, title, text ):
		print( title )
		print( text )
		return( None )
		#res = QtGui.QMessageBox.question( self, title, text,  buttons=QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel )
		#if res == QtGui.QMessageBox.Yes:
		#	return(True)
		#elif res == QtGui.QMessageBox.Cancel:
		#	return( False )
		#return( None )

class RecursiveDownloader( QtCore.QObject ):
	"""
		Download files and/or directories from the server into the local filesystem.
		The functionality is bound to a widget displaying the current progress.
		If downloading has finished, finished(PyQt_PyObject=self) is emited.
	"""
	
	directorySize = 15 #Letz count an directory as 15 Bytes
	finished = QtCore.Signal( QtCore.QObject )
	failed = QtCore.Signal( QtCore.QObject )
	downloadProgress = QtCore.Signal( (int,int) )

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
		self.localTargetDir = localTargetDir
		self.rootNode = rootNode
		self.modul = modul
		self.recursionInfo = [ (files, dirs, path, localTargetDir) ]
		self.cancel = False
		self.doDownloadRecursive()
	
	
	def doDownloadRecursive( self ):
		if self.cancel or len( self.recursionInfo ) == 0:
			self.finished.emit( self )
			return
		files, dirs,  path, localTargetDir = self.recursionInfo[ -1 ]
		if not os.path.exists( localTargetDir ):
			os.mkdir( localTargetDir )
		if len( files ) > 0:
			file = files.pop()
			dlkey = "/file/view/%s/file.dat" % file["dlkey"]
			self.lastFileInfo = file["name"],localTargetDir
			request = NetworkService.request( dlkey )
			request.downloadProgress.connect( self.onDownloadProgress )
			request.finished.connect( self.saveFile )
		elif len( dirs ) > 0:
			dir = dirs.pop()
			self.lastDirInfo = path, localTargetDir, dir
			request = NetworkService.request("/%s/list" % self.modul, {"rootNode":self.rootNode, "path":"%s/%s" % (path, dir)} )
			request.finished.connect( self.onDirList )
		else: # Were done with this recursion
			self.recursionInfo.pop()
			self.doDownloadRecursive()

	
	def onDirList( self, req ):
		oldPath, oldTargetDir, dirName = self.lastDirInfo
		data = NetworkService.decode( req )
		self.recursionInfo.append( (data["entrys"], data["subdirs"], "%s/%s" % (oldPath, dirName), os.path.join(oldTargetDir, dirName) ) )
		self.doDownloadRecursive()
	
	def saveFile( self, req ):
		name, targetDir = self.lastFileInfo
		fh = open( os.path.join( targetDir, name), "wb+" )
		fh.write( req.readAll().data() )
		self.doDownloadRecursive()

	def onDownloadProgress(self, bytesDone, bytesTotal ):
		self.downloadProgress.emit( bytesDone, bytesTotal )
		#self.ui.pbarTotal.setRange( 0, bytesTotal )
		#self.ui.pbarTotal.setValue( bytesDone )


class FileWrapper( TreeWrapper ):
	protocolWrapperInstancePriority = 3
	
	def __init__( self, *args, **kwargs ):
		super( FileWrapper, self ).__init__( *args, **kwargs )
		self.transferQueues = [] #Keep a reference to uploader/downloader
	
	def upload(self, files, rootNode, path ):
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
		uploader = RecursiveUploader( files, rootNode, path, self.modul )
		self.transferQueues.append( uploader )
		#self.ui.boxUpload.addWidget( uploader )
		uploader.finished.connect( self.delayEmitEntriesChanged )
		uploader.finished.connect( self.removeFromTransferQueue )
		#self.connect( uploader, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.delayEmitEntriesChanged )
		#self.connect( uploader, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.removeFromTransferQueue )
		#self.connect( uploader, QtCore.SIGNAL("failed(PyQt_PyObject)"), self.onTransferFailed )
		return( uploader )

	def download( self, targetDir, rootNode, path, files, dirs ):
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
		downloader = RecursiveDownloader( targetDir, rootNode, path, files, dirs, self.modul )
		self.transferQueues.append( downloader )
		#self.ui.boxUpload.addWidget( downloader )
		self.connect( downloader, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.delayEmitEntriesChanged )
		self.connect( downloader, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.removeFromTransferQueue )
		return( downloader )
	
	def removeFromTransferQueue( self, obj ):
		self.transferQueues.remove( obj )
	
def CheckForFileModul( modulName, modulList ):
	modulData = modulList[ modulName ]
	if "handler" in modulData.keys() and modulData["handler"].startswith("tree.file"):
		print( modulData["handler"] )
		return( True )
	return( False )
	
protocolWrapperClassSelector.insert( 3, CheckForFileModul, FileWrapper )
