# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from utils import Overlay, RegisterQueue, formatString, urlForItem
from network import NetworkService, RequestGroup
from event import event
from priorityqueue import viewDelegateSelector, protocolWrapperInstanceSelector, actionDelegateSelector
from widgets.edit import EditWidget
from mainwindow import WidgetHandler
from ui.listUI import Ui_List
from config import conf
import json

class ListTableModel( QtCore.QAbstractTableModel ):
	"""Model for displaying data within a listView"""
	GarbargeTypeName = "ListTableModel"
	_chunkSize = 25
	
	rebuildDelegates = QtCore.pyqtSignal( (object, ) )
	
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
		protoWrap.entitiesChanged.connect( self.reload )
		protoWrap.queryResultAvaiable.connect( self.addData )
		#self.connect( protoWrap, QtCore.SIGNAL("entitiesChanged()"), self.reload )
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
	
	def getModul( self ):
		return( self.modul )
	
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
		self.loadingKey = protoWrap.queryData( **filter )

	def addData( self, queryKey ):
		self.isLoading -= 1
		if queryKey is not None and queryKey!= self.loadingKey: #The Data is for a list we dont display anymore
			return
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		assert protoWrap is not None
		cacheTime, skellist, cursor = protoWrap.dataCache[ queryKey ]
		self.layoutAboutToBeChanged.emit()
		self.rebuildDelegates.emit( protoWrap.viewStructure )
		#self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
		#self.emit( QtCore.SIGNAL("rebuildDelegates(PyQt_PyObject)"), protoWrap.structure )
		#Rebuild our local cache of valid fields
		bones = {}
		for key, bone in protoWrap.viewStructure.items():
			bones[ key ] = bone
		self._validFields = [ x for x in self.fields if x in bones.keys() ]
		for item in skellist: #Insert the new Data at the coresponding Position
			self.dataCache.append( item )
		if len(skellist) < self._chunkSize:
			self.completeList = True
		self.cursor = cursor
		self.layoutChanged.emit()
		self.loadingKey = None
		#self.emit(QtCore.SIGNAL("layoutChanged()"))
		#self.emit(QtCore.SIGNAL("dataRecived()"))

	
	def repaint(self): #Currently an ugly hack to redraw the table
		self.layoutAboutToBeChanged.emit()
		self.layoutChanged.emit()
		#self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
		#self.emit(QtCore.SIGNAL("layoutChanged()"))
	
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

	def search( self, searchStr ):
		"""
			Start a search for the given string.
			If searchStr is None, it ends any currently active search.
			@param searchStr: Token to search for
			@type searchStr: String or None
		"""
		if searchStr:
			self.filter["search"] = searchStr
			self.reload()
		else:
			if "search" in self.filter.keys():
				del self.filter[ "search" ]
			self.reload()
	
	def flags( self, index ):
		if not index.isValid():
			return( QtCore.Qt.NoItemFlags )
		return( QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEnabled )
		

class ListTableView( QtGui.QTableView ):
	"""
		Provides an interface for Data structured as a simple list.
		
		@emits hierarchyChanged( PyQt_PyObject=emitter, PyQt_PyObject=modul, PyQt_PyObject=rootNode, PyQt_PyObject=itemID )
		@emits onItemClicked(PyQt_PyObject=item.data)
		@emits onItemDoubleClicked(PyQt_PyObject=item.data)
		@emits onItemActivated(PyQt_PyObject=item.data)
		
	"""
	GarbargeTypeName = "ListTableView"
	
	itemClicked = QtCore.pyqtSignal( (object,) )
	itemDoubleClicked = QtCore.pyqtSignal( (object,) )
	itemActivated = QtCore.pyqtSignal( (object,) )

	def __init__(self, parent, modul, fields=None, filter=None, *args, **kwargs ):
		super( ListTableView, self ).__init__( parent,  *args, **kwargs )
		self.modul = modul
		filter = filter or {}
		self.structureCache = None
		model = ListTableModel( self.modul, fields or ["name"], filter  )
		self.setModel( model )
		self.setDragDropMode( self.DragDrop )
		self.setDragEnabled( True )
		self.setAcceptDrops( True ) #Needed to recive dragEnterEvent, not actually wanted
		self.setSelectionBehavior( self.SelectRows )
		header = self.horizontalHeader()
		header.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		header.customContextMenuRequested.connect(self.tableHeaderContextMenuEvent)
		self.verticalHeader().hide()
		#self.connect( event, QtCore.SIGNAL("listChanged(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self.onListChanged )
		model.rebuildDelegates.connect( self.rebuildDelegates )
		model.layoutChanged.connect( self.realignHeaders )
		self.clicked.connect( self.onItemClicked )
		self.doubleClicked.connect( self.onItemDoubleClicked )

	def onItemClicked(self, index ):
		self.itemClicked.emit( self.model().getData()[index.row()] )

	def onItemDoubleClicked(self, index ):
		self.itemDoubleClicked.emit( self.model().getData()[index.row()] )
		#self.emit( QtCore.SIGNAL("onItemDoubleClicked(PyQt_PyObject)"), self.model().getData()[index.row()] )
		#self.emit( QtCore.SIGNAL("onItemActivated(PyQt_PyObject)"), self.model().getData()[index.row()] )

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
			print( delegateFactory )
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
			self.requestDelete( idList )
		elif e.key() == QtCore.Qt.Key_Return:
			for index in self.selectedIndexes():
				self.itemActivated.emit(  self.model().getData()[index.row()] )
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

	def requestDelete(self, ids):
		if QtGui.QMessageBox.question(	self,
						QtCore.QCoreApplication.translate("ListTableView", "Confirm delete"),
						QtCore.QCoreApplication.translate("ListTableView", "Delete %s entries?") % len( ids ),
						QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
						QtGui.QMessageBox.No) == QtGui.QMessageBox.No:
			return
		protoWrap = protocolWrapperInstanceSelector.select( self.model().modul )
		assert protoWrap is not None
		protoWrap.deleteEntities( ids )
	
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

	def dragEnterEvent(self, event ):
		"""
			Allow Drag&Drop to the outside (ie relationalBone)
		"""
		if event.source() == self:
			event.accept()
			tmpList = []
			for itemIndex in self.selectionModel().selection().indexes():
				tmpList.append( self.model().getData()[ itemIndex.row() ] )
			event.mimeData().setData( "viur/listDragData", json.dumps( { "entities": tmpList } ) )
			event.mimeData().setUrls( [ urlForItem( self.model().modul, x) for x in tmpList] )
		return( super( ListTableView, self ).dragEnterEvent( event ) )
	
	def dragMoveEvent( self, event ):
		"""
			We need to have drops enabled to recive dragEnterEvents, so we can add our mimeData;
			but we won't ever recive an actual drop.
		"""
		event.ignore()

	def getFilter( self ):
		return( self.model().getFilter() )
	
	def setFilter( self, filter ):
		self.model().setFilter( filter )
	
	def getModul( self ):
		return( self.model().getModul() )
	
	def getSelection( self ):
		"""
			Returns a list of items currently selected.
		"""
		return( [self.model().getData()[ x ] for x in set( [x.row() for x in self.selectionModel().selection().indexes()] ) ] )

	
class ListWidget( QtGui.QWidget ):
	
	itemClicked = QtCore.pyqtSignal( (object,) )
	itemDoubleClicked = QtCore.pyqtSignal( (object,) )
	itemActivated = QtCore.pyqtSignal( (object,) )
	
	def __init__(self, modul, fields=None, filter=None, actions=None, editOnDoubleClick=True, *args, **kwargs ):
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
		if editOnDoubleClick:
			self.list.itemDoubleClicked.connect( self.openEditor )
		self.list.itemClicked.connect( self.itemClicked )
		self.list.itemDoubleClicked.connect( self.itemDoubleClicked )
		self.list.itemActivated.connect( self.itemActivated )
		self.overlay = Overlay( self )
		protoWrap = protocolWrapperInstanceSelector.select( self.modul )
		assert protoWrap is not None
		protoWrap.busyStateChanged.connect( self.onBusyStateChanged )
		self.ui.searchBTN.released.connect( self.search )
		self.ui.editSearch.returnPressed.connect( self.search )
		#self.overlay.inform( self.overlay.BUSY )
		
	def onBusyStateChanged( self, busy ):
		if busy:
			self.overlay.inform( self.overlay.BUSY )
		else:
			self.overlay.clear()

	def setActions( self, actions ):
		"""
			Sets the actions avaiable for this widget (ie. its toolBar contents).
			Setting None removes all existing actions
			@param actions: List of actionnames
			@type actions: List or None
		"""
		self.toolBar.clear()
		for a in self.actions():
			self.removeAction( a )
		if not actions:
			return
		for action in actions:
			if action=="|":
				self.toolBar.addSeparator()
			else:
				actionWdg = actionDelegateSelector.select( "list.%s" % self.modul, action )
				if actionWdg is not None:
					actionWdg = actionWdg( self )
					if isinstance( actionWdg, QtGui.QAction ):
						self.toolBar.addAction( actionWdg )
						self.addAction( actionWdg )
					else:
						self.toolBar.addWidget( actionWdg )
	
	def getActions( self ):
		"""
			Returns a list of the currently activated actions on this list.
		"""
		return( self.actions() )

	def search( self, *args, **kwargs ):
		"""
			Start a search for the given string.
			If searchStr is None, it ends any currently active search.
			@param searchStr: Token to search for
			@type searchStr: String or None
		"""
		self.list.model().search( self.ui.editSearch.text() )
	
	def getFilter( self ):
		return( self.list.getFilter() )
	
	def setFilter( self, filter ):
		self.list.setFilter( filter )
		
	def getModul( self ):
		return( self.list.getModul() )
	
	def openEditor( self, item, clone=False ):
		"""
			Open a new Editor-Widget for the given entity.
			@param item: Entity to open the editor for
			@type item: Dict
			@param clone: Clone the given entry?
			@type clone: Bool
		"""
		myHandler = WidgetHandler.mainWindow.handlerForWidget( self ) #Always stack them as my child
		assert myHandler is not None
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
		modul = self.list.modul
		key = item["id"]
		handler = WidgetHandler( lambda: EditWidget( modul, EditWidget.appList, key, clone=clone ), descr, icon )
		handler.mainWindow.addHandler( handler, myHandler )

	def requestDelete( self, ids ):
		return( self.list.requestDelete( ids ) )
		
	def getSelection( self ):
		return( self.list.getSelection() )
