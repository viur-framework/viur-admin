# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
from viur_admin.bones.bone_interface import BoneEditInterface

from viur_admin.priorityqueue import editBoneSelector

class ClickableLineEdit(QtWidgets.QLineEdit):
	clicked = QtCore.pyqtSignal()

	def mouseReleaseEvent(self, event):
		self.clicked.emit()


class ColorEditBone(BoneEditInterface):
	def __init__(self, moduleName, boneName, readOnly, skelStructure, **kwargs):
		super(ColorEditBone, self).__init__(moduleName, boneName, readOnly, **kwargs)

		self.skelStructure = skelStructure
		lineLayout = QtWidgets.QHBoxLayout(self)
		self.lineEdit = QtWidgets.QLineEdit(self)
		self.button = QtWidgets.QPushButton('Auswählen', self)
		self.colordisplay = ClickableLineEdit(self)
		# self.colordisplay.setReadOnly(True)
		self.lineEdit.editingFinished.connect(self.refreshColor)
		self.button.clicked.connect(self.showDialog)
		self.colordisplay.clicked.connect(self.showDialog)
		lineLayout.addWidget(self.lineEdit)
		lineLayout.addWidget(self.colordisplay)
		lineLayout.addWidget(self.button)

	@staticmethod
	def fromSkelStructure(moduleName, boneName, skelStructure, **kwargs):
		return ColorEditBone(moduleName, boneName, skelStructure[boneName]["readonly"], skelStructure, **kwargs)

	def showDialog(self):
		acolor = QtWidgets.QColorDialog.getColor(
				QtGui.QColor(self.lineEdit.displayText()),
				self.lineEdit,
				self.skelStructure[self.boneName]["descr"])
		if acolor.isValid():
			self.lineEdit.setText(acolor.name())
			self.refreshColor()

	def refreshColor(self):
		self.colordisplay.setStyleSheet("QWidget { background-color: %s }" % str(self.lineEdit.displayText()))

	def unserialize(self, data):
		if self.boneName not in data.keys():
			return
		data = str(data[self.boneName]) if data[self.boneName] else ""
		self.lineEdit.setText(data)
		self.colordisplay.setStyleSheet("QWidget { background-color: %s }" % data)

	def serializeForPost(self):
		return {self.boneName: str(self.lineEdit.displayText())}


def CheckForColorBone(moduleName, boneName, skelStucture):
	res = skelStucture[boneName]["type"] == "color"
	return res


editBoneSelector.insert(2, CheckForColorBone, ColorEditBone)
