# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from utils import Overlay, RegisterQueue, formatString
from network import NetworkService, RequestGroup
from event import event
from priorityqueue import viewDelegateSelector, protocolWrapperInstanceSelector, actionDelegateSelector
from widgets.edit import EditWidget
from mainwindow import WidgetHandler
from config import conf

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
		handler = WidgetHandler( lambda: EditWidget( self.parentWidget().list.modul, EditWidget.appList, 0 ), descr, QtGui.QIcon("icons/actions/add_small.png") )
		event.emit( QtCore.SIGNAL('stackHandler(PyQt_PyObject)'), handler )
	
	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "list" or modul.startswith("list.") and actionName=="add") )
		
actionDelegateSelector.insert( 1, ListAddAction.isSuitableFor, ListAddAction )

class ListEditAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( ListEditAction, self ).__init__( QtGui.QIcon("icons/actions/edit_small.png"), QtCore.QCoreApplication.translate("ListHandler", "Edit entry"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
	
	def onTriggered( self, e ):
		if len( self.parentWidget().list.selectionModel().selection().indexes() )==0:
			return
		data = self.parentWidget().list.model().getData()[ self.parentWidget().list.selectionModel().selection().indexes()[0].row() ]
		self.parentWidget().openEditor( data, clone=False )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "list" or modul.startswith("list.") and actionName=="edit") )

actionDelegateSelector.insert( 1, ListEditAction.isSuitableFor, ListEditAction )

class ListCloneAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( ListCloneAction, self ).__init__( QtGui.QIcon("icons/actions/clone_small.png"), QtCore.QCoreApplication.translate("ListHandler", "Clone entry"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
	
	def onTriggered( self, e ):
		if len( self.parentWidget().list.selectionModel().selection().indexes() )==0:
			return
		data = self.parentWidget().list.model().getData()[ self.parentWidget().list.selectionModel().selection().indexes()[0].row() ]
		self.parentWidget().openEditor( data, clone=True )
	
	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "list" or modul.startswith("list.") and actionName=="clone") )

actionDelegateSelector.insert( 1, ListCloneAction.isSuitableFor, ListCloneAction )

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
		reqWrap = protocolWrapperInstanceSelector.select( self.parent().list.modul )
		assert reqWrap is not None
		reqWrap.deleteEntries( [x["id"] for x in deleteData] )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "list" or modul.startswith("list.") and actionName=="delete") )

actionDelegateSelector.insert( 1, ListDeleteAction.isSuitableFor, ListDeleteAction )
	
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
				#self.request.deleteLater()
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
		super( ListPreviewAction, self ).__init__(  QtGui.QIcon("icons/actions/preview_small.png"), QtCore.QCoreApplication.translate("ListHandler", "Preview"), parent )
		self.modul = self.parentWidget().list.modul
		self.widget = None
		if self.modul in conf.serverConfig["modules"].keys():
			modulConfig = conf.serverConfig["modules"][self.modul]
			if "previewurls" in modulConfig.keys() and modulConfig["previewurls"]:
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
			data = self.parentWidget().list.model().getData()[ rows[0] ]
			self.widget = Preview( self.previewURLs, self.modul, data )
	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "list" or modul.startswith("list.") and actionName=="preview") )

actionDelegateSelector.insert( 1, ListPreviewAction.isSuitableFor, ListPreviewAction )