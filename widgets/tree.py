# -*- coding: utf-8 -*-
from PySide import QtCore, QtGui
from utils import Overlay
from network import NetworkService, RequestGroup
from event import event
import utils
from priorityqueue import protocolWrapperInstanceSelector, actionDelegateSelector
from ui.treeUI import Ui_Tree
from mainwindow import WidgetHandler
from widgets.edit import EditWidget

class IndexItem (QtGui.QListWidgetItem):
	"""
		Shows one level in the path-widget.
	"""
	def __init__(self,i,Iconpath,caption):
		super(IndexItem,self).__init__(QtGui.QIcon(Iconpath) , caption)
		self.i = i

class DirItem(QtGui.QListWidgetItem):
	"""
		Displayes one subfolder inside a QListWidget
	"""
	def __init__( self, dirName ):
		super( DirItem, self ).__init__( QtGui.QIcon("icons/filetypes/folder.png"), str( dirName ) )
		self.dirName = dirName
	
	def __gt__( self, other ):
		if isinstance( other, TreeItem ):
			return( True )
		elif isinstance( other, DirItem ):
			return( self.dirName > other.dirName )
		else:
			return( str( self ) > str( other ) )

	def __lt__( self, other ):
		if isinstance( other, TreeItem ):
			return( False )
		elif isinstance( other, DirItem ):
			return( self.dirName < other.dirName )
		else:
			return( str( self ) < str( other ) )

class TreeItem(QtGui.QListWidgetItem):
	"""
		Displayes one generic entry inside a QListWidget.
		Can be overriden for a more accurate representation of the element.
	"""
	def __init__( self, data ):
		if isinstance( data, dict ) and "name" in data:
			name = str( data["name"] )
		else:
			name = " - "
		super( TreeItem, self ).__init__( QtGui.QIcon("icons/filetypes/unknown.png"), str( name ) )
		self.entryData = data

	def __gt__( self, other ):
		if isinstance( other, DirItem ):
			return( False )
		elif isinstance( other, TreeItem ):
			return( self.entryData["name"] > other.entryData["name"] )
		else:
			return( str( self ) > str( other ) )

	def __lt__( self, other ):
		if isinstance( other, DirItem ):
			return( True )
		elif isinstance( other, TreeItem ):
			return( self.entryData["name"] < other.entryData["name"] )
		else:
			return( str( self ) < str( other ) )

class TreeWidget( QtGui.QWidget ):
	"""
		Provides an interface for Data structured as a tree on the server.

		@emits treeChanged(PyQt_PyObject=emitter,PyQt_PyObject=modul,PyQt_PyObject=rootNode,PyQt_PyObject=itemID)
		@emits onItemClicked(PyQt_PyObject=item.data)
		@emits onItemDoubleClicked(PyQt_PyObject=item.data)
	"""
	
	gridSizeIcon = (128,128)
	gridSizeList = (64,64)
	cache = {} #Cache Requests sothat allready visited Dirs load much faster
	
	def __init__(self, modul, rootNode=None, path=None, treeItem=None, dirItem=None, actions=None, *args, **kwargs ):
		"""
			@param parent: Parent widget.
			@type parent: QWidget
			@param modul: Name of the modul to show the elements for
			@type modul: String
			@param rootNode: Key of the rootNode which data should be displayed. If None, this widget tries to choose one.
			@type rootNode: String or None
			@param path: If given, displaying starts in this path
			@type path: String or None
			@param treeItem: If set, use this class for displaying Entries inside the QListWidget.
			@param treeItem: QListWidgetItem
			@param treeItem: If set, use this class for displaying Directories inside the QListWidget.
			@param treeItem: QListWidgetItem
		"""
		super( TreeWidget, self ).__init__( *args, **kwargs )
		self.ui = Ui_Tree( )
		self.ui.setupUi( self )
		self.modul = modul
		self.currentRootNode = rootNode
		self.path = path or []
		self.searchStr = ""
		self.loadingKey = None #As loading is performed in background, they might return results for a dataset which isnt displayed anymore
		self.dirItem = dirItem or DirItem
		self.treeItem = treeItem or TreeItem
		self.editOnDoubleClick = True
		#self.ui.listWidget.dropEvent = self.dropEvent
		#self.ui.listWidget.dragEnterEvent = self.dragEnterEvent
		#self.ui.listWidget.dragMoveEvent = self.dragMoveEvent
		#self.ui.pathlist.dropEvent = self.pathListDropEvent
		#self.ui.pathlist.dragEnterEvent = self.pathListDragEnterEvent
		#self.ui.pathlist.dragMoveEvent = self.pathListDragMoveEvent
		#self._mouseMoveEvent = self.ui.listWidget.mouseMoveEvent
		#self.ui.listWidget.mouseMoveEvent = self.mouseMoveEvent
		#self._mousePressEvent = self.ui.listWidget.mousePressEvent
		#self.ui.listWidget.mousePressEvent = self.mousePressEvent
		#self.ui.pathlist.setAcceptDrops(True)
		self.overlay = Overlay( self )
		if not self.currentRootNode:
			self.setDefaultRootNode()
		else:
			self.loadData()
		self.clipboard = None  #(str repo,str path, bool doMove, list files, list dirs )
		self.startDrag = False
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		assert protoWrap is not None
		protoWrap.entitiesChanged.connect( self.onTreeChanged )
		#self.connect( protoWrap, QtCore.SIGNAL("entitiesChanged()"), self.onTreeChanged )
		if protoWrap.rootNodes:
			self.setRootNode( protoWrap.rootNodes[0]["key"], protoWrap.rootNodes[0]["name"] )
		#self.connect( event, QtCore.SIGNAL("treeChanged(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self.onTreeChanged )

		self.toolBar = QtGui.QToolBar( self )
		self.toolBar.setIconSize( QtCore.QSize( 32, 32 ) )
		self.ui.boxActions.addWidget( self.toolBar )
		self.setActions( actions if actions is not None else ["dirup","add","edit","clone","preview","delete"] )
		self.ui.listWidget.itemDoubleClicked.connect( self.listWidgetItemDoubleClicked )
		self.ui.pathlist.itemClicked.connect( self.pathListItemClicked )
		self.ui.listWidget.internalDrag( QtCore.Qt.MoveAction )
		#self.connect( self.tree, QtCore.SIGNAL("itemDoubleClicked(PyQt_PyObject)"), self.on_listWidget_itemDoubleClicked)

	def on_btnSearch_released(self, *args, **kwargs):
		self.search( self.ui.editSearch.text() )

	def on_editSearch_returnPressed(self):
		self.search( self.ui.editSearch.text() )
		
	def listWidgetItemDoubleClicked(self, item ):
		if( isinstance( item, self.treeItem ) ) and self.editOnDoubleClick:
			descr = QtCore.QCoreApplication.translate("TreeWidget", "Edit entry")
			handler = WidgetHandler( lambda: EditWidget(self.modul, EditWidget.appTree, item.entryData["id"]), descr )
			handler.stackHandler()
		elif( isinstance( item, DirItem ) ):
			self.path.append( item.dirName )
			self.loadData()

	def setActions( self, actions ):
		"""
			Sets the actions avaiable for this widget (ie. its toolBar contents).
			Setting None removes all existing actions
			@param actions: List of actionnames
			@type actions: List or None
		"""
		self.toolBar.clear()
		if not actions:
			return
		for action in actions:
			actionWdg = actionDelegateSelector.select( "tree.%s" % self.modul, action )
			if actionWdg is not None:
				actionWdg = actionWdg( self )
				if isinstance( actionWdg, QtGui.QAction ):
					self.toolBar.addAction( actionWdg )
				else:
					self.toolBar.addWidget( actionWdg )

	def onTreeChanged( self ):
		#gc.collect()
		#print("i am %s" % str(self) )
		#for x in gc.get_referrers( self ):
		#	print( x )
		#if emitter==self: #We issued this event - ignore it as we allready knew
		#	return
		#if modul and modul!=self.modul: #Not our modul
		#	return
		#if rootNode and rootNode!=self.currentRootNode: #Not in our Hierarchy
		#	return
		#Well, seems to affect us, refresh our view
		self.loadData()

	def prepareDeletion(self):
		"""
			Cleanup the mess we made; otherwise
			the gc cant keep up.
		"""
		self.ui.listWidget.dropEvent = None
		self.ui.listWidget.dragEnterEvent = None
		self.ui.listWidget.dragMoveEvent = None
		self.ui.pathlist.dropEvent = None
		self.ui.pathlist.dragEnterEvent = None
		self.ui.pathlist.dragMoveEvent = None
		self._mouseMoveEvent = None
		self.ui.listWidget.mouseMoveEvent = None
		self._mousePressEvent = None
		self.ui.listWidget.mousePressEvent = None

	def selectedItems(self):
		"""
			Returns the currently selected items.
			Dont mix these with the selectedItems from relationalBones.
			@returns: List
		"""
		return( self.ui.listWidget.selectedItems() )

	def flushCache(self, repo, path=None ):
		"""
			Remove a path (or a whole RootNode) from Cache, sothat new requests
			wont be served from cache
			
			@param rootNode: RootNode of the repository
			@type rootNode: String
			@param path: (Optional) path with will be marked dirty
			@type path: String
		"""
		if not repo in TreeWidget.cache.keys():
			return
		#if not path:
		#	TreeWidget.cache[ repo ] = {}
		#else:
		#	try:
		#		del TreeWidget.cache[repo][path]
		#	except KeyError:
		#		pass

	def mousePressEvent(self, event ):
		"""
			Remember the state of the MouseBtns, so we can initiate a drag-operation if needed.
		"""
		if self._mousePressEvent:
			self._mousePressEvent( event )
		if event.buttons() == QtCore.Qt.LeftButton and self.ui.listWidget.selectedItems():
			self.startDrag = True
		else:
			self.startDrag = False

	def mouseMoveEvent(self, event):
		"""
			The mouse as moved. We might need to initiate a drag-operation.
		"""
		if self.startDrag:
			mimeData = QtCore.QMimeData()
			urls = []
			for item in self.ui.listWidget.selectedItems():
				if isinstance( item, self.treeItem ):
					urls.append( utils.urlForItem( self.modul, item.data) )
			mimeData.setUrls( urls )
			drag = QtGui.QDrag(self)
			drag.setMimeData(mimeData)
			drag.setHotSpot(event.pos() - self.rect().topLeft())
			dropAction = drag.start(QtCore.Qt.CopyAction)
		elif self._mouseMoveEvent:
			self._mouseMoveEvent( event )

	def resizeEvent(self, resizeEvent):
		"""Ensure Items in listWidget get realigned if the available space changes"""
		super( TreeWidget, self ).resizeEvent( resizeEvent )
		self.ui.listWidget.reset()

	def dragMoveEvent( self, event ):
		event.accept()

	def dragEnterEvent(self, event ):
		"""
			Allow Drag&Drop inside this widget (ie. moving files to subdirs)
		"""
		print("----------------------------")
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
		"""
			Elements have been dropped onto the path-list.
			Check which folder (if any) was under the cursor when the items dropped
			and move them to the corresponding directory.
		"""

		if event.source()==self and self.clipboard:
			item = self.ui.pathlist.itemAt( event.pos() )
			path = "/".join( self.path[ : item.i ] ) or "/"
			srcRepo, srcPath, doMove, files, dirs = self.clipboard
			if path!=srcPath:
				self.copy( self.clipboard, self.currentRootNode, path )
				self.clipboard = None
	
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

	def setRootNode( self, rootNode, repoName="" ):
		"""
			Switch to the given RootNode of our modul and start displaying these items.
			@param rootNode: Key of the new rootNode.
			@type rootNode: String
			@param repoName: Human-readable description of the given rootNode
			@type repoName: -Currently ignored-
		"""
		if rootNode==self.currentRootNode:
			return
		self.currentRootNode = rootNode
		self.path = []
		self.loadData()
	
	def setDefaultRootNode(self):
		NetworkService.request("/%s/listRootNodes" % ( self.modul ), successHandler=self.onSetDefaultRootNode )
	
	def onSetDefaultRootNode(self, request):
		data =NetworkService.decode( request )
		self.rootNodes = data
		if not self.currentRootNode:
			try:
				self.currentRootNode = self.rootNodes[0]["key"]
			except:
				self.currentRootNode = None
				return
			self.loadData()

	def loadData( self, queryObj=None ):
		path = self.getPath()
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		self.loadingKey = protoWrap.queryData( self.setData, self.currentRootNode, self.path )
	
	def updatePathList(self ):
		foldericon= "icons/menu/folder_small.png"
		homeicon = "icons/menu/home_small.png"
		pathlist = self.ui.pathlist
		pathlist.clear()
		homeitem= IndexItem( 0, homeicon, QtCore.QCoreApplication.translate("TreeWidget", "Home") )
		pathlist.addItem(homeitem)
		if self.getPath()==None:
			return
		counter=1
		for acaption in self.path:
			aitem= IndexItem(counter, foldericon, acaption)
			pathlist.addItem(aitem)
			counter+=1

	def pathListItemClicked (self,clickeditem):
		if self.getPath()==None:
			self.path = []
		else:
			self.path = self.path[ : clickeditem.i ]
		self.loadData()

	def setData( self, queryKey, data, cursor ):
		if queryKey is not None and queryKey!= self.loadingKey: #The Data is for a list we dont display anymore
			return
		self.ui.listWidget.clear()
		for dir in data["subdirs"]:
			self.ui.listWidget.addItem( self.dirItem( dir ) )
		for entry in data["entrys"]:
			self.ui.listWidget.addItem( self.treeItem( entry ) )
		self.updatePathList()
		self.overlay.clear( )
	
	def getPath(self):
		if self.path == None:
			return( None )
		else:
			return( "/".join( self.path ) or "/" )

	def search( self, searchStr ):
		"""
			Start a search for the given string.
			If searchStr is None, it ends a currently active search.
			@param searchStr: Token to search for
			@type searchStr: String or None
		"""
		if searchStr:
			self.path = None
			self.searchStr = searchStr
			self.loadData( {"rootNode":self.currentRootNode, "path": "",  "name$lk": self.searchStr } )
		else:
			self.path = []
			self.searchStr = None
			self.loadData( )

	def onRequestSucceeded(self, request, *args, **kwargs):
		"""
			We modified something on the server, and that request succeded
		"""
		event.emit( QtCore.SIGNAL('treeChanged(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self, self.modul, self.currentRootNode, None )
		self.loadData()

	def mkdir(self, rootNode, path, dirName):
		"""
			Creates a new directory on the server.
			
			@param rootNode: rootNode to create the directory under.
			@type rootNode: String
			@param path: Path to create the directory in
			@type path: String
			@param dirName: Name of the new directory
			@type dirName: String
		"""
		request = NetworkService.request("/%s/mkDir"% self.modul, {"rootNode":rootNode, "path":path, "dirname":dirName}, successHandler=self.onRequestSucceeded, failureHandler=self.showError )
		#request.flushList = [ lambda*args, **kwargs: self.flushCache(rootNode, path) ]

	def delete( self, rootNode, path, files, dirs ):
		"""
			Delete files and/or directories from the server.
			Directories dont need to be empty, the server handles that case internally.
			
			@param rootNode: rootNode to delete from
			@type rootNode: String
			@param path: Path (relative to the rootNode) which contains the elements which should be deleted.
			@type path: String
			@param files: List of filenames in that directory.
			@type files: List
			@param dirs: List of directories in that directory.
			@type dirs: List
		"""
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		protoWrap.delete( rootNode, path, files, dirs )
		self.overlay.inform( self.overlay.BUSY )

	def copy(self, clipboard, rootNode, path ):
		"""
			Copy or move elements to the given rootNode/path.
			
			@param clipboard: Tuple holding all informations about the elements which get moved/copied
			@type clipboard: (srcRepo, srcPath, doMove, entities, dirs)
			@param rootNode: Destination rootNode
			@type rootNode: String
			@param path: Destination path
			@type path: String
		"""
		srcRepo, srcPath, doMove, files, dirs = clipboard
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		protoWrap.copy( srcRepo, srcPath, files, dirs, rootNode, path, doMove )
		self.overlay.inform( self.overlay.BUSY )
	
	def onProgessUpdate(self, request, done, maximum ):
		if request.queryType == "move":
			descr =  QtCore.QCoreApplication.translate("TreeWidget", "Moving: %s of %s finished.")
		elif request.queryType == "copy":
			descr =  QtCore.QCoreApplication.translate("TreeWidget", "Copying: %s of %s finished.")
		elif request.queryType == "delete":
			descr =  QtCore.QCoreApplication.translate("TreeWidget", "Deleting: %s of %s removed.")
		else:
			raise NotImplementedError()
		self.overlay.inform( self.overlay.BUSY, descr % (done, maximum) )
	
	def rename(self, rootNode, path, oldName, newName ):
		"""
			Rename an entity or directory.
			
			@param rootNode: rootNode the element is in
			@type rootNode: String
			@param path: Path to that element.
			@type path: String
			@param oldName: Old name of the element
			@type oldName: String
			@param newName: The new name for that element
			@type newName: String
		"""
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		protoWrap.rename( rootNode, path, oldName, newName )
		self.overlay.inform( self.overlay.BUSY )

	def showError(self, reqWrapper, error):
		self.overlay.inform( self.overlay.ERROR, str(error) )
		
	def on_listWidget_itemClicked( self, item ):
		"""
			A item has been selected. Emit onItemClicked.
		"""
		self.emit( QtCore.SIGNAL("onItemClicked(PyQt_PyObject)"), item.data )


	def on_listWidget_customContextMenuRequested(self, point ):
		menu = QtGui.QMenu( self )
		if self.ui.listWidget.itemAt(point):
			actionRename = menu.addAction( QtCore.QCoreApplication.translate("TreeWidget", "Rename") )
			menu.addSeparator ()
			actionCopy = menu.addAction( QtCore.QCoreApplication.translate("TreeWidget", "Copy") )
			actionMove = menu.addAction( QtCore.QCoreApplication.translate("TreeWidget", "Cut") )
			actionDelete = menu.addAction( QtCore.QCoreApplication.translate("TreeWidget", "Delete") )
			selection = menu.exec_( self.ui.listWidget.mapToGlobal( point ) )
			if( selection==actionRename and self.ui.listWidget.currentItem() ):
				item = self.ui.listWidget.currentItem()
				if isinstance( item, DirItem ):
					oldName = item.dirName
				else:
					oldName = item.data["name"]
				newName, okay = QtGui.QInputDialog.getText( self, QtCore.QCoreApplication.translate("TreeWidget", "Rename"), QtCore.QCoreApplication.translate("TreeWidget", "New name"), text=oldName )
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
			actionPaste = menu.addAction( QtCore.QCoreApplication.translate("TreeWidget", "Insert") )
			selection = menu.exec_( self.ui.listWidget.mapToGlobal( point ) )
			if( selection==actionPaste and self.clipboard ):
				# self.ui.listWidget.currentItem() ):
				self.copy( self.clipboard, self.currentRootNode, self.getPath() )

	def keyPressEvent( self, e ):
		"""
			Catch and handle QKeySequence.Delete.
		"""
		if e.matches( QtGui.QKeySequence.Delete ):
			dirs = []
			files = []
			for item in self.ui.listWidget.selectedItems():
				if isinstance( item, DirItem ):
					dirs.append( item.dirName )
				else:
					files.append( item.data["name"] )
			self.delete( self.currentRootNode, self.getPath(), files, dirs )		
		else:
			super( TreeWidget, self ).keyPressEvent( e )

