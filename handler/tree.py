# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, QtNetwork
from network import NetworkService
from event import event
from config import conf
from time import sleep, time
import sys, os, os.path
from utils import RegisterQueue, Overlay, loadIcon
from handler.list import ListCoreHandler
from mainwindow import WidgetHandler
from widgets.tree import TreeWidget, TreeItem, DirItem
from widgets.edit import EditWidget




class TreeBaseHandler( WidgetHandler ):
	def __init__( self, modul, *args, **kwargs ):
		config = conf.serverConfig["modules"][ modul ]
		if config["icon"]:
			if config["icon"].lower().startswith("http://") or config["icon"].lower().startswith("https://"):
				icon = config["icon"]
			else:
				icon = loadIcon( config["icon"] )
		else:
			icon = loadIcon( None )
		super( TreeBaseHandler, self ).__init__(  lambda: TreeWidget( modul ), icon=icon, vanishOnClose=False, *args, **kwargs )
		self.setText( 0, config["name"] )


class TreeHandler( QtCore.QObject ):
	"""
	Created automatically to route Events to its handler in this file.png
	Do not create another instance of this!
	"""
	def __init__(self, *args, **kwargs ):
		"""
		Do not instantiate this!
		All parameters are passed to QObject.__init__
		"""
		QtCore.QObject.__init__( self, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('requestModulHandler(PyQt_PyObject,PyQt_PyObject)'), self.requestModulHandler )

	
	def requestModulHandler(self, queue, modul ):
		"""Pushes a L{TreeBaseHandler} onto the queue if handled by "tree"
		
		@type queue: RegisterQueue
		@type modul: string
		@param modul: Name of the modul which should be handled
		"""
		config = conf.serverConfig["modules"][ modul ]
		if( config["handler"]=="tree" or config["handler"].startswith("tree.") ):
			f = lambda: TreeBaseHandler( modul )
			queue.registerHandler( 5, f )
	
	
	def openList(self, modulName, config ):
		if "name" in config.keys():
			name = config["name"]
		else:
			name = "Liste"
		if "icon" in config.keys():
			icon = config["icon"]
		else:
			icon = None
		event.emit( QtCore.SIGNAL('addHandlerWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), TreeList( modulName, config ), name, icon )

_fileHandler = TreeHandler()


