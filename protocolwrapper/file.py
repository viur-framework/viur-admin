#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt4 import QtCore
from network import NetworkService, RequestGroup
from time import time
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
	uploadProgress = QtCore.pyqtSignal( (int,int) )
	succeeded = QtCore.pyqtSignal( dict )
	failed = QtCore.pyqtSignal( )
	cancel = QtCore.pyqtSignal( )
	
	def __init__(self, fileName, node=None, *args, **kwargs ):
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
		self.node = node
		self.isCanceled = False
		self.cancel.connect( self.onCanceled )
		self.bytesTotal = len(open( self.fileName.encode(sys.getfilesystemencoding()),  "rb" ).read())
		self.bytesDone = 0
		NetworkService.request("/file/getUploadURL", successHandler=self.startUpload )
	
	def startUpload(self, req):
		self.uploadProgress.emit(0,1)
		url = req.readAll().data().decode("UTF-8")
		params = {"Filedata": open( self.fileName.encode(sys.getfilesystemencoding()),  "rb" ) }
		if self.node:
			params["node"] = self.node
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
		self.bytesDone = self.bytesTotal
		self.succeeded.emit( data )
		#self.emit( QtCore.SIGNAL("finished(PyQt_PyObject)"), data )
	
	def onProgress(self, req, bytesSend, bytesTotal ):
		self.bytesTotal = bytesTotal
		self.bytesDone = bytesSend
		self.uploadProgress.emit( bytesSend, bytesTotal )
		if self.isCanceled:
			req.abort()
	
	def getStats( self ):
		return( {	"dirsTotal": 0,
				"dirsDone": 0,
				"filesTotal": 1,
				"filesDone": 1 if self.bytesDone==self.bytesTotal else 0,
				"bytesTotal": self.bytesTotal,
				"bytesDone": self.bytesDone } )
	
	def onCanceled( self ):
		self.isCanceled = True
	

class RecursiveUploader( QtCore.QObject ):
	"""
		Upload files and/or directories from the the local filesystem to the server.
		This one is recursive, it supports uploading of files in subdirectories as well.
		Subdirectories on the server are created as needed.
		The functionality is bound to a widget displaying the current progress.
		If downloading has finished, finished(PyQt_PyObject=self) is emited.
	"""
	
	directorySize = 15 #Letz count an directory as 15 Bytes
	finished = QtCore.pyqtSignal( QtCore.QObject )
	failed = QtCore.pyqtSignal( QtCore.QObject )
	uploadProgress = QtCore.pyqtSignal( (int,int) )
	cancel = QtCore.pyqtSignal(  )
	
	def getDirName( self, name ):
		return( name.rstrip("/").split("/")[-1] )
	
	def __init__(self, files, node, modul, *args, **kwargs ):
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
		self.node = node
		self.modul = modul
		filteredFiles = [x for x in files if conf.cmdLineOpts.noignore or not any( [pattern(x) for pattern in ignorePatterns] ) ]
		#self.recursionInfo = [ (  ) ] , [node], {}) ]
		self.cancel.connect( self.onCanceled )
		self.isCanceled = False
		self.remainingRequests = 0
		self.stats = {	"dirsTotal": 0,
				"dirsDone": 0,
				"filesTotal": 0,
				"filesDone": 0,
				"bytesTotal": 0,
				"bytesDone": 0 }
		for fileName in files:
			if os.path.isdir( fileName.encode(sys.getfilesystemencoding() ) ):
				r = NetworkService.request( "/%s/list/node/%s" % (self.modul, self.node), successHandler=self.onDirListAvaiable )
				r.uploadDirName = fileName
				#r.uploadProgress.connect( self.uploadProgress )
				dirName = fileName.rstrip("/").split("/")[-1]
				self.stats["dirsTotal"] += 1
				self.remainingRequests += 1
			else:
				r = FileUploader( fileName, self.node, parent=self )
				r.uploadProgress.connect( self.uploadProgress )
				r.succeeded.connect( self.onRequestFinished )
				self.cancel.connect( r.cancel )
				self.remainingRequests += 1
		#for file in files:
		#	self.addTotalStat( file )
		
		#self.ui.pbarTotal.setRange(0, self.statsTotal["bytes"])
		#self.doUploadRecursive()
	
	def onRequestFinished( self, *args, **kwargs ):
		"""
			One of our sub-requests finished, decrease counter
		"""
		self.remainingRequests -= 1
		if self.remainingRequests==0:
			self.finished.emit( self )
	
	def getStats( self ):
		stats = {	"dirsTotal": 0,
				"dirsDone": 0,
				"filesTotal": 0,
				"filesDone": 0,
				"bytesTotal": 0,
				"bytesDone": 0 }
		# Merge my stats in
		for k in stats.keys():
			stats[ k ] += self.stats[ k ]
		for child in self.children():
			if "getStats" in dir( child ):
				tmp = child.getStats()
				for k in stats.keys():
					stats[ k ] += tmp[ k ]
		return( stats )
		
	def onDirListAvaiable( self, req ):
		if self.isCanceled:
			return
		data = NetworkService.decode( req )
		for skel in data["skellist"]:
			if skel["name"].lower() == self.getDirName( req.uploadDirName ).lower() :
				#This directory allready exists
				self.stats["dirsDone"] += 1
				r = RecursiveUploader( [ os.path.join( req.uploadDirName, x) for x in os.listdir( req.uploadDirName ) ], skel["id"], self.modul, parent=self )
				r.uploadProgress.connect( self.uploadProgress )
				r.finished.connect( self.onRequestFinished )
				self.cancel.connect( r.cancel )
				return
		r = NetworkService.request( "/%s/add/" % self.modul, {"node": self.node, "name": self.getDirName( req.uploadDirName ), "skelType":"node"}, secure=True, finishedHandler=self.onMkDir )
		r.uploadDirName = req.uploadDirName
		self.uploadProgress.emit( 0,1 )
	
	def onMkDir( self, req ):
		if self.isCanceled:
			return
		data = NetworkService.decode( req )
		assert data["action"] == "addSuccess"
		r = RecursiveUploader( [ os.path.join( req.uploadDirName, x) for x in os.listdir( req.uploadDirName ) ], data["values"]["id"], self.modul, parent=self )		
		r.uploadProgress.connect( self.uploadProgress )
		r.finished.connect( self.onRequestFinished )
		self.cancel.connect( r.cancel )
		self.stats["dirsDone"] += 1
		self.uploadProgress.emit( 0,1 )
	
	
	def onCanceled(self, *args, **kwargs ):
		self.isCanceled = True
	
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
			print("REK UP FINISHED")
			self.finished.emit( self )
			#self.emit( QtCore.SIGNAL("finished(PyQt_PyObject)"), self )
			return
		files, path, cache = self.recursionInfo[ -1 ]
		if not path.endswith( "/" ):
			path += "/"
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
				request = NetworkService.request("/%s/add/node"% self.modul, {"rootNode": self.rootNode, "path":path, "dirname":dirname}, finishedHandler=self.doUploadRecursive )
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
	finished = QtCore.pyqtSignal( QtCore.QObject )
	failed = QtCore.pyqtSignal( QtCore.QObject )
	downloadProgress = QtCore.pyqtSignal( (int,int) )

	def __init__(self, localTargetDir, files, dirs, modul, *args, **kwargs ):
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
		self.modul = modul
		self.cancel = False
		self.stats = {	"dirsTotal": 0,
				"dirsDone": 0,
				"filesTotal": 0,
				"filesDone": 0,
				"bytesTotal": 0,
				"bytesDone": 0 }
		self.remainingRequests = 0
		for file in files:
			self.remainingRequests += 1
			dlkey = "/%s/download/%s/file.dat" % (self.modul,file["dlkey"])
			request = NetworkService.request( dlkey, successHandler=self.saveFile, finishedHandler=self.onRequestFinished )
			request.fname = file["name"]
			request.fsize = file["size"]
			request.downloadProgress.connect( self.onDownloadProgress )
			self.stats["filesTotal"] += 1
			self.stats["bytesTotal"] += file["size"]
		for dir in dirs:
			assert not "~" in dir["name"] and not ".." in dir["name"]
			for t in ["node","leaf"]:
				self.remainingRequests += 1
				if not os.path.exists( os.path.join( self.localTargetDir, dir["name"] ) ):
					os.mkdir( os.path.join( self.localTargetDir, dir["name"] ) )
				request = NetworkService.request( "/%s/list/%s/%s" % (self.modul, t, dir["id"]), successHandler=self.onListDir, finishedHandler=self.onRequestFinished )
				request.dname = dir["name"]
				request.ntype = t
			self.stats["dirsTotal"] += 1
			self.stats["bytesTotal"] += self.directorySize
	
	def onRequestFinished( self, req ):
		self.remainingRequests -= 1 #Decrease our request counter
		if self.remainingRequests==0:
			QtCore.QTimer.singleShot( 100, self.onFinished )

	def onFinished( self ):
		# Delay emiting the finished signal
		self.finished.emit( self )

	def saveFile( self, req ):
		fh = open( os.path.join( self.localTargetDir, req.fname), "wb+" )
		fh.write( req.readAll().data() )
		self.stats["filesDone"] += 1
		self.stats["bytesDone"] += req.fsize
		self.downloadProgress.emit(0,0)

	def onDownloadProgress(self, bytesDone, bytesTotal ):
		self.downloadProgress.emit( bytesDone, bytesTotal )
		#self.ui.pbarTotal.setRange( 0, bytesTotal )
		#self.ui.pbarTotal.setValue( bytesDone )

	def onListDir( self, req ):
		data = NetworkService.decode( req )
		if len( data["skellist"])==0: #Nothing to do here
			return
		if req.ntype=="node":
			self.remainingRequests += 1
			r = RecursiveDownloader(	os.path.join( self.localTargetDir, req.dname ),
							[],
							data["skellist"],
							self.modul,
							parent=self )
			r.downloadProgress.connect( self.downloadProgress )
			r.finished.connect( self.onRequestFinished )
		else:
			self.remainingRequests += 1
			self.stats["dirsDone"] += 1
			self.stats["bytesDone"] += self.directorySize
			r = RecursiveDownloader(	os.path.join( self.localTargetDir, req.dname ),
							data["skellist"],
							[],
							self.modul,
							parent=self )
			r.downloadProgress.connect( self.downloadProgress )
			r.finished.connect( self.onRequestFinished )
		

	def getStats( self ):
		stats = {	"dirsTotal": 0,
				"dirsDone": 0,
				"filesTotal": 0,
				"filesDone": 0,
				"bytesTotal": 0,
				"bytesDone": 0 }
		# Merge my stats in
		for k in stats.keys():
			stats[ k ] += self.stats[ k ]
		for child in self.children():
			if "getStats" in dir( child ):
				tmp = child.getStats( )
				for k in stats.keys():
					stats[ k ] += tmp[ k ]
		return( stats )


class FileWrapper( TreeWrapper ):
	protocolWrapperInstancePriority = 3
	
	def __init__( self, *args, **kwargs ):
		super( FileWrapper, self ).__init__( *args, **kwargs )
		self.transferQueues = [] #Keep a reference to uploader/downloader
	
	def upload(self, files, node ):
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
		uploader = RecursiveUploader( files, node, self.modul, parent=self )
		#self.transferQueues.append( uploader )
		#self.ui.boxUpload.addWidget( uploader )
		uploader.finished.connect( self.delayEmitEntriesChanged )
		#uploader.finished.connect( self.removeFromTransferQueue )
		#self.connect( uploader, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.delayEmitEntriesChanged )
		#self.connect( uploader, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.removeFromTransferQueue )
		#self.connect( uploader, QtCore.SIGNAL("failed(PyQt_PyObject)"), self.onTransferFailed )
		return( uploader )

	def download( self, targetDir, files, dirs ):
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
		downloader = RecursiveDownloader( targetDir, files, dirs, self.modul )
		#self.transferQueues.append( downloader )
		#self.ui.boxUpload.addWidget( downloader )
		self.connect( downloader, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.delayEmitEntriesChanged )
		#self.connect( downloader, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.removeFromTransferQueue )
		return( downloader )
	
	#def removeFromTransferQueue( self, obj ):
	#	self.transferQueues.remove( obj )
	
def CheckForFileModul( modulName, modulList ):
	modulData = modulList[ modulName ]
	if "handler" in modulData.keys() and modulData["handler"].startswith("tree.simple.file"):
		return( True )
	return( False )
	
protocolWrapperClassSelector.insert( 3, CheckForFileModul, FileWrapper )
