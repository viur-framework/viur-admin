# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWidgets

from viur_admin.bones.base import BaseViewBoneDelegate
from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector, protocolWrapperInstanceSelector, \
	extendedSearchWidgetSelector
from viur_admin.ui.extendedBooleanFilterPluginUI import Ui_Form


class BooleanViewBoneDelegate(BaseViewBoneDelegate):
	def displayText(self, value, locale):
		if value:
			return QtCore.QCoreApplication.translate("BooleanEditBone", "Yes")
		else:
			return QtCore.QCoreApplication.translate("BooleanEditBone", "No")


class ExtendedBooleanFilterPlugin(QtWidgets.QGroupBox):
	def __init__(self, extension, parent=None):
		super(ExtendedBooleanFilterPlugin, self).__init__(parent)
		self.extension = extension
		# self.view = view
		# self.module = module
		self.ui = Ui_Form()
		self.ui.setupUi(self)
		self.setTitle(extension["name"])
		self.ui.values.addItem("Ignore", "")
		self.ui.values.addItem("Yes", "1")
		self.ui.values.addItem("No", "0")

	@staticmethod
	def canHandleExtension(extension):
		return (isinstance(extension, dict) and "type" in extension.keys() and (
					extension["type"] == "boolean" or extension["type"].startswith("boolean.")))


class BooleanEditBone(BoneEditInterface):
	def __init__(self, moduleName, boneName, readOnly, editWidget=None, *args, **kwargs):
		super(BooleanEditBone, self).__init__(moduleName, boneName, readOnly, editWidget, *args, **kwargs)
		self.layout = QtWidgets.QVBoxLayout(self)
		self.checkBox = QtWidgets.QCheckBox(self)
		if readOnly:
			self.checkBox.setDisabled(True)
		self.layout.addWidget(self.checkBox)

	@classmethod
	def fromSkelStructure(cls, moduleName, boneName, skelStructure, **kwargs):
		readOnly = "readonly" in skelStructure[boneName].keys() and skelStructure[boneName]["readonly"]
		return cls(moduleName, boneName, readOnly, **kwargs)

	def unserialize(self, data):
		protoWrap = protocolWrapperInstanceSelector.select(self.moduleName)
		assert protoWrap is not None
		if self.boneName in data.keys() and data[self.boneName]:
			self.checkBox.setChecked(True)

	def serializeForPost(self):
		return {self.boneName: self.checkBox.isChecked()}

	def serializeForDocument(self):
		return (self.serialize())


def CheckForBooleanBone(moduleName, boneName, skelStucture):
	return (skelStucture[boneName]["type"] == "bool")


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForBooleanBone, BooleanEditBone)
viewDelegateSelector.insert(2, CheckForBooleanBone, BooleanViewBoneDelegate)
extendedSearchWidgetSelector.insert(1, ExtendedBooleanFilterPlugin.canHandleExtension, ExtendedBooleanFilterPlugin)
