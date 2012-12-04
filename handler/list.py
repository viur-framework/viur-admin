from PyQt4 import QtCore, QtGui
from network import NetworkService
from event import event
from ui.listUI import Ui_List
from handler.edit import Edit, EditHandler
import time
import os, os.path
from ui.selectfieldsUI import Ui_SelectFields
from ui.editpreviewUI import Ui_EditPreview
from utils import RegisterQueue, Overlay, formatString, QueryAggregator
from config import conf

from mainwindow import EntryHandler


class SelectFields( QtGui.QMainWindow ):
	class AttributeItem (QtGui.QListWidgetItem):
		def __init__(self,attrname,infos):
			super(SelectFields.AttributeItem,self).__init__(infos["descr"])
			self.name=attrname
			self.data=infos	
	def __init__(self, model, *args, **kwargs ):
		super( SelectFields, self ).__init__( *args, **kwargs )
		self.ui = Ui_SelectFields()
		self.ui.setupUi( self )
		self.model = model
		self.activefields = model.fields
		self.listai=[]
		if not self.model.structureCache:
			return
		self.updateUI()
		event.emit( QtCore.SIGNAL('stackWidget(PyQt_PyObject)'), self )
		
	def updateUI(self):
		self.ui.listAvaiableFields.clear()
		for key in self.model.structureCache.keys():
			ai=SelectFields.AttributeItem(key, self.model.structureCache[ key ] )
			if key in self.activefields:
				ai.setCheckState(QtCore.Qt.Checked)
			else:
				ai.setCheckState(QtCore.Qt.Unchecked)
			self.ui.listAvaiableFields.addItem( ai )
			self.listai.append(ai)	
	
	def on_btnApply_released(self, *args, **kwargs ):
		event.emit( QtCore.SIGNAL('popWidget(PyQt_PyObject)'), self )
			
	def on_listAvaiableFields_currentRowChanged(self, i):
		self.update()
		
	def on_listAvaiableFields_currentItemChanged (self, item):
		self.update()
		
	def on_listAvaiableFields_itemClicked (self, item):
		self.update()
		
	def update(self):
		self.activefields =[]
		for ai in self.listai:
			if ai.checkState()==QtCore.Qt.Checked:
				self.activefields.append(ai.name)
		self.model.setDisplayedFields( self.activefields )

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
		self.structureCache = {}
		self.headers = []
		self.completeList = False #Have we all items?
		self.request = QueryAggregator()
		self.cursor = None
		self.setIndex = 0 #As loading is performed in background, they might return results for a dataset wich isnt displayed anymore
		self.reload()
	
	def selectColums( self ):
		SelectFields( self )
	
	def setDisplayedFields(self, fields ):
		self.emit(QtCore.SIGNAL("modelAboutToBeReset()"))
		self.fields = fields
		self.headers = []
		for key in self.fields:
			if  key in self.structureCache.keys() and key!="id":
				self.headers.append( self.structureCache[ key ]["descr"] )
			else:
				pass
		self.emit(QtCore.SIGNAL("modelReset()"))
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
		

	def loadNext(self, forceLoading=False):
		if not self.request.isIdle() and not forceLoading:
			return
		index = self.setIndex
		filter = self.filter.copy() or {}
		if not "orderby" in filter.keys():
			filter["orderby"] = "creationdate"
		if self.cursor:
			filter["cursor"] = self.cursor
		elif self.dataCache:
			if filter["orderby"] in self.dataCache[-1].keys():
				filter[ filter["orderby"]+"$gt" ] = self.dataCache[-1][filter["orderby"]]
		req = NetworkService.request("/%s/list?amount=%s" % (self.modul, self._chunkSize), filter)
		self.request.addQuery( req )
		self.connect( req, QtCore.SIGNAL("finished(PyQt_PyObject)"), lambda query: self.addData( query, index ) )
	
	def __del__(self):
		self.request.deleteLater()

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

	def addData( self, query, index ):
		try:
			data = NetworkService.decode( query )
		except ValueError: #Query was canceled
			return
		if index!=self.setIndex: #The Data is for a list we dont display anymore
			return
		self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
		if( data["structure"] ): #Reset Headers
			self.delegates = [] # Qt Dosnt take ownership of viewdelegates -> garbarge collected
			bones = {}
			for key, bone in data["structure"]:
				bones[ key ] = bone
			self.structureCache = bones
			self.headers = []
			colum = 0
			self.fields = [ x for x in self.fields if x in bones.keys()]
			for field in self.fields:
				self.headers.append( bones[field]["descr"] )
				#Locate the best ViewDeleate for this colum
				queue = RegisterQueue()
				event.emit( QtCore.SIGNAL('requestBoneViewDelegate(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), queue, self.modul, field, self.structureCache)
				delegate = queue.getBest()()
				self.tableView.setItemDelegateForColumn( colum, delegate  )
				self.delegates.append( delegate )
				self.connect( delegate, QtCore.SIGNAL('repaintRequest()'), self.repaint )
				colum += 1
		for item in data["skellist"]: #Insert the new Data at the coresponding Position
			self.dataCache.append( item )
		if len(data["skellist"]) < self._chunkSize:
			self.completeList = True
		if "cursor" in data.keys():
			self.cursor = data["cursor"]
		self.emit(QtCore.SIGNAL("layoutChanged()"))
		width = self.tableView.size().width()
		for x in range( 0, len( self.headers ) ):
			self.tableView.setColumnWidth(x, int( width/len( self.headers ) ) )
	
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

class List( QtGui.QWidget ):
	def __init__(self, modul, fields=None, filter=None, *args, **kwargs ):
		self.modul = modul
		self.page = 0
		filter = filter or {}
		if not "ui" in dir( self ):
			QtGui.QWidget.__init__( self, *args, **kwargs )
			self.ui = Ui_List()
			self.ui.setupUi( self )
			self.overlay = Overlay( self )
			self.toolBar = QtGui.QToolBar( self )
			self.toolBar.setIconSize( QtCore.QSize( 32, 32 ) )
			self.ui.tableView.verticalHeader().hide()
		self.model = ListTableModel( self.ui.tableView, self.modul, fields or ["name"], filter  )
		self.ui.tableView.setModel( self.model )
		self.selectionModel = self.ui.tableView.selectionModel()
		self.ui.editSearch.mousePressEvent = self.on_editSearch_clicked
		queue = RegisterQueue()
		event.emit( QtCore.SIGNAL('requestModulListActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), queue, self.modul, "", self )
		for item in queue.getAll():
			i = item( self )
			if isinstance( i, QtGui.QAction ):
				self.toolBar.addAction( i )
			else:
				self.toolBar.addWidget( i )
			#self.ui.boxActions.addWidget( item( self ) )
		self.connect( event, QtCore.SIGNAL('dataChanged(PyQt_PyObject,PyQt_PyObject)'),self.doreloaddata )
		if "search" in filter.keys():
			self.ui.editSearch.setText( filter["search"] )
		self.connect( self.model, QtCore.SIGNAL("layoutChanged()"), self.on_layoutChanged) #Hook Data-Avaiable event
		#self.ui.tableView.horizontalHeader().mousePressEvent = self.tableViewContextMenuEvent
		header = self.ui.tableView.horizontalHeader()
		header.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		header.customContextMenuRequested.connect(self.tableHeaderContextMenuEvent)
		self.ui.boxActions.addWidget( self.toolBar )
		self.overlay.inform( self.overlay.BUSY )

	def tableHeaderContextMenuEvent(self, point ):
		class FieldAction( QtGui.QAction ):
			def __init__(self, key, name, *args, **kwargs ):
				super( FieldAction, self ).__init__( *args, **kwargs )
				self.key = key
				self.name = name
				self.setText( self.name )
		menu = QtGui.QMenu( self )
		activeFields = self.model.fields
		actions = []
		if not self.model.structureCache:
			return
		for key in self.model.structureCache.keys():
			action = FieldAction( key, self.model.structureCache[ key ]["descr"], self )
			action.setCheckable( True )
			action.setChecked( key in activeFields )
			menu.addAction( action )
			actions.append( action )
		selection = menu.exec_( self.ui.tableView.mapToGlobal( point ) )
		if selection:
			self.model.setDisplayedFields( [ x.key for x in actions if x.isChecked() ] )
	

	def deleteLater(self):
		if not self.model.request.isIdle():
			self.model.request.abort()
		super( List, self ).deleteLater()

	def getFilter( self ):
		return( self.model.getFilter() )
		
	def getFields( self ):
		return( self.model.getFields() )

	def on_layoutChanged( self, *args, **kwargs ):
		self.overlay.clear()

	def on_btnConfig_released(self, *args, **kwargs ):
		self.model.selectColums()
	
	def reloadData(self ):
		self.model.reload()
		event.emit( QtCore.SIGNAL('dataChanged(PyQt_PyObject,PyQt_PyObject)'), self.modul, self )
	
	def doreloaddata(self, modulName, emitingEntry ):
		if (modulName!=self.modul or emitingEntry==self):
			return
		self.model.reload()
		
	def reload(self, filterobj):
		self.updateTabDescription()
		self.model.reload()
		
	def on_editSearch_clicked(self, *args, **kwargs):
		if self.ui.editSearch.text()==QtCore.QCoreApplication.translate("ListHandler", "Search") :
			self.ui.editSearch.setText("")

	def on_searchBTN_released(self):
		self.search()
	
	def search(self):
		filter = self.model.getFilter()
		searchstr=self.ui.editSearch.text()
		if searchstr=="" and "search" in filter.keys():
			del filter["search"]
		elif searchstr!="":
			filter["search"]=searchstr
		self.model.setFilter( filter )
	
	def on_tableView_doubleClicked(self, index):
		data = self.model.getData()[ index.row() ]
		if self.modul in conf.serverConfig["modules"].keys() and "name" in conf.serverConfig["modules"][ self.modul ].keys() :
			name = conf.serverConfig["modules"][ self.modul ]["name"]
		else:
			name = self.modul
		descr = QtCore.QCoreApplication.translate("ListHandler", "Edit: %s") % name
		widget = Edit(self.modul, data["id"])
		handler = EditHandler( self.modul, widget )
		event.emit( QtCore.SIGNAL('addHandler(PyQt_PyObject)'), handler )
	
class ListAddAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( ListAddAction, self ).__init__(  QtGui.QIcon("icons/actions/add_small.png"), QtCore.QCoreApplication.translate("ListHandler", "Add entry"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.New )
	
	def onTriggered( self, e ):
		if self.parentWidget().modul in conf.serverConfig["modules"].keys() and "name" in conf.serverConfig["modules"][ self.parentWidget().modul ].keys() :
			name = conf.serverConfig["modules"][ self.parentWidget().modul ]["name"]
		else:
			name = self.parentWidget().modul
		descr = QtCore.QCoreApplication.translate("ListHandler", "Add entry: %s") % name
		widget = Edit(self.parentWidget().modul, 0)
		handler = EditHandler( self.parentWidget().modul, widget )
		event.emit( QtCore.SIGNAL('addHandler(PyQt_PyObject)'), handler )
		#event.emit( QtCore.SIGNAL('addHandlerWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), Edit(self.parentWidget().modul, 0), descr, "icons/onebiticonset/onebit_31.png" )


class ListEditAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( ListEditAction, self ).__init__( QtGui.QIcon("icons/actions/edit_small.png"), QtCore.QCoreApplication.translate("ListHandler", "Edit entry"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( "Return" )
	
	def onTriggered( self, e ):
		if len( self.parentWidget().selectionModel.selection().indexes() )==0:
			return
		data = self.parentWidget().model.getData()[ self.parentWidget().selectionModel.selection().indexes()[0].row() ]
		if self.parentWidget().modul in conf.serverConfig["modules"].keys() and "name" in conf.serverConfig["modules"][ self.parentWidget().modul ].keys() :
			name = conf.serverConfig["modules"][ self.parentWidget().modul ]["name"]
		else:
			name = self.parentWidget().modul
		descr = QtCore.QCoreApplication.translate("ListHandler", "Edit entry: %s") % name
		widget = Edit(self.parentWidget().modul, data["id"])
		handler = EditHandler( self.parentWidget().modul, widget )
		event.emit( QtCore.SIGNAL('addHandler(PyQt_PyObject)'), handler )
		

class DeleteTask( QtCore.QObject ):
	def __init__( self, modul, files ):
		super( DeleteTask, self ).__init__( )
		self.stopNow = False
		self.modul = modul
		self.files = files
		self.iter = files.__iter__()
		self.request = None
		self.total = len(files)
		self.done = 0
		self.processNext()
	
	def processNext(self):
		try:
			assert not self.stopNow
			item = self.iter.__next__()
		except StopIteration:
			self.emit( QtCore.SIGNAL("taskFinished()") )
			self.request.deleteLater()
			return
		except AssertionError:
			self.emit( QtCore.SIGNAL("taskError(PyQt_PyObject)"), QtCore.QCoreApplication.translate("ListHandler", "Aborted") )
			self.request.deleteLater()
			return
		if self.request:
			self.request.deleteLater()
		self.request = NetworkService.request("/%s/delete/%s" % ( self.modul, item["id"] ), secure=True )
		self.connect( self.request, QtCore.SIGNAL("finished()"), self.processNext )
		self.connect( self.request, QtCore.SIGNAL("error(QNetworkReply::NetworkError)"), self.onError )
		self.emit( QtCore.SIGNAL("taskProgress(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self.total, self.done, "-" )
	
	def onError(self, error):
		self.stopNow=True

class ListDeleteAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( ListDeleteAction, self ).__init__(  QtGui.QIcon("icons/actions/delete_small.png"), QtCore.QCoreApplication.translate("ListHandler", "Delete"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.Delete )
		#self.setDisabled(True)
	
	def onTriggered( self, e ):
		indexes = self.parentWidget().selectionModel.selection().indexes()
		rows = []
		for index in indexes:
			row = index.row()
			if not row in rows:
				rows.append( row )
		if len( rows ) == 1:
			entryData = self.parentWidget().model.getData()[ indexes[0].row() ]
			config = conf.serverConfig["modules"][ self.parentWidget().modul ]
			if "formatstring" in config.keys():
				question = QtCore.QCoreApplication.translate("ListHandler", "Delete entry %s and everything beneath?") % formatString( config["formatstring"],  entryData )
			else:
				question = QtCore.QCoreApplication.translate("ListHandler", "Delete this entry and everything beneath?")
			if QtGui.QMessageBox.question(	self.parentWidget(),
										QtCore.QCoreApplication.translate("ListHandler", "Confirm delete"),
										question,
										QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
										QtGui.QMessageBox.No) == QtGui.QMessageBox.No:
				return
		elif len( indexes )>1:
			if QtGui.QMessageBox.question(	self.parentWidget(),
										QtCore.QCoreApplication.translate("ListHandler", "Confirm delete"),
										QtCore.QCoreApplication.translate("ListHandler", "Delete %s entries?") % len( rows ),
										QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
										QtGui.QMessageBox.No) == QtGui.QMessageBox.No:
				return
		deleteData = [ self.parentWidget().model.getData()[ row ] for row in rows ]
		self.deleteEntries( deleteData, self.parentWidget().modul )
	
	def deleteEntries(self, entries, modul ):
		if not entries:
			return
		self.parent().overlay.inform( self.parent().overlay.BUSY )
		self.task = DeleteTask( modul, entries )
		self.connect( self.task, QtCore.SIGNAL("taskProgress(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self.onTaskProgress )
		self.connect( self.task, QtCore.SIGNAL("taskError(PyQt_PyObject)"), self.onTaskError )
		self.connect( self.task, QtCore.SIGNAL("taskFinished()"), self.onTaskFinished )
		
	
	def onTaskProgress(self, total, done, name ):
		self.parent().overlay.inform( self.parent().overlay.BUSY, QtCore.QCoreApplication.translate("ListHandler", "Deleting entry %s of %s (%s)") % (done, total, name) )
	
	def onTaskFinished(self):
		event.emit( QtCore.SIGNAL('dataChanged(PyQt_PyObject,PyQt_PyObject)'), self.parentWidget().modul, self)
		self.parent().overlay.inform( self.parent().overlay.SUCCESS )
	
	def onTaskError(self, error):
		event.emit( QtCore.SIGNAL('dataChanged(PyQt_PyObject,PyQt_PyObject)'), self.parentWidget().modul, self)
		self.parent().overlay.inform( self.parent().overlay.ERROR )
	

class ListConfigAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( ListConfigAction, self ).__init__(  QtGui.QIcon("icons/actions/configure_small.png"),"Konfigurieren", parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.Preferences )
		
	
	def onTriggered( self, e ):
		self.parentWidget().model.selectColums()


class Preview( QtGui.QWidget ):
	def __init__( self, urls, modul, data, *args, **kwargs ):
		super( Preview, self).__init__( *args, **kwargs )
		self.ui = Ui_EditPreview()
		self.ui.setupUi( self )
		self.urls = [(k,v) for (k,v) in urls.items() ]
		self.urls.sort( key=lambda x: x[0] )
		self.modul = modul
		self.data = data
		self.request = None
		self.ui.cbUrls.addItems( [ x[0] for x in self.urls ] )
		if "actiondescr" in data.keys():
			self.setWindowTitle("%s: %s" % (data["actiondescr"],data["name"]))
		elif "name" in data.keys():
			self.setWindowTitle( QtCore.QCoreApplication.translate("ListHandler", "Preview: %s") % data["name"])
		else:
			self.setWindowTitle( QtCore.QCoreApplication.translate("ListHandler", "Preview") )
		self.show()
	
	def on_cbUrls_currentIndexChanged( self, idx ):
		if not isinstance( idx, int ):
			return
		url = self.urls[ idx ][1]
		url = url.replace("{{id}}",self.data["id"]).replace("{{modul}}",self.modul )
		self.currentURL = url
		if url.lower().startswith("http"):
			self.ui.webView.setUrl( QtCore.QUrl( self.currentURL ) )
		else:
			"""Its the originating server - Load the page in our context (cookies!)"""
			if self.request:
				self.request.deleteLater()
				self.request=None
			self.request = NetworkService.request( NetworkService.url.replace("/admin","")+url )
			self.connect( self.request, QtCore.SIGNAL("finished()"), self.setHTML )
			self.connect( self.request, QtCore.SIGNAL("error(QNetworkReply::NetworkError)"), lambda: self.setHTML(error=True) )
	
	def setHTML( self, error=False ):
		if error:
			html = QtCore.QCoreApplication.translate("ListHandler", "Preview not possible")
		else:
			html = bytes(self.request.readAll()).decode("UTF8")
		self.ui.webView.setHtml( html, QtCore.QUrl( NetworkService.url.replace("/admin","")+self.currentURL ) )
		
	def on_btnReload_released(self, *args, **kwargs):
		self.on_cbUrls_currentIndexChanged( self.ui.cbUrls.currentIndex () )


class ListPreviewAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( ListPreviewAction, self ).__init__(  QtGui.QIcon("icons/actions/preview_small.png"),"Vorschau", parent )
		self.modul = self.parentWidget().modul
		self.widget = None
		if self.modul in conf.serverConfig["modules"].keys():
			modulConfig = conf.serverConfig["modules"][self.modul]
			if "previewurls" in modulConfig.keys():
				self.setEnabled( True )
				self.previewURLs = modulConfig["previewurls"]
			else: 
				self.setEnabled( False )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.Open )

	def onTriggered( self, e ):
		indexes = self.parentWidget().selectionModel.selection().indexes()
		rows = []
		for index in indexes:
			row = index.row()
			if not row in rows:
				rows.append( row )
		if len( rows )>0:
			data = self.parentWidget().model.getData()[ rows[0] ]
			self.widget = Preview( self.previewURLs, self.modul, data )
	
	def __del__( self ):
		if self.widget:
			self.widget.deleteLater()


class PredefinedViewHandler( EntryHandler ):
	"""Holds one view for this modul (preconfigured from Server)"""
	
	def __init__( self, modul, viewName, *args, **kwargs ):
		super( PredefinedViewHandler, self ).__init__( modul, *args, **kwargs )
		self.viewName = viewName
		config = conf.serverConfig["modules"][ modul ]
		assert "views" in config.keys()
		myview = [ x for x in config["views"] if x["name"]==viewName][0]
		self.setText( 0, myview["name"] )
		if "icon" in myview.keys():
			self.setIcon( 0, QtGui.QIcon( myview["icon"] ) )
	
	def clicked( self ):
		if not self.widgets:
			config = conf.serverConfig["modules"][ self.modul ]
			myview = [ x for x in config["views"] if x["name"]==self.viewName][0]
			if all ( [(x in myview.keys()) for x in ["filter", "columns"]] ):
				self.addWidget( List( self.modul, myview["columns"],  myview["filter"] ) )
			else:
				self.addWidget( List( self.modul) )
		else:
			self.focus()


class ListCoreHandler( EntryHandler ):
	"""Class for holding the main (module) Entry within the modules-list"""
	
	def __init__( self, modul,  *args, **kwargs ):
		super( ListCoreHandler, self ).__init__( modul, *args, **kwargs )
		if modul in conf.serverConfig["modules"].keys():
			config = conf.serverConfig["modules"][ modul ]
			if config["icon"]:
				lastDot = config["icon"].rfind(".")
				smallIcon = config["icon"][ : lastDot ]+"_small"+config["icon"][ lastDot: ]
				if os.path.isfile( os.path.join( os.getcwd(), smallIcon ) ):
					self.setIcon( 0, QtGui.QIcon( smallIcon ) )
				else:
					self.setIcon( 0, QtGui.QIcon( config["icon"] ) )
			self.setText( 0, config["name"] )
			if "views" in config.keys():
				for view in config["views"]:
					self.addChild( PredefinedViewHandler( modul, view["name"] ) )
	
	def clicked( self ):
		if not self.widgets:
			config = conf.serverConfig["modules"][ self.modul ]
			if "columns" in config.keys():
				if "filter" in config.keys():
					self.addWidget( List( self.modul, config["columns"], config["filter"]  ) )
				else:
					self.addWidget( List( self.modul, config["columns"] ) )
			else:
				self.addWidget( List( self.modul ) )
		else:
			self.focus()
	
class ListHandler( QtCore.QObject ):
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('requestModulHandler(PyQt_PyObject,PyQt_PyObject)'), self.requestModulHandler )
		self.connect( event, QtCore.SIGNAL('requestModulListActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)') ,  self.requestModulListActions )
	
	def requestModulListActions(self, queue, modul, config, parent ):
		if isinstance( parent, List ):
			queue.registerHandler( 0, ListAddAction )
			queue.registerHandler( 2, ListEditAction )
			queue.registerHandler( 4, ListDeleteAction )
			queue.registerHandler( 5, ListPreviewAction )
			queue.registerHandler( 7, ListConfigAction )

	def requestModulHandler(self, queue, modulName ):
		f = lambda: ListCoreHandler( modulName )
		queue.registerHandler( 0, f )
	
	
	def openList(self, modulName, listConfigName ):
		l = ListList( modulName, listConfigName )
		event.emit( QtCore.SIGNAL('addHandlerWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), l , QtCore.QCoreApplication.translate("ListHandler", "List"), None )
		l.updateTabDescription()
		

_listHandler = ListHandler()
