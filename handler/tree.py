from ui.treeUI import Ui_Tree
from PyQt4 import QtCore, QtGui, QtNetwork
from network import NetworkService
from event import event
from config import conf
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse
from time import sleep, time
import sys, os, os.path
from handler.edit import Edit, EditHandler
from utils import RegisterQueue, Overlay, QueryAggregator
from handler.list import ListCoreHandler



class IndexItem (QtGui.QListWidgetItem):
	def __init__(self,i,Iconpath,caption):
		super(IndexItem,self).__init__(QtGui.QIcon(Iconpath) , caption)
		self.i = i

class DirItem(QtGui.QListWidgetItem):
	def __init__( self, dirName ):
		super( DirItem, self ).__init__( QtGui.QIcon("icons/filetypes/folder.png"), str( dirName ) )
		self.dirName = dirName
	
	def __gt__( self, other ):
		if isinstance( other, TreeItem ):
			return( False )
		else:
			return( super( DirItem, self ).__gt__( other ) )

	def __lt__( self, other ):
		if isinstance( other, TreeItem ):
			return( True )
		else:
			return( super( DirItem, self ).__lt__( other ) )

class TreeItem(QtGui.QListWidgetItem):
	def __init__( self, data ):
		if isinstance( data, dict ) and "name" in data:
			name = str( data["name"] )
		else:
			name = " - "
		super( TreeItem, self ).__init__( QtGui.QIcon("icons/filetypes/unknown.png"), str( name ) )
		self.data = data

	def __gt__( self, other ):
		if isinstance( other, DirItem ):
			return( True )
		else:
			return( super( TreeItem, self ).__gt__( other ) )

	def __lt__( self, other ):
		if isinstance( other, DirItem ):
			return( False )
		else:
			return( super( TreeItem, self ).__lt__( other ) )

class TreeList( QtGui.QWidget ):
	dirItem = DirItem
	treeItem = TreeItem
	gridSizeIcon = (128,128)
	gridSizeList = (64,64)
	cache = {} #Cache Requests sothat allready visited Dirs load much faster
	
	def __init__(self, modul, currentRootNode=None, path=None, *args, **kwargs ):
		self.modul = modul
		self.page = 0
		self.rootNodes = {}
		self.flushList = [] #List of lambda: functions, which flush a set of cache-entries
		config = conf.serverConfig["modules"][ modul ]
		self.currentRootNode = currentRootNode
		self.path = path or []
		self.request = None
		if not "ui" in dir( self ):
			QtGui.QWidget.__init__( self, *args, **kwargs )
			self.ui = Ui_Tree()
			self.ui.setupUi( self )
			self.ui.listWidget.dropEvent = self.dropEvent
			self.ui.listWidget.dragEnterEvent = self.dragEnterEvent
			self.ui.listWidget.dragMoveEvent = self.dragMoveEvent
			self.ui.pathlist.dropEvent = self.pathListDropEvent
			self.ui.pathlist.dragEnterEvent = self.pathListDragEnterEvent
			self.ui.pathlist.dragMoveEvent = self.pathListDragMoveEvent
			self._mouseMoveEvent = self.ui.listWidget.mouseMoveEvent
			self.ui.listWidget.mouseMoveEvent = self.mouseMoveEvent
			self._mousePressEvent = self.ui.listWidget.mousePressEvent
			self.ui.listWidget.mousePressEvent = self.mousePressEvent
			self.ui.pathlist.setAcceptDrops(True)
			self.overlay = Overlay( self )
			self.toolBar = QtGui.QToolBar( self )
			self.toolBar.setIconSize( QtCore.QSize( 32, 32 ) )
			self.ui.boxActions.addWidget( self.toolBar )
			shortCut = QtGui.QShortcut( self.ui.editSearch )
			shortCut.setKey("Return")
			self.connect( shortCut,  QtCore.SIGNAL("activated()"), self.on_btnSearch_released )
			queue = RegisterQueue()
			event.emit( QtCore.SIGNAL('requestTreeModulActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), queue, self.modul, self )
			for item in queue.getAll():
				i = item( self )
				if isinstance( i, QtGui.QAction ):
					self.toolBar.addAction( i )
					self.ui.listWidget.addAction( i )
				else:
					self.toolBar.addWidget( i )
		if not self.currentRootNode:
			self.setDefaultRootNode()
		else:
			self.reloadData()
		self.connect( event, QtCore.SIGNAL('dataChanged(PyQt_PyObject,PyQt_PyObject)'), self.onDataChanged )
		self.clipboard = None  #(str repo,str path, bool doMove, list files, list dirs )
		self.startDrag = False

	def flushCache(self, repo, path=None ):
		"""
			Remove a path (or a whole RootNode) from Cache, sothat new requests
			wont be served from cache
			
			@param rootNode: RootNode of the repository
			@type rootNode: String
			@param path: (Optional) path with will be marked dirty
			@type path: String
		"""
		if not repo in TreeList.cache.keys():
			return
		if not path:
			TreeList.cache[ repo ] = {}
		else:
			try:
				del TreeList.cache[repo][path]
			except KeyError:
				pass

	def mousePressEvent(self, event ):
		if event.buttons() == QtCore.Qt.LeftButton and self.ui.listWidget.selectedItems():
			self.startDrag = True
		else:
			self.startDrag = False
		if self._mousePressEvent:
			self._mousePressEvent( event )

	def mouseMoveEvent(self, event):
		if self.startDrag:
			mimeData = QtCore.QMimeData()
			urls = []
			for item in self.ui.listWidget.selectedItems():
				if isinstance( item, TreeItem ):
					urls.append( QtCore.QUrl( "%s/%s/view/%s/%s" % ( NetworkService.url.replace("/admin", "") , self.modul, item.data["id"], item.data["name"] ) ) )
			mimeData.setUrls( urls )
			drag = QtGui.QDrag(self)
			drag.setMimeData(mimeData)
			drag.setHotSpot(event.pos() - self.rect().topLeft())
			dropAction = drag.start(QtCore.Qt.CopyAction)
		elif self._mouseMoveEvent:
			self._mouseMoveEvent( event )

	def onDataChanged(self, modul, emitingEntry ):
		if modul == self.modul and emitingEntry!=self:
			self.reloadData()

	def resizeEvent(self, resizeEvent):
		"""Ensure Items in listWidget get realigned if the available space changes"""
		super( TreeList, self ).resizeEvent( resizeEvent )
		self.ui.listWidget.reset()

	def dragMoveEvent( self, event ):
		event.accept()

	def dragEnterEvent(self, event ):
		if event.source() == self:
			event.accept()
			dirs = []
			files = []
			for item in self.ui.listWidget.selectedItems():
				if isinstance( item, self.dirItem ):
					dirs.append( item.dirName )
				else:
					files.append( item.data["name"] )
			self.clipboard = (self.currentRootNode, self.getPath(), True, files, dirs )

	def dropEvent(self, event):
		if event.source() == self:
			item = self.ui.listWidget.itemAt( event.pos() )
			if isinstance( item, self.dirItem ) and self.clipboard:
				self.copy( self.clipboard, self.currentRootNode,"/".join( self.path+[ item.dirName ] ) )
				self.clipboard = None

	def pathListDropEvent(self, event):
		if event.source()==self and self.clipboard:
			item = self.ui.pathlist.itemAt( event.pos() )
			path = "/".join( self.path[ : item.i ] ) or "/"
			srcRepo, srcPath, doMove, files, dirs = self.clipboard
			if path!=srcPath:
				self.copy( self.clipboard, self.currentRootNode, path )
				self.clipboard = None
		pass
	
	def pathListDragEnterEvent(self, event):
		if event.source()==self:
			event.accept()
			dirs = []
			files = []
			for item in self.ui.listWidget.selectedItems():
				if isinstance( item, self.dirItem ):
					dirs.append( item.dirName )
				else:
					files.append( item.data["name"] )
			self.clipboard = (self.currentRootNode, self.getPath(), True, files, dirs )

	def pathListDragMoveEvent(self, event):
		event.accept()

	def setRootNode( self, repoID, repoName ):
		if repoID==self.currentRootNode:
			return
		self.currentRootNode = repoID
		self.path = []
		self.reloadData()
	
	def setDefaultRootNode(self):
		if self.request:
			self.request.deleteLater()
		self.request = NetworkService.request("/%s/listRootNodes" % ( self.modul ) )
		self.connect( self.request, QtCore.SIGNAL("finished()"), self.onSetDefaultRootNode )
	
	def onSetDefaultRootNode(self):
		data =NetworkService.decode( self.request )
		self.request.deleteLater()
		self.rootNodes = data
		if not self.currentRootNode:
			try:
				self.currentRootNode = self.rootNodes[0]["key"]
			except:
				self.currentRootNode = None
				return
			self.reloadData()

	def reloadData( self, queryObj=None ):
		if self.request:
			self.request.deleteLater()
			self.request = None
		if self.flushList:
			while 1:
				try:
					task = self.flushList.pop()
				except IndexError:
					break
				task()
		path = self.getPath()
		if not self.currentRootNode in TreeList.cache.keys():
			TreeList.cache[ self.currentRootNode ] = {}
		if path in TreeList.cache[ self.currentRootNode ].keys() and not queryObj: # We have this Cached
			self.updatePathList()
			self.setData( TreeList.cache[ self.currentRootNode ][ path ] )
		else: # We need to fetch this
			self.overlay.inform( self.overlay.BUSY )
			self.updatePathList()
			self.request = NetworkService.request("/%s/list" % self.modul, queryObj or {"rootNode":self.currentRootNode, "path":path} )
			self.connect( self.request, QtCore.SIGNAL("finished()"), self.setData )
	
	def updatePathList(self ):
		foldericon= "icons/menu/folder_small.png"
		homeicon = "icons/menu/home_small.png"
		pathlist = self.ui.pathlist
		pathlist.clear()
		if self.getPath()==None:
			homeitem= IndexItem(0,homeicon, QtCore.QCoreApplication.translate("TreeHandler", "Home"))
			pathlist.addItem(homeitem)
			return
		homeitem= IndexItem(0,homeicon, QtCore.QCoreApplication.translate("TreeHandler", "Home") )
		pathlist.addItem(homeitem)
		counter=1
		for acaption in self.path:
			aitem= IndexItem(counter, foldericon, acaption)
			pathlist.addItem(aitem)
			counter+=1

	def on_pathlist_itemClicked (self,clickeditem):
		if self.getPath()==None:
			self.path = []
		else:
			self.path = self.path[ : clickeditem.i ]
		self.reloadData()

	def setData( self, data=None ):
		if not data:
			data = NetworkService.decode( self.request )
			self.request.deleteLater()
			self.request = None
			event.emit( QtCore.SIGNAL('dataChanged(PyQt_PyObject,PyQt_PyObject)'), self.modul, self )
		if self.getPath()!=None:
			TreeList.cache[ self.currentRootNode ][ self.getPath() ] = data
		self.ui.listWidget.clear()
		for dir in data["subdirs"]:
			self.ui.listWidget.addItem( self.dirItem( dir ) )
		for entry in data["entrys"]:
			self.ui.listWidget.addItem( self.treeItem( entry ) )
		self.overlay.clear( )
	

	def getPath(self):
		if self.path == None:
			return( None )
		else:
			return( "/".join( self.path ) or "/" )

	def mkdir(self, modulName, rootNode, path, dirName):
		if self.request:
			self.request.deleteLater()
		self.flushList.append( lambda*args, **kwargs: self.flushCache(rootNode, path) )
		self.request = NetworkService.request("/%s/mkDir"%modulName, {"rootNode":rootNode, "path":path, "dirname":dirName} )
		self.connect( self.request, QtCore.SIGNAL("finished()"), self.reloadData )
		self.connect( self.request, QtCore.SIGNAL("error (QNetworkReply::NetworkError)"), self.showError )
	
	def showError(self, error):
		if self.request:
			self.request.deleteLater()
			self.request = None
		self.overlay.inform( self.overlay.ERROR, str(error) )
		
	
	def on_listWidget_itemDoubleClicked(self, item ):
		if( isinstance( item, DirItem ) ):
			self.path.append( item.dirName )
			self.reloadData()
		else:
			descr = QtCore.QCoreApplication.translate("TreeHandler", "Edit entry")
			widget = Edit(self.modul, item.data["id"])
			handler = EditHandler( self.modul, widget )
			event.emit( QtCore.SIGNAL('addHandler(PyQt_PyObject)'), handler )
			
	def on_listWidget_customContextMenuRequested(self, point ):
		menu = QtGui.QMenu( self )
		if self.ui.listWidget.itemAt(point):
			actionRename = menu.addAction( QtCore.QCoreApplication.translate("TreeHandler", "Rename") )
			menu.addSeparator ()
			actionCopy = menu.addAction( QtCore.QCoreApplication.translate("TreeHandler", "Copy") )
			actionMove = menu.addAction( QtCore.QCoreApplication.translate("TreeHandler", "Cut") )
			actionDelete = menu.addAction( QtCore.QCoreApplication.translate("TreeHandler", "Delete") )
			selection = menu.exec_( self.ui.listWidget.mapToGlobal( point ) )
			if( selection==actionRename and self.ui.listWidget.currentItem() ):
				item = self.ui.listWidget.currentItem()
				if isinstance( item, DirItem ):
					oldName = item.dirName
				else:
					oldName = item.data["name"]
				newName, okay = QtGui.QInputDialog.getText( self, QtCore.QCoreApplication.translate("TreeHandler", "Rename"), QtCore.QCoreApplication.translate("TreeHandler", "New name"), text=oldName )
				if okay:
					self.rename( self.currentRootNode, self.getPath(), oldName, newName )
			elif selection == actionCopy or selection == actionMove:
				dirs = []
				files = []
				for item in self.ui.listWidget.selectedItems():
					if isinstance( item, DirItem ):
						dirs.append( item.dirName )
					else:
						files.append( item.data["name"] )
				doMove = (selection==actionMove)
				self.clipboard = ( self.currentRootNode, self.getPath(), doMove, files, dirs )
			elif selection == actionDelete:
				dirs = []
				files = []
				for item in self.ui.listWidget.selectedItems():
					if isinstance( item, DirItem ):
						dirs.append( item.dirName )
					else:
						files.append( item.data["name"] )
				self.delete( self.currentRootNode, self.getPath(), files, dirs )				
		else:
			actionPaste = menu.addAction( QtCore.QCoreApplication.translate("TreeHandler", "Insert") )
			selection = menu.exec_( self.ui.listWidget.mapToGlobal( point ) )
			if( selection==actionPaste and self.clipboard ):
				# self.ui.listWidget.currentItem() ):
				self.copy( self.clipboard, self.currentRootNode, self.getPath() )

	def delete( self, rootNode, path, files, dirs ):
		self.overlay.inform( self.overlay.BUSY )
		if self.request:
			self.request.deleteLater()
		self.request = QueryAggregator()
		for file in files:
			self.request.addQuery( NetworkService.request("/%s/delete" % self.modul, {	"rootNode":rootNode, 
										"path": path, 
										"name": file, 
										"type": "entry" } ) )
		for dir in dirs:
			self.request.addQuery( NetworkService.request("/%s/delete" % self.modul, {	"rootNode":rootNode, 
										"path": path, 
										"name": dir, 
										"type": "dir" } ) )
		self.flushList.append( lambda *args, **kwargs:  self.flushCache( rootNode, path ) )
		self.connect( self.request, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.onQueryAggregationFinished )
		self.overlay.inform( self.overlay.BUSY )
	
	def onQueryAggregationFinished(self, query=None ):
		if isinstance( self.request, QtNetwork.QNetworkReply ) or self.request.isIdle(): #This was the last one
			self.request.deleteLater()
			self.request = None
			self.reloadData()
			self.overlay.clear()

	def copy(self, clipboard, rootNode, path ):
		if self.request:
			self.request.deleteLater()
		self.request = QueryAggregator()
		srcRepo, srcPath, doMove, files, dirs = clipboard
		for file in files:
			self.request.addQuery( NetworkService.request( "/%s/copy" % self.modul , {"srcrepo": srcRepo,
									"srcpath": srcPath,
									"name": file,
									"destrepo": rootNode,
									"destpath": path,
									"deleteold": "1" if doMove else "0",
									"type":"entry"} ) )
		for dir in dirs:
			self.request.addQuery( NetworkService.request( "/%s/copy" % self.modul, {"srcrepo": srcRepo,
									"srcpath": srcPath,
									"name": dir,
									"destrepo": rootNode,
									"destpath": path,
									"deleteold": "1" if doMove else "0",
									"type":"dir"} ) )
		self.flushList.append( lambda *args, **kwargs: self.flushCache(rootNode, path) ) #Target Path
		self.flushList.append( lambda *args, **kwargs: self.flushCache(srcRepo, srcPath) ) #Source Path
		self.connect( self.request, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.onQueryAggregationFinished )
		self.overlay.inform( self.overlay.BUSY )
	
	def rename(self, rootNode, path, oldName, newName ):
		if self.request:
			self.request.deleteLater()
		self.flushList.append( lambda *args, **kwargs: self.flushCache(rootNode, path) )
		self.request = NetworkService.request( "/%s/rename" % self.modul , {"rootNode":rootNode, "path":path, "src": oldName, "dest":newName } )
		self.connect( self.request, QtCore.SIGNAL("finished()"), self.reloadData )
		self.overlay.inform( self.overlay.BUSY )
		
	def on_btnSearch_released(self, *args, **kwargs):
		self.path = None
		self.reloadData( {"rootNode":self.currentRootNode, "path": "",  "serach": self.ui.editSearch.text() }  )


class TreeEdit( Edit ):
	def __init__( self, modul, id=0, rootNode="", path="", *args, **kwargs ):
		self.rootNode = rootNode
		self.path = path
		super( TreeEdit, self ).__init__( modul, id, *args, **kwargs )
	
	def reloadData(self):
		if self.id: #We are in Edit-Mode
			self.request = NetworkService.request("/%s/edit/%s" % ( self.modul, self.id ), {"rootNode": self.rootNode, "path": self.path } )
		else:
			self.request = NetworkService.request("/%s/add/" % ( self.modul ), {"rootNode": self.rootNode, "path": self.path } )
		self.connect( self.request, QtCore.SIGNAL("finished()"), self.setData )

	def save(self, data ):
		if self.request:
			self.request.deleteLater()
			self.request = None
		print( data )
		data.update( {"rootNode": self.rootNode, "path": self.path } )
		print( data )
		if self.id:
			self.request = NetworkService.request("/%s/edit/%s" % ( self.modul, self.id ), data, secure=True )
		else:
			self.request = NetworkService.request("/%s/add/" % ( self.modul ), data, secure=True )
		self.connect( self.request, QtCore.SIGNAL("finished()"), self.onSaveResult )

	def emitEntryChanged( self, modul ):
		event.emit( QtCore.SIGNAL('dataChanged(PyQt_PyObject,PyQt_PyObject)'), modul, self )

class TreeAddAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( TreeAddAction, self ).__init__(  QtGui.QIcon("icons/actions/add_icon_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "Add entry"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.New )
	
	def onTriggered( self, e ):
		config = conf.serverConfig["modules"][ self.parent().modul ]
		if "name" in config.keys():
			name = QtCore.QCoreApplication.translate("TreeHandler", "Add entry: %s") % config["name"]
		else:
			name = QtCore.QCoreApplication.translate("TreeHandler", "Add entry")
		widget = TreeEdit(self.parent().modul, 0, rootNode=self.parent().currentRootNode, path=self.parent().getPath())
		handler = EditHandler( self.parentWidget().modul, widget )
		event.emit( QtCore.SIGNAL('addHandler(PyQt_PyObject)'), handler )


class TreeDirUpAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( TreeDirUpAction, self ).__init__(  QtGui.QIcon("icons/actions/folder_back_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "Directory up"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
	
	def onTriggered( self, e ):
		self.parent().path = self.parent().path[ : -1 ]
		self.parent().reloadData()

class TreeMkDirAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( TreeMkDirAction, self ).__init__(  QtGui.QIcon("icons/actions/folder_add_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "New directory"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( "SHIFT+Ctrl+N" )
		self.setShortcutContext( QtCore.Qt.WidgetWithChildrenShortcut )
	
	def onTriggered( self, e ):
		(dirName, okay) = QtGui.QInputDialog.getText( self.parent(), QtCore.QCoreApplication.translate("TreeHandler", "Create directory"), QtCore.QCoreApplication.translate("TreeHandler", "Directory name") )
		if dirName and okay:
			self.parent().mkdir( self.parent().modul, self.parent().currentRootNode, self.parent().getPath(), dirName )

class TreeDeleteAction( QtGui.QAction ): 
	def __init__(self, parent, *args, **kwargs ):
		super( TreeDeleteAction, self ).__init__(  QtGui.QIcon("icons/actions/delete_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "Delete"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.Delete )
		self.setShortcutContext( QtCore.Qt.WidgetWithChildrenShortcut )
	
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
		self.parent().delete( self.parent().currentRootNode, self.parent().getPath(), [ x["name"] for x in files], dirs )

class TreeBaseHandler( ListCoreHandler ):
	def __init__( self, modul, *args, **kwargs ):
		super( TreeBaseHandler, self ).__init__( modul, *args, **kwargs )
		config = conf.serverConfig["modules"][ modul ]
		if config["icon"]:
			lastDot = config["icon"].rfind(".")
			smallIcon = config["icon"][ : lastDot ]+"_small"+config["icon"][ lastDot: ]
			if os.path.isfile( os.path.join( os.getcwd(), smallIcon ) ):
				self.setIcon( 0, QtGui.QIcon( smallIcon ) )
			else:
				self.setIcon( 0, QtGui.QIcon( config["icon"] ) )
		self.setText( 0, config["name"] )

	def clicked( self ):
		if not self.widgets:
			self.addWidget( TreeList( self.modul ) )
		else:
			self.focus()

class TreeHandler( QtCore.QObject ):
	"""
	Created automatically to route Events to its handler in this file.png
	Do not create another instance of this!
	"""
	def __init__(self, *args, **kwargs ):
		"""
		Do not instantiate this!
		All parameters are passed to QObject.__init__
		"""
		QtCore.QObject.__init__( self, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('requestTreeModulActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)') ,  self.requestModulListActions )
		self.connect( event, QtCore.SIGNAL('requestModulHandler(PyQt_PyObject,PyQt_PyObject)'), self.requestModulHandler )

	
	def requestModulHandler(self, queue, modul ):
		"""Pushes a L{TreeBaseHandler} onto the queue if handled by "tree"
		
		@type queue: RegisterQueue
		@type modul: string
		@param modul: Name of the modul which should be handled
		"""
		config = conf.serverConfig["modules"][ modul ]
		if( config["handler"]=="tree" ):
			f = lambda: TreeBaseHandler( modul )
			queue.registerHandler( 5, f )
	
	
	def requestModulListActions(self, queue, modul, parent ):
		config = conf.serverConfig["modules"][ modul ]
		if config and config["handler"]=="tree":
			queue.registerHandler( 2, TreeDirUpAction )
			queue.registerHandler( 4, TreeAddAction )
			queue.registerHandler( 8, TreeMkDirAction )
			queue.registerHandler( 10, TreeDeleteAction )
			

	
	def openList(self, modulName, config ):
		if "name" in config.keys():
			name = config["name"]
		else:
			name = "Liste"
		if "icon" in config.keys():
			icon = config["icon"]
		else:
			icon = None
		event.emit( QtCore.SIGNAL('addHandlerWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), TreeList( modulName, config ), name, icon )

_fileHandler = TreeHandler()


