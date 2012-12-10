from ui.fileUploadProgressUI import Ui_FileUploadProgress
from ui.fileDownloadProgressUI import Ui_FileDownloadProgress
from PyQt4 import QtCore, QtGui
from network import NetworkService
from event import event
from config import conf
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse
from time import sleep, time
import sys, os
from handler.tree import TreeList, TreeDirUpAction, TreeMkDirAction, TreeDeleteAction,  TreeItem, DirItem
from handler.list import ListCoreHandler
from handler.edit import Edit, EditHandler
from PyQt4.QtCore import QUrl
import utils

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
			print("esc1")
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

class FileItem( TreeItem):

	def __init__( self, data ):
		super( FileItem, self ).__init__( data )
		self.data = data
		self.req = None
		extension=self.data["name"].split(".")[-1].lower()
		if os.path.isfile("icons/filetypes/%s.png"%(extension)):
			icon = QtGui.QIcon("icons/filetypes/%s.png"%(extension))
		else:
			icon = QtGui.QIcon("icons/filetypes/unknown.png")		
		
		if "meta_mime" in data.keys() and str(data["meta_mime"]).lower().startswith("image"):
			if utils.cachedFileExists( data["dlkey"] ):
				self.updateIcon( open( utils.getCachedFileName( data["dlkey"] ), "rb" ).read() )
			else:
				self.req = NetworkService.request( "/file/view/%s/file.dat" % data["dlkey"] )
				self.req.connect( self.req , QtCore.SIGNAL("finished()"), self.updateIcon )
	
	def updateIcon(self, data=None ):
		pixmap = QtGui.QPixmap()
		if data==None:
			data = self.req.readAll()
			open( utils.getCachedFileName( self.data["dlkey"] ), "w+b" ).write( data )
			pixmap.loadFromData( data )
			self.req.deleteLater()
			self.req = None
		else:
			pixmap.loadFromData( data ) 
		if( pixmap.isNull() ):
			extension=self.data["name"].split(".")[-1].upper()
			if os.path.isfile("icons/filetypes/%s.png"%(extension)):
				icon = QtGui.QIcon("icons/filetypes/%s.png"%(extension))
			else:
				icon = QtGui.QIcon("icons/filetypes/unknown.png")
		else:
			icon = QtGui.QIcon( pixmap.scaled( 128,128 ) )
		self.setIcon( icon )
		self.setToolTip("<img src=\"%s\" width=\"200\" height=\"200\"><br>%s" % ( utils.getCachedFileName( self.data["dlkey"] ), str( self.data["name"] ) ) )
		w = self.listWidget()
		if w:
			w.reset()
	
	def toURL( self ):
		return( "/file/view/%s/%s" % (self.data["dlkey"],self.data["name"]))
	
	def __del__(self):
		if self.req:
			self.req.abort()
		


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
				tmp = self.askOverwriteFile( QtCore.QCoreApplication.translate("FileHandler", "File %s exists in %s. Overwrite?") % (file[ file.rfind("/")+1: ], path))
				if tmp==None: #Dont overwrite
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

class UploadHandler( ):
	
	def __init__( self, *args, **kwargs ):
		super( UploadHandler, self ).__init__( *args, **kwargs )
		self.startDrag = False

	def flushCache(self, *args, **kwargs ):
		super( UploadHandler, self ).flushCache( *args,  **kwargs )
		
	def doUpload(self, files, rootNode, path ):
		if not files:
			return
		uploader = RecursiveUploader( files, rootNode, path, self.modul )
		self.ui.boxUpload.addWidget( uploader )
		self.connect( uploader, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.onTransferFinished )
		self.connect( uploader, QtCore.SIGNAL("failed(PyQt_PyObject)"), self.onTransferFailed )
	
	def onTransferFinished(self, task):
		self.flushCache( task.rootNode )
		self.reloadData()
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
			super( UploadHandler, self ).dropEvent( event )

	def dragEnterEvent( self, event ):
		if ( all( [ file.toLocalFile() and (str(file.toLocalFile()).startswith("file://") or str(file.toLocalFile()).startswith("/") or str(file.toLocalFile())[1]==":")  for file in event.mimeData().urls() ] ) ) and len(event.mimeData().urls())>0:
			event.accept()
		else:
			super( UploadHandler, self ).dragEnterEvent( event )

	def mouseMoveEvent(self, event):
		if self.startDrag:
			mimeData = QtCore.QMimeData()
			urls = []
			for item in self.ui.listWidget.selectedItems():
				if isinstance( item, FileItem ):
					urls.append( QtCore.QUrl( "%s/file/view/%s/%s" % ( NetworkService.url.replace("/admin", "") , item.data["dlkey"], item.data["name"] ) ) )
			mimeData.setUrls( urls )
			drag = QtGui.QDrag(self)
			drag.setMimeData(mimeData)
			drag.setHotSpot(event.pos() - self.rect().topLeft())
			dropAction = drag.start(QtCore.Qt.CopyAction)
		elif self._mouseMoveEvent:
			self._mouseMoveEvent( event )

	def on_listWidget_customContextMenuRequested(self, point ):
		#FIXME: Copy&Paste from tree.py
		menu = QtGui.QMenu( self )
		if self.ui.listWidget.itemAt(point):
			dirs = []
			files = []
			for item in self.ui.listWidget.selectedItems():
				if isinstance( item, DirItem ):
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
				if isinstance( item, DirItem ):
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

	def mousePressEvent(self, event ):
		if event.buttons() == QtCore.Qt.LeftButton and self.ui.listWidget.selectedItems():
			self.startDrag = True
		else:
			self.startDrag = False
		if self._mousePressEvent:
			self._mousePressEvent( event )


class FileList( UploadHandler, TreeList ):
	treeItem = FileItem
	
	def on_btnSearch_released(self, *args, **kwargs):
		self.path = None
		self.reloadData( {"rootNode":self.currentRootNode, "path": "",  "name$lk": self.ui.editSearch.text() }  )


class FileUploadAction( QtGui.QAction ): 
	def __init__(self, parent, *args, **kwargs ):
		super( FileUploadAction, self ).__init__(  QtGui.QIcon("icons/actions/upload_small.png"), QtCore.QCoreApplication.translate("FileHandler", "Upload files"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.New )
	
	def onTriggered( self, e ):
		files = QtGui.QFileDialog.getOpenFileNames()
		self.parent().doUpload( files, self.parent().currentRootNode, self.parent().getPath() )


class FileDownloadAction( QtGui.QAction ): 
	def __init__(self, parent, *args, **kwargs ):
		super( FileDownloadAction, self ).__init__(  QtGui.QIcon("icons/actions/download_small.png"), QtCore.QCoreApplication.translate("FileHandler", "Download files"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.Save )
	
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
		targetDir = QtGui.QFileDialog.getExistingDirectory( self.parentWidget() )
		if not targetDir:
			return
		self.parent().download( targetDir, self.parent().currentRootNode, self.parent().getPath(), files, dirs )


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


