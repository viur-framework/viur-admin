# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from utils import Overlay, RegisterQueue, formatString
from network import NetworkService, RequestGroup
from event import event

class ListTableModel( QtCore.QAbstractTableModel ):
	"""Model for displaying data within a listView"""
	_chunkSize = 25
	def __init__(self, tableView, modul, fields=None, filter=None, parent=None, *args): 
		QtCore.QAbstractTableModel.__init__(self, parent, *args) 
		self.tableView = tableView
		self.modul = modul
		self.fields = fields or ["name"]
		self.filter = filter or {}
		self.skippedkeys=[]
		self.dataCache = []
		self.headers = []
		self.completeList = False #Have we all items?
		self.isLoading = 0
		self.cursor = None
		self.setIndex = 0 #As loading is performed in background, they might return results for a dataset which isnt displayed anymore
		self.reload()

	def setDisplayedFields(self, fields ):
		self.fields = fields
		self.reload()
	
	def setFilterbyName(self, filterName):
		self.name = filterName
		config = None # getListConfig( self.modul, filterName )
		if config:
			if "columns" in config.keys():
				self.fields = config["columns"]
			if "filter" in config.keys():
				self.filter = config["filter"]
	
	def setFilter(self, filter ):
		self.filter = filter
		self.reload()
	
	def getFilter( self ):
		return( self.filter )
		
	def getFields( self ):
		return( self.fields )
	
	def reload( self ):
		self.emit(QtCore.SIGNAL("modelAboutToBeReset()"))
		self.setIndex += 1
		self.dataCache = []
		self.completeList = False
		self.cursor = False
		self.emit(QtCore.SIGNAL("modelReset()"))
		self.loadNext(True)

	def rowCount(self, parent): 
		if self.completeList:
			return( len( self.dataCache ) )
		else:
			return( len( self.dataCache )+1 )

	def columnCount(self, parent): 
		try:
			return len(self.headers) 
		except:
			return( 0 )

	def data(self, index, role): 
		if not index.isValid(): 
			return None
		elif role != QtCore.Qt.DisplayRole: 
			return None
		if index.row() >= 0 and ( index.row() < len(self.dataCache )  ):
			try:
				return( self.dataCache[index.row()][ self.fields[index.column()] ] )
			except:
				return( "" )
		else:
			if not self.completeList:
				self.loadNext(  )
			return( "-Lade-" )

	def headerData(self, col, orientation, role):
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			return self.headers[col]
		return None

	def loadNext(self, forceLoading=False):
		if self.isLoading and not forceLoading:
			return
		self.isLoading += 1
		index = self.setIndex
		filter = self.filter.copy() or {}
		if not "orderby" in filter.keys():
			filter["orderby"] = "creationdate"
		if self.cursor:
			filter["cursor"] = self.cursor
		elif self.dataCache:
			if filter["orderby"] in self.dataCache[-1].keys():
				filter[ filter["orderby"]+"$gt" ] = self.dataCache[-1][filter["orderby"]]
		req = NetworkService.request("/%s/list?amount=%s" % (self.modul, self._chunkSize), filter, successHandler=self.addData)
		req.requestIndex = index

	def addData( self, query ):
		data = NetworkService.decode( query )
		self.isLoading -= 1
		if query.requestIndex!=self.setIndex: #The Data is for a list we dont display anymore
			return
		self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
		if( data["structure"] ): #Reset Headers
			self.emit( QtCore.SIGNAL("rebuildDelegates(PyQt_PyObject)"), data["structure"] )
		for item in data["skellist"]: #Insert the new Data at the coresponding Position
			self.dataCache.append( item )
		if len(data["skellist"]) < self._chunkSize:
			self.completeList = True
		if "cursor" in data.keys():
			self.cursor = data["cursor"]
		self.emit(QtCore.SIGNAL("layoutChanged()"))

	
	def repaint(self): #Currently an ugly hack to redraw the table
		self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
		self.emit(QtCore.SIGNAL("layoutChanged()"))
	
	def getData(self):
		return self.dataCache
		
	def sort(self, colum, order ):
		if self.fields[ colum ]=="id" \
			or ("cantSort" in dir(self.delegates[colum]) \
			and self.delegates[colum].cantSort ):
				return
		filter = self.filter
		filter["orderby"] = self.fields[ colum ]
		if order == QtCore.Qt.DescendingOrder:
			filter["orderdir"] = "1"
		else:
			filter["orderdir"] = "0"
		self.setFilter( filter )

class ListWidget( QtGui.QTableView ):
	"""
		Provides an interface for Data structured as a simple list.
		
		@emits hierarchyChanged( PyQt_PyObject=emitter, PyQt_PyObject=modul, PyQt_PyObject=rootNode, PyQt_PyObject=itemID )
		@emits onItemClicked(PyQt_PyObject=item.data)
		@emits onItemDoubleClicked(PyQt_PyObject=item.data)
		@emits onItemActivated(PyQt_PyObject=item.data)
		
	"""
	
	def __init__(self, parent, modul, fields=None, filter=None, *args, **kwargs ):
		super( ListWidget, self ).__init__( parent,  *args, **kwargs )
		self.modul = modul
		filter = filter or {}
		self.structureCache = None
		model = ListTableModel( self, self.modul, fields or ["name"], filter  )
		self.setModel( model )
		self.overlay = Overlay( self )
		header = self.horizontalHeader()
		header.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		header.customContextMenuRequested.connect(self.tableHeaderContextMenuEvent)
		self.verticalHeader().hide()
		self.connect( model, QtCore.SIGNAL("layoutChanged()"), self.on_layoutChanged) #Hook Data-Avaiable event
		self.connect( event, QtCore.SIGNAL("listChanged(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self.onListChanged )
		self.connect( model, QtCore.SIGNAL("rebuildDelegates(PyQt_PyObject)"), self.rebuildDelegates )
		self.connect( model, QtCore.SIGNAL("layoutChanged()"), self.realignHeaders )
		self.connect( self, QtCore.SIGNAL("clicked (const QModelIndex&)"), self.onItemClicked )
		self.connect( self, QtCore.SIGNAL("doubleClicked (const QModelIndex&)"), self.onItemDoubleClicked )

	def onItemClicked(self, index ):
		self.emit( QtCore.SIGNAL("onItemClicked(PyQt_PyObject)"), self.model().getData()[index.row()] )

	def onItemDoubleClicked(self, index ):
		self.emit( QtCore.SIGNAL("onItemDoubleClicked(PyQt_PyObject)"), self.model().getData()[index.row()] )
		self.emit( QtCore.SIGNAL("onItemActivated(PyQt_PyObject)"), self.model().getData()[index.row()] )

	def onListChanged(self, emitter, modul, itemID ):
		"""
			Respond to changed Data - refresh our view
		"""
		if emitter==self: #We issued this event - ignore it as we allready knew
			return
		if modul and modul!=self.modul: #Not our modul
			return
		#Well, seems to affect us, refresh our view
		self.model().reload()

	def realignHeaders(self):
		"""
			Distribute space evenly through all displayed columns.
		"""
		width = self.size().width()
		for x in range( 0, len( self.model().headers ) ):
			self.setColumnWidth(x, int( width/len( self.model().headers ) ) )

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
			event.emit( QtCore.SIGNAL('requestBoneViewDelegate(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), queue, self.modul, field, self.structureCache)
			delegate = queue.getBest()()
			self.setItemDelegateForColumn( colum, delegate  )
			self.delegates.append( delegate )
			self.connect( delegate, QtCore.SIGNAL('repaintRequest()'), self.repaint )
			colum += 1

	def keyPressEvent( self, e ):
		if e.matches( QtGui.QKeySequence.Delete ):
			rows = []
			for index in self.selectedIndexes():
				row = index.row()
				if not row in rows:
					rows.append( row )
			idList = []
			for row in rows:
				data = self.model().getData()[ row ]
				idList.append( data["id"] )
			self.delete( idList, ask=True )
		elif e.key() == QtCore.Qt.Key_Return:
			for index in self.selectedIndexes():
				self.emit( QtCore.SIGNAL("onItemActivated(PyQt_PyObject)"), self.model().getData()[index.row()] )
		else:
			super( ListWidget, self ).keyPressEvent( e )

	def tableHeaderContextMenuEvent(self, point ):
		class FieldAction( QtGui.QAction ):
			def __init__(self, key, name, *args, **kwargs ):
				super( FieldAction, self ).__init__( *args, **kwargs )
				self.key = key
				self.name = name
				self.setText( self.name )
		menu = QtGui.QMenu( self )
		activeFields = self.model().fields
		actions = []
		if not self.structureCache:
			return
		for key in self.structureCache.keys():
			action = FieldAction( key, self.structureCache[ key ]["descr"], self )
			action.setCheckable( True )
			action.setChecked( key in activeFields )
			menu.addAction( action )
			actions.append( action )
		selection = menu.exec_( self.mapToGlobal( point ) )
		if selection:
			self.model().setDisplayedFields( [ x.key for x in actions if x.isChecked() ] )

	def on_layoutChanged( self, *args, **kwargs ):
		self.overlay.clear()
		
	def delete(self, ids, ask=False ):
		if ask:
			if QtGui.QMessageBox.question(	self,
										QtCore.QCoreApplication.translate("ListWidget", "Confirm delete"),
										QtCore.QCoreApplication.translate("ListWidget", "Delete %s entries?") % len( ids ),
										QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
										QtGui.QMessageBox.No) == QtGui.QMessageBox.No:
				return
		self.overlay.inform( self.overlay.BUSY )
		reqGroup = RequestGroup( finishedHandler=self.onQuerySuccess )
		for id in ids:
			reqGroup.addQuery( NetworkService.request("/%s/delete/%s" % ( self.modul, id ), secure=True ) )
	
	def onQuerySuccess(self, query ):
		self.model().reload()
		event.emit( QtCore.SIGNAL("listChanged(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self, self.modul, None )
		self.overlay.inform( self.overlay.SUCCESS )
