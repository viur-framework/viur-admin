# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWidgets

from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector


class BaseViewBoneDelegate(QtWidgets.QStyledItemDelegate):
	request_repaint = QtCore.pyqtSignal()

	def __init__(self, modulName, boneName, skelStructure, *args, **kwargs):
		super().__init__(**kwargs)
		self.skelStructure = skelStructure
		self.boneName = boneName
		self.modulName = modulName


class BaseEditBone(QtWidgets.QWidget):
	def getLineEdit(self):
		return (QtWidgets.QLineEdit(self))

	def setParams(self):
		if self.readOnly:
			self.lineEdit.setReadOnly(True)
		else:
			self.lineEdit.setReadOnly(False)

	def __init__(self, modulName, boneName, readOnly, *args, **kwargs):
		super(BaseEditBone, self).__init__(*args, **kwargs)
		self.boneName = boneName
		self.readOnly = readOnly
		self.layout = QtWidgets.QHBoxLayout(self)
		self.lineEdit = self.getLineEdit()
		self.layout.addWidget(self.lineEdit)
		self.setParams()
		self.lineEdit.show()

	@staticmethod
	def fromSkelStructure(modulName, boneName, skelStructure):
		readOnly = "readonly" in skelStructure[boneName].keys() and skelStructure[boneName]["readonly"]
		return BaseEditBone(modulName, boneName, readOnly)

	def unserialize(self, data):
		if self.boneName in data.keys():
			self.lineEdit.setText(str(data[self.boneName]) if data[self.boneName] else "")

	def serializeForPost(self):
		return {self.boneName: self.lineEdit.displayText()}

	def serializeForDocument(self):
		return self.serialize()

# Register this Bone in the global queue
editBoneSelector.insert(0, lambda *args, **kwargs: True, BaseEditBone)
viewDelegateSelector.insert(0, lambda *args, **kwargs: True, BaseViewBoneDelegate)
