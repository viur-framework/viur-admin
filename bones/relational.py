# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets
from event import event
from utils import RegisterQueue, formatString, Overlay, WidgetHandler
from ui.relationalselectionUI import Ui_relationalSelector
from widgets.list import ListWidget
from widgets.edit import EditWidget
from widgets.selectedEntities import SelectedEntitiesWidget
from network import NetworkService
from config import conf
from priorityqueue import editBoneSelector, viewDelegateSelector
from priorityqueue import protocolWrapperInstanceSelector

class BaseBone:
	pass


class RelationalViewBoneDelegate(QtWidgets.QStyledItemDelegate):
	cantSort = True
	def __init__(self, modul, boneName, structure):
		super(RelationalViewBoneDelegate, self).__init__()
		self.format = "$(name)"
		if "format" in structure[boneName].keys():
			self.format = structure[boneName]["format"]
		self.modul = modul
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
		self.layoutAboutToBeChanged.emit()
		self.dataCache = []
		for skel in data["skellist"]:
			self.dataCache.append( skel )
		self.layoutChanged.emit()
	
	def getItem(self, label):
		res = [ x for x in self.dataCache if formatString( self.format, self.structure, x)==label ]
		if len(res):
			return( res[0] )
		return( None )
	

class RelationalEditBone( QtWidgets.QWidget ):
	GarbargeTypeName = "RelationalEditBone"
	skelType = None

	def __init__(self, modulName, boneName, readOnly, destModul, multiple, format="$(name)", *args, **kwargs ):
		super( RelationalEditBone,  self ).__init__( *args, **kwargs )
		self.modulName =  modulName
		self.boneName = boneName
		self.readOnly = readOnly
		self.toModul = destModul
		self.multiple = multiple
		self.format = format
		self.overlay = Overlay( self )
		if not self.multiple:
			self.layout = QtGui.QHBoxLayout( self )
		else:
			self.layout = QtGui.QVBoxLayout( self )
			self.previewWidget = QtWidgets.QWidget( self )
			self.previewLayout = QtGui.QVBoxLayout( self.previewWidget )
			self.layout.addWidget( self.previewWidget )
		self.addBtn = QtGui.QPushButton( QtCore.QCoreApplication.translate("RelationalEditBone", "Change selection"), parent=self )
		iconadd = QtGui.QIcon()
		iconadd.addPixmap(QtGui.QPixmap("icons/actions/change_selection.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.addBtn.setIcon(iconadd)
		self.addBtn.released.connect( self.onAddBtnReleased )
		if not self.multiple:
			self.entry = QtGui.QLineEdit( self )
			self.installAutoCompletion()
			self.layout.addWidget( self.entry )
			icon6 = QtGui.QIcon()
			icon6.addPixmap(QtGui.QPixmap("icons/actions/cancel.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
			self.delBtn = QtGui.QPushButton( "", parent=self )
			self.delBtn.setIcon(icon6)
			self.delBtn.released.connect( self.onDelBtnReleased )
			self.layout.addWidget( self.addBtn )
			self.layout.addWidget( self.delBtn )
			self.selection = None
		else:
			self.selection = []
			self.layout.addWidget( self.addBtn )
		

	@classmethod
	def fromSkelStructure( cls, modulName, boneName, skelStructure ):
		readOnly = "readonly" in skelStructure[ boneName ].keys() and skelStructure[ boneName ]["readonly"]
		multiple = skelStructure[boneName]["multiple"]
		if "modul" in skelStructure[ boneName ].keys():
			destModul = skelStructure[ boneName ][ "modul" ]
		else:
			destModul = skelStructure[ boneName ]["type"].split(".")[1]
		format= "$(name)"
		if "format" in skelStructure[ boneName ].keys():
			format = skelStructure[ boneName ]["format"]
		return( cls( modulName, boneName, readOnly, multiple=multiple, destModul=destModul, format=format ) )

	def installAutoCompletion( self ):
		"""
			Installs our autoCompleter on self.entry if possible
		"""
		if not self.multiple:
			self.autoCompletionModel = AutocompletionModel( self.toModul, format, {} ) #FIXME: {} was self.skelStructure
			self.autoCompleter = QtGui.QCompleter( self.autoCompletionModel )
			self.autoCompleter.setModel( self.autoCompletionModel )
			self.autoCompleter.setCaseSensitivity( QtCore.Qt.CaseInsensitive )
			self.entry.setCompleter( self.autoCompleter )
			self.entry.textChanged.connect( self.reloadAutocompletion )
			self.autoCompleter.activated.connect( self.setAutoCompletion )  #Broken...
			self.autoCompleter.highlighted.connect( self.setAutoCompletion ) 

	def updateVisiblePreview(self):
		protoWrap = protocolWrapperInstanceSelector.select( self.toModul )
		assert protoWrap is not None
		if self.skelType is None:
			structure = protoWrap.viewStructure
		elif self.skelType=="leaf":
			structure = protoWrap.viewLeafStructure
		elif self.skelType=="node":
			structure = protoWrap.viewNodeStructure
		if structure is None:
			return
		if self.multiple:
			widgetItem = self.previewLayout.takeAt( 0 )
			while widgetItem:
				widgetItem = self.previewLayout.takeAt( 0 )
			if self.selection and len(self.selection)>0:
				for item in self.selection:
					lbl = QtGui.QLabel( self.previewWidget )
					lbl.setText( formatString( self.format, structure, item ) ) 
					self.previewLayout.addWidget( lbl )
				self.addBtn.setText("Auswahl ändern")
			else:
				self.addBtn.setText("Auswählen")
		else:
			if self.selection:
				self.entry.setText( formatString( self.format, structure, self.selection ) )
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
		self.updateVisiblePreview()
	
	def onAddBtnReleased(self, *args, **kwargs ):
		editWidget = RelationalBoneSelector(self.modulName, self.boneName, self.multiple, self.toModul, self.selection )
		editWidget.selectionChanged.connect( self.setSelection )

	def onDelBtnReleased(self, *args, **kwargs ):
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


class RelationalBoneSelector( QtWidgets.QWidget ):
	
	selectionChanged = QtCore.pyqtSignal( (object, ) )
	displaySourceWidget = ListWidget
	displaySelectionWidget = SelectedEntitiesWidget
	GarbargeTypeName = "RelationalBoneSelector"
	
	def __init__(self, modulName, boneName, multiple, toModul, selection, *args, **kwargs ):
		super( RelationalBoneSelector, self ).__init__( *args, **kwargs )
		self.modulName = modulName
		self.boneName = boneName
		self.multiple = multiple
		self.modul = toModul
		self.selection = selection
		self.ui = Ui_relationalSelector()
		self.ui.setupUi( self )
		layout = QtGui.QHBoxLayout( self.ui.tableWidget )
		self.ui.tableWidget.setLayout( layout )
		self.list = self.displaySourceWidget( self.modul, editOnDoubleClick=False, parent=self )
		layout.addWidget( self.list )
		self.list.show()
		layout = QtGui.QHBoxLayout( self.ui.listSelected )
		self.ui.listSelected.setLayout( layout )
		self.selection = self.displaySelectionWidget( self.modul, selection, parent=self )
		layout.addWidget( self.selection )
		self.selection.show()
		if not self.multiple:
			#self.list.setSelectionMode( self.list.SingleSelection )
			self.selection.hide()
			self.ui.lblSelected.hide()
		self.list.itemDoubleClicked.connect( self.onSourceItemDoubleClicked )
		self.ui.btnSelect.clicked.connect( self.onBtnSelectReleased )
		self.ui.btnCancel.clicked.connect( self.onBtnCancelReleased )
		event.emit( 'stackWidget', self )

	def getBreadCrumb( self ):
		protoWrap = protocolWrapperInstanceSelector.select( self.modulName )
		assert protoWrap is not None
		#FIXME: Bad hack to get the editWidget we belong to
		for widget in WidgetHandler.mainWindow.handlerForWidget( self ).widgets:
			if isinstance( widget, EditWidget ):
				if (not widget.key) or widget.clone: #We're adding a new entry
					if widget.skelType=="leaf":
						skel = protoWrap.addLeafStructure
					elif widget.skelType=="node":
						skel = protoWrap.addNodeStructure
					else:
						skel = protoWrap.addStructure
				else:
					if widget.skelType=="leaf":
						skel = protoWrap.editLeafStructure
					elif widget.skelType=="node":
						skel = protoWrap.editNodeStructure
					else:
						skel = protoWrap.editStructure
		assert skel is not None
		assert self.boneName in skel.keys()
		return( QtCore.QCoreApplication.translate("RelationalBoneSelector", "Select %s") % skel[ self.boneName ]["descr"], QtGui.QIcon( "icons/actions/change_selection.svg" ) )


	def onSourceItemDoubleClicked(self, item):
		"""
			An item has been doubleClicked in our listWidget.
			Read its properties and add them to our selection.
		"""
		data = item
		if self.multiple:
			self.selection.extend( [data] )
		else:
			self.selectionChanged.emit( [data] )
			event.emit( "popWidget", self )

	def onBtnSelectReleased(self, *args, **kwargs):
		self.selectionChanged.emit( self.selection.get() )
		event.emit( "popWidget", self )

	def onBtnCancelReleased(self, *args,  **kwargs ):
		event.emit( "popWidget", self )

	def getFilter( self ):
		return( self.list.getFilter() )
	
	def setFilter( self, filter ):
		return( self.list.setFilter( filter ) )
	
	def getModul( self ):
		return( self.list.getModul() )


def CheckForRelationalicBone(  modulName, boneName, skelStucture ):
	return( skelStucture[boneName]["type"].startswith("relational.") )

#Register this Bone in the global queue
editBoneSelector.insert( 2, CheckForRelationalicBone, RelationalEditBone)
viewDelegateSelector.insert( 2, CheckForRelationalicBone, RelationalViewBoneDelegate)

