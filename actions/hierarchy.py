# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
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
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.New )
	
	def onTriggered( self, e ):
		#config = conf.serverConfig["modules"][ self.parent().modul ]
		widget = lambda: EditWidget(self.parent().modul, EditWidget.appHierarchy, 0, rootNode=self.parent().hierarchy.currentRootNode)
		handler = WidgetHandler(  widget, descr=QtCore.QCoreApplication.translate("Hierarchy", "Add entry"), icon=QtGui.QIcon("icons/actions/add_small.png") )
		event.emit( QtCore.SIGNAL('stackHandler(PyQt_PyObject)'), handler )
	
	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "hierarchy" or modul.startswith("hierarchy.") and actionName=="add") )

actionDelegateSelector.insert( 1, HierarchyAddAction.isSuitableFor, HierarchyAddAction )

class HierarchyEditAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( HierarchyEditAction, self ).__init__(  QtGui.QIcon("icons/actions/edit_small.png"), QtCore.QCoreApplication.translate("Hierarchy", "Edit entry"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( "Return" )
	
	def onTriggered( self, e ):
		parent = self.parent()
		for item in parent.hierarchy.selectedItems():
			widget = lambda: EditWidget(parent.modul, EditWidget.appHierarchy, item.data["id"] )
			handler = WidgetHandler( widget, descr=QtCore.QCoreApplication.translate("Hierarchy", "Edit entry"), icon=QtGui.QIcon("icons/actions/edit_small.png")  )
			event.emit( QtCore.SIGNAL('stackHandler(PyQt_PyObject)'), handler )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "hierarchy" or modul.startswith("hierarchy.") and actionName=="edit") )

actionDelegateSelector.insert( 1, HierarchyEditAction.isSuitableFor, HierarchyEditAction )

class HierarchyDeleteAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( HierarchyDeleteAction, self ).__init__(  QtGui.QIcon("icons/actions/delete_small.png"), QtCore.QCoreApplication.translate("Hierarchy", "Delete entry"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.Delete )
	
	def onTriggered( self, e ):
		parent = self.parent()
		for item in parent.hierarchy.selectedItems():
			#config = conf.serverConfig["modules"][ self.parentWidget().modul ]
			#if "formatstring" in config.keys():
			#	question = QtCore.QCoreApplication.translate("HierarchyHandler", "Delete entry %s and everything beneath?") % formatString( config["formatstring"],  item.data )
			#else: # FIXME: TDB (new signature for formatString
			question = QtCore.QCoreApplication.translate("HierarchyHandler", "Delete this entry and everything beneath?")
			res = QtGui.QMessageBox.question(	self.parentWidget(),
											QtCore.QCoreApplication.translate("HierarchyHandler", "Confirm delete"),
											question,
											QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No
										)
			if res == QtGui.QMessageBox.Yes:
				parent.hierarchy.delete( item.data["id"] )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "hierarchy" or modul.startswith("hierarchy.") and actionName=="delete") )

actionDelegateSelector.insert( 1, HierarchyDeleteAction.isSuitableFor, HierarchyDeleteAction )
