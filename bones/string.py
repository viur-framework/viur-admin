from PyQt4 import QtCore, QtGui
from event import event
from bones.base import BaseViewBoneDelegate

class StringViewBoneDelegate( BaseViewBoneDelegate ):
	def displayText(self, value, locale ):
		if self.boneName in self.skelStructure.keys() and "multiple" in self.skelStructure[ self.boneName ].keys() and self.skelStructure[ self.boneName ]["multiple"]:
			value = ", ".join( value )
		return( super(StringViewBoneDelegate, self).displayText( value, locale ) )

class Tag( QtGui.QWidget ):
	def __init__( self, tag, editMode, *args, **kwargs ):
		super( Tag,  self ).__init__( *args, **kwargs )
		self.layout = QtGui.QHBoxLayout( self )
		self.tag = tag
		self.lblDisplay = QtGui.QLabel( tag, self )
		self.editField = QtGui.QLineEdit( tag, self )
		self.btnDelete = QtGui.QPushButton( "Löschen", self )
		self.layout.addWidget( self.lblDisplay )
		self.layout.addWidget( self.editField )
		self.layout.addWidget( self.btnDelete )
		if editMode:
			self.lblDisplay.hide()
			self.editField.show()
		else:
			self.lblDisplay.show()
			self.editField.hide()
		self.connect( self.editField, QtCore.SIGNAL("editingFinished()"), self.onEditingFinished )
		self.connect( self.btnDelete, QtCore.SIGNAL("released()"), lambda *args, **kwargs: self.deleteLater() )
		self.lblDisplay.mousePressEvent = self.onEdit
	
	def onEdit( self, *args, **kwargs ):
		self.lblDisplay.hide()
		self.editField.show()
		self.editField.setFocus()
	
	def onEditingFinished( self, *args, **kwargs ):
		self.tag = self.editField.text()
		self.lblDisplay.setText( self.tag )
		self.lblDisplay.show()
		self.editField.hide()

class StringEditBone( QtGui.QWidget ):
	def __init__(self, modulName, boneName, skelStructure, *args, **kwargs ):
		super( StringEditBone,  self ).__init__( *args, **kwargs )
		self.skelStructure = skelStructure
		self.boneName = boneName
		self.layout = QtGui.QVBoxLayout( self ) 
		self.btnAdd = QtGui.QPushButton( "Hinzufügen", self )
		self.layout.addWidget( self.btnAdd )
		self.connect( self.btnAdd, QtCore.SIGNAL("released()"), lambda *args, **kwargs: self.genTag("",True) )
		self.btnAdd.show()

	def unserialize( self, data ):
		if not self.boneName in data.keys():
			return
		data = data[ self.boneName ]
		if not data:
			return
		if isinstance( data,list ):
			for tagStr in data:
				self.genTag( tagStr )
		else:
			self.genTag( data )

	def serialize(self):
		res = []
		for child in self.children():
			if isinstance( child, Tag ):
				res.append( child.tag )
		return( res )

	def serializeForDocument(self):
		return( self.serialize( ) )

	def genTag( self, tag, editMode=False ):
		self.layout.addWidget( Tag( tag, editMode ) )


class StringHandler( QtCore.QObject ):
	"""Override the default if we are a selectMulti String Bone"""
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('requestBoneViewDelegate(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.onRequestBoneViewDelegate ) #RegisterObj, ModulName, BoneName, SkelStructure
		self.connect( event, QtCore.SIGNAL('requestBoneEditWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.onRequestBoneEditWidget )

	def onRequestBoneViewDelegate(self, registerObject, modulName, boneName, skelStructure ):
		if skelStructure[boneName]["type"]=="str" and skelStructure[boneName]["multiple"]:
			registerObject.registerHandler( 5, lambda: StringViewBoneDelegate(registerObject, modulName, boneName, skelStructure) )

	def onRequestBoneEditWidget(self, registerObject,  modulName, boneName, skelStructure ):
		if skelStructure[boneName]["type"]=="str" and skelStructure[boneName]["multiple"]:
			registerObject.registerHandler( 10, StringEditBone( modulName, boneName, skelStructure ) )

_stringHandler = StringHandler()
