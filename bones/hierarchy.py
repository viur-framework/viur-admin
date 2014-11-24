# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets
from event import event
from utils import RegisterQueue, Overlay, formatString
from os import path
from bones.relational import RelationalViewBoneDelegate, RelationalEditBone, RelationalBoneSelector
from widgets.hierarchy import HierarchyWidget
from widgets.selectedEntities import SelectedEntitiesWidget
from priorityqueue import editBoneSelector, viewDelegateSelector

class HierarchyItemViewBoneDelegate( RelationalViewBoneDelegate ):
	pass


class HierarchyItemBone( RelationalEditBone ):
	
	def onAddBtnReleased(self, *args, **kwargs ):
		editWidget = HierarchyBoneSelector(self.modulName, self.boneName, self.multiple, self.toModul, self.selection )
		editWidget.selectionChanged.connect( self.setSelection )
	
	def installAutoCompletion( self ):
		"""
			Prevent installing an autoCompletion for this modul (not implementet yet)
		"""
		if not self.multiple:
			self.entry.setReadOnly( True )
			

class HierarchyBoneSelector( RelationalBoneSelector ):
	displaySourceWidget = HierarchyWidget
	
	def onSourceItemDoubleClicked(self, item):
		"""
			An item has been doubleClicked in our listWidget.
			Read its properties and add them to our selection.
		"""
		data = item.entryData
		if self.multiple:
			self.selection.extend( [data] )
		else:
			self.selectionChanged.emit( [data] )
			event.emit( "popWidget", self )

def CheckForHierarchyItemBone(  modulName, boneName, skelStucture ):
	return( skelStucture[boneName]["type"].startswith("hierarchy.") )
	
	
editBoneSelector.insert( 1, CheckForHierarchyItemBone, HierarchyItemBone)

