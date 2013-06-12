# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from event import event
from utils import RegisterQueue, Overlay, formatString
from ui.relationalselectionUI import Ui_relationalSelector
from ui.treeselectorUI import Ui_TreeSelector
from os import path
from bones.relational import RelationalViewBoneDelegate, RelationalEditBone, RelationalBoneSelector
from widgets.tree import TreeWidget
from widgets.selectedEntities import SelectedEntitiesWidget
from priorityqueue import editBoneSelector, viewDelegateSelector

class TreeItemViewBoneDelegate( RelationalViewBoneDelegate ):
	pass


class TreeItemBone( RelationalEditBone ):
	skelType = "leaf"
	def onAddBtnReleased(self, *args, **kwargs ):
		self.editWidget = TreeBoneSelector(self.modulName, self.boneName, self.multiple, self.toModul, self.selection )
		self.editWidget.selectionChanged.connect( self.setSelection )

class TreeSelectedEntities( SelectedEntitiesWidget ):
	skelType = "leaf"

class TreeBoneSelector( RelationalBoneSelector ):
	displaySourceWidget = TreeWidget
	displaySelectionWidget = TreeSelectedEntities
	
	def onSourceItemDoubleClicked(self, item):
		"""
			An item has been doubleClicked in our listWidget.
			Read its properties and add them to our selection.
		"""
		if not isinstance( item, self.list.getLeafItemClass() ):
			return
		data = item.entryData
		if self.multiple:
			self.selection.extend( [data] )
		else:
			self.selectionChanged.emit( [data] )


def CheckForTreeItemBone(  modulName, boneName, skelStucture ):
	return( skelStucture[boneName]["type"].startswith("treeitem.") )
	
	
editBoneSelector.insert( 1, CheckForTreeItemBone, TreeItemBone)

