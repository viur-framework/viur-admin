# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWidgets

from viur_admin.bones.base import BaseViewBoneDelegate
from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector, protocolWrapperInstanceSelector, \
	extendedSearchWidgetSelector
from viur_admin.ui.extendedSelectOneFilterPluginUI import Ui_Form
from viur_admin.utils import wheelEventFilter


class SelectOneViewBoneDelegate(BaseViewBoneDelegate):
	def displayText(self, value, locale):
		items = dict([(str(k), str(v)) for k, v in self.skelStructure[self.boneName]["values"]])
		if str(value) in items.keys():
			return items[str(value)]
		else:
			return value


class FixedComboBox(QtWidgets.QComboBox):
	"""
		Subclass of QComboBox which doesn't accept QWheelEvents if it doesnt have focus
	"""

	def __init__(self, *args, **kwargs):
		super(FixedComboBox, self).__init__(*args, **kwargs)
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		self.installEventFilter(wheelEventFilter)

	def focusInEvent(self, e):
		self.setFocusPolicy(QtCore.Qt.WheelFocus)
		super(FixedComboBox, self).focusInEvent(e)

	def focusOutEvent(self, e):
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		super(FixedComboBox, self).focusOutEvent(e)


class ExtendedSelectOneFilterPlugin(QtWidgets.QGroupBox):
	def __init__(self, extension, parent=None):
		super(ExtendedSelectOneFilterPlugin, self).__init__(parent)
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
	def canHandleExtension(extension):
		return (
				isinstance(extension, dict) and
				"type" in extension.keys() and (
						(
								(extension["type"] == "select" or extension["type"].startswith("select.")) and
								not extension.get("multiple", False)
						)
						or (extension["type"] == "selectone" or extension["type"].startswith("selectone."))
				)
		)


class SelectOneEditBone(BoneEditInterface):
	def __init__(self, moduleName, boneName, readOnly, values, sortBy="keys", editWidget=None, *args, **kwargs):
		super(SelectOneEditBone, self).__init__(moduleName, boneName, readOnly, editWidget, *args, **kwargs)
		self.editWidget = editWidget
		self.moduleName = moduleName
		self.boneName = boneName
		self.readOnly = readOnly
		self.values = values
		self.layout = QtWidgets.QVBoxLayout(self)
		self.comboBox = FixedComboBox(self)
		self.layout.addWidget(self.comboBox)
		tmpList = values
		if sortBy == "keys":
			tmpList.sort(key=lambda x: x[0])  # Sort by keys
		else:
			tmpList.sort(key=lambda x: x[1])  # Values
		self.comboBox.addItems([x[1] for x in tmpList])

	@staticmethod
	def fromSkelStructure(moduleName, boneName, skelStructure, **kwargs):
		readOnly = "readonly" in skelStructure[boneName].keys() and skelStructure[boneName]["readonly"]
		if "sortBy" in skelStructure[boneName].keys():
			sortBy = skelStructure[boneName]["sortBy"]
		else:
			sortBy = "keys"
		values = list(skelStructure[boneName]["values"])
		if "required" not in skelStructure[boneName] or not skelStructure[boneName]["required"]:
			values.insert(0, ["", ""])
		return SelectOneEditBone(moduleName, boneName, readOnly, values=values, sortBy=sortBy, **kwargs)

	def unserialize(self, data):
		protoWrap = protocolWrapperInstanceSelector.select(self.moduleName)
		assert protoWrap is not None
		if 1:  # There might be junk comming from the server
			items = dict([(str(k), str(v)) for k, v in self.values])
			if str(data[self.boneName]) in items.keys():
				self.comboBox.setCurrentIndex(self.comboBox.findText(items[str(data[self.boneName])]))
			else:
				self.comboBox.setCurrentIndex(-1)
		else:  # except:
			self.comboBox.setCurrentIndex(-1)

	def serializeForPost(self):
		currentValue = str(self.comboBox.currentText())
		for key, value in self.values:
			if str(value) == currentValue:
				return {self.boneName: str(key)}
		return {self.boneName: None}


def CheckForSelectOneBone(moduleName, boneName, skelStucture):
	return (
			(skelStucture[boneName]["type"] == "select" or skelStucture[boneName]["type"].startswith("select.") and not
			skelStucture[boneName].get("multiple", False)) or
			skelStucture[boneName]["type"] == "selectone" or skelStucture[boneName]["type"].startswith("selectone."))


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForSelectOneBone, SelectOneEditBone)
viewDelegateSelector.insert(2, CheckForSelectOneBone, SelectOneViewBoneDelegate)
extendedSearchWidgetSelector.insert(1, ExtendedSelectOneFilterPlugin.canHandleExtension, ExtendedSelectOneFilterPlugin)
