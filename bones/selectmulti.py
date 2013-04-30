
from PySide import QtCore, QtGui
from event import event

class SelectMultiViewBoneDelegate(QtGui.QStyledItemDelegate):
	def __init__(self,registerObject, modulName, boneName, skelStructure, *args, **kwargs ):
		super( QtGui.QStyledItemDelegate,self ).__init__()
		self.skelStructure = skelStructure
		self.boneName = boneName
		self.modulName=modulName

	def displayText(self, value, locale ):
		boneValues = {str(k): str(v) for k, v in self.skelStructure[ self.boneName ]["values"].items() }
		resStr = ", ".join( [ boneValues[str(x)] for x in value if str(x) in boneValues.keys() ] )
		return( super( SelectMultiViewBoneDelegate, self ).displayText( resStr, locale ) )

class SelectMultiEditBone( QtGui.QWidget ):
	def __init__(self, modulName, boneName, skelStructure, *args, **kwargs ):
		super( SelectMultiEditBone,  self ).__init__( *args, **kwargs )
		self.skelStructure = skelStructure
		self.boneName = boneName
		self.layout = QtGui.QVBoxLayout( self ) 
		self.checkboxes = {}
		if "sortBy" in self.skelStructure[ boneName ].keys():
			sortBy = self.skelStructure[ boneName ][ "sortBy" ]
		else:
			sortBy = "keys"
		tmpList = list( self.skelStructure[ boneName ]["values"].items() )
		if sortBy=="keys":
			tmpList.sort( key=lambda x: x[0] ) #Sort by keys
		else:
			tmpList.sort( key=lambda x: x[1] ) #Values
		for key, descr in tmpList:
			cb = QtGui.QCheckBox( descr, self )
			self.layout.addWidget( cb )
			cb.show()
			self.checkboxes[ key ] = cb

	def unserialize( self, data ):
		if not self.boneName in data.keys():
			return
		for key, checkbox in self.checkboxes.items():
			checkbox.setChecked( key in data[self.boneName] )

	def serializeForPost(self):
		return( { self.boneName: [ key for key, checkbox in self.checkboxes.items() if checkbox.isChecked() ] } )

	def serializeForDocument(self):
		return( self.serialize( ) )

class SelectMultiHandler( QtCore.QObject ):
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('requestBoneViewDelegate(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.onRequestBoneViewDelegate ) #RegisterObj, ModulName, BoneName, SkelStructure
		self.connect( event, QtCore.SIGNAL('requestBoneEditWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.onRequestBoneEditWidget ) 
		
	
	def onRequestBoneViewDelegate(self, registerObject, modulName, boneName, skelStucture):
		if skelStucture[boneName]["type"]=="selectmulti":
			registerObject.registerHandler( 5, lambda: SelectMultiViewBoneDelegate( registerObject, modulName, boneName, skelStucture) )

	def onRequestBoneEditWidget(self, registerObject,  modulName, boneName, skelStucture ):
		if skelStucture[boneName]["type"]=="selectmulti":
			registerObject.registerHandler( 10, SelectMultiEditBone( modulName, boneName, skelStucture ) )

_selectMultiHandler = SelectMultiHandler()
