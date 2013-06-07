# -*- coding: utf-8 -*-
from PySide import QtCore, QtGui
from utils import Overlay
from network import NetworkService
from event import event
import utils
from config import conf
from widgets.edit import EditWidget
from priorityqueue import protocolWrapperInstanceSelector, actionDelegateSelector
from ui.hierarchyUI import Ui_Hierarchy
from mainwindow import WidgetHandler

class HierarchyAddAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( HierarchyAddAction, self ).__init__(  QtGui.QIcon("icons/actions/add_small.png"), QtCore.QCoreApplication.translate("Hierarchy", "Add entry") , parent )
		self.triggered.connect( self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.New )
	
	def onTriggered( self ):
		#config = conf.serverConfig["modules"][ self.parent().modul ]
		widget = lambda: EditWidget(self.parent().modul, EditWidget.appHierarchy, 0, node=self.parent().hierarchy.currentRootNode)
		handler = WidgetHandler(  widget, descr=QtCore.QCoreApplication.translate("Hierarchy", "Add entry"), icon=QtGui.QIcon("icons/actions/add_small.png") )
		handler.stackHandler()
		#event.emit( QtCore.SIGNAL('stackHandler(PyQt_PyObject)'), handler )
	
	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "hierarchy" or modul.startswith("hierarchy.")) and actionName=="add")

actionDelegateSelector.insert( 1, HierarchyAddAction.isSuitableFor, HierarchyAddAction )

class HierarchyEditAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( HierarchyEditAction, self ).__init__(  QtGui.QIcon("icons/actions/edit_small.png"), QtCore.QCoreApplication.translate("Hierarchy", "Edit entry"), parent )
		self.triggered.connect( self.onTriggered )
		self.setShortcut( "Return" )
	
	def onTriggered( self ):
		parent = self.parent()
		for item in parent.hierarchy.selectedItems():
			widget = lambda: EditWidget(parent.modul, EditWidget.appHierarchy, item.entryData["id"] )
			handler = WidgetHandler( widget, descr=QtCore.QCoreApplication.translate("Hierarchy", "Edit entry"), icon=QtGui.QIcon("icons/actions/edit_small.png")  )
			handler.stackHandler()
			#event.emit( QtCore.SIGNAL('stackHandler(PyQt_PyObject)'), handler )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "hierarchy" or modul.startswith("hierarchy.")) and actionName=="edit")

actionDelegateSelector.insert( 1, HierarchyEditAction.isSuitableFor, HierarchyEditAction )

class HierarchyDeleteAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( HierarchyDeleteAction, self ).__init__(  QtGui.QIcon("icons/actions/delete_small.png"), QtCore.QCoreApplication.translate("Hierarchy", "Delete entry"), parent )
		self.triggered.connect( self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.Delete )
	
	def onTriggered( self ):
		parent = self.parent()
		for item in parent.hierarchy.selectedItems():
			self.parent().hierarchy.requestDelete( item.entryData["id"] )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "hierarchy" or modul.startswith("hierarchy.")) and actionName=="delete")

actionDelegateSelector.insert( 1, HierarchyDeleteAction.isSuitableFor, HierarchyDeleteAction )
