# -*- coding: utf-8 -*-
from ui.hierarchyUI import Ui_Hierarchy
from PyQt4 import QtCore, QtGui
from network import NetworkService
from event import event
from config import conf
from time import sleep, time
import sys, os, os.path
from utils import RegisterQueue, Overlay, formatString, loadIcon
from mainwindow import WidgetHandler
from widgets.hierarchy import HierarchyWidget
from widgets.edit import EditWidget




class HierarchyRepoHandler( WidgetHandler ): #FIXME
	"""Class for holding one Repo-Entry within the modules-list"""
	def __init__( self, modul, repo, *args, **kwargs ):
		super( HierarchyRepoHandler, self ).__init__( lambda: HierarchyWidget( modul, repo["key"]  ), descr=repo["name"], vanishOnClose=False, *args, **kwargs )


class HierarchyCoreHandler( WidgetHandler ): #FIXME
	"""Class for holding the main (module) Entry within the modules-list"""
	
	def __init__( self, modul,  *args, **kwargs ):
		self.modul = modul
		config = conf.serverConfig["modules"][ modul ]
		if config["icon"]:
			if config["icon"].lower().startswith("http://") or config["icon"].lower().startswith("https://"):
				icon = config["icon"]
			else:
				icon = loadIcon( config["icon"] )
		else:
			icon = loadIcon( None )
		super( HierarchyCoreHandler, self ).__init__( lambda: HierarchyWidget( modul ), icon=icon, vanishOnClose=False, *args, **kwargs )
		self.setText( 0, config["name"] )
		self.repos = []
		self.tmpObj = QtGui.QWidget()
		fetchTask = NetworkService.request("/%s/listRootNodes" % modul, parent=self.tmpObj )
		self.tmpObj.connect(fetchTask, QtCore.SIGNAL("finished()"), self.setRepos) 

	def setRepos( self ):
		data = NetworkService.decode( self.fetchTask )
		self.tmpObj.deleteLater()
		self.tmpObj = None
		self.repos = data
		if len( self.repos ) > 1:
			for repo in self.repos:
				d = HierarchyRepoHandler( self.modul, repo )
				self.addChild( d )

class HierarchyHandler( QtCore.QObject ):
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		#self.connect( event, QtCore.SIGNAL('requestModulHandler(PyQt_PyObject,PyQt_PyObject)'), self.requestModulHandler )
		event.connectWithPriority( 'requestModulHandler', self.requestModulHandler, event.lowPriority )

	def requestModulHandler(self, queue, modul ):
		config = conf.serverConfig["modules"][ modul ]
		if( config["handler"]=="hierarchy" ):
			f = lambda: HierarchyCoreHandler( modul )
			queue.registerHandler( 5, f )


_hierarchyHandler = HierarchyHandler()


