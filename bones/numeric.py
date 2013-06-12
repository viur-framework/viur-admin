#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt4 import QtCore, QtGui
from event import event
from bones.base import BaseEditBone
from bones.base import BaseViewBoneDelegate
from priorityqueue import editBoneSelector, viewDelegateSelector
from math import pow

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

	def __init__( self, modulName, boneName, readOnly, precision=0, min=-pow(2,30), max=pow(2,30), *args, **kwargs ):
		self.precision = precision #Needed for getLineEdit
		self.min = min
		self.max = max
		super( NumericEditBone, self ).__init__( modulName, boneName, readOnly )

	@staticmethod
	def fromSkelStructure( modulName, boneName, skelStructure ):
		readOnly = "readonly" in skelStructure[ boneName ].keys() and skelStructure[ boneName ]["readonly"]
		precision = int( skelStructure[ boneName ]["precision"] ) if "precision" in skelStructure[boneName].keys() else 0
		if "min" in skelStructure[ boneName ].keys() and "max" in skelStructure[ boneName ].keys():
			minVal = skelStructure[ boneName ]["min"]
			maxVal = skelStructure[ boneName ]["max"]
		else:
			minVal = -pow(2,30)
			maxVal = pow(2,30)
		return( NumericEditBone( modulName, boneName, readOnly, precision=precision, min=minVal, max=maxVal ) ) 

	def getLineEdit(self):
		if self.precision:
			spinBox=QtGui.QDoubleSpinBox( self )
			spinBox.setDecimals( self.precision )
		else: #Just ints
			spinBox=QtGui.QSpinBox( self )
		spinBox.setRange( self.min , self.max)
		return (spinBox)

#		if "min" in self.boneStructure.keys() and "max" in self.boneStructure.keys():


	def unserialize(self, data):
		if not self.boneName in data.keys():
			return
		if not self.precision:
			self.lineEdit.setValue( int( data[ self.boneName ] ) if data[ self.boneName ] else 0 )
		else:
			self.lineEdit.setValue( float ( data[ self.boneName ] ) if data[ self.boneName ] else 0 )
		

	def serializeForPost(self):
		return( { self.boneName: str( self.lineEdit.value() ) } )

	def serializeForDocument(self):
		return( self.serialize( ) )


def CheckForNumericBone(  modulName, boneName, skelStucture ):
	return( skelStucture[boneName]["type"]=="numeric" )

#Register this Bone in the global queue
editBoneSelector.insert( 2, CheckForNumericBone, NumericEditBone)
viewDelegateSelector.insert( 2, CheckForNumericBone, NumericViewBoneDelegate)
