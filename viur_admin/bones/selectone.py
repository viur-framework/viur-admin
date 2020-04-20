# -*- coding: utf-8 -*-
from typing import Any, Dict, Tuple, List, Union

from PyQt5 import QtCore, QtWidgets, QtGui

from viur_admin.bones.base import BaseViewBoneDelegate, LanguageContainer
from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector, protocolWrapperInstanceSelector, \
	extendedSearchWidgetSelector
from viur_admin.ui.extendedSelectOneFilterPluginUI import Ui_Form
from viur_admin.utils import wheelEventFilter


class SelectOneViewBoneDelegate(BaseViewBoneDelegate):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.editingModel = None
		self.editingIndex = None
		self.editingItem = None
		self.commitData.connect(self.commitDataCb)

	def displayText(self, value: str, locale: QtCore.QLocale) -> str:
		items = dict([(str(k), str(v)) for k, v in self.skelStructure[self.boneName]["values"]])
		if str(value) in items:
			return items[str(value)]
		else:
			return value

	def createEditor(self, parent, option, index):
		print("In CREATE EDITOR")
		protoWrap = protocolWrapperInstanceSelector.select(self.moduleName)
		assert protoWrap is not None
		skelStructure = protoWrap.editStructure
		wdgGen = editBoneSelector.select(self.moduleName, self.boneName, skelStructure)
		widget = wdgGen.fromSkelStructure(self.moduleName, self.boneName, skelStructure, editWidget=self)
		widget.setParent(parent)
		#print(self.skelStructure)

		return widget

	def editorEvent(self, event: QtCore.QEvent, model: QtCore.QAbstractItemModel, option: 'QStyleOptionViewItem', index: QtCore.QModelIndex):
		self.editingModel = model
		self.editingIndex = index
		self.editingItem = model.dataCache[index.row()]
		return False

	def commitDataCb(self, editor):
		protoWrap = protocolWrapperInstanceSelector.select(self.moduleName)
		assert protoWrap is not None
		self.editTaskID = protoWrap.edit(self.editingItem["key"], **{self.boneName: editor.serializeForPost()})
		self.editingModel = None
		self.editingIndex = None


class FixedComboBox(QtWidgets.QComboBox):
	"""
		Subclass of QComboBox which doesn't accept QWheelEvents if it doesnt have focus
	"""

	def __init__(self, *args: Any, **kwargs: Any):
		super(FixedComboBox, self).__init__(*args, **kwargs)
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		self.installEventFilter(wheelEventFilter)

	def focusInEvent(self, e: QtGui.QFocusEvent) -> None:
		self.setFocusPolicy(QtCore.Qt.WheelFocus)
		super(FixedComboBox, self).focusInEvent(e)

	def focusOutEvent(self, e: QtGui.QFocusEvent) -> None:
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		super(FixedComboBox, self).focusOutEvent(e)


class ExtendedSelectOneFilterPlugin(QtWidgets.QGroupBox):
	def __init__(self, extension: Dict[str, Any], parent: Union[QtWidgets.QWidget, None] = None):
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
	def canHandleExtension(extension: Dict[str, Any]) -> bool:
		return (
				isinstance(extension, dict) and
				"type" in extension and (
						(
								(extension["type"] == "select" or extension["type"].startswith("select.")) and
								not extension.get("multiple", False)
						)
						or (extension["type"] == "selectone" or extension["type"].startswith("selectone."))
				)
		)


class SelectOneEditBone(BoneEditInterface):
	def __init__(
			self,
			moduleName: str,
			boneName: str,
			readOnly: bool,
			values: List[Tuple[str, Any]],
			sortBy: str="keys",
			editWidget: Union[QtWidgets.QWidget, None] = None,
			*args: Any,
			**kwargs: Any):
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
		#if sortBy == "keys":
		#	tmpList.sort(key=lambda x: x[0])  # Sort by keys
		#else:
		#	tmpList.sort(key=lambda x: x[1])  # Values
		self.comboBox.addItems([x[1] for x in tmpList])

	@staticmethod
	def fromSkelStructure(
			moduleName: str,
			boneName: str,
			skelStructure: Dict[str, Any],
			**kwargs: Any) -> Any:
		myStruct = skelStructure[boneName]
		readOnly = "readonly" in myStruct and myStruct["readonly"]
		if "sortBy" in myStruct:
			sortBy = myStruct["sortBy"]
		else:
			sortBy = "keys"
		values = list(myStruct["values"])
		if "required" not in myStruct or not myStruct["required"]:
			values.insert(0, ["", ""])
		widgetGen = lambda: SelectOneEditBone(moduleName, boneName, readOnly, values=values, sortBy=sortBy, **kwargs)
		if myStruct.get("languages"):
			preLangWidgetGen = widgetGen
			widgetGen = lambda: LanguageContainer(myStruct["languages"], preLangWidgetGen)
		return widgetGen()

	def unserialize(self, data: Dict[str, Any]) -> None:
		if 1:  # There might be junk comming from the server
			items = dict([(str(k), str(v)) for k, v in self.values])
			if str(data) in items:
				self.comboBox.setCurrentIndex(self.comboBox.findText(items[str(data)]))
			else:
				self.comboBox.setCurrentIndex(-1)
		else:  # except:
			self.comboBox.setCurrentIndex(-1)

	def serializeForPost(self) -> Dict[str, Any]:
		currentValue = str(self.comboBox.currentText())
		for key, value in self.values:
			if str(value) == currentValue:
				return str(key)
		return None


def CheckForSelectOneBone(
		moduleName: str,
		boneName: str,
		skelStucture: Dict[str, Any]) -> bool:
	isSelect = skelStucture[boneName]["type"] == "select" or skelStucture[boneName]["type"].startswith("select.")
	return isSelect and not skelStucture[boneName]["multiple"]


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForSelectOneBone, SelectOneEditBone)
viewDelegateSelector.insert(2, CheckForSelectOneBone, SelectOneViewBoneDelegate)
extendedSearchWidgetSelector.insert(1, ExtendedSelectOneFilterPlugin.canHandleExtension, ExtendedSelectOneFilterPlugin)
