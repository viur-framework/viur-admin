from PyQt4 import QtCore, QtGui
from network import NetworkService
from event import event
import time
import os, os.path
from ui.editpreviewUI import Ui_EditPreview
from utils import RegisterQueue, Overlay, formatString, loadIcon
from config import conf
from mainwindow import WidgetHandler
from widgets.list import ListWidget
from priorityqueue import protocolWrapperInstanceSelector


class PredefinedViewHandler( WidgetHandler ): #EntryHandler
	"""Holds one view for this modul (preconfigured from Server)"""
	
	def __init__( self, modul, viewName, *args, **kwargs ):
		config = conf.serverConfig["modules"][ modul ]
		myview = [ x for x in config["views"] if x["name"]==viewName][0]
		if all ( [(x in myview.keys()) for x in ["filter", "columns"]] ):
			widgetFactory = lambda: ListWidget( modul, myview["columns"],  myview["filter"] )
		else:
			widgetFactory = lambda: ListWidget( modul )
		if "icon" in myview.keys():
			if myview["icon"].lower().startswith("http://") or myview["icon"].lower().startswith("https://"):
				icon = myview["icon"]
			else:
				icon = loadIcon( myview["icon"] )
		else:
			icon = loadIcon( None )
		super( PredefinedViewHandler, self ).__init__( widgetFactory, icon=icon, vanishOnClose=False, *args, **kwargs )
		self.viewName = viewName
		self.setText( 0, myview["name"] )
	


class ListCoreHandler( WidgetHandler ): #EntryHandler
	"""Class for holding the main (module) Entry within the modules-list"""
	
	def __init__( self, modul,  *args, **kwargs ):
		# Config parsen
		config = conf.serverConfig["modules"][ modul ]
		if "columns" in config.keys():
			if "filter" in config.keys():
				widgetGen = lambda :ListWidget( modul, config["columns"], config["filter"]  )
			else:
				widgetGen = lambda: ListWidget( modul, config["columns"] )
		else:
			widgetGen = lambda: ListWidget( modul)
		if config["icon"]:
			if config["icon"].lower().startswith("http://") or config["icon"].lower().startswith("https://"):
				icon = config["icon"]
			else:
				icon = loadIcon( config["icon"] )
		else:
			icon = loadIcon( None )
		super( ListCoreHandler, self ).__init__( widgetGen, descr=config["name"], icon=icon, vanishOnClose=False, *args, **kwargs )
		if "views" in config.keys():
			for view in config["views"]:
				self.addChild( PredefinedViewHandler( modul, view["name"] ) )
			
	
	
class ListHandler( QtCore.QObject ):
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		event.connectWithPriority( 'requestModulHandler', self.requestModulHandler, event.lowPriority )
		#self.connect( event, QtCore.SIGNAL('requestModulHandler(PyQt_PyObject,PyQt_PyObject)'), self.requestModulHandler )
		#self.connect( event, QtCore.SIGNAL('requestModulListActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)') ,  self.requestModulListActions )
	

	def requestModulHandler(self, queue, modulName ):
		f = lambda: ListCoreHandler( modulName )
		queue.registerHandler( 0, f )

_listHandler = ListHandler()
