#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PySide import QtCore, QtGui
from event import event
from bones.base import BaseEditBone
from priorityqueue import editBoneSelector

class ColorEditBone( BaseEditBone ):

	def getLineEdit(self):
		aWidget=QtGui.QWidget()
		aWidget.layout = QtGui.QHBoxLayout( aWidget )
		self.lineEdit1=QtGui.QLineEdit( self );
		self.button = QtGui.QPushButton('Auswählen', self)
		self.colordisplay=QtGui.QLineEdit( self );
		self.colordisplay.setReadOnly(True)
		aWidget.connect(self.lineEdit1, QtCore.SIGNAL('editingFinished ()'), self.refreshColor)
		aWidget.connect(self.button, QtCore.SIGNAL('clicked()'), self.showDialog)
		aWidget.layout.addWidget(self.lineEdit1)
		aWidget.layout.addWidget(self.colordisplay)
		aWidget.layout.addWidget(self.button)
		return (aWidget)
		
	def setParams(self):
		if self.readOnly:
			self.setEnabled( False )
		else:
			self.setEnabled( True )

	def showDialog(self):
		acolor=QtGui.QColorDialog.getColor(QtGui.QColor(self.lineEdit1.displayText()),self.lineEdit1,self.boneStructure["descr"])
		if acolor.isValid():
			self.lineEdit1.setText(acolor.name())
			self.refreshColor()
			
	def refreshColor(self,text=""):
		self.colordisplay.setStyleSheet("QWidget { background-color: %s }" % str( self.lineEdit1.displayText() ))


	def unserialize(self, data):
		if not self.boneName in data.keys():
			return
		data=str( data[ self.boneName ] ) if data[ self.boneName ] else ""
		self.lineEdit1.setText( data )
		self.colordisplay.setStyleSheet("QWidget { background-color: %s }" % data)

	def serializeForPost(self):
		return( { self.boneName: str( self.lineEdit1.displayText() ) } )


def CheckForColorBone(  modulName, boneName, skelStucture ):
	return( skelStucture[boneName]["type"]=="color" )

editBoneSelector.insert( 2, CheckForColorBone, ColorEditBone )
