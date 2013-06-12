#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from widgets.file import FileWidget
from bones.treeitem import TreeItemBone, TreeBoneSelector

from priorityqueue import editBoneSelector


class FileItemBone( TreeItemBone ):
	skelType = "leaf"
	def onAddBtnReleased(self, *args, **kwargs ):
		self.editWidget = FileBoneSelector(self.modulName, self.boneName, self.multiple, self.toModul, self.selection )
		self.editWidget.selectionChanged.connect( self.setSelection )


class FileBoneSelector( TreeBoneSelector ):
	displaySourceWidget = FileWidget


	
	

def CheckForFileBone(  modulName, boneName, skelStucture ):
	return( skelStucture[boneName]["type"].startswith("treeitem.file") )
	
	
editBoneSelector.insert( 4, CheckForFileBone, FileItemBone)