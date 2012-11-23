from ui.adminUI import Ui_MainWindow
from PyQt4 import QtCore, QtGui, QtWebKit
from event import event
from config import conf
import time
from utils import RegisterQueue, showAbout
from tasks import TaskViewer
from analytics import AnalytisWidget


class EntryHandler( QtGui.QTreeWidgetItem ):
	""" 
	Holds the items displayed top-left within the admin.
	Each of these provides access to one modul and holds the references
	to the widgets shown inside L{MainWindow.ui.stackedWidget}
	"""
	def __init__( self, modul, *args, **kwargs ):
		"""
		@type modul: string
		@param modul: Name of the modul handled
		"""
		super( EntryHandler, self ).__init__( *args, **kwargs )
		self.modul = modul
		self.widgets = []
		self.largeIcon = None
		if modul in conf.serverConfig["modules"].keys():
			config = conf.serverConfig["modules"][ modul ]
			if config["icon"]:
				self.largeIcon = QtGui.QIcon( config["icon"] )

	def getBreadCrumb( self ):
		return( self.text(0), self.largeIcon or self.icon(0) )
		
	def addWidget( self, widget ):
		"""
		Adds a widget to the stack.
		The widget gains focus.
		
		@type widget: QWidget
		@param widget: The widget to add
		"""
		if not widget in self.widgets:
			self.widgets.append( widget )
		self.setIcon( 2, QtGui.QIcon( "icons/actions/delete.png" ) )
		self.focus()
	
	def focus( self ):
		"""
		If this handler holds at least one widget, the last widget
		on the stack gains focus
		"""
		if self.widgets:
			event.emit( QtCore.SIGNAL("focusWidget(PyQt_PyObject,PyQt_PyObject)"), self.widgets[-1], self )
	
	def close( self ):
		"""
		Closes the last widget on the stack.
		If no more widgets are left, the X-Icon is removed.
		
		Gets called automaticaly if the user clicks this X-Icon.
		"""
		if self.widgets:
			w = self.widgets[-1]
			event.emit( QtCore.SIGNAL("closeWidget(PyQt_PyObject)"), w )
			w.deleteLater()
			self.widgets.remove( w )
		if not self.widgets:
			self.setIcon( 2, QtGui.QIcon( ) )
		else:
			self.focus()
	
	def remove( self ):
		"""
		Closes *all* widgets of this handler
		"""
		while self.widgets:
			w = self.widgets[-1]
			event.emit( QtCore.SIGNAL("closeWidget(PyQt_PyObject)"), w )
			w.deleteLater()
			self.widgets.remove( w )
		event.emit( QtCore.SIGNAL("removeHandler(PyQt_PyObject)"), self )
	
	def clicked( self ):
		"""
		Called whenever the user selects the handler from the treeWidget.
		"""
		pass
		
	def sticky( self ):
		"""
		Toggles sticky of this item
		"""
		pass
	
	def contextMenu( self ):
		"""
		Currently unused
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
		self.ui.treeWidget.setColumnWidth(0,244)
		self.ui.treeWidget.setColumnWidth(1,25)
		self.ui.treeWidget.setColumnWidth(2,25)
		self.connect( event, QtCore.SIGNAL('loginSucceeded()'), self.setup )
		self.connect( event, QtCore.SIGNAL('focusWidget(PyQt_PyObject,PyQt_PyObject)'), self.focusWidget )
		self.connect( event, QtCore.SIGNAL('closeWidget(PyQt_PyObject)'), self.closeWidget )
		self.connect( event, QtCore.SIGNAL('addHandler(PyQt_PyObject)'), self.addHandler )
		self.connect( event, QtCore.SIGNAL('removeHandler(PyQt_PyObject)'), self.removeHandler )
		self.connect( event, QtCore.SIGNAL('stackWidget(PyQt_PyObject)'), self.stackWidget )
		self.connect( event, QtCore.SIGNAL("popWidget(PyQt_PyObject)"), self.popWidget )
		self.connect( event, QtCore.SIGNAL("statusMessage(PyQt_PyObject,PyQt_PyObject)"), self.statusMessage )
		self.currentHandler = None
		self.helpBrowser = None
		self.startPage = None
		self.rebuildBreadCrumbs( )


	def rebuildBreadCrumbs( self ):
		"""
		Rebuilds the breadcrump-path.
		Currently, it displayes the current modul, its icon and
		stacks the path as children to its handler
		"""
		self.ui.modulLbl.setText( QtCore.QCoreApplication.translate("MainWindow", "Welcome to ViUR!")  )
		self.ui.iconLbl.setPixmap( QtGui.QPixmap("icons/viur_logo.png").scaled(64,64,QtCore.Qt.IgnoreAspectRatio) )
		if self.currentHandler:
			data = self.currentHandler.getBreadCrumb()
			if data:
				txt, icon = data
				self.ui.modulLbl.setText( txt[ : 35 ] )
				if icon:
					sizes = icon.availableSizes()
					if len(sizes):
						pixmap = icon.pixmap( sizes[0] )
						self.ui.iconLbl.setPixmap( pixmap.scaled(64,64,QtCore.Qt.IgnoreAspectRatio) )
			
			if self.currentHandler.parent(): #Its on the 2nd Level
				self.currentHandler.takeChildren()
				currentHandler = self.currentHandler
				for widget in self.currentHandler.widgets[1:]:
					if "getBreadCrumb" in dir(widget):
						data = widget.getBreadCrumb()
						if data:
							txt, icon = data
							newHandler = QtGui.QTreeWidgetItem()
							newHandler.setText(0, txt )
							def mkClickHandler( handler ):
								return lambda *args, **kwargs: handler.parent().clicked()
							newHandler.clicked = mkClickHandler( newHandler )
							currentHandler.addChild( newHandler )
							currentHandler = newHandler 
							self.ui.modulLbl.setText( txt )
							if icon:
								newHandler.setIcon(0, icon )
								sizes = icon.availableSizes()
								if len(sizes):
									pixmap = icon.pixmap( sizes[0] )
									self.ui.iconLbl.setPixmap( pixmap.scaled(64,64,QtCore.Qt.IgnoreAspectRatio) )
				def expandRecursive( handler ):
					self.ui.treeWidget.expandItem( handler )
					for idx in range( 0, handler.childCount() ):
						expandRecursive( handler.child( idx ) )
				expandRecursive( self.currentHandler )
			
		
	def focusWidget( self, widget, handler ):
		"""
		Ensures that the widget gains focus.
		If the widget is not a child of stackedWidget, it gets added.
		
		@type widget: QWidget
		@param widget: Widget to focus
		@type handler: EntryHandler
		@param handler: Handler requesting the focus
		"""
		if self.ui.stackedWidget.indexOf( widget )==-1:
			self.ui.stackedWidget.addWidget( widget )
		self.ui.stackedWidget.setCurrentWidget( widget )
		if self.currentHandler:
			self.ui.treeWidget.setItemSelected( self.currentHandler, False )
		self.currentHandler = handler
		if self.currentHandler.parent():
			self.ui.treeWidget.expandItem( self.currentHandler.parent() )
		self.ui.treeWidget.setItemSelected( self.currentHandler, True )
		self.rebuildBreadCrumbs()
	
	def stackWidget( self, widget ):
		"""
		Stacks a new widget to the current handler
		
		@type widget: QWidget
		@param widget: Widget to stack
		"""
		self.currentHandler.addWidget( widget )
		self.rebuildBreadCrumbs()
		
	def popWidget( self, widget ):
		"""
		Removes a widget from the currentHandler's stack.
		The widget looses focus and gets deleted.
		
		@type widget: QWidget
		@param widget: Widget to remove. Must be on the current handler's stack.
		"""
		if self.currentHandler:
			assert widget in self.currentHandler.widgets
			self.currentHandler.close()
		self.rebuildBreadCrumbs()
	
	def closeWidget( self, widget ):
		"""
		Removes a widget from the stackWidget.
		The widget is *not* removed from any handler nor it gets deleted.
		
		@type widget: QWidget
		@param widget: Widget to remove
		"""
		self.ui.stackedWidget.removeWidget( widget )
		def findCurrentHandler( currentWidget, widgetItem ):
			if "widgets" in dir( widgetItem ):
				if currentWidget in widgetItem.widgets:
					return( widgetItem )
			for i in range(0,widgetItem.childCount()):
				c = widgetItem.child( i )
				res = findCurrentHandler( currentWidget, c )
				if res:
					return( res )
			return( None )
		r = findCurrentHandler( self.ui.stackedWidget.currentWidget(), self.ui.treeWidget.invisibleRootItem() )
		if r:
			self.ui.treeWidget.setItemSelected( self.currentHandler, False )
			self.ui.treeWidget.setItemSelected( self.currentHandler, True )
		self.currentHandler = r
		self.rebuildBreadCrumbs()
	
	def on_treeWidget_itemClicked (self, item, colum):
		if colum==0:
			item.clicked()
		elif colum==1: #Stick it
			pass #This is obsolete
		elif colum==2: #Close
			item.close()
	
	def addHandler( self, handler ):
		"""
		Adds an handler as child of the matching toplevel handler for its modul.
		
		Note: The toplevel handler are created during startup via 
		QtCore.SIGNAL('requestModulHandler(PyQt_PyObject,PyQt_PyObject)')
		
		@type handler: EntryHandler
		"""
		for idx in range( 0 , self.ui.treeWidget.topLevelItemCount() ):
			item = self.ui.treeWidget.topLevelItem( idx )
			if item.modul == handler.modul:
				item.addChild( handler )
				self.ui.treeWidget.expandItem( item )
		self.ui.treeWidget.sortItems( 0, QtCore.Qt.AscendingOrder )
	
	def removeHandler( self, handler ):
		"""
		Removes a subhandler added by L{addHandler}.
		It does *not* remove toplevel handlers, even if requested to do so.
		
		@type handler: EntryHandler
		"""
		for idx in range( 0 , self.ui.treeWidget.topLevelItemCount() ):
			item = self.ui.treeWidget.topLevelItem( idx )
			if item.modul == handler.modul:
				item.removeChild( handler )
		self.rebuildBreadCrumbs()
	
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
			self.startPage = AnalytisWidget()
			self.ui.stackedWidget.addWidget( self.startPage )
		self.ui.treeWidget.clear()
		data = conf.serverConfig
		event.emit( QtCore.SIGNAL('downloadedConfig(PyQt_PyObject)'), data )
		handlers = []
		if not "modules" in conf.portal.keys():
			conf.portal["modules"] = {}
		for modul, cfg in data["modules"].items():
			queue = RegisterQueue()
			event.emit( QtCore.SIGNAL('requestModulHandler(PyQt_PyObject,PyQt_PyObject)'),queue, modul )
			handler = queue.getBest()()
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
	
