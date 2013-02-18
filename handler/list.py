from PyQt4 import QtCore, QtGui
from network import NetworkService
from event import event
from ui.listUI import Ui_List
import time
import os, os.path
from ui.editpreviewUI import Ui_EditPreview
from utils import RegisterQueue, Overlay, formatString
from config import conf
from mainwindow import EntryHandler, WidgetHandler
from widgets.list import ListWidget, ListTableModel
from widgets.edit import EditWidget


class List( QtGui.QWidget ):
	def __init__(self, modul, fields=None, filter=None, *args, **kwargs ):
		super( List, self ).__init__( *args, **kwargs )
		self.modul = modul
		self.ui = Ui_List()
		self.ui.setupUi( self )
		layout = QtGui.QHBoxLayout( self.ui.tableWidget )
		self.ui.tableWidget.setLayout( layout )
		self.list = ListWidget( self.ui.tableWidget, modul, fields, filter )
		layout.addWidget( self.list )
		self.list.show()
		self.toolBar = QtGui.QToolBar( self )
		self.toolBar.setIconSize( QtCore.QSize( 32, 32 ) )
		self.ui.editSearch.mousePressEvent = self.on_editSearch_clicked
		if filter is not None and "search" in filter.keys():
			self.ui.editSearch.setText( filter["search"] )
		queue = RegisterQueue()
		event.emit( QtCore.SIGNAL('requestModulListActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), queue, modul, "", self )
		for item in queue.getAll():
			i = item( self )
			if isinstance( i, QtGui.QAction ):
				self.toolBar.addAction( i )
			else:
				self.toolBar.addWidget( i )
		self.ui.boxActions.addWidget( self.toolBar )
		self.connect( self.list, QtCore.SIGNAL("onItemActivated(PyQt_PyObject)"), self.openEditor )

	def on_editSearch_clicked(self, *args, **kwargs):
		if self.ui.editSearch.text()==QtCore.QCoreApplication.translate("ListHandler", "Search") :
			self.ui.editSearch.setText("")

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
		if self.list.modul in conf.serverConfig["modules"].keys() and "name" in conf.serverConfig["modules"][ self.list.modul ].keys() :
			name = conf.serverConfig["modules"][ self.list.modul ]["name"]
		else:
			name = self.list.modul
		widget = EditWidget( self.list.modul, EditWidget.appList, item["id"], clone=clone )
		handler = WidgetHandler( self.list.modul, widget )
		event.emit( QtCore.SIGNAL('addHandler(PyQt_PyObject)'), handler )
	
class ListAddAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( ListAddAction, self ).__init__(  QtGui.QIcon("icons/actions/add_small.png"), QtCore.QCoreApplication.translate("ListHandler", "Add entry"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.New )
	
	def onTriggered( self, e ):
		if self.parentWidget().list.modul in conf.serverConfig["modules"].keys() and "name" in conf.serverConfig["modules"][ self.parentWidget().list.modul ].keys() :
			name = conf.serverConfig["modules"][ self.parentWidget().list.modul ]["name"]
		else:
			name = self.parentWidget().list.modul
		descr = QtCore.QCoreApplication.translate("ListHandler", "Add entry: %s") % name
		widget = EditWidget( self.parentWidget().list.modul, EditWidget.appList, 0 )
		handler = WidgetHandler( self.parentWidget().list.modul, widget )
		event.emit( QtCore.SIGNAL('addHandler(PyQt_PyObject)'), handler )
		#event.emit( QtCore.SIGNAL('addHandlerWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), Edit(self.parentWidget().list.modul, 0), descr, "icons/onebiticonset/onebit_31.png" )


class ListEditAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( ListEditAction, self ).__init__( QtGui.QIcon("icons/actions/edit_small.png"), QtCore.QCoreApplication.translate("ListHandler", "Edit entry"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
	
	def onTriggered( self, e ):
		if len( self.parentWidget().list.selectionModel().selection().indexes() )==0:
			return
		data = self.parentWidget().list.model().getData()[ self.parentWidget().list.selectionModel().selection().indexes()[0].row() ]
		self.parentWidget().openEditor( data, clone=False )
		
class ListCloneAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( ListCloneAction, self ).__init__( QtGui.QIcon("icons/actions/clone_small.png"), QtCore.QCoreApplication.translate("ListHandler", "Clone entry"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
	
	def onTriggered( self, e ):
		if len( self.parentWidget().list.selectionModel().selection().indexes() )==0:
			return
		data = self.parentWidget().list.model().getData()[ self.parentWidget().list.selectionModel().selection().indexes()[0].row() ]
		self.parentWidget().openEditor( data, clone=True )
		

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
	
	def onTriggered( self, e ):
		indexes = self.parentWidget().list.selectedIndexes()
		rows = []
		for index in indexes:
			row = index.row()
			if not row in rows:
				rows.append( row )
		deleteData = [ self.parentWidget().list.model().getData()[ row ] for row in rows ]
		self.parent().list.delete( [x["id"] for x in deleteData], ask=True )
	


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
		self.modul = self.parentWidget().list.modul
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
		indexes = self.parentWidget().list.selectionModel().selection().indexes()
		rows = []
		for index in indexes:
			row = index.row()
			if not row in rows:
				rows.append( row )
		if len( rows )>0:
			data = self.parentWidget().list.model.getData()[ rows[0] ]
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
		event.connectWithPriority( QtCore.SIGNAL('requestModulHandler(PyQt_PyObject,PyQt_PyObject)'), self.requestModulHandler, event.lowPriority )
		event.connectWithPriority( QtCore.SIGNAL('requestModulListActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.requestModulListActions, event.lowPriority )
		#self.connect( event, QtCore.SIGNAL('requestModulHandler(PyQt_PyObject,PyQt_PyObject)'), self.requestModulHandler )
		#self.connect( event, QtCore.SIGNAL('requestModulListActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)') ,  self.requestModulListActions )
	
	def requestModulListActions(self, queue, modul, config, parent ):
		if isinstance( parent, List ):
			queue.registerHandler( 0, ListAddAction )
			queue.registerHandler( 2, ListEditAction )
			queue.registerHandler( 4, ListCloneAction )
			queue.registerHandler( 6, ListDeleteAction )
			queue.registerHandler( 8, ListPreviewAction )

	def requestModulHandler(self, queue, modulName ):
		f = lambda: ListCoreHandler( modulName )
		queue.registerHandler( 0, f )

_listHandler = ListHandler()
