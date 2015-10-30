# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWidgets

from viur_admin.bones.base import BaseViewBoneDelegate
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector, protocolWrapperInstanceSelector


class BooleanViewBoneDelegate(BaseViewBoneDelegate):
	def displayText(self, value, locale):
		if value:
			return (QtCore.QCoreApplication.translate("BooleanEditBone", "Yes"))
		else:
			return (QtCore.QCoreApplication.translate("BooleanEditBone", "No"))


class BooleanEditBone(QtWidgets.QWidget):
	def __init__(self, modulName, boneName, readOnly, editWidget=None, *args, **kwargs):
		super(BooleanEditBone, self).__init__(*args, **kwargs)
		self.editWidget = editWidget
		self.modulName = modulName
		self.boneName = boneName
		self.readOnly = readOnly
		self.layout = QtWidgets.QVBoxLayout(self)
		self.checkBox = QtWidgets.QCheckBox(self)
		if readOnly:
			self.checkBox.setDisabled(True)
		self.layout.addWidget(self.checkBox)

	@classmethod
	def fromSkelStructure(cls, modulName, boneName, skelStructure, **kwargs):
		readOnly = "readonly" in skelStructure[boneName].keys() and skelStructure[boneName]["readonly"]
		return cls(modulName, boneName, readOnly, **kwargs)

	def unserialize(self, data):
		protoWrap = protocolWrapperInstanceSelector.select(self.modulName)
		assert protoWrap is not None
		if self.boneName in data.keys() and data[self.boneName]:
			self.checkBox.setChecked(True)

	def serializeForPost(self):
		return {self.boneName: self.checkBox.isChecked()}

	def serializeForDocument(self):
		return (self.serialize())


def CheckForBooleanBone(modulName, boneName, skelStucture):
	return (skelStucture[boneName]["type"] == "bool")


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForBooleanBone, BooleanEditBone)
viewDelegateSelector.insert(2, CheckForBooleanBone, BooleanViewBoneDelegate)
