#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets
from viur_admin.bones.bone_interface import BoneEditInterface

from viur_admin.bones.base import BaseViewBoneDelegate
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector


class SelectMultiViewBoneDelegate(BaseViewBoneDelegate):
	def __init__(self, moduleName, boneName, skelStructure, *args, **kwargs):
		super(SelectMultiViewBoneDelegate, self).__init__(moduleName, boneName, skelStructure, *args, **kwargs)
		self.skelStructure = skelStructure
		self.boneName = boneName
		self.moduleName = moduleName

	def displayText(self, value, locale):
		# print("SelectMultiViewBoneDelegate.displayText", value, locale)
		boneValues = {str(k): str(v) for k, v in self.skelStructure[self.boneName]["values"]}
		resStr = ", ".join([str(x) in boneValues and boneValues[str(x)] or str(x) for x in value])
		# print("SelectMultiViewBoneDelegate res", repr(boneValues), repr(resStr))
		return super(SelectMultiViewBoneDelegate, self).displayText(resStr, locale)


class SelectMultiEditBone(BoneEditInterface):
	def __init__(self, moduleName, boneName, readOnly, values, sortBy="keys", editWidget=None, *args, **kwargs):
		super(SelectMultiEditBone, self).__init__(moduleName, boneName, readOnly, editWidget, *args, **kwargs)
		self.layout = QtWidgets.QVBoxLayout(self)
		self.checkboxes = {}
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

	@staticmethod
	def fromSkelStructure(moduleName, boneName, skelStructure, **kwargs):
		readOnly = "readonly" in skelStructure[boneName].keys() and skelStructure[boneName]["readonly"]
		if "sortBy" in skelStructure[boneName].keys():
			sortBy = skelStructure[boneName]["sortBy"]
		else:
			sortBy = "keys"
		values = list(skelStructure[boneName]["values"])
		return SelectMultiEditBone(moduleName, boneName, readOnly, values=values, sortBy=sortBy, **kwargs)

	def unserialize(self, data):
		if not self.boneName in data.keys():
			return
		for key, checkbox in self.checkboxes.items():
			checkbox.setChecked(key in data[self.boneName])

	def serializeForPost(self):
		return {self.boneName: [key for key, checkbox in self.checkboxes.items() if checkbox.isChecked()]}


def CheckForSelectMultiBone(moduleName, boneName, skelStucture):
	return skelStucture[boneName]["type"] == "selectmulti" or skelStucture[boneName]["type"].startswith("selectmulti.")


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForSelectMultiBone, SelectMultiEditBone)
viewDelegateSelector.insert(2, CheckForSelectMultiBone, SelectMultiViewBoneDelegate)
