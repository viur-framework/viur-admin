# -*- coding: utf-8 -*-
from ui.adminUI import Ui_MainWindow
from PyQt4 import QtCore, QtGui, QtWebKit
from event import event
from config import conf
import time, os
from utils import RegisterQueue, showAbout
from tasks import TaskViewer
import startpages
import gc
from network import NetworkService, RemoteFile

class BaseHandler( QtGui.QTreeWidgetItem ):
	
	def focus( self ):
		"""
		If this handler holds at least one widget, the last widget
		on the stack gains focus
		"""
		pass
	
	def close( self ):
		pass
	
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

	def getBreadCrumb(self):
		return( self.text(0), self.icon(0) )

class WidgetHandler( BaseHandler ):
	""" 
	Holds the items displayed top-left within the admin.
	Each of these provides access to one modul and holds the references
	to the widgets shown inside L{MainWindow.ui.stackedWidget}
	"""
	def __init__( self, widgetGenerator, descr="", icon=None, vanishOnClose=True, *args, **kwargs ):
		"""
		@type modul: string
		@param modul: Name of the modul handled
		"""
		super( WidgetHandler, self ).__init__( *args, **kwargs )
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
			event.emit( QtCore.SIGNAL("addWidget(PyQt_PyObject)"), self.widgets[ -1 ] )
			self.setIcon( 1, QtGui.QIcon( "icons/actions/exit_small.png") )
		event.emit( QtCore.SIGNAL("focusHandler(PyQt_PyObject)"), self )
	
	def close( self ):
		"""
		Closes *all* widgets of this handler
		"""
		if self.widgets:
			event.emit( QtCore.SIGNAL("removeWidget(PyQt_PyObject)"), self.widgets[ -1 ] )
		if len( self.widgets ) > 1:
			self.widgets = self.widgets[ : -1]
			self.focus()
		elif len( self.widgets )==1:
			self.widgets = []
			if self.vanishOnClose:
				event.emit( QtCore.SIGNAL("removeHandler(PyQt_PyObject)"), self )
			else:
				event.emit( QtCore.SIGNAL("unfocusHandler(PyQt_PyObject)"), self )
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
	
class GroupHandler( BaseHandler ):
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
		event.connectWithPriority( QtCore.SIGNAL('loginSucceeded()'), self.setup, event.lowPriority )
		event.connectWithPriority( QtCore.SIGNAL('addHandler(PyQt_PyObject,PyQt_PyObject)'), self.addHandler, event.lowestPriority )
		event.connectWithPriority( QtCore.SIGNAL('stackHandler(PyQt_PyObject)'), self.stackHandler, event.lowestPriority )
		event.connectWithPriority( QtCore.SIGNAL('focusHandler(PyQt_PyObject)'), self.focusHandler, event.lowPriority )
		event.connectWithPriority( QtCore.SIGNAL('unfocusHandler(PyQt_PyObject)'), self.unfocusHandler, event.lowPriority )
		event.connectWithPriority( QtCore.SIGNAL('removeHandler(PyQt_PyObject)'), self.removeHandler, event.lowPriority )
		event.connectWithPriority( QtCore.SIGNAL('stackWidget(PyQt_PyObject)'), self.stackWidget, event.lowPriority )
		event.connectWithPriority( QtCore.SIGNAL('popWidget(PyQt_PyObject)'), self.popWidget, event.lowPriority )
		event.connectWithPriority( QtCore.SIGNAL('addWidget(PyQt_PyObject)'), self.addWidget, event.lowPriority )
		event.connectWithPriority( QtCore.SIGNAL('removeWidget(PyQt_PyObject)'), self.removeWidget, event.lowPriority )
		event.connectWithPriority( QtCore.SIGNAL('rebuildBreadCrumbs()'), self.rebuildBreadCrumbs, event.lowPriority )
		self.handlerStack = []
		self.currentWidget = None
		self.helpBrowser = None
		self.startPage = None
		self.rebuildBreadCrumbs( )

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
		if self.handlerStack:
			self.ui.treeWidget.setItemSelected( self.handlerStack[-1], False )
		while handler in self.handlerStack:
			self.handlerStack.remove( handler )
		self.handlerStack.append( handler )
		if handler.parent():
			self.ui.treeWidget.expandItem( handler.parent() )
		self.ui.treeWidget.setItemSelected( self.handlerStack[-1], True )
		assert self.ui.stackedWidget.indexOf( handler.widgets[-1] ) != -1
		self.ui.stackedWidget.setCurrentWidget( handler.widgets[-1] )
		self.rebuildBreadCrumbs()
	
	def stackHandler( self, handler ):
		"""
			Stacks a new handler to the current handler
		
			@param handler: handler to stack
			@type handler: BaseHandler
		"""
		assert self.handlerStack
		self.handlerStack[-1].addChild( handler )
		handler.focus()
	
	def stackWidget(self, widget ):
		"""
			Stacks a new widget to the current handler.
			This widget doesnt have its own handler, so it wont appear in the QTreeWidget.
			The last widget on a handler's stack allways hides all other widgets of that handler.
			
			@param widget: Widget to stack on the current handler
			@type widget: QWidget
		"""
		assert self.handlerStack
		self.handlerStack[-1].widgets.append( widget )
		self.ui.stackedWidget.addWidget( widget )
		self.handlerStack[-1].focus()
		
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
		widget.setParent( None )
		widget = None
		gc.collect()
	
	def popWidget( self, widget ):
		"""
			Removes a widget from the currentHandler's stack.
			The widget looses focus and gets detached from that handler.
			If no more referents are left to that widget, its garbarge-collected.
			
			@type widget: QWidget
			@param widget: Widget to remove. Must be on the current handler's stack.
		"""
		assert self.handlerStack
		assert widget in self.handlerStack[-1].widgets
		self.handlerStack[-1].close()
		self.rebuildBreadCrumbs()

	def unfocusHandler(self, handler ):
		"""
			Moves the focus to the next handler on our stack (if any).
			
			@param handler: The handler requesting the unfocus. *Must* be the last on the stack.
			@type handler: BaseHandler
		"""
		while handler in self.handlerStack:
			self.handlerStack.remove( handler )
		if self.handlerStack:
			self.focusHandler( self.handlerStack[ -1 ] )

	def removeHandler( self, handler ):
		"""
			Removes a handler added by addHandler or stackHandler.
			@type handler: EntryHandler
		"""
		def removeRecursive( handler, parent ):
			for subIdx in range( 0 , parent.childCount() ):
					child = parent.child( subIdx )
					if child == handler:
						parent.removeChild( handler )
						return
					removeRecursive( handler, child )
		removeRecursive( handler, self.ui.treeWidget.invisibleRootItem() )
		if handler in self.handlerStack:
			self.handlerStack.remove( handler )
		for widget in handler.widgets:
			if self.ui.stackedWidget.indexOf( widget ) != -1:
				self.ui.stackedWidget.removeWidget( widget )
		if self.handlerStack:
			self.focusHandler( self.handlerStack[ -1 ] )
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
		if self.handlerStack:
			try:
				txt, icon = self.handlerStack[-1].getBreadCrumb()
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
			event.emit( QtCore.SIGNAL('requestModulHandler(PyQt_PyObject,PyQt_PyObject)'),queue, modul )
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
		self.show()
		self.ui.treeWidget.sortItems( 0, QtCore.Qt.AscendingOrder )
		event.emit( QtCore.SIGNAL('mainWindowInitialized()') )
		QtGui.QApplication.restoreOverrideCursor()

	def on_modulsList_itemClicked (self, item):
		"""
		Forwards the clicked-event to the selected handler
		"""
		if item and "clicked" in dir( item ):
			item.clicked()

	def on_modulsList_itemDoubleClicked( self, item ):
		"""Called if the user selects an Item from the ModuleTree"""
		if item and "doubleClicked" in dir( item ):
			item.doubleClicked()

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
	
