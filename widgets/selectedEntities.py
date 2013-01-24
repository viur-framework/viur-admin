# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from event import event
from utils import RegisterQueue,  formatString, itemFromUrl
from handler.list import ListTableModel
from ui.relationalselectionUI import Ui_relationalSelector
from widgets.list import ListWidget, ListTableModel
from network import NetworkService
from config import conf

class SelectedEntitiesTableModel( QtCore.QAbstractTableModel ):
	def __init__(self, parent, modul, selection, *args, **kwargs):
		QtCore.QAbstractTableModel.__init__(self, parent, *args) 
		self.modul = modul
		self.dataCache = []
		self.fields = ["name"]
		self.headers = []
		for item in selection:
			self.addItem( item )
	
	def addItem( self, item ):
		if not item:
			return
		if isinstance( item, dict ):
			id = item["id"]
		elif isinstance( item, basestring ):
			id = item
		else:
			raise NotImplementedError()
		NetworkService.request("/%s/view/%s" % (self.modul, id), successHandler= self.onItemDataAvaiable )
	
	def onItemDataAvaiable(self, query ):
		data = NetworkService.decode( query )
		item = data["values"]
		self.emit( QtCore.SIGNAL("rebuildDelegates(PyQt_PyObject)"), data["structure"] )
		self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
		self.dataCache.append( item )
		self.emit(QtCore.SIGNAL("layoutChanged()"))
	
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
			return str( self.dataCache[index.row()][ self.fields[index.column()] ] )

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
	def __init__(self, parent, modul, selection=None, *args, **kwargs ):
		super( SelectedEntitiesWidget, self ).__init__( *args, **kwargs )
		self.selection = selection or []
		if isinstance( self.selection, dict ): #This was a singleSelection before
			self.selection = [ self.selection ]
		self.setModel( SelectedEntitiesTableModel( self, modul, selection ) )
		self.setAcceptDrops( True )
		self.connect( self, QtCore.SIGNAL("itemDoubleClicked (QListWidgetItem *)"), self.itemDoubleClicked )
		self.connect( self.model(), QtCore.SIGNAL("rebuildDelegates(PyQt_PyObject)"), self.rebuildDelegates )
	
	def rebuildDelegates( self, data ):
		"""
			(Re)Attach the viewdelegates to the table.
			@param data: Skeleton-structure send from the server
			@type data: dict
		"""
		self.delegates = [] # Qt Dosnt take ownership of viewdelegates -> garbarge collected
		bones = {}
		for key, bone in data:
			bones[ key ] = bone
		self.structureCache = bones
		self.model().headers = []
		colum = 0
		fields = [ x for x in self.model().fields if x in bones.keys()]
		for field in fields:
			self.model().headers.append( bones[field]["descr"] )
			#Locate the best ViewDeleate for this colum
			queue = RegisterQueue()
			event.emit( QtCore.SIGNAL('requestBoneViewDelegate(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), queue, self.model().modul, field, self.structureCache)
			delegate = queue.getBest()()
			self.setItemDelegateForColumn( colum, delegate  )
			self.delegates.append( delegate )
			self.connect( delegate, QtCore.SIGNAL('repaintRequest()'), self.repaint )
			colum += 1	
	
	def itemDoubleClicked(self, item):
		self.model().removeItemAtIndex( self.indexFromItem( item ) )

	def dropEvent(self, event):
		mime = event.mimeData()
		print( mime.urls() )
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
		self.model().clear()
		for s in selection:
			self.model().addItem( s )
	
	def extend(self, selection):
		for s in selection:
			self.model().addItem( s )
	
	def get(self):
		return( self.model().getData() )

	def dragMoveEvent(self, event):
		print( "enter:", event )
		event.accept()

	def dragEnterEvent(self, event):
		print( "enter:", event )
		mime = event.mimeData()
		if not mime.hasUrls():
			event.ignore()
		if not any( [ itemFromUrl( x ) for x in mime.urls() ] ):
			event.ignore()
		event.accept()
	
	def keyPressEvent( self, e ):
		if e.matches( QtGui.QKeySequence.Delete ):
			for index in self.selectionModel().selection().indexes():
				self.model().removeItemAtIndex( index )
		else:
			super( SelectedEntitiesWidget, self ).keyPressEvent( e )
