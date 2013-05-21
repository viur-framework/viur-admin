# -*- coding: utf-8 -*-
from PySide import QtCore, QtGui
from utils import Overlay
from network import NetworkService
from event import event
import utils
from config import conf
from widgets.edit import EditWidget
from priorityqueue import protocolWrapperInstanceSelector, actionDelegateSelector
from ui.hierarchyUI import Ui_Hierarchy

class HierarchyItem(QtGui.QTreeWidgetItem):
	"""
		Displayes one entry in a QTreeWidget.
		Its comparison-methods have been overriden to reflect the sort-order on the server.
	"""	
	def __init__( self, modul, data ):
		config = conf.serverConfig["modules"][ modul ]
		if "format" in config.keys():
			format = config["format"]
		else:
			format = "$(name)"
		protoWrap = protocolWrapperInstanceSelector.select( modul )
		assert protoWrap is not None
		itemName = utils.formatString( format, protoWrap.structure, data )
		super( HierarchyItem, self ).__init__( [str( itemName )] )
		self.loaded = False
		self.entryData = data
		self.setChildIndicatorPolicy( QtGui.QTreeWidgetItem.ShowIndicator )

	def __gt__( self, other ):
		if isinstance( other, HierarchyItem ) and "sortindex" in self.entryData.keys() and "sortindex" in other.entryData.keys():
			return( self.entryData["sortindex"] > other.entryData["sortindex"] )
		else:
			return( super( HierarchyItem, self ).__gt__( other ) )

	def __lt__( self, other ):
		if isinstance( other, HierarchyItem ) and "sortindex" in self.entryData.keys() and "sortindex" in other.entryData.keys():
			return( self.entryData["sortindex"] < other.entryData["sortindex"] )
		else:
			return( super( HierarchyItem, self ).__lt__( other ) )
			

class HierarchyTreeWidget( QtGui.QTreeWidget ):
	"""
		Provides an interface for Data structured as a hierarchy on the server.
		
		@emits hierarchyChanged( PyQt_PyObject=emitter, PyQt_PyObject=modul, PyQt_PyObject=rootNode, PyQt_PyObject=itemID )
		@emits onItemClicked(PyQt_PyObject=item.data)
		@emits onItemDoubleClicked(PyQt_PyObject=item.data)
		
	"""
	
	itemClicked = QtCore.Signal( (object,) )
	itemDoubleClicked = QtCore.Signal( (object,) )
	
	def __init__(self, parent, modul, rootNode=None, *args, **kwargs ):
		"""
			@param parent: Parent widget.
			@type parent: QWidget
			@param modul: Name of the modul to show the elements for
			@type modul: String
			@param rootNode: Key of the rootNode which data should be displayed. If None, this widget tries to choose one.
			@type rootNode: String or None
		"""
		super( HierarchyTreeWidget, self ).__init__( parent, *args, **kwargs )
		self.modul = modul
		self.currentRootNode = rootNode
		self.loadingKey = None
		self.overlay = Overlay( self )
		self.expandList = []
		self.setHeaderHidden( True )
		self.setAcceptDrops( True )
		self.setDragDropMode( self.InternalMove )
		self.rootNodes = None
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		assert protoWrap is not None
		if not self.currentRootNode:
			protoWrap.getRootNodes( self.onRootNodesAvaiable )
		#	#self.loadRootNodes( self.)
		protoWrap.entitiesChanged.connect( self.onHierarchyChanged )
		#self.connect( protoWrap, QtCore.SIGNAL("entitiesChanged()"), self.onHierarchyChanged )
		#self.connect( self, QtCore.SIGNAL("itemExpanded(QTreeWidgetItem *)"), self.onItemExpanded )
		self.itemExpanded.connect( self.onItemExpanded )
		#self.connect( event, QtCore.SIGNAL("hierarchyChanged(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self.onHierarchyChanged )
		#self.connect( self,  QtCore.SIGNAL("itemClicked(QTreeWidgetItem *,int)"), self.onItemClicked )
		self.itemClicked.connect( self.onItemClicked )
		#self.connect( self, QtCore.SIGNAL("itemDoubleClicked (QTreeWidgetItem *,int)"), self.onItemDoubleClicked )
		self.itemDoubleClicked.connect( self.onItemDoubleClicked )


	def onItemClicked( self, item ):
		"""
			A item has been selected. Emit onItemClicked.
		"""
		self.itemClicked.emit( item.entryData )

	def onItemDoubleClicked(self, item ):
		"""
			A item has been doubleClicked. Emit onItemDoubleClicked.
		"""
		self.itemDoubleClicked.emit( item.entryData )
		
	def onHierarchyChanged(self ):
		"""
			Respond to changed Data - refresh our view
		"""
		#Well, seems to affect us, refresh our view
		#First, save all expanded items
		print("p4")
		self.expandList = []
		it = QtGui.QTreeWidgetItemIterator( self )
		while( it.value() ):
			if it.value().isExpanded():
				self.expandList.append( it.value().entryData["id"] )
			it+=1
		#Now clear the treeview and reload data
		self.clear()
		self.loadData()

	def setRootNode( self, rootNode, repoName=None ):
		"""
			Set the current rootNode.
			(A Modul might have several independent hierarchies)
			@param rootNode: Key of the RootNode.
			@type rootNode: String
			@param repoName: Displayed name of the rootNode (currently unused)
			@param repoName: String or None
		"""
		print("p14")
		self.currentRootNode = rootNode
		self.clear()
		self.loadData()

	def onItemExpanded(self, item, *args, **kwargs):
		"""
			An item has just been expanded.
			Check, if we allready have information about the elements beneath, otherwhise load them.
		"""
		print("p3")
		if not item.loaded:
			while( item.takeChild(0) ):
				pass
			self.loadData( item.entryData["id"] )

	def onRootNodesAvaiable(self, rootNodes ):
		print("p12")
		self.rootNodes = rootNodes
		if not self.currentRootNode:
			try:
				self.currentRootNode = list( self.rootNodes )[0]["key"]
			except:
				return
			self.loadData()
	
	def onLoadError(self, request, error ):
		print("p11")
		self.overlay.inform( self.overlay.ERROR, str(error) )
	
	def onRequestSucceeded(self, request):
		"""
			We modified something on the server, and that request succeded
		"""
		print("p10")
		event.emit( QtCore.SIGNAL('hierarchyChanged(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self, self.modul, self.currentRootNode, None )
		self.loadData()
		
	def loadData(self, parent=None):
		self.overlay.inform( self.overlay.BUSY )
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		assert protoWrap is not None
		protoWrap.queryData( self.setData, (parent or self.currentRootNode) )
		#NetworkService.request( "/%s/list/%s" % (self.modul, (parent or self.currentRootNode) ), successHandler=self.setData, failureHandler=self.onLoadError )

	def setData(self, queryKey, data, cursor ):
		#if queryKey is not None and queryKey!= self.loadingKey: #The Data is for a list we dont display anymore
		#	return
		print("p9")
		if len( data ):
			if data[0]["parententry"] == self.currentRootNode:
				self.clear()
		for itemData in data:
			tvItem = HierarchyItem( self.modul, itemData )
			if( itemData["parententry"] == self.currentRootNode ):
				self.addTopLevelItem( tvItem )
			else:
				self.insertItem( tvItem )
			if tvItem.entryData["id"] in self.expandList:
				tvItem.setExpanded(True)
		self.sortItems(0, QtCore.Qt.AscendingOrder)
		self.setSortingEnabled( False )
		self.overlay.clear()

	def insertItem( self, newItem, fromChildren=None ):
		"""
			New data got avaiable - insert it into the corresponding locations.
		"""
		print("p5")
		if not fromChildren:
			idx = 0
			item = self.topLevelItem( idx )
			while item:
				if item.entryData["id"] == newItem.entryData["parententry"]:
					item.addChild( newItem )
					item.loaded=True
					return
				self.insertItem( newItem, item )
				idx += 1
				item = self.topLevelItem( idx )
		else:
			idx = 0
			child = fromChildren.child( idx )
			while child:
				if child.entryData["id"] == newItem.entryData["parententry"]:
					child.addChild( newItem )
					child.loaded=True
					return
				self.insertItem( newItem, child )
				idx += 1
				child = fromChildren.child( idx )

	def dragEnterEvent( self, event ):
		""""
			Add URL-Mimedata to the dragevent, so it can be dropped outside.
		"""
		print("p2")
		if event.source() == self:
			mimeData = event.mimeData()
			urls = []
			for item in self.selectedItems():
				urls.append( utils.urlForItem( self.modul, item.entryData) )
			mimeData.setUrls( urls )
		super( HierarchyTreeWidget, self ).dragEnterEvent( event )

	def dropEvent( self, event ):
		"""
			An Item has been moved inside our HierarchyWidget,
			Move it to the correct location on the server.
		"""
		print("p1")
		try:
			dragedItem =  self.selectedItems()[0]
		except:
			return
		targetItem = self.itemAt( event.pos() )
		QtGui.QTreeWidget.dropEvent( self, event )
		if not targetItem: #Moved to the end of the list
			self.reparent( dragedItem.entryData["id"], self.currentRootNode )
			if self.topLevelItemCount()>1:
				self.updateSortIndex( dragedItem.entryData["id"], self.topLevelItem( self.topLevelItemCount()-2 ).entryData["sortindex"]+1 )
		else:
			if id(dragedItem.parent()) == id(targetItem): #Moved to subitem
				self.reparent( dragedItem.entryData["id"], targetItem.entryData["id"] )
			else: # Moved within its parent list
				while( targetItem ):
					childIndex = 0
					while( childIndex < targetItem.childCount() ):
						currChild = targetItem.child( childIndex )
						if currChild == dragedItem:
							self.reparent( dragedItem.entryData["id"], targetItem.entryData["id"] )
							if childIndex==0 and targetItem.childCount()>1: # is now 1st item
								self.updateSortIndex( dragedItem.entryData["id"], targetItem.child( 1 ).entryData["sortindex"]-1 )
							elif childIndex==(targetItem.childCount()-1) and childIndex>0: #is now lastitem
								self.updateSortIndex( dragedItem.entryData["id"], targetItem.child( childIndex-1 ).entryData["sortindex"]+1 )
							elif childIndex>0 and childIndex<(targetItem.childCount()-1): #in between
								newSortIndex = ( targetItem.child( childIndex-1 ).entryData["sortindex"]+ targetItem.child( childIndex+1 ).entryData["sortindex"] ) / 2.0
								self.updateSortIndex( dragedItem.entryData["id"], newSortIndex )
							else: # We are the only one in this layer
								pass
							return
						childIndex += 1
					targetItem = targetItem.parent()
				childIndex = 0
				currChild = self.topLevelItem( childIndex )
				while( currChild ):
					if currChild == dragedItem:
						self.reparent( dragedItem.entryData["id"], self.currentRootNode )
						if childIndex==0 and self.topLevelItemCount()>1: # is now 1st item
							self.updateSortIndex( dragedItem.entryData["id"], self.topLevelItem( 1 ).entryData["sortindex"]-1 )
						elif childIndex==(self.topLevelItemCount()-1) and childIndex>0: #is now lastitem
							self.updateSortIndex( dragedItem.entryData["id"], self.topLevelItem( childIndex-1 ).entryData["sortindex"]+1 )
						elif childIndex>0 and childIndex<(self.topLevelItemCount()-1): #in between
							newSortIndex = ( self.topLevelItem( childIndex-1 ).entryData["sortindex"]+ self.topLevelItem( childIndex+1 ).entryData["sortindex"] ) / 2.0
							self.updateSortIndex( dragedItem.entryData["id"], newSortIndex )
						else: # We are the only one in this layer
							pass
						return
					childIndex+=1
					currChild = self.topLevelItem( childIndex )

	def reparent(self, itemKey, destParent):
		print("p6")
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		assert protoWrap is not None
		protoWrap.reparent( itemKey, destParent )
		self.overlay.inform( self.overlay.BUSY )

	def updateSortIndex(self, itemKey, newIndex):
		print("p7")
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		assert protoWrap is not None
		protoWrap.updateSortIndex( itemKey, newIndex )
		self.overlay.inform( self.overlay.BUSY )

	def delete( self, id ):
		print("p8")
		"""
			Delete the entity with the given id
		"""
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		assert protoWrap is not None
		protoWrap.delete( id )
		self.overlay.inform( self.overlay.BUSY )
		





class HierarchyWidget( QtGui.QWidget ):
	
	def __init__(self, modul, repoID=None, actions=None, *args, **kwargs ):
		super( HierarchyWidget, self ).__init__( *args, **kwargs )
		self.ui = Ui_Hierarchy()
		self.ui.setupUi( self )
		layout = QtGui.QHBoxLayout( self.ui.treeWidget )
		self.ui.treeWidget.setLayout( layout )
		self.hierarchy =  HierarchyTreeWidget( self.ui.treeWidget, modul )
		layout.addWidget( self.hierarchy )
		#self.ui.treeWidget.addChild( self.hierarchy )
		self.hierarchy.show()
		self.toolBar = QtGui.QToolBar( self )
		self.toolBar.setIconSize( QtCore.QSize( 32, 32 ) )
		self.ui.boxActions.addWidget( self.toolBar )
		self.modul = modul
		self.page = 0
		self.rootNodes = {}
		config = conf.serverConfig["modules"][ modul ]
		self.currentRootNode = None
		self.isSorting=False
		self.path = []
		self.request = None
		self.overlay = Overlay( self )
		self.setAcceptDrops( True )
		self.ui.webView.hide()
		self.setActions( actions if actions is not None else ["add","edit","clone","preview","delete"] )
		self.connect( self.hierarchy, QtCore.SIGNAL("onItemClicked(PyQt_PyObject)"), self.onItemClicked )
		self.connect( self.hierarchy, QtCore.SIGNAL("onItemDoubleClicked(PyQt_PyObject)"), self.onItemDoubleClicked )

	def setActions( self, actions ):
		"""
			Sets the actions avaiable for this widget (ie. its toolBar contents).
			Setting None removes all existing actions
			@param actions: List of actionnames
			@type actions: List or None
		"""
		print("x1")
		self.toolBar.clear()
		if not actions:
			return
		for action in actions:
			actionWdg = actionDelegateSelector.select( "hierarchy.%s" % self.modul, action )
			if actionWdg is not None:
				actionWdg = actionWdg( self )
				if isinstance( actionWdg, QtGui.QAction ):
					self.toolBar.addAction( actionWdg )
				else:
					self.toolBar.addWidget( actionWdg )

	def onItemClicked( self, item ):
		"""
			A item has been selected. If we have a previewURL -> show it
		"""
		print("x2")
		config = conf.serverConfig["modules"][ self.modul ]
		if "previewURL" in config.keys():
			previewURL = config["previewURL"].replace("{{id}}",item["id"])
			if not previewURL.lower().startswith("http"):
				previewURL = NetworkService.url.replace("/admin","")+previewURL
			self.loadPreview( previewURL )

	def onItemDoubleClicked(self, item ):
		"""
			Open a editor for this entry.
		"""
		print("x3")
		widget = lambda: EditWidget(self.modul, EditWidget.appHierarchy, item["id"] )
		handler = WidgetHandler( widget, descr=QtCore.QCoreApplication.translate("Hierarchy", "Edit entry"), icon=QtGui.QIcon("icons/actions/edit_small.png") )
		event.emit( QtCore.SIGNAL('stackHandler(PyQt_PyObject)'), handler )

	def loadPreview( self, url ):
		print("x4")
		self.request = NetworkService.request( url )
		self.connect(self.request, QtCore.SIGNAL("finished()"), self.setHTML )
	
	def setHTML( self ):
		print("x5")
		try: #This request might got canceled meanwhile..
			html = bytes( self.request.readAll() )
		except:
			return
		self.request.deleteLater()
		self.request= None
		self.ui.webView.setHtml( html.decode("UTF-8"), QtCore.QUrl( NetworkService.url.replace("/admin","") ) )
		self.ui.webView.show()
