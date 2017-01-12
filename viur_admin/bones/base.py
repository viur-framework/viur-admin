# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWidgets

from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector


class BaseViewBoneDelegate(QtWidgets.QStyledItemDelegate):
	request_repaint = QtCore.pyqtSignal()

	def __init__(self, moduleName, boneName, skelStructure, *args, **kwargs):
		super().__init__(**kwargs)
		self.skelStructure = skelStructure
		self.boneName = boneName
		self.moduleName = moduleName


class BaseEditBone(BoneEditInterface):
	def __init__(self, moduleName, boneName, readOnly, editWidget=None, *args, **kwargs):
		super(BaseEditBone, self).__init__(moduleName, boneName, readOnly, editWidget, *args, **kwargs)
		self.layout = QtWidgets.QHBoxLayout(self)
		self.lineEdit = QtWidgets.QLineEdit()
		self.layout.addWidget(self.lineEdit)
		self.setParams()
		self.lineEdit.show()

	def setParams(self):
		if self.readOnly:
			self.setEnabled(False)
		else:
			self.setEnabled(True)

	@staticmethod
	def fromSkelStructure(moduleName, boneName, skelStructure, **kwargs):
		readOnly = "readonly" in skelStructure[boneName].keys() and skelStructure[boneName]["readonly"]
		return BaseEditBone(moduleName, boneName, readOnly, **kwargs)

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
