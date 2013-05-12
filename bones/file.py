#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PySide import QtCore, QtGui
from event import event
from utils import RegisterQueue
from network import RemoteFile
from handler.file import  FileItem
from bones.treeitem import BaseTreeItemBoneSelector, TreeItemEditBone
from widgets.file import FileWidget
from widgets.selectedFiles import SelectedFilesWidget
from ui.treeselectorUI import Ui_TreeSelector
from os import path
from priorityqueue import editBoneSelector, viewDelegateSelector

def formatBoneDescr( data ):
	if data and "name" in data.keys():
		return( str( data["name"] ) )
	else:
		return( "" )

class FileViewBoneDelegate(QtGui.QStyledItemDelegate):

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
			return
		if not record["dlkey"] in self.cache.keys():
			self.cache[ record["dlkey"] ] = None
			RemoteFile( record["dlkey"], successHandler=self.setImage )
			return
		elif not self.cache[ record["dlkey"] ]: #Image not loaded yet
			return
		painter.save()
		painter.drawImage(option.rect, self.cache[ record["dlkey"] ] )
		painter.restore()


class FileEditBone( TreeItemEditBone ):
	treeItem = FileItem
	def __init__(self, modulName, boneName, readOnly, multiple, destModul, format="$(name)",  *args, **kwargs ):
		QtGui.QWidget.__init__( self )
		self.modulName = modulName
		self.boneName = boneName
		self.toModul = destModul
		self.format = format
		if "format" in skelStructure[ boneName ].keys():
			self.format = skelStructure[ boneName ]["format"]
		self.layout = QtGui.QVBoxLayout( self )
		self.listWidget = QtGui.QListWidget( self )
		self.listWidget.setViewMode( QtGui.QListView.IconMode )
		self.listWidget.setGridSize( QtCore.QSize( 128, 128 ) )
		self.listWidget.setIconSize( QtCore.QSize( 96, 96 ) )
		self.listWidget.setWordWrap( True )
		self.layout.addWidget( self.listWidget )
		self.w = QtGui.QWidget()
		hlayout = QtGui.QHBoxLayout( self.w )
		self.addBtn = QtGui.QPushButton( QtCore.QCoreApplication.translate("FileBone", "Change selection"), parent=self )
		iconadd = QtGui.QIcon()
		iconadd.addPixmap(QtGui.QPixmap("icons/actions/relationalselect.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.addBtn.setIcon(iconadd)
		self.addBtn.connect( self.addBtn, QtCore.SIGNAL('released()'), self.on_addBtn_released )
		if not self.multiple:
			self.listWidget.hide()
			self.entry = QtGui.QLineEdit( self )
			self.entry.setReadOnly(True)
			#self.entry.mouseMoveEvent = self.showSingleFilePreview
			hlayout.addWidget( self.entry )
			icon6 = QtGui.QIcon()
			icon6.addPixmap(QtGui.QPixmap("icons/actions/relationaldeselect.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
			self.delBtn = QtGui.QPushButton( "", parent=self )
			self.delBtn.setIcon(icon6)
			hlayout.addWidget( self.addBtn )
			hlayout.addWidget( self.delBtn )
			self.delBtn.connect( self.delBtn, QtCore.SIGNAL('released()'), self.on_delBtn_released )
			self.selection = None
		else:
			hlayout.addWidget( self.addBtn )
			self.selection = []
		self.layout.addWidget( self.w )
	
	@staticmethod
	def fromSkelStructure( modulName, boneName, skelStructure ):
		readOnly = "readonly" in skelStructure[ boneName ].keys() and skelStructure[ boneName ]["readonly"]
		multiple = skelStructure[boneName]["multiple"]
		destModul = skelStructure[ boneName ]["type"].split(".")[1]
		format= "$(name)"
		if "format" in skelStructure[ boneName ].keys():
			format = skelStructure[ boneName ]["format"]
		return( FileEditBone( modulName, boneName, readOnly, multiple=multiple, destModul=destModul, format=format ) )
	
	def onToolTipAvaiable(self, remoteFile):
		"""
			Called, as soon the File displayed inside the Tooltip is ready
		"""
		self.entry.setToolTip("<img src=\"%s\" width=\"200\" height=\"200\"><br>%s" % ( remoteFile.getFileName( ), str( self.selection["name"] ) ) )
	

	def unserialize( self, *args, **kwargs ):
		super( FileEditBone, self ).unserialize( *args, **kwargs )
		self.updatePreview()
	
	
	def setSelection( self, *args, **kwargs ):
		super( FileEditBone, self ).setSelection( *args, **kwargs )
		self.updatePreview()
		
	def updatePreview( self ):
		if self.multiple and isinstance( self.selection, list ):
			self.listWidget.clear()
			for item in self.selection:
				fi = FileItem( item )
				self.listWidget.addItem( fi )
			self.listWidget.reset()
		elif isinstance( self.selection, dict ):
			self.entry.setText( self.selection["name"] )
			RemoteFile( self.selection["dlkey"], successHandler=self.onToolTipAvaiable )

class BaseFileBoneSelector( BaseTreeItemBoneSelector ):
	treeItem = FileItem
	
	def __init__(self, modulName, boneName, skelStructure, selection, setSelection, parent=None, widget=None, *args, **kwargs ):
		super( BaseFileBoneSelector, self ).__init__( modulName, boneName, skelStructure, selection, setSelection, parent, widget = FileWidget, *args, **kwargs )
		self.selection.deleteLater()
		self.selection = SelectedFilesWidget( self, self.modul, selection )
		self.ui.listSelected.layout().addWidget( self.selection )
		self.selection.show()
	
	def getBreadCrumb( self ):
		return( QtCore.QCoreApplication.translate("FileBone", "Select file"), QtGui.QIcon( QtGui.QPixmap( "icons/actions/relationalselect.png" ) ) )
		


def CheckForFileBone(  modulName, boneName, skelStucture ):
	return( skelStucture[boneName]["type"]=="treeitem.file" )

#Register this Bone in the global queue
editBoneSelector.insert( 2, CheckForFileBone, FileEditBone)
viewDelegateSelector.insert( 2, CheckForFileBone, FileViewBoneDelegate)
