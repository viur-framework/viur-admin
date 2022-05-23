# -*- coding: utf-8 -*-
from typing import Any, Dict, List

from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.priorityqueue import editBoneSelector
from viur_admin.bones.base import BaseViewBoneDelegate, LanguageContainer, ListMultiContainer


class ClickableLineEdit(QtWidgets.QLineEdit):
	clicked = QtCore.pyqtSignal()

	def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
		self.clicked.emit()


class ColorEditBone(BoneEditInterface):
	def __init__(
			self,
			moduleName: str,
			boneName: str,
			readOnly: bool,
			required: bool,
			boneStructure: dict,
			**kwargs: Any):
		super(ColorEditBone, self).__init__(moduleName, boneName, readOnly, required, **kwargs)
		self.boneStructure = boneStructure
		lineLayout = QtWidgets.QHBoxLayout(self.editWidget)
		self.lineEdit = QtWidgets.QLineEdit(self.editWidget)
		self.button = QtWidgets.QPushButton('Auswählen', self.editWidget)
		self.colordisplay = ClickableLineEdit(self.editWidget)
		self.colordisplay.setReadOnly(readOnly is True)
		# self.lineEdit.editingFinished.connect(self.refreshColor)
		self.button.clicked.connect(self.showDialog)
		self.colordisplay.clicked.connect(self.showDialog)
		lineLayout.addWidget(self.lineEdit)
		lineLayout.addWidget(self.colordisplay)
		lineLayout.addWidget(self.button)

	@staticmethod
	def fromSkelStructure(
			moduleName: str,
			boneName: str,
			boneStructure: dict,
			**kwargs: Any) -> Any:
		readOnly = bool(boneStructure.get("readonly"))
		required = bool(boneStructure.get("required"))
		widgetGen = lambda: ColorEditBone(
			moduleName,
			boneName,
			readOnly,
			required,
			boneStructure,
			**kwargs)
		if boneStructure.get("multiple"):
			preMultiWidgetGen = widgetGen
			widgetGen = lambda: ListMultiContainer(preMultiWidgetGen)
		if boneStructure.get("languages"):
			preLangWidgetGen = widgetGen
			widgetGen = lambda: LanguageContainer(boneStructure["languages"], preLangWidgetGen)
		return widgetGen()

	def showDialog(self) -> None:
		acolor = QtWidgets.QColorDialog.getColor(
			QtGui.QColor(self.lineEdit.displayText()),
			self.lineEdit,
			self.boneStructure["descr"])
		if acolor.isValid():
			self.lineEdit.setText(acolor.name())
			self.refreshColor()

	def refreshColor(self) -> None:
		self.colordisplay.setStyleSheet("QWidget { background-color: %s }" % str(self.lineEdit.displayText()))

	def unserialize(self, data: dict, errors: List[Dict]) -> None:
		self.setErrors(errors)
		data = str(data) if data else ""
		self.lineEdit.setText(data)
		self.colordisplay.setStyleSheet("QWidget { background-color: %s }" % data)

	def serializeForPost(self) -> dict:
		return str(self.lineEdit.displayText())


def CheckForColorBone(
		moduleName: str,
		boneName: str,
		boneStructure: Dict[str, Any]) -> bool:
	return boneStructure["type"] == "color"


editBoneSelector.insert(2, CheckForColorBone, ColorEditBone)
