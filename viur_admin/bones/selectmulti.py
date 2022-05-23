#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Union, Any, List, Dict

from PyQt5 import QtWidgets

from viur_admin.bones.base import BaseViewBoneDelegate, LanguageContainer
from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector, extendedSearchWidgetSelector
from viur_admin.ui.extendedSelectMultiFilterPluginUI import Ui_Form


class SelectMultiViewBoneDelegate(BaseViewBoneDelegate):
	def __init__(self, moduleName: str, boneName: str, boneStructure: dict, *args: Any, **kwargs: Any):
		super(SelectMultiViewBoneDelegate, self).__init__(moduleName, boneName, boneStructure, *args, **kwargs)
		self.boneStructure = boneStructure
		self.boneName = boneName
		self.moduleName = moduleName

	def displayText(self, value: str, locale: Any) -> str:
		value = value.get(self.boneName)
		if not value:
			return ""
		# print("SelectMultiViewBoneDelegate.displayText", value, locale)
		boneValues = {str(k): str(v) for k, v in self.boneStructure["values"]}
		resStr = ", ".join([str(x) in boneValues and boneValues[str(x)] or str(x) for x in value])
		# print("SelectMultiViewBoneDelegate res", repr(boneValues), repr(resStr))
		return resStr


class SelectMultiEditBone(BoneEditInterface):
	def __init__(
			self,
			moduleName: str,
			boneName: str,
			readOnly: bool,
			required: bool,
			values: List[Any],
			sortBy: str = "keys",
			editWidget: QtWidgets.QWidget = None,
			*args: Any,
			**kwargs: Any):
		super(SelectMultiEditBone, self).__init__(moduleName, boneName, readOnly, required, editWidget, *args, **kwargs)
		self.layout = QtWidgets.QVBoxLayout(self.editWidget)
		self.checkboxes: Dict[str, QtWidgets.QCheckBox] = dict()
		tmpList = values
		#if sortBy == "keys":
		#	tmpList.sort(key=lambda x: x[0])  # Sort by keys
		#else:
		#	tmpList.sort(key=lambda x: x[1])  # Values
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
			boneStructure: dict,
			**kwargs: Any) -> Any:
		readOnly = "readonly" in boneStructure and boneStructure["readonly"]
		required = "required" in boneStructure and boneStructure["required"]
		if "sortBy" in boneStructure:
			sortBy = boneStructure["sortBy"]
		else:
			sortBy = "keys"
		values = list(boneStructure["values"])
		widgetGen = lambda: cls(
			moduleName,
			boneName,
			readOnly,
			required,
			values=values,
			sortBy=sortBy,
			**kwargs)
		if boneStructure.get("languages"):
			preLangWidgetGen = widgetGen
			widgetGen = lambda: LanguageContainer(boneStructure["languages"], preLangWidgetGen)
		return widgetGen()

	def unserialize(self, data: Dict[str, Any], errors: List[Dict]) -> None:
		self.setErrors(errors)
		for key, checkbox in self.checkboxes.items():
			checkbox.setChecked(isinstance(data, list) and key in data)

	def serializeForPost(self) -> Dict[str, Any]:
		return [key for key, checkbox in self.checkboxes.items() if checkbox.isChecked()]



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
		boneStructure: Dict[str, Any]) -> bool:
	isSelect = boneStructure["type"] == "select" or boneStructure["type"].startswith("select.")
	return isSelect and bool(boneStructure.get("multiple"))


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForSelectMultiBone, SelectMultiEditBone)
viewDelegateSelector.insert(2, CheckForSelectMultiBone, SelectMultiViewBoneDelegate)
extendedSearchWidgetSelector.insert(
	1,
	ExtendedSelectMultiFilterPlugin.canHandleExtension,
	ExtendedSelectMultiFilterPlugin)
