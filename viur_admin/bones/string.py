# -*- coding: utf-8 -*-

from html import unescape as unescapeHtml
from typing import Union, List, Dict, Any, Callable

from PyQt5 import QtWidgets, QtGui, QtCore

from viur_admin.bones.base import BaseViewBoneDelegate, LanguageContainer, ListMultiContainer, chooseLang
from viur_admin.bones.bone_interface import BoneEditInterface

from viur_admin.event import event
from viur_admin.log import getLogger
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector, extendedSearchWidgetSelector, protocolWrapperInstanceSelector
from viur_admin.ui.extendedStringSearchPluginUI import Ui_Form
from viur_admin.utils import wheelEventFilter, ViurTabBar, loadIcon

logger = getLogger(__name__)




class StringViewBoneDelegate(BaseViewBoneDelegate):
	def isEditable(self):
		if self.boneStructure.get("readonly") or self.boneStructure.get("languages") \
				or self.boneStructure.get("multiple"):
			return False
		return True

	def createEditor(self, parent, option, index):
		protoWrap = protocolWrapperInstanceSelector.select(self.moduleName)
		assert protoWrap is not None
		skelStructure = protoWrap.editStructure
		wdgGen = editBoneSelector.select(self.moduleName, self.boneName, skelStructure[self.boneName])
		widget = wdgGen.fromSkelStructure(self.moduleName, self.boneName, skelStructure[self.boneName], editWidget=parent)
		widget.unserialize(self.editingItem.get(self.boneName), {})
		widget.setParent(parent)
		widget.layout().setSpacing(0)
		widget.layout().setContentsMargins(0, 0, 0, 0)
		QtCore.QTimer.singleShot(1, lambda: widget.lineEdit.setFocus())
		return widget

	def displayText(self, value: str, locale: QtCore.QLocale) -> str:
		value = value.get(self.boneName)
		if not value:
			return ""
		# print("StringViewBoneDelegate.displayText:", value, locale)
		if "multiple" in self.boneStructure:
			multiple = self.boneStructure["multiple"]
		else:
			multiple = False
		if "languages" in self.boneStructure:
			languages = self.boneStructure["languages"]
		else:
			languages = None
		if multiple and languages:
			try:
				value = ", ".join(chooseLang(value, languages, self.language))
			except:
				value = ""
		elif multiple and not languages:
			value = ", ".join(value)
		elif not multiple and languages:
			value = chooseLang(value, languages, self.language)
		else:  # Not multiple nor languages
			return value

	def commitDataCb(self, editor):
		protoWrap = protocolWrapperInstanceSelector.select(self.moduleName)
		assert protoWrap is not None
		self.editTaskID = protoWrap.edit(self.editingItem["key"], **{self.boneName: editor.serializeForPost()})
		self.editingModel = None
		self.editingIndex = None


class Tag(QtWidgets.QWidget):
	def __init__(
			self,
			tag: str,
			editMode: int,
			*args: Any,
			**kwargs: Any):
		# print("Tag.init", tag, editMode)
		super(Tag, self).__init__(*args, **kwargs)
		self.setLayout(QtWidgets.QHBoxLayout(self))
		self.tag = tag
		self.lblDisplay = QtWidgets.QLabel(tag, self)
		self.editField = QtWidgets.QLineEdit(tag, self)
		self.btnDelete = QtWidgets.QPushButton("Löschen", self)
		self.btnDelete.setIcon(loadIcon("cancel-cross"))
		self.layout().addWidget(self.lblDisplay)
		self.layout().addWidget(self.editField)
		self.layout().addWidget(self.btnDelete)
		if editMode:
			self.lblDisplay.hide()
			self.editField.show()
		else:
			self.lblDisplay.show()
			self.editField.hide()
		self.editField.editingFinished.connect(self.onEditingFinished)
		self.btnDelete.released.connect(self.deleteLater)
		self.lblDisplay.mousePressEvent = self.onEdit

	def onEdit(
			self,
			*args: Any,
			**kwargs: Any) -> None:
		self.lblDisplay.hide()
		self.editField.show()
		self.editField.setFocus()

	def onEditingFinished(
			self,
			*args: Any,
			**kwargs: Any) -> None:
		self.tag = self.editField.text()
		self.lblDisplay.setText(str(self.tag))
		self.lblDisplay.show()
		self.editField.hide()


class ExtendedStringFilterPlugin(QtWidgets.QGroupBox):
	def __init__(self, extension: Dict[str, Any], parent: Union[QtWidgets.QWidget, None] = None):
		super(ExtendedStringFilterPlugin, self).__init__(parent)
		self.extension = extension
		# self.view = view
		# self.module = module
		self.ui = Ui_Form()
		self.ui.setupUi(self)
		self.setTitle(extension["name"])

	@staticmethod
	def canHandleExtension(extension: Dict[str, Any]) -> bool:
		return (isinstance(extension, dict) and "type" in extension and (
				extension["type"] == "string" or extension["type"].startswith("string.")))


class StringEditBone(BoneEditInterface):
	def __init__(
			self,
			moduleName: str,
			boneName: str,
			readOnly: bool,
			required: bool,
			multiple: bool = False,
			languages: List[str] = None,
			editWidget: Union[QtWidgets.QWidget, None] = None,
			*args: Any,
			**kwargs: Any):
		super(StringEditBone, self).__init__(moduleName, boneName, readOnly, required, editWidget=editWidget, *args, **kwargs)
		self.editWidget.setLayout(QtWidgets.QVBoxLayout(self.editWidget))
		self.lineEdit = QtWidgets.QLineEdit(self.editWidget)
		self.editWidget.layout().addWidget(self.lineEdit)
		self.lineEdit.show()
		self.lineEdit.setReadOnly(self.readOnly)
		self.editWidget.setFocusPolicy(QtCore.Qt.StrongFocus)
		self.editWidget.installEventFilter(wheelEventFilter)


	@staticmethod
	def fromSkelStructure(
			moduleName: str,
			boneName: str,
			boneStructure: Dict[str, Any],
			**kwargs: Any) -> Any:
		readOnly = bool(boneStructure.get("readonly"))
		required = bool(boneStructure.get("required"))
		widgetGen = lambda: StringEditBone(
			moduleName,
			boneName,
			readOnly,
			required,
			multiple=False,
			languages=None,
			**kwargs)
		if boneStructure.get("multiple"):
			preMultiWidgetGen = widgetGen
			widgetGen = lambda: ListMultiContainer(preMultiWidgetGen)
		if boneStructure.get("languages"):
			preLangWidgetGen = widgetGen
			widgetGen = lambda: LanguageContainer(boneStructure["languages"], preLangWidgetGen)
		return widgetGen()

	def unserialize(self, data: Dict[str, Any], errors: List[Dict]) -> None:
		self.setErrors(errors)
		if not data:
			return
		self.lineEdit.setText(unescapeHtml(str(data)))

	def serializeForPost(self) -> Dict[str, Any]:
		return self.lineEdit.text()


def CheckForStringBone(moduleName: str, boneName: str, boneStructure: Dict[str, Any]) -> bool:
	return boneStructure["type"] == "str" or boneStructure["type"].startswith("str.")


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForStringBone, StringEditBone)
viewDelegateSelector.insert(2, CheckForStringBone, StringViewBoneDelegate)
extendedSearchWidgetSelector.insert(1, ExtendedStringFilterPlugin.canHandleExtension, ExtendedStringFilterPlugin)
