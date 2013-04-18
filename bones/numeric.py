import sys
from PySide import QtCore, QtGui
from event import event
from bones.base import BaseEditBone
from bones.base import BaseViewBoneDelegate

class NumericViewBoneDelegate( BaseViewBoneDelegate ):
	def displayText(self, value, locale ):
		if self.boneName in self.skelStructure.keys() and "precision" in self.skelStructure[ self.boneName ].keys():
			try:
				if not self.skelStructure[ self.boneName ]["precision"]: #Its an int:
					value = str( int( value ) )
				else:
					value = ("%#."+str( int( self.skelStructure[ self.boneName ]["precision"] ) )+"f" ) % value
			except:
				value = str(value)
		return( super(NumericViewBoneDelegate, self).displayText( value, locale ) )

class NumericEditBone( BaseEditBone ):
	def getLineEdit(self):
		if not isinstance(  self.boneStructure, dict ):
			return( QtGui.QSpinBox( self ) )
		if "precision" in self.boneStructure.keys():
			if self.boneStructure["precision"]:
				spinBox=QtGui.QDoubleSpinBox( self )
				spinBox.setDecimals(self.boneStructure["precision"])
			else: #Just ints
				spinBox=QtGui.QSpinBox( self )
		elif "mode" in self.boneStructure.keys() and self.boneStructure["mode"]=="float": #Old API
			spinBox=QtGui.QDoubleSpinBox( self )
			spinBox.setDecimals(8)
		else:
			spinBox=QtGui.QSpinBox( self )
		if "min" in self.boneStructure.keys() and "max" in self.boneStructure.keys():
			spinBox.setRange(self.boneStructure["min"],self.boneStructure["max"])
		return (spinBox)


	def unserialize(self, data):
		if not self.boneName in data.keys():
			return
		if "precision" in self.boneStructure.keys() and not self.boneStructure["precision"]:
			self.lineEdit.setValue( int( data[ self.boneName ] ) if data[ self.boneName ] else 0 )
		else:
			self.lineEdit.setValue( float ( data[ self.boneName ] ) if data[ self.boneName ] else 0 )
		

	def serialize(self):
		return( str( self.lineEdit.value() ) )

	def serializeForDocument(self):
		return( self.serialize( ) )

class NumericHandler( QtCore.QObject ):
	"""Override the default if we are a numericBone"""
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('requestBoneViewDelegate(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.onRequestBoneViewDelegate ) 
		self.connect( event, QtCore.SIGNAL('requestBoneEditWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.onRequestBoneEditWidget )

	def onRequestBoneEditWidget(self, registerObject,  modulName, boneName, skelStructure ):
		if skelStructure[boneName]["type"]=="numeric":
			registerObject.registerHandler( 10, NumericEditBone( modulName, boneName, skelStructure ) )

	def onRequestBoneViewDelegate(self, registerObject, modulName, boneName, skelStructure ):
		if skelStructure[boneName]["type"]=="numeric":
			registerObject.registerHandler( 5, lambda: NumericViewBoneDelegate(registerObject, modulName, boneName, skelStructure) )

_numericHandler = NumericHandler()
