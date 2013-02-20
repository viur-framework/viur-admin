from PyQt4 import QtCore, QtGui
from network import NetworkService
from event import event
from config import conf
from mainwindow import WidgetHandler
from widgets.edit import EditWidget
import os

class SingletonEntryHandler( WidgetHandler ): #FIXME
	"""Class for holding the main (module) Entry within the modules-list"""
	
	def __init__( self, modul,  *args, **kwargs ):
		widgetFactory = lambda: EditWidget( modul, EditWidget.appSingleton, "singleton"  )
		super( SingletonEntryHandler, self ).__init__( widgetFactory, vanishOnClose=False , *args, **kwargs )
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

class SingletonHandler( QtCore.QObject ):
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('requestModulHandler(PyQt_PyObject,PyQt_PyObject)'), self.requestModulHandler )

	def requestModulHandler(self, queue, modulName ):
		config = conf.serverConfig["modules"][ modulName ]
		if( config["handler"]=="singleton" ):
			f = lambda: SingletonEntryHandler( modulName )
			queue.registerHandler( 5, f )
	
_singletonHandler = SingletonHandler()
