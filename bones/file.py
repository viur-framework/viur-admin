#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from widgets.file import FileWidget
from bones.treeitem import TreeItemBone, TreeBoneSelector
from priorityqueue import editBoneSelector, viewDelegateSelector
from network import RemoteFile 
from utils import formatString

class FileViewBoneDelegate(QtGui.QStyledItemDelegate):

	cantSort = True
	def __init__(self, modul, boneName, structure):
		super(FileViewBoneDelegate, self).__init__()
		self.format = "$(name)"
		if "format" in structure[boneName].keys():
			self.format = structure[boneName]["format"]
		self.modul = modul
		self.structure = structure
		self.boneName = boneName

	def setImage( self, remoteFile ):
		fn = remoteFile.getFileName( )
		try:
			self.cache[ remoteFile.dlKey ] = QtGui.QImage( fn )
		except:
			pass
		self.emit( QtCore.SIGNAL('repaintRequest()') )
        
	def paint(self, painter, option, index):
		if not "cache" in dir( self ):
			self.cache = {}
		model = index.model()
		try:
			record = model.dataCache[index.row()][ model.fields[index.column()] ]
			if record and isinstance( record, list ) and len( record )>0:
				record = record[0]
		except:
			record = None
		if not record:
			return( super( FileViewBoneDelegate, self ).paint( painter, option, index ) )
		if not record["dlkey"] in self.cache.keys():
			self.cache[ record["dlkey"] ] = None
			RemoteFile( record["dlkey"], successHandler=self.setImage )
			return( super( FileViewBoneDelegate, self ).paint( painter, option, index ) )
		elif not self.cache[ record["dlkey"] ]: #Image not loaded yet
			return( super( FileViewBoneDelegate, self ).paint( painter, option, index ) )
		painter.save()
		painter.drawImage(option.rect, self.cache[ record["dlkey"] ] )
		painter.restore()

	def displayText(self, value, locale ):
		return( formatString( self.format, self.structure, value ) )


class FileItemBone( TreeItemBone ):
	skelType = "leaf"
	def onAddBtnReleased(self, *args, **kwargs ):
		editWidget = FileBoneSelector(self.modulName, self.boneName, self.multiple, self.toModul, self.selection, parent=self )
		editWidget.selectionChanged.connect( self.setSelection )


class FileBoneSelector( TreeBoneSelector ):
	displaySourceWidget = FileWidget


def CheckForFileBone(  modulName, boneName, skelStucture ):
	return( skelStucture[boneName]["type"].startswith("treeitem.file") )


#Register this Bone in the global queue
editBoneSelector.insert( 4, CheckForFileBone, FileItemBone)
viewDelegateSelector.insert( 4, CheckForFileBone, FileViewBoneDelegate)
