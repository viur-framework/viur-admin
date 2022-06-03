#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Union, Any, List, Dict

from PyQt5 import QtWidgets, QtCore

from viur_admin.bones.base import BaseViewBoneDelegate, LanguageContainer
from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector, extendedSearchWidgetSelector
from viur_admin.ui.extendedSelectMultiFilterPluginUI import Ui_Form
from math import floor


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

class DynamicGridLayout(QtWidgets.QGridLayout):
	"""
		Like a Grid-Layout, but it will automatically demternine how many colums are possible given
		the preffered size of it's contents and re-align it's childs left to right, top to bottom.
	"""
	def __init__(self, parent):
		super().__init__(parent)
		self.currentWidth: int = 1  # Width in pixels, that we currently have

	def addItem(self, item: QtWidgets.QLayoutItem) -> None:
		# Just push an item to the end (=new row), then reflow everything
		nextRow = self.rowCount()+1
		super().addItem(item, nextRow, 0)
		self._relayout()

	def setGeometry(self, rect):
		# The space we allocate has changed (resize etc). Reflow everything
		super().setGeometry(rect)
		if self.currentWidth != rect.width():
			self.currentWidth = rect.width()
			self._relayout()

	def _relayout(self):
		# Perform the actual reflow. Grab each child, determine its preferred width and rebuild the grid.
		itemList = []
		maxWidth: int = 1  # Maximum preferred size of our children
		while self.count():
			item = self.takeAt(0)  # Remove item from layout, so we can re-add it below
			if item.sizeHint().width() > maxWidth:
				maxWidth = item.sizeHint().width()
			itemList.append(item)
		columnCount = floor(self.currentWidth/(maxWidth+20))
		currentRow = currentColumn = 0
		for item in itemList:
			super().addItem(item, currentRow, currentColumn)
			currentColumn += 1
			if currentColumn >= columnCount:
				currentColumn = 0
				currentRow += 1

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
		self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred))
		#self.layout = QtWidgets.QVBoxLayout(self.editWidget)
		self.layout = DynamicGridLayout(self.editWidget)
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
