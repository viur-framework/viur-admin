
from PySide import QtCore, QtGui
from event import event


class BaseViewBoneDelegate(QtGui.QStyledItemDelegate):
	def __init__(self,registerObject, modulName, boneName, skelStructure, *args, **kwargs ):
		super( QtGui.QStyledItemDelegate,self ).__init__()
		self.skelStructure = skelStructure
		self.boneName = boneName
		self.modulName=modulName


class BaseEditBone( QtGui.QWidget ):
	def getLineEdit(self):
		return (QtGui.QLineEdit( self ))
	
	def setParams(self):
		if "readonly" in self.boneStructure.keys() and self.boneStructure["readonly"]:
			self.lineEdit.setReadOnly( True )
		else:
			self.lineEdit.setReadOnly( False )

	def __init__(self, modulName, boneName, skelStructure, *args, **kwargs ):
		super( BaseEditBone,  self ).__init__( *args, **kwargs )
		self.boneStructure=skelStructure[boneName]
		self.boneName = boneName
		self.layout = QtGui.QHBoxLayout( self ) 
		self.lineEdit = self.getLineEdit()
		self.layout.addWidget( self.lineEdit )
		self.setParams()
		self.lineEdit.show()
	
	def unserialize(self, data):
		if self.boneName in data.keys():
			self.lineEdit.setText( str( data[ self.boneName ] ) if data[ self.boneName ] else "" )
	
	def serialize(self):
		return( str( self.lineEdit.displayText() ) )

	def serializeForDocument(self):
		return( self.serialize( ) )
		
class BaseHandler( QtCore.QObject ):
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('requestBoneViewDelegate(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.onRequestBoneViewDelegate ) #RegisterObj, ModulName, BoneName, SkelStructure
		self.connect( event, QtCore.SIGNAL('requestBoneEditWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.onRequestBoneEditWidget )

	def onRequestBoneViewDelegate(self, registerObject, modulName, boneName, skelStructure ):
		registerObject.registerHandler( 0, lambda: BaseViewBoneDelegate(registerObject, modulName, boneName, skelStructure) )

	def onRequestBoneEditWidget(self, registerObject,  modulName, boneName, skelData ):
		registerObject.registerHandler( 0, BaseEditBone( modulName, boneName, skelData ) )

_baseHandler = BaseHandler()
