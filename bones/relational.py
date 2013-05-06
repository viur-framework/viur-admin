# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from event import event
from utils import RegisterQueue, formatString, Overlay
from ui.relationalselectionUI import Ui_relationalSelector
from widgets.list import ListWidget
from widgets.selectedEntities import SelectedEntitiesWidget
from network import NetworkService
from config import conf
from priorityqueue import editBoneSelector, viewDelegateSelector

class BaseBone:
	pass


class RelationalViewBoneDelegate(QtGui.QStyledItemDelegate):
	cantSort = True
	def __init__(self, structure, boneName):
		super(RelationalViewBoneDelegate, self).__init__()
		self.format = "$(name)"
		if "format" in structure[boneName].keys():
			self.format = structure[boneName]["format"]
		self.structure = structure
		self.boneName = boneName

	def displayText(self, value, locale ):
		return( formatString( self.format, self.structure, value ) )

class AutocompletionModel( QtCore.QAbstractListModel ):
	def __init__( self,  modul, format, structure, *args, **kwargs ):
		super( AutocompletionModel, self ).__init__( *args, **kwargs )
		self.modul = modul
		self.format = format
		self.structure = structure
		self.dataCache = []
	
	def rowCount(self, *args, **kwargs):
		return( len( self.dataCache ) )
	
	def data(self, index, role): 
		if not index.isValid(): 
			return None
		elif role != QtCore.Qt.ToolTipRole and role != QtCore.Qt.EditRole and role != QtCore.Qt.DisplayRole: 
			return None
		if( index.row() >=0 and index.row()< self.rowCount() ):
			return( formatString( self.format, self.structure, self.dataCache[ index.row() ] ) )

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
		res = [ x for x in self.dataCache if formatString( self.format, self.structure, x)==label ]
		if len(res):
			return( res[0] )
		return( None )
	

class RelationalEditBone( QtGui.QWidget ):
	GarbargeTypeName = "RelationalEditBone"

	def __init__(self, modulName, boneName, readOnly, destModul, multiple, format="$(name)", *args, **kwargs ):
		super( RelationalEditBone,  self ).__init__( *args, **kwargs )
		self.modulName =  modulName
		self.boneName = boneName
		self.readOnly = readOnly
		self.toModul = destModul
		self.multiple = multiple
		self.format = format
		self.targetModulStructure = None
		self.overlay = Overlay( self )
		if not self.multiple:
			self.layout = QtGui.QHBoxLayout( self )
		else:
			self.layout = QtGui.QVBoxLayout( self )
			self.previewWidget = QtGui.QWidget( self )
			self.previewLayout = QtGui.QVBoxLayout( self.previewWidget )
			self.layout.addWidget( self.previewWidget )
		self.addBtn = QtGui.QPushButton( QtCore.QCoreApplication.translate("RelationalEditBone", "Change selection"), parent=self )
		iconadd = QtGui.QIcon()
		iconadd.addPixmap(QtGui.QPixmap("icons/actions/relationalselect.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.addBtn.setIcon(iconadd)
		self.addBtn.connect( self.addBtn, QtCore.SIGNAL('released()'), self.on_addBtn_released )
		if not self.multiple:
			self.entry = QtGui.QLineEdit( self )
			self.autoCompletionModel = AutocompletionModel( self.toModul, format, {} ) #FIXME: {} was self.skelStructure
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
		NetworkService.request( "/%s/list?amount=1" % self.toModul, successHandler=self.onTargetModulStructureAvaiable ) #Fetch the structure of our referenced modul
		self.overlay.inform( self.overlay.BUSY )
		

	@staticmethod
	def fromSkelStructure( modulName, boneName, skelStructure ):
		readOnly = "readonly" in skelStructure[ boneName ].keys() and skelStructure[ boneName ]["readonly"]
		multiple = skelStructure[boneName]["multiple"]
		destModul = skelStructure[ boneName ]["type"].split(".")[1]
		format= "$(name)"
		if "format" in skelStructure[ boneName ].keys():
			format = skelStructure[ boneName ]["format"]
		return( RelationalEditBone( modulName, boneName, readOnly, multiple=multiple, destModul=destModul, format=format ) )

	def onTargetModulStructureAvaiable( self, req ):
		data = NetworkService.decode( req )
		self.targetModulStructure = data["structure"]
		self.updateVisiblePreview()
		self.overlay.clear()

	def updateVisiblePreview(self):
		if self.targetModulStructure is None:
			return
		if self.multiple:
			widgetItem = self.previewLayout.takeAt( 0 )
			while widgetItem:
				widgetItem = self.previewLayout.takeAt( 0 )
			if self.selection and len(self.selection)>0:
				for item in self.selection:
					lbl = QtGui.QLabel( self.previewWidget )
					lbl.setText( formatString( self.format, self.targetModulStructure, item ) ) 
					self.previewLayout.addWidget( lbl )
				self.addBtn.setText("Auswahl ändern")
			else:
				self.addBtn.setText("Auswählen")
		else:
			if self.selection:
				print( self.selection )
				self.entry.setText( formatString( self.format, self.targetModulStructure, self.selection ) )
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
		if self.multiple:
			self.selection = selection
		elif len( selection )>0 :
			self.selection = selection[0]
		else:
			self.selection = None
		event.emit( QtCore.SIGNAL("popWidget(PyQt_PyObject)"), self.editWidget )
		self.editWidget = None
		self.updateVisiblePreview()
	
	def on_addBtn_released(self, *args, **kwargs ):
		#queue = RegisterQueue()
		#event.emit( QtCore.SIGNAL('requestRelationalBoneSelection(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), queue, self.modulName, self.boneName, self.skelStructure, self.selection, self.setSelection )
		self.editWidget = BaseRelationalBoneSelector(self.modulName, self.boneName, self.multiple, self.toModul, self.selection )
		self.connect( self.editWidget, QtCore.SIGNAL("selectionChanged(PyQt_PyObject)"), self.setSelection )
		#self.editWidget = queue.getBest()()

	def on_delBtn_released(self, *args, **kwargs ):
		if self.multiple:
			self.selection = []
		else:
			self.selection = None
		self.updateVisiblePreview()

	def unserialize( self, data ):
		self.selection = data[ self.boneName ]
		self.updateVisiblePreview()

	def serializeForPost(self):
		if not self.selection:
			return( { self.boneName:None } )
		if self.multiple:
			return( { self.boneName: [ str( x["id"] ) for x in self.selection ] } )
		elif self.selection:
			return( { self.boneName: str( self.selection["id"] ) } )
		else:
			return( { self.boneName: None } )


class BaseRelationalBoneSelector( QtGui.QWidget ):
	""" 	
		FIXME: This claas should derive from hander.List
	"""
	GarbargeTypeName = "BaseRelationalBoneSelector"
	def __init__(self, modulName, boneName, multiple, toModul, selection, *args, **kwargs ):
		QtGui.QWidget.__init__( self, *args, **kwargs )
		self.modulName = modulName
		self.boneName = boneName
		self.multiple = multiple
		self.modul = toModul
		self.selection = selection
		self.page = 0
		self.ui = Ui_relationalSelector()
		self.ui.setupUi( self )
		layout = QtGui.QHBoxLayout( self.ui.tableWidget )
		self.ui.tableWidget.setLayout( layout )
		self.list = ListWidget( self.ui.tableWidget, self.modul )
		layout.addWidget( self.list )
		self.list.show()
		layout = QtGui.QHBoxLayout( self.ui.listSelected )
		self.ui.listSelected.setLayout( layout )
		self.selection = SelectedEntitiesWidget( self, self.modul, selection, self.list )
		layout.addWidget( self.selection )
		self.selection.show()
		#self.selectedModel = RelationalSelectedTableModel( self.ui.tableSelected, self.modul,  self.model, self.selection, True  )
		#self.ui.tableSelected.setModel( self.selectedModel )
		#self.tableSelectedselectionModel = self.ui.tableSelected.selectionModel(  )
		#self.ui.tableSelected.keyPressEvent = self.on_tableSelected_keyPressEvent
		if not self.multiple:
			self.list.setSelectionMode( self.list.SingleSelection )
			self.selection.hide()
			self.ui.lblSelected.hide()
		#header = self.ui.tableView.horizontalHeader()
		#header.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		#header.customContextMenuRequested.connect(self.tableHeaderContextMenuEvent)
		event.emit( QtCore.SIGNAL('stackWidget(PyQt_PyObject)'), self )
		self.connect( self.list, QtCore.SIGNAL("doubleClicked(const QModelIndex&)"), self.onSourceItemDoubleClicked )

	def onSourceItemDoubleClicked(self, index):
		"""
			An item has been doubleClicked in our listWidget.
			Read its properties and add them to our selection.
		"""
		data = self.list.model().getData()[ index.row() ]
		if self.multiple:
			self.selection.extend( [data] )
		if not self.multiple:
			self.emit( QtCore.SIGNAL("selectionChanged(PyQt_PyObject)"), [data] )
			#self.setSelection( [data] )
			#event.emit( QtCore.SIGNAL("popWidget(PyQt_PyObject)"), self )

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
		self.emit( QtCore.SIGNAL("selectionChanged(PyQt_PyObject)"), self.selection.get() )
		#self.setSelection( self.selection.get() )
		#event.emit( QtCore.SIGNAL("popWidget(PyQt_PyObject)"), self )

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


def CheckForRelationalicBone(  modulName, boneName, skelStucture ):
	return( skelStucture[boneName]["type"].startswith("relational.") )

#Register this Bone in the global queue
editBoneSelector.insert( 2, CheckForRelationalicBone, RelationalEditBone)
viewDelegateSelector.insert( 2, CheckForRelationalicBone, RelationalViewBoneDelegate)

