#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5 import QtGui, QtWidgets

from viur_admin.bones.base import BaseEditBone
from viur_admin.priorityqueue import editBoneSelector


class ColorEditBone(BaseEditBone):
	def getLineEdit(self):
		aWidget = QtWidgets.QWidget()
		aWidget.layout = QtWidgets.QHBoxLayout(aWidget)
		self.lineEdit1 = QtWidgets.QLineEdit(self);
		self.button = QtWidgets.QPushButton('Auswählen', self)
		self.colordisplay = QtWidgets.QLineEdit(self);
		self.colordisplay.setReadOnly(True)
		self.lineEdit1.editingFinished.connect(self.refreshColor)
		self.button.clicked.connect(self.showDialog)
		aWidget.layout.addWidget(self.lineEdit1)
		aWidget.layout.addWidget(self.colordisplay)
		aWidget.layout.addWidget(self.button)
		return aWidget

	def setParams(self):
		if self.readOnly:
			self.setEnabled(False)
		else:
			self.setEnabled(True)

	def showDialog(self):
		acolor = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.lineEdit1.displayText()), self.lineEdit1,
		                                         self.boneStructure["descr"])
		if acolor.isValid():
			self.lineEdit1.setText(acolor.name())
			self.refreshColor()

	def refreshColor(self, text=""):
		self.colordisplay.setStyleSheet("QWidget { background-color: %s }" % str(self.lineEdit1.displayText()))

	def unserialize(self, data):
		if self.boneName not in data.keys():
			return
		data = str(data[self.boneName]) if data[self.boneName] else ""
		self.lineEdit1.setText(data)
		self.colordisplay.setStyleSheet("QWidget { background-color: %s }" % data)

	def serializeForPost(self):
		return {self.boneName: str(self.lineEdit1.displayText())}


def CheckForColorBone(modulName, boneName, skelStucture):
	return skelStucture[boneName]["type"] == "color"


editBoneSelector.insert(2, CheckForColorBone, ColorEditBone)
