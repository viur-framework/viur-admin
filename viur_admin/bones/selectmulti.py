#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets

from viur_admin.bones.base import BaseViewBoneDelegate
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector


class SelectMultiViewBoneDelegate(BaseViewBoneDelegate):
	def __init__(self, modulName, boneName, skelStructure, *args, **kwargs):
		super(SelectMultiViewBoneDelegate, self).__init__(modulName, boneName, skelStructure, *args, **kwargs)
		self.skelStructure = skelStructure
		self.boneName = boneName
		self.modulName = modulName

	def displayText(self, value, locale):
		# print("SelectMultiViewBoneDelegate.displayText", value, locale)
		boneValues = {str(k): str(v) for k, v in self.skelStructure[self.boneName]["values"].items()}
		resStr = ", ".join([str(x) in boneValues and boneValues[str(x)] or str(x) for x in value])
		# print("SelectMultiViewBoneDelegate res", repr(boneValues), repr(resStr))
		return super(SelectMultiViewBoneDelegate, self).displayText(resStr, locale)


class SelectMultiEditBone(QtWidgets.QWidget):
	def __init__(self, modulName, boneName, readOnly, values, sortBy="keys", editWidget=None, *args, **kwargs):
		super(SelectMultiEditBone, self).__init__(*args, **kwargs)
		self.editWidget = editWidget
		self.modulName = modulName
		self.boneName = boneName
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
	def fromSkelStructure(modulName, boneName, skelStructure, **kwargs):
		readOnly = "readonly" in skelStructure[boneName].keys() and skelStructure[boneName]["readonly"]
		if "sortBy" in skelStructure[boneName].keys():
			sortBy = skelStructure[boneName]["sortBy"]
		else:
			sortBy = "keys"
		values = list(skelStructure[boneName]["values"].items())
		return SelectMultiEditBone(modulName, boneName, readOnly, values=values, sortBy=sortBy, **kwargs)

	def unserialize(self, data):
		if not self.boneName in data.keys():
			return
		for key, checkbox in self.checkboxes.items():
			checkbox.setChecked(key in data[self.boneName])

	def serializeForPost(self):
		return {self.boneName: [key for key, checkbox in self.checkboxes.items() if checkbox.isChecked()]}

	def serializeForDocument(self):
		return self.serialize()


def CheckForSelectMultiBone(modulName, boneName, skelStucture):
	return skelStucture[boneName]["type"] == "selectmulti" or skelStucture[boneName]["type"].startswith("selectmulti.")


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForSelectMultiBone, SelectMultiEditBone)
viewDelegateSelector.insert(2, CheckForSelectMultiBone, SelectMultiViewBoneDelegate)
