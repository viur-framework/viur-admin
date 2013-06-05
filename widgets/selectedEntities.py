# -*- coding: utf-8 -*-
from PySide import QtCore, QtGui
from event import event
from utils import RegisterQueue,  formatString, itemFromUrl
from ui.relationalselectionUI import Ui_relationalSelector
from widgets.list import ListWidget
from network import NetworkService
from config import conf
from priorityqueue import viewDelegateSelector, protocolWrapperInstanceSelector, actionDelegateSelector

class SelectedEntitiesTableModel( QtCore.QAbstractTableModel ):
	"""
		The model holding the currently selected entities.
	"""
	
	def __init__(self, parent, modul, selection, *args, **kwargs):
		"""
			@param parent: Our parent widget.
			@type parent: QWidget.
			@param modul: Name of the modul which items were going to display.
			@type modul: String
			@param selection: Currently selected items.
			@type selection: List-of-Dict, Dict or None
		"""
		super( SelectedEntitiesTableModel, self ).__init__(parent, *args, **kwargs) 
		self.modul = modul
		self.dataCache = []
		self.fields = ["name"]
		self.headers = []
		self.entryFetches = [] #List of fetch-Tasks we issued
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		assert protoWrap is not None
		protoWrap.entityAvailable.connect( self.onItemDataAvaiable )
		for item in (selection or []):
			self.addItem( item )
	
	def addItem( self, item ):
		"""
			Adds an item to the model.
			The only relevant information is item["id"], the rest if freshly fetched from the server.
			@param item: The new item 
			@type item: Dict or String
		"""
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		assert protoWrap is not None
		if not item:
			return
		if isinstance( item, dict ):
			id = item["id"]
			if "_type" in item.keys():
				self.entryFetches.append( protoWrap.queryEntry( id, item["_type"] ) )
			else:
				self.entryFetches.append( protoWrap.queryEntry( id ) )
		elif isinstance( item, str ):
			#FIXME: Pray that this is not the tree module...
			self.entryFetches.append( protoWrap.queryEntry( item ) )
		else:
			raise NotImplementedError()
		#self.entryFetches.append( protoWrap.queryEntry( id ) )
		#NetworkService.request("/%s/view/%s" % (self.modul, id), successHandler= self.onItemDataAvaiable )
	
	def onItemDataAvaiable(self, item ):
		"""
			Fetching the updated information from the server finished.
			Start displaying that item.
		"""
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		assert protoWrap is not None
		if item is None or not item["id"] in self.entryFetches:
			return
		self.entryFetches.remove( item["id"] )
		self.layoutAboutToBeChanged.emit()
		self.dataCache.append( item )
		self.layoutChanged.emit()
	
	def rowCount(self, parent): 
		if not self.dataCache:
			return( 0 )
		return( len(self.dataCache) )

	def columnCount(self, parent): 
		return( len( self.headers ) )

	def data(self, index, role): 
		if not index.isValid(): 
			return None
		elif role != QtCore.Qt.DisplayRole: 
			return None
		if( index.row() >= 0 and index.row()<len(self.dataCache)  ):
			return( self.dataCache[index.row()][ self.fields[index.column()] ] )

	def headerData(self, col, orientation, role):
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			return self.headers[col]
		return None

	def removeItemAtIndex(self, index):
		if not index.isValid() or index.row()>=len( self.dataCache ):
			return
		self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
		self.dataCache.pop( index.row() )
		self.emit(QtCore.SIGNAL("layoutChanged()"))
	
	def getData(self):
		return self.dataCache
	
	def clear(self):
		self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
		self.dataCache = []
		self.emit(QtCore.SIGNAL("layoutChanged()"))

class SelectedEntitiesWidget( QtGui.QTableView ):
	"""
		Displayes the currently selected entities of one relationalBone.
	"""
	skelType = None
	
	def __init__(self, modul, selection=None, skelType=None, *args, **kwargs ):
		"""
			@param parent: Parent-Widget
			@type parent: QWidget
			@param modul: Modul which entities we'll display. (usually "file" in this context)
			@type modul: String
			@param selection: Currently selected Items.
			@type selection: List-of-Dict, Dict or None
		"""
		assert skelType in [None,"node","leaf"]
		super( SelectedEntitiesWidget, self ).__init__( *args, **kwargs )
		self.selection = selection or []
		if selection and not isinstance( self.selection, list ): #This was a singleSelection before
			self.selection = [ self.selection ]
		self.setModel( SelectedEntitiesTableModel( self, modul, self.selection ) )
		self.setAcceptDrops( True )
		self.doubleClicked.connect( self.onItemDoubleClicked )
		self.rebuildDelegates()
		
		#self.connect( self, QtCore.SIGNAL("itemDoubleClicked (QListWidgetItem *)"), self.itemDoubleClicked )
		#self.connect( self.model(), QtCore.SIGNAL("rebuildDelegates(PyQt_PyObject)"), self.rebuildDelegates )
	

	def rebuildDelegates( self ):
		"""
			(Re)Attach the viewdelegates to the table.
			@param data: Skeleton-structure send from the server
			@type data: dict
		"""
		protoWrap = protocolWrapperInstanceSelector.select( self.model().modul )
		assert protoWrap is not None
		self.delegates = [] # Qt Dosnt take ownership of viewdelegates -> garbarge collected
		if self.skelType is None:
			structureCache = protoWrap.viewStructure
		elif self.skelType=="node":
			structureCache = protoWrap.viewNodeStructure
		elif self.skelType=="leaf":
			structureCache = protoWrap.viewLeafStructure
		self.model().headers = []
		colum = 0
		fields = [ x for x in self.model().fields if x in structureCache.keys()]
		for field in fields:
			self.model().headers.append( structureCache[field]["descr"] )
			#Locate the best ViewDeleate for this colum
			delegateFactory = viewDelegateSelector.select( self.model().modul, field, structureCache )
			delegate = delegateFactory( self.model().modul, field, structureCache )
			self.setItemDelegateForColumn( colum, delegate )
			self.delegates.append( delegate )
			self.connect( delegate, QtCore.SIGNAL('repaintRequest()'), self.repaint )
			colum += 1

	def onItemDoubleClicked(self, index):
		"""
			One of our Items has been double-clicked.
			Remove it from the selection
		"""
		self.model().removeItemAtIndex( index )

	def dropEvent(self, event):
		"""
			We got a Drop! Add them to the selection if possible.
			All relevant informations are read from the URLs attached to this drop.
		"""
		mime = event.mimeData()
		if not mime.hasUrls():
			return
		for url in mime.urls():
			res = itemFromUrl( url )
			if not res:
				continue
			modul, id, name = res
			if modul!=self.model().modul:
				continue
			self.extend( [ {"id": id, "name": name} ] )

	def set(self, selection):
		"""
			Set our current selection to "selection".
			@param selection: The new selection
			@type selection: List-of-Dict, Dict or None
		"""
		self.model().clear()
		for s in selection:
			self.model().addItem( s )
	
	def extend(self, selection):
		"""
			Append the given items to our selection.
			@param selection: New items
			@type selection: List
		"""
		for s in selection:
			self.model().addItem( s )
	
	def get(self):
		"""
			Returns the currently selected items.
			@returns: List or None
		"""
		return( self.model().getData() )

	def dragMoveEvent(self, event):
		event.accept()

	def dragEnterEvent(self, event):
		mime = event.mimeData()
		if not mime.hasUrls():
			event.ignore()
		if not any( [ itemFromUrl( x ) for x in mime.urls() ] ):
			event.ignore()
		event.accept()
	
	def keyPressEvent( self, e ):
		"""
			Catch and handle QKeySequence.Delete.
		"""
		if e.matches( QtGui.QKeySequence.Delete ):
			for index in self.selectionModel().selection().indexes():
				self.model().removeItemAtIndex( index )
		else:
			super( SelectedEntitiesWidget, self ).keyPressEvent( e )
