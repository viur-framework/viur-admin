# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from event import event
from utils import RegisterQueue,  formatString
from handler.list import ListTableModel
from ui.relationalselectionUI import Ui_relationalSelector
from widgets.list import ListWidget, ListTableModel
from widgets.selectedEntities import SelectedEntitiesWidget
from network import NetworkService
from config import conf

class BaseBone:
	pass


class RelationalViewBoneDelegate(QtGui.QStyledItemDelegate):
	cantSort = True
	def __init__(self, structure):
		super(RelationalViewBoneDelegate, self).__init__()
		self.format = "$(name)"
		if "format" in structure.keys():
			self.format = structure["format"]

	def displayText(self, value, locale ):
		return( formatString( self.format, value ) )

class AutocompletionModel( QtCore.QAbstractListModel ):
	def __init__( self,  modul, format, *args, **kwargs ):
		super( AutocompletionModel, self ).__init__( *args, **kwargs )
		self.modul = modul
		self.format = format
		self.dataCache = []
	
	def rowCount(self, *args, **kwargs):
		return( len( self.dataCache ) )
	
	def data(self, index, role): 
		if not index.isValid(): 
			return None
		elif role != QtCore.Qt.ToolTipRole and role != QtCore.Qt.EditRole and role != QtCore.Qt.DisplayRole: 
			return None
		if( index.row() >=0 and index.row()< self.rowCount() ):
			return( formatString( self.format, self.dataCache[ index.row() ] ) )

	def setCompletionPrefix(self, prefix ):
		NetworkService.request("/%s/list" % self.modul, {"name$lk": prefix, "orderby":"name" }, successHandler=self.addCompletionData )
		
	def addCompletionData(self, req ):
		try:
			data = NetworkService.decode( req )
		except ValueError: #Query was canceled
			return
		self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
		self.dataCache = []
		for skel in data["skellist"]:
			self.dataCache.append( skel )
		self.emit(QtCore.SIGNAL("layoutChanged()"))
	
	def getItem(self, label):
		res = [ x for x in self.dataCache if formatString( self.format, x)==label ]
		if len(res):
			return( res[0] )
		return( None )
	

class RelationalEditBone( QtGui.QWidget ):
	def __init__(self, modulName, boneName, skelStructure, *args, **kwargs ):
		super( RelationalEditBone,  self ).__init__( *args, **kwargs )
		self.skelStructure = skelStructure
		self.modulName = modulName
		self.boneName = boneName
		self.toModul = self.skelStructure[ self.boneName ]["type"].split(".")[1]
		if not skelStructure[boneName]["multiple"]:
			self.layout = QtGui.QHBoxLayout( self )
		else:
			self.layout = QtGui.QVBoxLayout( self )
			self.previewWidget = QtGui.QWidget( self )
			self.previewLayout = QtGui.QVBoxLayout( self.previewWidget )
			self.layout.addWidget( self.previewWidget )
		self.addBtn = QtGui.QPushButton( "Auswählen", parent=self )
		iconadd = QtGui.QIcon()
		iconadd.addPixmap(QtGui.QPixmap("icons/actions/relationalselect.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.addBtn.setIcon(iconadd)
		self.addBtn.connect( self.addBtn, QtCore.SIGNAL('released()'), self.on_addBtn_released )
		if not skelStructure[boneName]["multiple"]:
			self.entry = QtGui.QLineEdit( self )
			self.autoCompletionModel = AutocompletionModel( self.toModul, self.skelStructure[ self.boneName ]["format"] )
			self.autoCompleter = QtGui.QCompleter( self.autoCompletionModel )
			self.autoCompleter.setModel( self.autoCompletionModel )
			self.autoCompleter.setCaseSensitivity( QtCore.Qt.CaseInsensitive )
			self.entry.setCompleter( self.autoCompleter )
			self.entry.connect( self.entry, QtCore.SIGNAL('textChanged(QString)'), self.reloadAutocompletion )
			self.autoCompleter.connect( self.autoCompleter, QtCore.SIGNAL('activated(QString)'), self.setAutoCompletion )  #Broken...
			self.autoCompleter.connect( self.autoCompleter, QtCore.SIGNAL('highlighted(QString)'), self.setAutoCompletion ) 
			self.layout.addWidget( self.entry )
			icon6 = QtGui.QIcon()
			icon6.addPixmap(QtGui.QPixmap("icons/actions/relationaldeselect.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
			self.delBtn = QtGui.QPushButton( "", parent=self )
			self.delBtn.setIcon(icon6)
			self.layout.addWidget( self.addBtn )
			self.layout.addWidget( self.delBtn )
			self.delBtn.connect( self.delBtn, QtCore.SIGNAL('released()'), self.on_delBtn_released )
			self.selection = None
		else:
			self.selection = []
			self.layout.addWidget( self.addBtn )
	
	def updateVisiblePreview(self):
		if self.skelStructure[self.boneName]["multiple"]:
			widgetItem = self.previewLayout.takeAt( 0 )
			while widgetItem:
				widgetItem = self.previewLayout.takeAt( 0 )
			if self.selection and len(self.selection)>0:
				for item in self.selection:
					lbl = QtGui.QLabel( self.previewWidget )
					lbl.setText( formatString( self.skelStructure[ self.boneName ]["format"], item ) )
					self.previewLayout.addWidget( lbl )
				self.addBtn.setText("Auswahl ändern")
			else:
				self.addBtn.setText("Auswählen")
		else:
			if self.selection:
				self.entry.setText( formatString( self.skelStructure[ self.boneName ]["format"], self.selection ) )
			else:
				self.entry.setText( "" )

	def reloadAutocompletion(self, text ):
		if text and len(text)>2:
			self.autoCompletionModel.setCompletionPrefix( text )
	
	def setAutoCompletion(self, label ):
		res = self.autoCompletionModel.getItem( label )
		if res:
			self.setSelection( [ res ] )

	def setSelection(self, selection):
		if self.skelStructure[self.boneName]["multiple"]:
			self.selection = selection
		elif len( selection )>0 :
			self.selection = selection[0]
		else:
			self.selection = None
		self.updateVisiblePreview()
	
	def on_addBtn_released(self, *args, **kwargs ):
		queue = RegisterQueue()
		event.emit( QtCore.SIGNAL('requestRelationalBoneSelection(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), queue, self.modulName, self.boneName, self.skelStructure, self.selection, self.setSelection )
		self.editWidget = queue.getBest()()

	def on_delBtn_released(self, *args, **kwargs ):
		if self.skelStructure[ self.boneName ]["multiple"]:
			self.selection = []
		else:
			self.selection = None
		self.updateVisiblePreview()

	def unserialize( self, data ):
		self.selection = data[ self.boneName ]
		self.updateVisiblePreview()

	def serialize(self):
		if not self.selection:
			return( None )
		if self.skelStructure[self.boneName]["multiple"]:
			return( [ str( x["id"] ) for x in self.selection ] )
		elif self.selection:
			return( str( self.selection["id"] ) )
		else:
			return( None )


class BaseRelationalBoneSelector( QtGui.QWidget ):
	""" 	
		FIXME: This claas should derive from hander.List
	"""
	def __init__(self, modulName, boneName, skelStructure, selection, setSelection,  *args, **kwargs ):
		QtGui.QWidget.__init__( self, *args, **kwargs )
		self.modulName = modulName
		self.boneName = boneName
		self.skelStructure = skelStructure
		self.selection = selection
		self.setSelection = setSelection
		self.modul = self.skelStructure[ self.boneName ]["type"].split(".")[1]
		self.page = 0
		self.ui = Ui_relationalSelector()
		self.ui.setupUi( self )
		layout = QtGui.QHBoxLayout( self.ui.tableWidget )
		self.ui.tableWidget.setLayout( layout )
		self.list = ListWidget( self.ui.tableWidget, self.modul )
		layout.addWidget( self.list )
		self.list.show()
		if not self.skelStructure[ self.boneName ]["multiple"]:
			self.multiSelection = False
		else:
			self.multiSelection = True
		layout = QtGui.QHBoxLayout( self.ui.listSelected )
		self.ui.listSelected.setLayout( layout )
		self.selection = SelectedEntitiesWidget( self, self.modul, selection, self.list )
		layout.addWidget( self.selection )
		self.selection.show()
		#self.selectedModel = RelationalSelectedTableModel( self.ui.tableSelected, self.modul,  self.model, self.selection, True  )
		#self.ui.tableSelected.setModel( self.selectedModel )
		#self.tableSelectedselectionModel = self.ui.tableSelected.selectionModel(  )
		#self.ui.tableSelected.keyPressEvent = self.on_tableSelected_keyPressEvent
		if not self.multiSelection:
			self.list.setSelectionMode( self.list.SingleSelection )
			self.selection.hide()
			self.ui.lblSelected.hide()
		#header = self.ui.tableView.horizontalHeader()
		#header.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		#header.customContextMenuRequested.connect(self.tableHeaderContextMenuEvent)
		event.emit( QtCore.SIGNAL('stackWidget(PyQt_PyObject)'), self )
		self.selection.connect( self.list, QtCore.SIGNAL("doubleClicked(const QModelIndex&)"), self.onSourceItemDoubleClicked )

	def onSourceItemDoubleClicked(self, index):
		"""
			An item has been doubleClicked in our listWidget.
			Read its properties and add them to our selection.
		"""
		data = self.list.model().getData()[ index.row() ]
		if self.multiSelection:
			self.selection.extend( [data] )
		if not self.multiSelection:
			self.setSelection( [data] )
			event.emit( QtCore.SIGNAL("popWidget(PyQt_PyObject)"), self )

	def reload(self, newFilter=None):
		if newFilter == None:
			newFilter = self.model().getFilter()
		self.model().setFilter( newFilter )
	
	def reloadData(self ):
		event.emit( QtCore.SIGNAL('dataChanged(PyQt_PyObject,PyQt_PyObject)'), self.modulName, self )
	
	def onDataChanged(self, modulName, emitingEntry):
		if (modulName==self.modul or emitingEntry==self):
			self.reload( )
		
	def on_tableSelected_doubleClicked (self,index):
		self.selectedModel.removeItemAtIndex( index )
		
	def on_tableSelected_keyPressEvent(self, key):
		"""Remove the currently selected Items from the selection"""
		if( key.key()==QtCore.Qt.Key_Delete ):
			selIdx = self.ui.tableSelected.selectedIndexes()
			selIdx.sort( key=lambda x: x.row() )
			selIdx.reverse()
			for index in selIdx:
				self.selectedModel.removeItemAtIndex( index )

	def on_btnSelect_released(self, *args, **kwargs):
		self.setSelection( self.selection.get() )
		event.emit( QtCore.SIGNAL("popWidget(PyQt_PyObject)"), self )

	def on_btnCancel_released(self, *args,  **kwargs ):
		event.emit( QtCore.SIGNAL("popWidget(PyQt_PyObject)"), self )

	def on_editSearch_returnPressed(self):
		self.search()
	
	def on_btnSearch_released(self):
		self.search()
	
	def search(self):
		searchstr=self.ui.editSearch.text()
		filter = self.model().getFilter()
		if searchstr=="" and "search" in filter.keys():
			del filter["search"]
		elif searchstr!="":
			filter["search"]= searchstr
		self.model().setFilter( filter )

class RelationalHandler( QtCore.QObject ):
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('requestBoneViewDelegate(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.onRequestBoneViewDelegate ) #RegisterObj, ModulName, BoneName, SkelStructure
		self.connect( event, QtCore.SIGNAL('requestBoneEditWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.onRequestBoneEditWidget ) 
		self.connect( event, QtCore.SIGNAL('requestRelationalBoneSelection(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.relationalBoneSeletor )
	
	def onRequestBoneViewDelegate(self, registerObject, modulName, boneName, skelStucture):
		if skelStucture[boneName]["type"].startswith("relational."):
			registerObject.registerHandler( 5, lambda: RelationalViewBoneDelegate(skelStucture[boneName]) )

	def onRequestBoneEditWidget(self, registerObject,  modulName, boneName, skelStucture ):
		if skelStucture[boneName]["type"].startswith("relational."):
			registerObject.registerHandler( 10, RelationalEditBone( modulName, boneName, skelStucture ) )

	def relationalBoneSeletor(self, registerObject, modulName, boneName, skelStructure, selection, setSelection ):
		registerObject.registerHandler( 10, lambda: BaseRelationalBoneSelector( modulName, boneName, skelStructure, selection, setSelection ) )

_RelationalHandler = RelationalHandler()
