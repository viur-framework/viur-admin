# -*- coding: utf-8 -*-
from ui.hierarchyUI import Ui_Hierarchy
from PySide import QtCore, QtGui
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
		self.fetchTask = NetworkService.request("/%s/listRootNodes" % modul )
		self.tmpObj.connect(self.fetchTask, QtCore.SIGNAL("finished()"), self.setRepos) 

	def setRepos( self ):
		data = NetworkService.decode( self.fetchTask )
		self.fetchTask.deleteLater()
		self.fetchTask = None
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
		self.connect( event, QtCore.SIGNAL('requestHierarchyListActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)') ,  self.requestHierarchyListActions )
		#self.connect( event, QtCore.SIGNAL('requestModulHandler(PyQt_PyObject,PyQt_PyObject)'), self.requestModulHandler )
		event.connectWithPriority( 'requestModulHandler', self.requestModulHandler, event.lowPriority )

	def requestHierarchyListActions(self, queue, modul, parent ):
		config = conf.serverConfig["modules"][ modul ]
		if config and config["handler"]=="hierarchy":
			queue.registerHandler( 2, HierarchyAddAction )
			queue.registerHandler( 3, HierarchyEditAction )
			queue.registerHandler( 4, HierarchyDeleteAction )

	def requestModulHandler(self, queue, modul ):
		config = conf.serverConfig["modules"][ modul ]
		if( config["handler"]=="hierarchy" ):
			f = lambda: HierarchyCoreHandler( modul )
			queue.registerHandler( 5, f )


_hierarchyHandler = HierarchyHandler()


