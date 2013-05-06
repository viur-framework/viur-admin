# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from utils import Overlay, RegisterQueue, formatString
from network import NetworkService, RequestGroup
from event import event
from priorityqueue import viewDelegateSelector, protocolWrapperInstanceSelector, actionDelegateSelector
from widgets.edit import EditWidget
from mainwindow import WidgetHandler
from ui.listUI import Ui_List
from config import conf

class ListTableModel( QtCore.QAbstractTableModel ):
	"""Model for displaying data within a listView"""
	GarbargeTypeName = "ListTableModel"
	_chunkSize = 25
	def __init__(self, modul, fields=None, filter=None, parent=None, *args): 
		QtCore.QAbstractTableModel.__init__(self, parent, *args) 
		self.modul = modul
		self.fields = fields or ["name"]
		self._validFields = [] #Due to miss-use, someone might request displaying fields which dont exists. These are the fields that are valid
		self.filter = filter or {}
		self.skippedkeys=[]
		self.dataCache = []
		self.headers = []
		self.completeList = False #Have we all items?
		self.isLoading = 0
		self.cursor = None
		self.loadingKey = None #As loading is performed in background, they might return results for a dataset which isnt displayed anymore
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		assert protoWrap is not None
		self.connect( protoWrap, QtCore.SIGNAL("entitiesChanged()"), self.reload )
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
				return( self.dataCache[index.row()][ self._validFields[index.column()] ] )
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
		filter = self.filter.copy() or {}
		if not "orderby" in filter.keys():
			filter["orderby"] = "creationdate"
		if self.cursor:
			filter["cursor"] = self.cursor
		elif self.dataCache:
			invertedOrderDir = False
			if "orderdir" in filter.keys() and str(filter["orderdir"]) == "1":
				invertedOrderDir = True
			if filter["orderby"] in self.dataCache[-1].keys():
				if invertedOrderDir:
					filter[ filter["orderby"]+"$lt" ] = self.dataCache[-1][filter["orderby"]]
				else:
					filter[ filter["orderby"]+"$gt" ] = self.dataCache[-1][filter["orderby"]]
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		assert protoWrap is not None
		filter["amount"] = self._chunkSize 
		self.loadingKey = protoWrap.queryData( self.addData, **filter )

	def addData( self, queryKey, data, cursor ):
		self.isLoading -= 1
		if queryKey is not None and queryKey!= self.loadingKey: #The Data is for a list we dont display anymore
			return
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		assert protoWrap is not None
		self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
		self.emit( QtCore.SIGNAL("rebuildDelegates(PyQt_PyObject)"), protoWrap.structure )
		#Rebuild our local cache of valid fields
		bones = {}
		for key, bone in protoWrap.structure.items():
			bones[ key ] = bone
		self._validFields = [ x for x in self.fields if x in bones.keys() ]
		for item in data: #Insert the new Data at the coresponding Position
			self.dataCache.append( item )
		if len(data) < self._chunkSize:
			self.completeList = True
		self.cursor = cursor
		self.emit(QtCore.SIGNAL("layoutChanged()"))
		self.emit(QtCore.SIGNAL("dataRecived()"))

	
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

class ListTableView( QtGui.QTableView ):
	"""
		Provides an interface for Data structured as a simple list.
		
		@emits hierarchyChanged( PyQt_PyObject=emitter, PyQt_PyObject=modul, PyQt_PyObject=rootNode, PyQt_PyObject=itemID )
		@emits onItemClicked(PyQt_PyObject=item.data)
		@emits onItemDoubleClicked(PyQt_PyObject=item.data)
		@emits onItemActivated(PyQt_PyObject=item.data)
		
	"""
	GarbargeTypeName = "ListTableView"

	def __init__(self, parent, modul, fields=None, filter=None, *args, **kwargs ):
		super( ListTableView, self ).__init__( parent,  *args, **kwargs )
		self.modul = modul
		filter = filter or {}
		self.structureCache = None
		model = ListTableModel( self.modul, fields or ["name"], filter  )
		self.setModel( model )
		self.overlay = Overlay( self )
		header = self.horizontalHeader()
		header.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		header.customContextMenuRequested.connect(self.tableHeaderContextMenuEvent)
		self.verticalHeader().hide()
		self.connect( event, QtCore.SIGNAL("listChanged(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self.onListChanged )
		self.connect( model, QtCore.SIGNAL("rebuildDelegates(PyQt_PyObject)"), self.rebuildDelegates )
		self.connect( model, QtCore.SIGNAL("layoutChanged()"), self.realignHeaders )
		self.connect( self, QtCore.SIGNAL("clicked (const QModelIndex&)"), self.onItemClicked )
		self.connect( self, QtCore.SIGNAL("doubleClicked (const QModelIndex&)"), self.onItemDoubleClicked )
		self.connect( model, QtCore.SIGNAL("dataRecived()"), self.onDataRecived )
		self.overlay.inform( self.overlay.BUSY )

	def onDataRecived(self):
		"""
			The model just recived data from the server,
			clear our overlay
		"""
		self.overlay.clear()

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

	def rebuildDelegates( self, bones ):
		"""
			(Re)Attach the viewdelegates to the table.
			@param data: Skeleton-structure send from the server
			@type data: dict
		"""
		self.delegates = [] # Qt Dosnt take ownership of viewdelegates -> garbarge collected
		self.structureCache = bones
		self.model().headers = []
		colum = 0
		fields = [ x for x in self.model().fields if x in bones.keys()]
		for field in fields:
			self.model().headers.append( bones[field]["descr"] )
			#Locate the best ViewDeleate for this colum
			delegateFactory = viewDelegateSelector.select( self.modul, field, self.structureCache )
			delegate = delegateFactory( self.modul, field, self.structureCache )
			self.setItemDelegateForColumn( colum, delegate )
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
			super( ListTableView, self ).keyPressEvent( e )

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

	def delete(self, ids, ask=False ):
		if ask:
			if QtGui.QMessageBox.question(	self,
							QtCore.QCoreApplication.translate("ListTableView", "Confirm delete"),
							QtCore.QCoreApplication.translate("ListTableView", "Delete %s entries?") % len( ids ),
							QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
							QtGui.QMessageBox.No) == QtGui.QMessageBox.No:
				return
		self.overlay.inform( self.overlay.BUSY )
		reqGroup = RequestGroup( finishedHandler=self.onQuerySuccess )
		for id in ids:
			reqGroup.addQuery( NetworkService.request("/%s/delete/%s" % ( self.modul, id ), secure=True ) )
		reqGroup.queryType = "delete"
		self.connect( reqGroup, QtCore.SIGNAL("progessUpdate(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self.onProgessUpdate )
	
	def onProgessUpdate(self, request, done, maximum ):
		if request.queryType == "delete":
			descr =  QtCore.QCoreApplication.translate("ListTableView", "Deleting: %s of %s removed.")
		else:
			raise NotImplementedError()
		self.overlay.inform( self.overlay.BUSY, descr % (done, maximum) )

	def onQuerySuccess(self, query ):
		self.model().reload()
		event.emit( QtCore.SIGNAL("listChanged(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self, self.modul, None )
		self.overlay.inform( self.overlay.SUCCESS )


	
class ListWidget( QtGui.QWidget ):
	def __init__(self, modul, fields=None, filter=None, actions=None, *args, **kwargs ):
		super( ListWidget, self ).__init__( *args, **kwargs )
		self.modul = modul
		self.ui = Ui_List()
		self.ui.setupUi( self )
		layout = QtGui.QHBoxLayout( self.ui.tableWidget )
		self.ui.tableWidget.setLayout( layout )
		self.list = ListTableView( self.ui.tableWidget, modul, fields, filter )
		layout.addWidget( self.list )
		self.list.show()
		self.toolBar = QtGui.QToolBar( self )
		self.toolBar.setIconSize( QtCore.QSize( 32, 32 ) )
		self.ui.boxActions.addWidget( self.toolBar )
		if filter is not None and "search" in filter.keys():
			self.ui.editSearch.setText( filter["search"] )
		self.setActions( actions if actions is not None else ["add","edit","clone","preview","delete"] )
		self.connect( self.list, QtCore.SIGNAL("onItemActivated(PyQt_PyObject)"), self.openEditor )

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
			actionWdg = actionDelegateSelector.select( "list.%s" % self.modul, action )
			if actionWdg is not None:
				actionWdg = actionWdg( self )
				if isinstance( actionWdg, QtGui.QAction ):
					self.toolBar.addAction( actionWdg )
				else:
					self.toolBar.addWidget( actionWdg )

	def on_editSearch_returnPressed(self):
		self.search()

	def on_searchBTN_released(self):
		self.search()
		
	def search(self):
		filter = self.list.model().getFilter()
		searchstr=self.ui.editSearch.text()
		if searchstr=="" and "search" in filter.keys():
			del filter["search"]
		elif searchstr!="":
			filter["search"]=searchstr
		self.list.model().setFilter( filter )
	
	def openEditor( self, item, clone=False ):
		"""
			Open a new Editor-Widget for the given entity.
			@param item: Entity to open the editor for
			@type item: Dict
			@param clone: Clone the given entry?
			@type clone: Bool
		"""
		if clone:
			icon = QtGui.QIcon("icons/actions/clone.png")
			if self.list.modul in conf.serverConfig["modules"].keys() and "name" in conf.serverConfig["modules"][ self.list.modul ].keys() :
				descr=QtCore.QCoreApplication.translate("List", "Clone: %s") % conf.serverConfig["modules"][ self.list.modul ]["name"]
			else:
				descr=QtCore.QCoreApplication.translate("List", "Clone entry")
		else:
			icon = QtGui.QIcon("icons/actions/edit.png")
			if self.list.modul in conf.serverConfig["modules"].keys() and "name" in conf.serverConfig["modules"][ self.list.modul ].keys() :
				descr=QtCore.QCoreApplication.translate("List", "Edit: %s") % conf.serverConfig["modules"][ self.list.modul ]["name"]
			else:
				descr=QtCore.QCoreApplication.translate("List", "Edit entry")
		handler = WidgetHandler( lambda: EditWidget( self.list.modul, EditWidget.appList, item["id"], clone=clone ), descr, icon  )
		event.emit( QtCore.SIGNAL('stackHandler(PyQt_PyObject)'), handler )

