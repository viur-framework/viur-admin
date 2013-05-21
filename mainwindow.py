# -*- coding: utf-8 -*-
from ui.adminUI import Ui_MainWindow
from PySide import QtCore, QtGui, QtWebKit
from event import event
from config import conf
import time, os
from utils import RegisterQueue, showAbout
from tasks import TaskViewer
import startpages
from network import NetworkService, RemoteFile
from priorityqueue import protocolWrapperClassSelector


class WidgetHandler( QtGui.QTreeWidgetItem ):
	""" 
	Holds the items displayed top-left within the admin.
	Each of these provides access to one modul and holds the references
	to the widgets shown inside L{MainWindow.ui.stackedWidget}
	"""
	mainWindow = None
	
	def __init__( self, widgetGenerator, descr="", icon=None, vanishOnClose=True, mainWindow=None, *args, **kwargs ):
		"""
		@type modul: string
		@param modul: Name of the modul handled
		"""
		super( WidgetHandler, self ).__init__( *args, **kwargs )
		if mainWindow:
			self.mainWindow = mainWindow
		if self.mainWindow is None:
			raise UnboundLocalError("You either have to create the mainwindow before using this class or specifiy an replacement.")
		self.widgets = []
		self.widgetGenerator = widgetGenerator
		self.setText(0, descr)
		if icon is not None:
			if isinstance( icon, QtGui.QIcon):
				self.setIcon(0, icon )
			elif isinstance( icon, str ):
				RemoteFile( icon, successHandler=self.loadIconFromRequest )
		self.vanishOnClose = vanishOnClose
		#self.largeIcon = None
		#if modul in conf.serverConfig["modules"].keys():
		#	config = conf.serverConfig["modules"][ modul ]
		#	if config["icon"]:
		#		self.largeIcon = QtGui.QIcon( config["icon"] )

	def loadIconFromRequest( self, request ):
		icon = QtGui.QIcon( request.getFileName() )
		self.setIcon(0, icon)

	def focus( self ):
		"""
		If this handler holds at least one widget, the last widget
		on the stack gains focus
		"""
		if not self.widgets:
			self.widgets.append( self.widgetGenerator() )
			self.mainWindow.addWidget( self.widgets[ -1 ] )
			#event.emit( QtCore.SIGNAL("addWidget(PyQt_PyObject)"), self.widgets[ -1 ] )
			self.setIcon( 1, QtGui.QIcon( "icons/actions/exit_small.png") )
		self.mainWindow.focusHandler( self )
		#event.emit( QtCore.SIGNAL("focusHandler(PyQt_PyObject)"), self )
	
	def close( self ):
		"""
		Closes *all* widgets of this handler
		"""
		if self.widgets:
			self.mainWindow.removeWidget( self.widgets[ -1 ] )
			#event.emit( QtCore.SIGNAL("removeWidget(PyQt_PyObject)"), self.widgets[ -1 ] )
		if len( self.widgets ) > 1:
			self.widgets = self.widgets[ : -1]
			self.focus()
		elif len( self.widgets )==1:
			self.widgets = []
			if self.vanishOnClose:
				self.mainWindow.removeHandler( self )
				#event.emit( QtCore.SIGNAL("removeHandler(PyQt_PyObject)"), self )
			else:
				self.mainWindow.unfocusHandler( self )
				#event.emit( QtCore.SIGNAL("unfocusHandler(PyQt_PyObject)"), self )
				self.setIcon( 1, QtGui.QIcon() )
	
	def getBreadCrumb(self):
		for widget in self.widgets[ : : -1 ]:
			try:
				txt, icon = widget.getBreadCrumb()
				if not icon:
					icon = QtGui.QIcon()
				elif not isinstance( icon, QtGui.QIcon ):
					icon = QtGui.QIcon( icon )
				return( txt, icon )
			except:
				continue
		return( self.text(0), self.icon(0) )

	def clicked( self ):
		"""
		Called whenever the user selects the handler from the treeWidget.
		"""
		self.focus()
		
	def contextMenu( self ):
		"""
		Currently unused
		"""
		pass
	
	def stackHandler( self ):
		self.mainWindow.stackHandler( self )
	
class GroupHandler( QtGui.QTreeWidgetItem ):
	"""
		Toplevel widget for one modul-group
	"""
	pass


class MainWindow( QtGui.QMainWindow ):
	"""
	The main window.
	Holds the code for loading and processing the config (from the server) and
	mannaging the viewport
	"""
	
	def __init__( self, *args, **kwargs ):
		QtGui.QMainWindow.__init__(self, *args, **kwargs )
		self.ui = Ui_MainWindow()
		self.ui.setupUi( self )
		self.ui.treeWidget.setColumnWidth(0,269)
		self.ui.treeWidget.setColumnWidth(1,25)
		event.connectWithPriority( 'loginSucceeded()', self.setup, event.lowPriority )
		#event.connectWithPriority( QtCore.SIGNAL('addHandler(PyQt_PyObject,PyQt_PyObject)'), self.addHandler, event.lowestPriority )
		#event.connectWithPriority( QtCore.SIGNAL('stackHandler(PyQt_PyObject)'), self.stackHandler, event.lowestPriority )
		#event.connectWithPriority( QtCore.SIGNAL('focusHandler(PyQt_PyObject)'), self.focusHandler, event.lowPriority )
		#event.connectWithPriority( QtCore.SIGNAL('unfocusHandler(PyQt_PyObject)'), self.unfocusHandler, event.lowPriority )
		#event.connectWithPriority( QtCore.SIGNAL('removeHandler(PyQt_PyObject)'), self.removeHandler, event.lowPriority )
		event.connectWithPriority( 'stackWidget(PyQt_PyObject)', self.stackWidget, event.lowPriority )
		event.connectWithPriority( 'popWidget(PyQt_PyObject)', self.popWidget, event.lowPriority )
		#event.connectWithPriority( QtCore.SIGNAL('addWidget(PyQt_PyObject)'), self.addWidget, event.lowPriority )
		#event.connectWithPriority( QtCore.SIGNAL('removeWidget(PyQt_PyObject)'), self.removeWidget, event.lowPriority )
		#event.connectWithPriority( QtCore.SIGNAL('rebuildBreadCrumbs()'), self.rebuildBreadCrumbs, event.lowPriority )
		WidgetHandler.mainWindow = self
		self.ui.treeWidget.itemClicked.connect( self.on_treeWidget_itemClicked )
		self.currentWidget = None
		self.helpBrowser = None
		self.startPage = None
		self.rebuildBreadCrumbs( )

	def handlerForWidget( self, wdg = None ):
		def findRekursive( wdg, node ):
			if "widgets" in dir( node ) and isinstance( node.widgets, list ):
				for w in node.widgets:
					if w == wdg:
						return( node )
			for x in range(0, node.childCount() ):
				res = findRekursive( wdg, node.child( x ) )
				if res is not None:
					return( res )
			return( None )
			
		if wdg is None:
			wdg = self.ui.stackedWidget.currentWidget()
			if wdg is None:
				return( None )
		return( findRekursive( wdg, self.ui.treeWidget.invisibleRootItem() ) )

	def addHandler( self, handler, parent=None ):
		"""
		Adds an handler as child of parent.
		If parent is None, handler is added to the toplevel.
		
		@param handler: Handler to add
		@type handler: BaseHandler
		@param parent: Parent to stack handler to. If None, stack it to the toplevel
		@type handler: BaseHandler or None
		"""
		if parent:
			parent.addChild( handler )
			self.ui.treeWidget.expandItem( parent )
		else:
			self.ui.treeWidget.invisibleRootItem().addChild( handler )
		self.ui.treeWidget.sortItems( 0, QtCore.Qt.AscendingOrder )


	def focusHandler( self, handler ):
		"""
		Ensures that the widget gains focus.
		
		@type handler: BaseHandler
		@param handler: Handler requesting the focus
		"""
		currentHandler = self.handlerForWidget()
		if currentHandler:
			self.ui.treeWidget.setItemSelected( currentHandler, False )
		print( type( handler ) )
		print( type( self.ui.stackedWidget ) )
		if handler.parent():
			self.ui.treeWidget.expandItem( handler.parent() )
		self.ui.treeWidget.setItemSelected( handler, True )
		assert self.ui.stackedWidget.indexOf( handler.widgets[-1] ) != -1
		self.ui.stackedWidget.setCurrentWidget( handler.widgets[-1] )
		self.rebuildBreadCrumbs()
	
	def stackHandler( self, handler ):
		"""
			Stacks a new handler to the current handler
		
			@param handler: handler to stack
			@type handler: BaseHandler
		"""
		currentHandler = self.handlerForWidget()
		assert currentHandler
		currentHandler.addChild( handler )
		handler.focus()
	
	def stackWidget(self, widget ):
		"""
			Stacks a new widget to the current handler.
			This widget doesnt have its own handler, so it wont appear in the QTreeWidget.
			The last widget on a handler's stack allways hides all other widgets of that handler.
			
			@param widget: Widget to stack on the current handler
			@type widget: QWidget
		"""
		print("ssss")
		currentHandler = self.handlerForWidget()
		assert currentHandler
		currentHandler.widgets.append( widget )
		self.ui.stackedWidget.addWidget( widget )
		currentHandler.focus()
		
	def addWidget( self, widget ):
		assert self.ui.stackedWidget.indexOf( widget ) == -1
		self.ui.stackedWidget.addWidget( widget )

	def removeWidget( self, widget ):
		assert self.ui.stackedWidget.indexOf( widget ) != -1
		self.ui.stackedWidget.removeWidget( widget )
		try:
			widget.prepareDeletion()
		except AttributeError:
			pass
		#widget.setParent( None )
		widget.deleteLater()
		widget = None
	
	def popWidget( self, widget ):
		"""
			Removes a widget from the currentHandler's stack.
			The widget looses focus and gets detached from that handler.
			If no more referents are left to that widget, its garbarge-collected.
			
			@type widget: QWidget
			@param widget: Widget to remove. Must be on the current handler's stack.
		"""
		currentHandler = self.handlerForWidget(widget)
		currentHandler.close()
		self.rebuildBreadCrumbs()

	def unfocusHandler(self, handler ):
		"""
			Moves the focus to the next handler on our stack (if any).
			
			@param handler: The handler requesting the unfocus. *Must* be the last on the stack.
			@type handler: BaseHandler
		"""
		currentHandler = self.handlerForWidget()
		if currentHandler:
			self.focusHandler( currentHandler )

	def removeHandler( self, handler ):
		"""
			Removes a handler added by addHandler or stackHandler.
			@type handler: EntryHandler
		"""
		def removeRecursive( handler, parent ):
			for subIdx in range( 0 , parent.childCount() ):
				child = parent.child( subIdx )
				if id(child) == id(handler):
					parent.removeChild( handler )
					return
				removeRecursive( handler, child )
		removeRecursive( handler, self.ui.treeWidget.invisibleRootItem() )
		for widget in handler.widgets:
			if self.ui.stackedWidget.indexOf( widget ) != -1:
				self.ui.stackedWidget.removeWidget( widget )
		currentHandler = self.handlerForWidget()
		if currentHandler:
			self.focusHandler( currentHandler )
		self.rebuildBreadCrumbs()

	def on_treeWidget_itemClicked (self, item, colum):
		if colum==0:
			item.clicked()
		elif colum==1: #Close
			item.close()

	def rebuildBreadCrumbs( self ):
		"""
		Rebuilds the breadcrump-path.
		Currently, it displayes the current modul, its icon and
		stacks the path as children to its handler
		"""
		self.ui.modulLbl.setText( QtCore.QCoreApplication.translate("MainWindow", "Welcome to ViUR!")  )
		self.ui.iconLbl.setPixmap( QtGui.QPixmap("icons/viur_logo.png").scaled(64,64,QtCore.Qt.IgnoreAspectRatio) )
		currentHandler = self.handlerForWidget()
		if currentHandler:
			try:
				txt, icon = currentHandler.getBreadCrumb()
			except:
				return
			self.ui.modulLbl.setText( txt[ : 35 ] )
			if icon:
				sizes = icon.availableSizes()
				if len(sizes):
					pixmap = icon.pixmap( sizes[0] )
					self.ui.iconLbl.setPixmap( pixmap.scaled(64,64,QtCore.Qt.IgnoreAspectRatio) )

	def resetLoginWindow( self ):
		"""
		Emits QtCore.SIGNAL('resetLoginWindow()')
		"""
		event.emit( QtCore.SIGNAL('resetLoginWindow()') )

	def setup( self ):
		"""
		Initializes everything based on the config recived from the server.
		It
			- Resets the ui to sane defaults.
			- Emits QtCore.SIGNAL('downloadedConfig(PyQt_PyObject)') with the dict recived
			- Requests a toplevel handler for each modul
			- Finnaly emits QtCore.SIGNAL('mainWindowInitialized()')
		"""
		if not self.startPage:
			if "configuration" in conf.serverConfig.keys():
				if "analyticsKey" in conf.serverConfig["configuration"].keys():
					self.startPage = startpages.AnalytisWidget()
				elif "startPage" in conf.serverConfig["configuration"].keys():
					self.startPage = startpages.WebWidget()
			if not self.startPage: #Still not
				self.startPage = startpages.DefaultWidget()
			self.ui.stackedWidget.addWidget( self.startPage )
			
		self.ui.treeWidget.clear()
		data = conf.serverConfig
		event.emit( QtCore.SIGNAL('downloadedConfig(PyQt_PyObject)'), data )
		handlers = []
		groupHandlers = {}
		if "configuration" in data.keys() and "modulGroups" in data["configuration"].keys():
			for group in data["configuration"]["modulGroups"]:
				if not all( [x in group.keys() for x in ["name", "prefix", "icon"] ] ): #Assert that all required properties are there
					continue
				groupHandlers[ group["prefix"] ] = GroupHandler( "tl-handler-%s" % group["prefix"] )
				groupHandlers[ group["prefix"] ].setText(0, group["name"] )
				groupHandlers[ group["prefix"] ].setText(0, group["name"] )
				lastDot = group["icon"].rfind(".")
				smallIcon = group["icon"][ : lastDot ]+"_small"+group["icon"][ lastDot: ]
				if os.path.isfile( os.path.join( os.getcwd(), smallIcon ) ):
					groupHandlers[ group["prefix"] ].setIcon( 0, QtGui.QIcon( smallIcon ) )
				else:
					groupHandlers[ group["prefix"] ].setIcon( 0, QtGui.QIcon( group["icon"] ) )
				self.ui.treeWidget.addTopLevelItem( groupHandlers[ group["prefix"] ] )
		if not "modules" in conf.portal.keys():
			conf.portal["modules"] = {}
		for modul, cfg in data["modules"].items():
			queue = RegisterQueue()
			event.emit( 'requestModulHandler',queue, modul )
			handler = queue.getBest()()
			if "name" in cfg.keys() and groupHandlers:
				parent = None
				for groupName in groupHandlers.keys():
					if cfg["name"].startswith( groupName ):
						parent = groupHandlers[ groupName ]
				if parent:
					parent.addChild( handler )
				else:
					self.ui.treeWidget.addTopLevelItem( handler )
			else:
				self.ui.treeWidget.addTopLevelItem( handler )
			handlers.append( handler )
			event.emit( QtCore.SIGNAL('modulHandlerInitialized(PyQt_PyObject)'), modul )
			wrapperClass = protocolWrapperClassSelector.select( modul, data["modules"] )
			if wrapperClass is not None:
				wrapperClass( modul )
		self.show()
		self.ui.treeWidget.sortItems( 0, QtCore.Qt.AscendingOrder )
		event.emit( QtCore.SIGNAL('mainWindowInitialized()') )
		QtGui.QApplication.restoreOverrideCursor()


	def statusMessage(self, type, message):
		"""
		Display a Message on our Statusbar
		
		@type type: string
		@param type: Type of the message
		@type message: string
		@param message: Text to display
		
		"""
		self.ui.statusbar.showMessage( "%s: %s" % (time.strftime("%H:%M"), message), 5000 )
	
	def on_actionAbout_triggered(self, checked=None):
		if checked is None: return
		showAbout( self )
	
	def on_actionHelp_triggered(self):
		if self.helpBrowser:
			self.helpBrowser.deleteLater()
		self.helpBrowser = QtWebKit.QWebView( )
		self.helpBrowser.setUrl( QtCore.QUrl( "http://www.viur.is/site/Admin-Dokumentation" ) )
		self.helpBrowser.setWindowTitle( QtCore.QCoreApplication.translate("Help", "Help") )
		self.helpBrowser.setWindowIcon( QtGui.QIcon( QtGui.QPixmap( "icons/menu/help.png" ) ) )
		self.helpBrowser.show()
	
	def on_actionTasks_triggered(self, checked=None):
		if checked is None: return
		self.tasks = TaskViewer()
	
