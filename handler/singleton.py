from PyQt4 import QtCore, QtGui
from network import NetworkService
from event import event
from config import conf
from mainwindow import WidgetHandler
from widgets.edit import EditWidget
from utils import loadIcon
import os

class SingletonEntryHandler( WidgetHandler ): 
	"""Class for holding the main (module) Entry within the modules-list"""
	
	def __init__( self, modul,  *args, **kwargs ):
		widgetFactory = lambda: EditWidget( modul, EditWidget.appSingleton, "singleton"  )
		name = ""
		if modul in conf.serverConfig["modules"].keys():
			config = conf.serverConfig["modules"][ modul ]
			if config["icon"]:
				if config["icon"].lower().startswith("http://") or config["icon"].lower().startswith("https://"):
					icon = config["icon"]
				else:
					icon = loadIcon( config["icon"] )
			else:
				icon = loadIcon( "icons/modules/singleton.svg" )
			name = config["name"]
		super( SingletonEntryHandler, self ).__init__( widgetFactory, icon=icon, vanishOnClose=False , *args, **kwargs )
		self.setText(0,name)

	def getBreadCrumb(self):
		"""
			Dont use the description of our edit widget here
		"""
		return( self.text(0), self.icon(0) )

class SingletonHandler( QtCore.QObject ):
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		event.connectWithPriority( 'requestModulHandler', self.requestModulHandler, event.lowPriority )

	def requestModulHandler(self, queue, modulName ):
		config = conf.serverConfig["modules"][ modulName ]
		if( config["handler"]=="singleton" ):
			f = lambda: SingletonEntryHandler( modulName )
			queue.registerHandler( 5, f )
	
_singletonHandler = SingletonHandler()
