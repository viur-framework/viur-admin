# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from network import NetworkService
from event import event
from config import conf
from time import sleep, time
import sys, os, os.path
from utils import RegisterQueue, Overlay, loadIcon
from handler.list import ListCoreHandler
from mainwindow import WidgetHandler
from widgets.tree import TreeWidget
from widgets.edit import EditWidget
from priorityqueue import protocolWrapperInstanceSelector, actionDelegateSelector


class TreeSimpleEditAction( QtGui.QAction ):
	"""
		Overriden edit-action which prevents editing Nodes
	"""
	def __init__(self, parent, *args, **kwargs ):
		super( TreeSimpleEditAction, self ).__init__(  QtGui.QIcon("icons/actions/edit_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "Edit entry"), parent )
		self.parent().itemSelectionChanged.connect( self.onItemSelectionChanged )
		self.triggered.connect( self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.Open )
		self.setShortcutContext( QtCore.Qt.WidgetWithChildrenShortcut )
		self.setEnabled( False )

	def onItemSelectionChanged( self ):
		entries = self.parent().selectedItems()
		if len( entries) != 1:
			self.setEnabled( False )
			return
		if not isinstance( entries[0], self.parent().getLeafItemClass() ):
			self.setEnabled( False )
			return
		self.setEnabled( True )

	def onTriggered( self, e ):
		name = QtCore.QCoreApplication.translate("TreeHandler", "Edit entry")
		entries = []
		for item in self.parent().selectedItems():
			if isinstance( item, self.parent().getLeafItemClass() ):
				entries.append( item.entryData )
		for entry in entries:
			if isinstance( item, self.parent().getLeafItemClass() ):
				skelType="leaf"
			else:
				skelType="node"
			modul = self.parent().modul
			key = entry["id"]
			widget = lambda: EditWidget( modul, EditWidget.appTree, key, skelType=skelType )
			handler = WidgetHandler( widget, descr=name, icon=QtGui.QIcon("icons/actions/edit_small.png") )
			handler.stackHandler()

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "tree.simple" or modul.startswith("tree.simple.")) and actionName=="edit")
		
actionDelegateSelector.insert( 3, TreeSimpleEditAction.isSuitableFor, TreeSimpleEditAction )


class TreeMkDirAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( TreeMkDirAction, self ).__init__(  QtGui.QIcon("icons/actions/folder_add_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "New directory"), parent )
		self.triggered.connect( self.onTriggered )
		self.setShortcut( "SHIFT+Ctrl+N" )
		self.setShortcutContext( QtCore.Qt.WidgetWithChildrenShortcut )
	
	def onTriggered( self, e ):
		(dirName, okay) = QtGui.QInputDialog.getText( self.parent(), QtCore.QCoreApplication.translate("TreeHandler", "Create directory"), QtCore.QCoreApplication.translate("TreeHandler", "Directory name") )
		if dirName and okay:
			reqWrap = protocolWrapperInstanceSelector.select( self.parent().modul )
			assert reqWrap is not None
			reqWrap.add( self.parent().getNode(), "node", name=dirName )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "tree" or modul.startswith("tree.")) and actionName=="mkdir")
		
actionDelegateSelector.insert( 1, TreeMkDirAction.isSuitableFor, TreeMkDirAction )


class TreeSimpleRenameAction( QtGui.QAction ):
	"""
		Allow renaming directories
	"""
	def __init__(self, parent, *args, **kwargs ):
		super( TreeSimpleRenameAction, self ).__init__(  QtGui.QIcon("icons/actions/rename_small.png"), QtCore.QCoreApplication.translate("TreeHandler", "Rename entry"), parent )
		self.parent().itemSelectionChanged.connect( self.onItemSelectionChanged )
		self.triggered.connect( self.onTriggered )
		self.setShortcut( "F2" )
		self.setShortcutContext( QtCore.Qt.WidgetWithChildrenShortcut )
		self.setEnabled( False )

	def onItemSelectionChanged( self ):
		entries = self.parent().selectedItems()
		if len( entries) != 1:
			self.setEnabled( False )
			return
		if not isinstance( entries[0], self.parent().getNodeItemClass() ):
			self.setEnabled( False )
			return
		self.setEnabled( True )

	def onTriggered( self, e ):
		name = QtCore.QCoreApplication.translate("TreeSimpleRenameAction", "Edit entry")
		entries = self.parent().selectedItems()
		if len( entries) != 1:
			return
		entry = entries[0]
		if not isinstance( entry, self.parent().getNodeItemClass() ): #Cant rename an leaf
			return
		name, res = QtGui.QInputDialog.getText(	self.parent(),
							QtCore.QCoreApplication.translate("TreeSimpleRenameAction", "Rename directory"),
							QtCore.QCoreApplication.translate("TreeSimpleRenameAction", "New name:"),
							text = entry.entryData["name"]
							)
		if not res:
			return #Cancel was clicked
		protpWrap = protocolWrapperInstanceSelector.select( self.parent().modul )
		assert protpWrap is not None
		data = entry.entryData.copy()
		data["name"] = name
		key = data["id"]
		del data["id"]
		protpWrap.edit( key, "node", **data )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( (modul == "tree.simple" or modul.startswith("tree.simple.")) and actionName=="rename")
		
actionDelegateSelector.insert( 3, TreeSimpleRenameAction.isSuitableFor, TreeSimpleRenameAction )
