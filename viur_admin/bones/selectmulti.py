#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Union, Any, List, Dict

from PyQt5 import QtWidgets

from viur_admin.bones.base import BaseViewBoneDelegate
from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector, extendedSearchWidgetSelector
from viur_admin.ui.extendedSelectMultiFilterPluginUI import Ui_Form


class SelectMultiViewBoneDelegate(BaseViewBoneDelegate):
	def __init__(self, moduleName: str, boneName: str, skelStructure: dict, *args: Any, **kwargs: Any):
		super(SelectMultiViewBoneDelegate, self).__init__(moduleName, boneName, skelStructure, *args, **kwargs)
		self.skelStructure = skelStructure
		self.boneName = boneName
		self.moduleName = moduleName

	def displayText(self, value: str, locale: Any) -> str:
		# print("SelectMultiViewBoneDelegate.displayText", value, locale)
		boneValues = {str(k): str(v) for k, v in self.skelStructure[self.boneName]["values"]}
		resStr = ", ".join([str(x) in boneValues and boneValues[str(x)] or str(x) for x in value])
		# print("SelectMultiViewBoneDelegate res", repr(boneValues), repr(resStr))
		return super(SelectMultiViewBoneDelegate, self).displayText(resStr, locale)


class SelectMultiEditBone(BoneEditInterface):
	def __init__(
			self,
			moduleName: str,
			boneName: str,
			readOnly: bool,
			values: List[Any],
			sortBy: str = "keys",
			editWidget: QtWidgets.QWidget = None,
			*args: Any,
			**kwargs: Any):
		super(SelectMultiEditBone, self).__init__(moduleName, boneName, readOnly, editWidget, *args, **kwargs)
		self.layout = QtWidgets.QVBoxLayout(self)
		self.checkboxes: Dict[str, QtWidgets.QCheckBox] = dict()
		tmpList = values
		if sortBy == "keys":
			tmpList.sort(key=lambda x: x[0])  # Sort by keys
		else:
			tmpList.sort(key=lambda x: x[1])  # Values
		for key, descr in tmpList:
			cb = QtWidgets.QCheckBox(descr, self)
			self.layout.addWidget(cb)
			cb.show()
			self.checkboxes[key] = cb

	@classmethod
	def fromSkelStructure(
			cls,
			moduleName: str,
			boneName: str,
			skelStructure: dict,
			**kwargs: Any) -> Any:
		readOnly = "readonly" in skelStructure[boneName] and skelStructure[boneName]["readonly"]
		if "sortBy" in skelStructure[boneName]:
			sortBy = skelStructure[boneName]["sortBy"]
		else:
			sortBy = "keys"
		values = list(skelStructure[boneName]["values"])
		return cls(
			moduleName,
			boneName,
			readOnly,
			values=values,
			sortBy=sortBy,
			**kwargs)

	def unserialize(self, data: Dict[str, Any]) -> None:
		if self.boneName not in data:
			return
		for key, checkbox in self.checkboxes.items():
			checkbox.setChecked(key in data[self.boneName])

	def serializeForPost(self) -> Dict[str, Any]:
		return {self.boneName: [key for key, checkbox in self.checkboxes.items() if checkbox.isChecked()]}


class ExtendedSelectMultiFilterPlugin(QtWidgets.QGroupBox):
	def __init__(
			self,
			extension: dict,
			parent: Union[QtWidgets.QWidget, None] = None):
		super(ExtendedSelectMultiFilterPlugin, self).__init__(parent)
		self.extension = extension
		# self.view = view
		# self.module = module
		self.ui = Ui_Form()
		self.ui.setupUi(self)
		self.setTitle(extension["name"])
		self.ui.values.addItem("", None)
		for userData, text in extension["values"].items():
			self.ui.values.addItem(text, userData)

	@staticmethod
	def canHandleExtension(extension: Dict[str, Any]) -> bool:
		return (
				isinstance(extension, dict) and
				"type" in extension and (
						(
								(extension["type"] == "select" or extension["type"].startswith("select.")) and
								extension.get("multiple", True)
						)
						or (extension["type"] == "selectmulti" or extension["type"].startswith("selectmulti."))
				)
		)


def CheckForSelectMultiBone(
		moduleName: str,
		boneName: str,
		skelStucture: Dict[str, Any]) -> bool:
	return (
			((skelStucture[boneName]["type"] == "select" or skelStucture[boneName]["type"].startswith("select.")) and
			 skelStucture[boneName].get("multiple", False)) or
			skelStucture[boneName]["type"] == "selectmulti" or skelStucture[boneName]["type"].startswith(
		"selectmulti."))


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForSelectMultiBone, SelectMultiEditBone)
viewDelegateSelector.insert(2, CheckForSelectMultiBone, SelectMultiViewBoneDelegate)
extendedSearchWidgetSelector.insert(
	1,
	ExtendedSelectMultiFilterPlugin.canHandleExtension,
	ExtendedSelectMultiFilterPlugin)
