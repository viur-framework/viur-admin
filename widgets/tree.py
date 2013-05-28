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
import json

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

class PathListView( QtGui.QListWidget ):
	pathChanged = QtCore.Signal( (list,) )
	rootNodeChanged = QtCore.Signal( (str,) )
	
	def __init__( self, modul, rootNode, path=None, *args, **kwargs ):
		super( PathListView, self ).__init__( *args, **kwargs )
		self.setAcceptDrops( True )
		self.modul = modul
		self.rootNode = rootNode
		self.setPath( path or [] )
		self.itemClicked.connect( self.pathListItemClicked )
		self.setFlow( self.LeftToRight )
		self.setFixedHeight( 35 )
	
	def dragEnterEvent(self, event ):
		if event.mimeData().hasFormat("viur/treeDragData"):
			event.accept()
		else:
			event.ignore()
	
	def dragMoveEvent( self, event ):
		if self.itemAt( event.pos() ):
			event.accept()
		else:
			event.ignore()
	
	def dropEvent( self, event ):
		dataDict = json.loads( event.mimeData().data("viur/treeDragData").data().decode("UTF-8") )
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		assert protoWrap is not None
		destIndex = self.itemAt( event.pos() ).i
		protoWrap.copy(	dataDict["srcRootNode"],
				dataDict["srcPath"],
				dataDict["files"],
				dataDict["dirs"],
				self.rootNode,
				self.path[ : destIndex ],
				True )
	
	@QtCore.Slot( list )
	def setPath( self, path, isInitialCall=False ):
		foldericon= "icons/menu/folder_small.png"
		homeicon = "icons/menu/home_small.png"
		self.path = path
		self.clear()
		homeitem= IndexItem( 0, homeicon, QtCore.QCoreApplication.translate("TreeWidget", "Home") )
		self.addItem(homeitem)
		counter=1
		for acaption in self.path:
			aitem= IndexItem(counter, foldericon, acaption)
			self.addItem(aitem)
			counter+=1
		if isInitialCall:
			self.pathChanged.emit( self.path )
	
	@QtCore.Slot( str )
	def setRootNode( self, rootNode ):
		self.rootNode = rootNode
		
	def pathListItemClicked (self, clickeditem):
		self.setPath( self.path[ : clickeditem.i ] )
		self.pathChanged.emit( self.path )


class TreeListView( QtGui.QListWidget ):
	
	gridSizeIcon = (128,128)
	gridSizeList = (64,64)
	
	treeItem = TreeItem
	dirItem = DirItem

	pathChanged = QtCore.Signal( (list,) )
	rootNodeChanged = QtCore.Signal( (str,) )
	
	def __init__(self, modul, rootNode=None, path=None, *args, **kwargs ):
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
		super( TreeListView, self ).__init__( *args, **kwargs )
		self.modul = modul
		self.rootNode = rootNode
		self.path = path or []
		self.loadingKey = None #As loading is performed in background, they might return results for a dataset which isnt displayed anymore
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		assert protoWrap is not None
		protoWrap.entitiesChanged.connect( self.onTreeChanged )
		#self.connect( protoWrap, QtCore.SIGNAL("entitiesChanged()"), self.onTreeChanged )
		self.itemDoubleClicked.connect( self.onItemDoubleClicked )
		self.setContextMenuPolicy( QtCore.Qt.CustomContextMenu )
		self.customContextMenuRequested.connect( self.onCustomContextMenuRequested )
		self.setDragEnabled( True )
		self.setAcceptDrops( True )
		self.setViewMode( self.IconMode )
		self.setIconSize( QtCore.QSize( *[x-24 for x in self.gridSizeIcon] ) )
		self.setGridSize( QtCore.QSize( *self.gridSizeIcon ) )
		if self.rootNode is not None:
			self.loadData()
	
	## Getters & Setters
	
	def getPath(self):
		if self.path == None:
			return( [] )
		else:
			return( self.path )
	
	def getRootNode( self ):
		return( self.rootNode )
		
	def getModul( self ):
		return( self.modul )
	
	@QtCore.Slot( list )
	def setPath( self, path, isInitialCall=False ):
		assert isinstance( path, list )
		self.path = path
		self.loadData()
		if isInitialCall:
			self.pathChanged.emit( self.path )

	def onItemDoubleClicked(self, item ):
		if( isinstance( item, self.dirItem ) ):
			self.path.append( item.dirName )
			self.loadData()
			self.pathChanged.emit( self.getPath() )

	def dragEnterEvent(self, event ):
		"""
			Allow Drag&Drop inside this widget (ie. moving files to subdirs)
		"""
		if event.source() == self:
			event.accept()
			dirs = []
			files = []
			for item in self.selectedItems():
				if isinstance( item, self.dirItem ):
					dirs.append( item.dirName )
				else:
					files.append( item.entryData["name"] )
			event.mimeData().setData( "viur/treeDragData", json.dumps( {	"srcRootNode": self.rootNode,
											"srcPath": self.getPath(),
											"dirs": dirs,
											"files": files } ) )

	def dragMoveEvent( self, event ):
		if isinstance( self.itemAt( event.pos() ), self.treeItem ):
			event.ignore()
		else:
			event.accept()

	def dropEvent( self, event ):
		dataDict = json.loads( event.mimeData().data("viur/treeDragData").data().decode("UTF-8") )
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		assert protoWrap is not None
		destItem = self.itemAt( event.pos() )
		if not isinstance( destItem, self.dirItem ):
			# Entries have no childs, only dirItems can have children
			return
		protoWrap.copy(	dataDict["srcRootNode"],
				dataDict["srcPath"],
				dataDict["files"],
				dataDict["dirs"],
				self.rootNode,
				self.path+[destItem.dirName],
				True )

	def setRootNode( self, rootNode, repoName="" ):
		"""
			Switch to the given RootNode of our modul and start displaying these items.
			@param rootNode: Key of the new rootNode.
			@type rootNode: String
			@param repoName: Human-readable description of the given rootNode
			@type repoName: -Currently ignored-
		"""
		if rootNode==self.rootNode:
			return
		self.rootNode = rootNode
		self.path = []
		self.loadData()
	
	def setDefaultRootNode(self):
		NetworkService.request("/%s/listRootNodes" % ( self.modul ), successHandler=self.onSetDefaultRootNode )
	
	def onSetDefaultRootNode(self, request):
		data =NetworkService.decode( request )
		self.rootNodes = data
		if not self.rootNode:
			try:
				self.rootNode = self.rootNodes[0]["key"]
			except:
				self.rootNode = None
				return
			self.loadData()

	def loadData( self, queryObj=None ):
		path = self.getPath()
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		self.loadingKey = protoWrap.queryData( self.setData, self.rootNode, self.path )
		
	def onTreeChanged( self ):
		self.loadData()

	def setData( self, queryKey, data, cursor ):
		if queryKey is not None and queryKey!= self.loadingKey: #The Data is for a list we dont display anymore
			return
		self.clear()
		for dir in data["subdirs"]:
			self.addItem( self.dirItem( dir ) )
		for entry in data["entrys"]:
			self.addItem( self.treeItem( entry ) )
		#self.updatePathList()
		#self.overlay.clear( )
		
	def onCustomContextMenuRequested(self, point ):
		import sys
		menu = QtGui.QMenu( self )
		if self.itemAt(point):
			actionRename = menu.addAction( QtCore.QCoreApplication.translate("TreeWidget", "Rename") )
			actionRename.task = "rename"
			menu.addSeparator ()
			actionCopy = menu.addAction( QtCore.QCoreApplication.translate("TreeWidget", "Copy") )
			actionCopy.task = "copy"
			actionMove = menu.addAction( QtCore.QCoreApplication.translate("TreeWidget", "Cut") )
			actionMove.task = "move"
			actionDelete = menu.addAction( QtCore.QCoreApplication.translate("TreeWidget", "Delete") )
			actionDelete.task = "delete"
		elif QtGui.QApplication.clipboard().mimeData().hasFormat("viur/treeDragData"):
			actionPaste = menu.addAction( QtCore.QCoreApplication.translate("TreeWidget", "Insert") )
			actionPaste.task = "paste"
		menu.triggered.connect( self.onContextMenuTriggered )
		menu.popup( self.mapToGlobal( point ) )

	def onContextMenuTriggered( self, action ):
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		assert protoWrap is not None
		if( action.task=="rename" and self.currentItem() ):
			item = self.currentItem()
			if isinstance( item, DirItem ):
				oldName = item.dirName
			else:
				oldName = item.entryData["name"]
			newName, okay = QtGui.QInputDialog.getText( self, QtCore.QCoreApplication.translate("TreeWidget", "Rename"), QtCore.QCoreApplication.translate("TreeWidget", "New name"), text=oldName )
			if okay:
				protoWrap.rename( self.rootNode, self.getPath(), oldName, newName )
		elif action.task=="copy" or action.task=="move":
			dirs = []
			files = []
			for item in self.selectedItems():
				if isinstance( item, DirItem ):
					dirs.append( item.dirName )
				else:
					files.append( item.entryData["name"] )
			doMove = (action.task=="move")
			mimeData = QtCore.QMimeData()
			mimeData.setData( "viur/treeDragData", json.dumps( {	"srcRootNode": self.rootNode,
										"srcPath": self.getPath(),
										"dirs": dirs,
										"files": files,
										"domove": doMove } ) )
			QtGui.QApplication.clipboard().setMimeData( mimeData )
		elif action.task=="delete":
			dirs = []
			files = []
			for item in self.selectedItems():
				if isinstance( item, DirItem ):
					dirs.append( item.dirName )
				else:
					files.append( item.data["name"] )
			protoWrap.delete( self.rootNode, self.getPath(), files, dirs )
		elif action.task=="paste":
				# self.currentItem() ):
				data = json.loads( QtGui.QApplication.clipboard().mimeData().data("viur/treeDragData").data().decode("UTF-8") )
				#srcRootNode, srcPath, files, dirs, destRootNode, destPath, doMove ):
				protoWrap.copy( data["srcRootNode"], data["srcPath"], data["files"], data["dirs"], self.rootNode, self.getPath(), data["domove"] )
				#self.copy( self.clipboard, self.rootNode, self.getPath() )
	
	def getTreeItemClass( self ):
		return( self.treeItem )
		
	def getDirItemClass( self ):
		return( self.dirItem )

class TreeWidget( QtGui.QWidget ):
	"""
		Provides an interface for Data structured as a tree on the server.

		@emits treeChanged(PyQt_PyObject=emitter,PyQt_PyObject=modul,PyQt_PyObject=rootNode,PyQt_PyObject=itemID)
		@emits onItemClicked(PyQt_PyObject=item.data)
		@emits onItemDoubleClicked(PyQt_PyObject=item.data)
	"""
	treeWidget = TreeListView
	
	pathChanged = QtCore.Signal( (list,) )
	rootNodeChanged = QtCore.Signal( (str,) )
	currentItemChanged = QtCore.Signal( (QtGui.QListWidgetItem,QtGui.QListWidgetItem) )

	def __init__(self, modul, rootNode=None, path=None, actions=None, *args, **kwargs ):
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
		self.rootNode = rootNode
		self.path = path
		self.tree = self.treeWidget( modul, rootNode, path )
		self.ui.listWidgetBox.layout().addWidget( self.tree )
		self.pathList = PathListView( modul, rootNode, path )
		self.ui.pathListBox.layout().addWidget( self.pathList )
		self.editOnDoubleClick = True
		
		# Inbound Signals 
		self.pathList.pathChanged.connect( self.pathChanged )
		self.tree.pathChanged.connect( self.pathChanged )
		self.pathList.rootNodeChanged.connect( self.rootNodeChanged )
		self.tree.rootNodeChanged.connect( self.rootNodeChanged )
		
		# Outbound Signals
		self.pathChanged.connect( self.tree.setPath )
		self.pathChanged.connect( self.pathList.setPath )
		self.rootNodeChanged.connect( self.tree.setRootNode )
		self.rootNodeChanged.connect( self.pathList.setRootNode )
		
		# Internal Signals
		self.pathChanged.connect( self.setPath )
		self.rootNodeChanged.connect( self.setRootNode )
		
		"""
		#Cross-connection between sub-widgets
		self.pathList.pathChanged.connect( self.tree.setPath )
		self.tree.pathChanged.connect( self.pathList.setPath )
		self.pathList.rootNodeChanged.connect( self.tree.setRootNode )
		self.tree.rootNodeChanged.connect( self.pathList.setRootNode )

		#Inbound signals
		self.pathList.pathChanged.connect( self.onPathChanged )
		self.tree.pathChanged.connect( self.onPathChanged )
		self.pathList.rootNodeChanged.connect( self.onRootNodeChanged )
		self.tree.rootNodeChanged.connect( self.onRootNodeChanged )
		self.tree.currentItemChanged.connect( self.currentItemChanged )
		
		#Outbound signals
		self.pathChanged.connect( self.tree.setPath )
		self.pathChanged.connect( self.pathList.setPath )
		self.rootNodeChanged.connect( self.tree.setRootNode )
		self.rootNodeChanged.connect( self.pathList.setRootNode )
		"""
		#self.ui.listWidget.dropEvent = self.dropEvent
		#self.ui.listWidget.dragEnterEvent = self.dragEnterEvent
		#self.ui.listWidget.dragMoveEvent = self.dragMoveEvent
		#self.pathList.dropEvent = self.pathListDropEvent
		#self.pathList.dragEnterEvent = self.pathListDragEnterEvent
		#self.pathList.dragMoveEvent = self.pathListDragMoveEvent
		#self._mouseMoveEvent = self.ui.listWidget.mouseMoveEvent
		#self.ui.listWidget.mouseMoveEvent = self.mouseMoveEvent
		#self._mousePressEvent = self.ui.listWidget.mousePressEvent
		#self.ui.listWidget.mousePressEvent = self.mousePressEvent
		#self.pathList.setAcceptDrops(True)
		self.overlay = Overlay( self )

		self.clipboard = None  #(str repo,str path, bool doMove, list files, list dirs )
		self.startDrag = False

		#self.connect( event, QtCore.SIGNAL("treeChanged(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self.onTreeChanged )

		self.toolBar = QtGui.QToolBar( self )
		self.toolBar.setIconSize( QtCore.QSize( 32, 32 ) )
		self.ui.boxActions.addWidget( self.toolBar )
		self.setActions( actions if actions is not None else ["dirup","mkdir","add","edit","clone","preview","delete"] )
		#self.ui.listWidget.itemDoubleClicked.connect( self.listWidgetItemDoubleClicked )
		#self.pathList.itemClicked.connect( self.pathListItemClicked )
		#self.ui.listWidget.internalDrag( QtCore.Qt.MoveAction )
		#self.connect( self.tree, QtCore.SIGNAL("itemDoubleClicked(PyQt_PyObject)"), self.on_listWidget_itemDoubleClicked)
		#self.tree.pathChanged.connect( self.updatePathList )
		protoWrap = protocolWrapperInstanceSelector.select( modul )
		assert protoWrap is not None
		protoWrap.busyStateChanged.connect( self.onBusyStateChanged )
		if protoWrap.rootNodes:
			self.onRootNodesAvaiable()
		else:
			protoWrap.rootNodesAvaiable.connect( self.onRootNodesAvaiable )

	def onRootNodesAvaiable( self ):
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		self.setRootNode( protoWrap.rootNodes[0]["key"], protoWrap.rootNodes[0]["name"] )

	def onPathChanged( self, path ):
		self.path = path
	
	def onRootNodeChanged( self, rootNode ):
		self.rootNode = rootNode
	
	def onBusyStateChanged( self, busy ):
		print("Im now: ",busy)
		if busy:
			self.overlay.inform( self.overlay.BUSY )
		else:
			self.overlay.clear()

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
			actionWdg = actionDelegateSelector.select( "tree.%s" % self.getModul(), action )
			if actionWdg is not None:
				actionWdg = actionWdg( self )
				if isinstance( actionWdg, QtGui.QAction ):
					self.toolBar.addAction( actionWdg )
				else:
					self.toolBar.addWidget( actionWdg )


	def selectedItems(self):
		"""
			Returns the currently selected items.
			Dont mix these with the selectedItems from relationalBones.
			@returns: List
		"""
		return( self.tree.selectedItems() )




	def setRootNode( self, rootNode, repoName="" ):
		"""
			Switch to the given RootNode of our modul and start displaying these items.
			@param rootNode: Key of the new rootNode.
			@type rootNode: String
			@param repoName: Human-readable description of the given rootNode
			@type repoName: -Currently ignored-
		"""
		if rootNode==self.rootNode:
			return
		self.rootNode = rootNode
		self.path = []
		self.rootNodeChanged.emit( self.rootNode )
		self.pathChanged.emit( self.path )
	
	def getPath(self):
		return( self.path )
	
	def setPath( self, path, isInitialCall=False ):
		self.path = path
		if isInitialCall:
			self.pathChanged.emit( self.path )
	
	def getRootNode( self ):
		return( self.rootNode )
	
	def getModul( self ):
		return( self.modul )

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
			self.loadData( {"rootNode":self.rootNode, "path": "",  "name$lk": self.searchStr } )
		else:
			self.path = []
			self.searchStr = None
			self.loadData( )

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
					self.rename( self.rootNode, self.getPath(), oldName, newName )
			elif selection == actionCopy or selection == actionMove:
				dirs = []
				files = []
				for item in self.ui.listWidget.selectedItems():
					if isinstance( item, DirItem ):
						dirs.append( item.dirName )
					else:
						files.append( item.data["name"] )
				doMove = (selection==actionMove)
				self.clipboard = ( self.rootNode, self.getPath(), doMove, files, dirs )
			elif selection == actionDelete:
				dirs = []
				files = []
				for item in self.ui.listWidget.selectedItems():
					if isinstance( item, DirItem ):
						dirs.append( item.dirName )
					else:
						files.append( item.data["name"] )
				self.delete( self.rootNode, self.getPath(), files, dirs )				
		else:
			actionPaste = menu.addAction( QtCore.QCoreApplication.translate("TreeWidget", "Insert") )
			selection = menu.exec_( self.ui.listWidget.mapToGlobal( point ) )
			if( selection==actionPaste and self.clipboard ):
				# self.ui.listWidget.currentItem() ):
				self.copy( self.clipboard, self.rootNode, self.getPath() )

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
			self.delete( self.rootNode, self.getPath(), files, dirs )		
		else:
			super( TreeWidget, self ).keyPressEvent( e )

	def getTreeItemClass( self ):
		return( self.tree.getTreeItemClass() )
		
	def getDirItemClass( self ):
		return( self.tree.getDirItemClass() )
