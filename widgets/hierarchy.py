# -*- coding: utf-8 -*-
from PySide import QtCore, QtGui
from utils import Overlay
from network import NetworkService
from event import event
import utils
from widgets.edit import EditWidget


class HierarchyItem(QtGui.QTreeWidgetItem):
	"""
		Displayes one entry in a QTreeWidget.
		Its comparison-methods have been overriden to reflect the sort-order on the server.
	"""	
	def __init__( self, data ):
		if "name" in data.keys():
			name = data["name"]
		else:
			name = "---"
		super( HierarchyItem, self ).__init__( [str( name )] )
		self.loaded = False
		self.data = data
		self.setChildIndicatorPolicy( QtGui.QTreeWidgetItem.ShowIndicator )

	def __gt__( self, other ):
		if isinstance( other, HierarchyItem ) and "sortindex" in self.data.keys() and "sortindex" in other.data.keys():
			return( self.data["sortindex"] > other.data["sortindex"] )
		else:
			return( super( HierarchyItem, self ).__gt__( other ) )

	def __lt__( self, other ):
		if isinstance( other, HierarchyItem ) and "sortindex" in self.data.keys() and "sortindex" in other.data.keys():
			return( self.data["sortindex"] < other.data["sortindex"] )
		else:
			return( super( HierarchyItem, self ).__lt__( other ) )
			

class HierarchyWidget( QtGui.QTreeWidget ):
	"""
		Provides an interface for Data structured as a hierarchy on the server.
		
		@emits hierarchyChanged( PyQt_PyObject=emitter, PyQt_PyObject=modul, PyQt_PyObject=rootNode, PyQt_PyObject=itemID )
		@emits onItemClicked(PyQt_PyObject=item.data)
		@emits onItemDoubleClicked(PyQt_PyObject=item.data)
		
	"""
	
	def __init__(self, parent, modul, rootNode=None, *args, **kwargs ):
		"""
			@param parent: Parent widget.
			@type parent: QWidget
			@param modul: Name of the modul to show the elements for
			@type modul: String
			@param rootNode: Key of the rootNode which data should be displayed. If None, this widget tries to choose one.
			@type rootNode: String or None
		"""
		super( HierarchyWidget, self ).__init__( parent, *args, **kwargs )
		self.modul = modul
		self.currentRootNode = rootNode
		self.overlay = Overlay( self )
		self.expandList = []
		self.setHeaderHidden( True )
		self.setAcceptDrops( True )
		self.setDragDropMode( self.InternalMove )
		if not self.currentRootNode:
			self.loadRootNodes()
		self.connect( self, QtCore.SIGNAL("itemExpanded(QTreeWidgetItem *)"), self.onItemExpanded )
		self.connect( event, QtCore.SIGNAL("hierarchyChanged(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self.onHierarchyChanged )
		self.connect( self,  QtCore.SIGNAL("itemClicked(QTreeWidgetItem *,int)"), self.onItemClicked )
		self.connect( self, QtCore.SIGNAL("itemDoubleClicked (QTreeWidgetItem *,int)"), self.onItemDoubleClicked )


	def onItemClicked( self, item ):
		"""
			A item has been selected. Emit onItemClicked.
		"""
		self.emit( QtCore.SIGNAL("onItemClicked(PyQt_PyObject)"), item.data )

	def onItemDoubleClicked(self, item ):
		"""
			A item has been doubleClicked. Emit onItemDoubleClicked.
		"""
		self.emit( QtCore.SIGNAL("onItemDoubleClicked(PyQt_PyObject)"), item.data )
		
	def onHierarchyChanged(self, emitter, modul, rootNode, itemID ):
		"""
			Respond to changed Data - refresh our view
		"""
		if emitter==self: #We issued this event - ignore it as we allready knew
			return
		if modul and modul!=self.modul: #Not our modul
			return
		if rootNode and rootNode!=self.currentRootNode: #Not in our Hierarchy
			return
		#Well, seems to affect us, refresh our view
		#First, save all expanded items
		self.expandList = []
		it = QtGui.QTreeWidgetItemIterator( self )
		while( it.value() ):
			if it.value().isExpanded():
				self.expandList.append( it.value().data["id"] )
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
		self.currentRootNode = rootNode
		self.clear()
		self.loadData()

	def onItemExpanded(self, item, *args, **kwargs):
		"""
			An item has just been expanded.
			Check, if we allready have information about the elements beneath, otherwhise load them.
		"""
		if not item.loaded:
			while( item.takeChild(0) ):
				pass
			self.loadData( item.data["id"] )

	def loadRootNodes(self):
		self.overlay.inform( self.overlay.BUSY )
		NetworkService.request("/%s/listRootNodes" % ( self.modul ), successHandler=self.onLoadRepositories )
		#self.connect(self.request, QtCore.SIGNAL("finished()"), self.onLoadRepositories )
	
	def onLoadRepositories(self, request ):
		data = NetworkService.decode( request )
		self.rootNodes = data
		if not self.currentRootNode:
			try:
				self.currentRootNode = list( self.rootNodes )[0]["key"]
			except:
				return
			self.loadData()
	
	def onLoadError(self, request, error ):
		self.overlay.inform( self.overlay.ERROR, str(error) )
	
	def onRequestSucceeded(self, request):
		"""
			We modified something on the server, and that request succeded
		"""
		event.emit( QtCore.SIGNAL('hierarchyChanged(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self, self.modul, self.currentRootNode, None )
		self.loadData()
		
	def loadData(self, parent=None):
		self.overlay.inform( self.overlay.BUSY )
		NetworkService.request( "/%s/list/%s" % (self.modul, (parent or self.currentRootNode) ), successHandler=self.setData, failureHandler=self.onLoadError )

	def setData(self, request):
		data = NetworkService.decode( request )
		if len( data["skellist"] ):
			if data["skellist"][0]["parententry"] == self.currentRootNode:
				self.clear()
		for itemData in data["skellist"]:
			tvItem = HierarchyItem( itemData )
			if( itemData["parententry"] == self.currentRootNode ):
				self.addTopLevelItem( tvItem )
			else:
				self.insertItem( tvItem )
			self.addTopLevelItem( tvItem )
			if tvItem.data["id"] in self.expandList:
				tvItem.setExpanded(True)
		self.sortItems(0, QtCore.Qt.AscendingOrder)
		self.setSortingEnabled( False )
		self.overlay.clear()

	def insertItem( self, newItem, fromChildren=None ):
		"""
			New data got avaiable - insert it into the corresponding locations.
		"""
		if not fromChildren:
			idx = 0
			item = self.topLevelItem( idx )
			while item:
				if item.data["id"] == newItem.data["parententry"]:
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
				if child.data["id"] == newItem.data["parententry"]:
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
		if event.source() == self:
			mimeData = event.mimeData()
			urls = []
			for item in self.selectedItems():
				urls.append( utils.urlForItem( self.modul, item.data) )
			mimeData.setUrls( urls )
		super( HierarchyWidget, self ).dragEnterEvent( event )

	def dropEvent( self, event ):
		"""
			An Item has been moved inside our HierarchyWidget,
			Move it to the correct location on the server.
		"""
		try:
			dragedItem =  self.selectedItems()[0]
		except:
			return
		targetItem = self.itemAt( event.pos() )
		QtGui.QTreeWidget.dropEvent( self, event )
		if not targetItem: #Moved to the end of the list
			self.reparent( dragedItem.data["id"], self.currentRootNode )
			if self.topLevelItemCount()>1:
				self.updateSortIndex( dragedItem.data["id"], self.topLevelItem( self.topLevelItemCount()-2 ).data["sortindex"]+1 )
		else:
			if dragedItem.parent() == targetItem: #Moved to subitem
				self.reparent( dragedItem.data["id"], targetItem.data["id"] )
			else: # Moved within its parent list
				while( targetItem ):
					childIndex = 0
					while( childIndex < targetItem.childCount() ):
						currChild = targetItem.child( childIndex )
						if currChild == dragedItem:
							self.reparent( dragedItem.data["id"], targetItem.data["id"] )
							if childIndex==0 and targetItem.childCount()>1: # is now 1st item
								self.updateSortIndex( dragedItem.data["id"], targetItem.child( 1 ).data["sortindex"]-1 )
							elif childIndex==(targetItem.childCount()-1) and childIndex>0: #is now lastitem
								self.updateSortIndex( dragedItem.data["id"], targetItem.child( childIndex-1 ).data["sortindex"]+1 )
							elif childIndex>0 and childIndex<(targetItem.childCount()-1): #in between
								newSortIndex = ( targetItem.child( childIndex-1 ).data["sortindex"]+ targetItem.child( childIndex+1 ).data["sortindex"] ) / 2.0
								self.updateSortIndex( dragedItem.data["id"], newSortIndex )
							else: # We are the only one in this layer
								pass
							return
						childIndex += 1
					targetItem = targetItem.parent()
				childIndex = 0
				currChild = self.topLevelItem( childIndex )
				while( currChild ):
					if currChild == dragedItem:
						self.reparent( dragedItem.data["id"], self.currentRootNode )
						if childIndex==0 and self.topLevelItemCount()>1: # is now 1st item
							self.updateSortIndex( dragedItem.data["id"], self.topLevelItem( 1 ).data["sortindex"]-1 )
						elif childIndex==(self.topLevelItemCount()-1) and childIndex>0: #is now lastitem
							self.updateSortIndex( dragedItem.data["id"], self.topLevelItem( childIndex-1 ).data["sortindex"]+1 )
						elif childIndex>0 and childIndex<(self.topLevelItemCount()-1): #in between
							newSortIndex = ( self.topLevelItem( childIndex-1 ).data["sortindex"]+ self.topLevelItem( childIndex+1 ).data["sortindex"] ) / 2.0
							self.updateSortIndex( dragedItem.data["id"], newSortIndex )
						else: # We are the only one in this layer
							pass
						return
					childIndex+=1
					currChild = self.topLevelItem( childIndex )

	def reparent(self, itemKey, destParent):
		NetworkService.request( "/%s/reparent" % self.modul, { "item": itemKey, "dest": destParent }, True, successHandler=self.onRequestSucceeded, failureHandler=self.onLoadError )

	def updateSortIndex(self, itemKey, newIndex):
		self.request = NetworkService.request( "/%s/setIndex" % self.modul, { "item": itemKey, "index": newIndex }, True, successHandler=self.onRequestSucceeded, failureHandler=self.onLoadError )


	def delete( self, id ):
		"""
			Delete the entity with the given id
		"""
		NetworkService.request("/%s/delete/%s" % (self.modul, id), secure=True, successHandler=self.onRequestSucceeded )
