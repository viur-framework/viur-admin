# -*- coding: utf-8 -*-
from typing import Union, Any, Dict, List

from PyQt5 import QtCore, QtWidgets

from viur_admin.bones.base import BaseViewBoneDelegate
from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector, extendedSearchWidgetSelector
from viur_admin.ui.extendedBooleanFilterPluginUI import Ui_Form


class BooleanViewBoneDelegate(BaseViewBoneDelegate):
	def displayText(self, value: str, locale: QtCore.QLocale) -> str:
		if value:
			return QtCore.QCoreApplication.translate("BooleanEditBone", "Yes")
		else:
			return QtCore.QCoreApplication.translate("BooleanEditBone", "No")


class ExtendedBooleanFilterPlugin(QtWidgets.QGroupBox):
	def __init__(self, extension: dict, parent: QtWidgets.QWidget = None):
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
	def canHandleExtension(extension: dict) -> bool:
		return (isinstance(extension, dict) and "type" in extension and (
				extension["type"] == "boolean" or extension["type"].startswith("boolean.")))


class BooleanEditBone(BoneEditInterface):
	def __init__(
			self,
			moduleName: str,
			boneName: str,
			readOnly: bool,
			editWidget: Union[QtWidgets.QWidget, None] = None,
			*args: Any,
			**kwargs: Any):
		super(BooleanEditBone, self).__init__(moduleName, boneName, readOnly, editWidget, *args, **kwargs)
		self.layout = QtWidgets.QVBoxLayout(self)
		self.checkBox = QtWidgets.QCheckBox(self)
		if readOnly:
			self.checkBox.setDisabled(True)
		self.layout.addWidget(self.checkBox)

	@classmethod
	def fromSkelStructure(
			cls,
			moduleName: str,
			boneName: str,
			skelStructure: dict,
			**kwargs: Any) -> Any:
		readOnly = "readonly" in skelStructure[boneName] and skelStructure[boneName]["readonly"]
		return cls(moduleName, boneName, readOnly, **kwargs)

	def unserialize(self, data: dict) -> None:
		if data.get(self.boneName):
			self.checkBox.setChecked(True)

	def serializeForPost(self) -> dict:
		return {self.boneName: self.checkBox.isChecked()}

	def serializeForDocument(self) -> dict:
		return self.serialize()


def CheckForBooleanBone(
		moduleName: str,
		boneName: str,
		skelStucture: Dict[str, Any]) -> bool:
	return skelStucture[boneName]["type"] == "bool"


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForBooleanBone, BooleanEditBone)
viewDelegateSelector.insert(2, CheckForBooleanBone, BooleanViewBoneDelegate)
extendedSearchWidgetSelector.insert(1, ExtendedBooleanFilterPlugin.canHandleExtension, ExtendedBooleanFilterPlugin)
