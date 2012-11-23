
from PyQt4 import QtCore, QtGui
from event import event
from bones.base import BaseViewBoneDelegate

class SelectOneViewBoneDelegate(BaseViewBoneDelegate):
	def gettext(self,data):
		items = dict( [(str(k), str(v)) for k, v in self.skelStructure[ self.boneName ]["values"].items() ] )
		if str(data) in items.keys():
			return ( items[str(data)])
		else:
			return("")

class SelectOneEditBone( QtGui.QWidget ):
	def __init__(self, modulName, boneName, skelStructure, *args, **kwargs ):
		super( SelectOneEditBone,  self ).__init__( *args, **kwargs )
		self.skelStructure = skelStructure
		self.boneName = boneName
		self.layout = QtGui.QVBoxLayout( self ) 
		self.comboBox = QtGui.QComboBox( self )
		self.layout.addWidget( self.comboBox )
		self.comboBox.addItems( [x for x in self.skelStructure[ self.boneName ]["values"].values() ] )

	def unserialize( self, data ):
		try: #There might be junk comming from the server
			items = dict( [(str(k), str(v)) for k, v in self.skelStructure[ self.boneName ]["values"].items() ] )
			if str(data[ self.boneName]) in items.keys():
				self.comboBox.setCurrentIndex( self.comboBox.findText( items[ str(data[ self.boneName]) ] ) )
			else:
				self.comboBox.setCurrentIndex(-1)
		except:
			self.comboBox.setCurrentIndex(-1)

	def serialize(self):
		for key, value in self.skelStructure[ self.boneName ]["values"].items():
			if str(value) == str( self.comboBox.currentText() ):
				return( str(key) )
		return( None )
		
	def serializeForDocument(self):
		return( self.serialize( ) )

class SelectOneHandler( QtCore.QObject ):
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('requestBoneViewDelegate(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.onRequestBoneViewDelegate ) #RegisterObj, ModulName, BoneName, SkelStructure
		self.connect( event, QtCore.SIGNAL('requestBoneEditWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.onRequestBoneEditWidget )
	
	def onRequestBoneViewDelegate(self, registerObject, modulName, boneName, skelStucture):
		if skelStucture[boneName]["type"]=="selectone":
			registerObject.registerHandler( 10, lambda: SelectOneViewBoneDelegate(registerObject,modulName, boneName, skelStucture) )

	def onRequestBoneEditWidget(self, registerObject,  modulName, boneName, skelStucture ):
		if skelStucture[boneName]["type"]=="selectone":
			registerObject.registerHandler( 10, SelectOneEditBone( modulName, boneName, skelStucture ) )

_selectOneHandler = SelectOneHandler()
