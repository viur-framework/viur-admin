# -*- coding: utf-8 -*-
from typing import Any, Dict, List

from PyQt5 import QtCore, QtWidgets

from viur_admin.bones.base import BaseViewBoneDelegate
from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector


class PasswordViewBoneDelegate(BaseViewBoneDelegate):
	def displayText(self, value: str, locale: QtCore.QLocale) -> str:
		return ""


# class PasswordValidator(QtGui.QValidator):
# 	def __init__(self, lineEdit, lineEditCheck, parent):
# 		super().__init__(parent)
# 		self.lineEdit = lineEdit
# 		self.lineEditCheck = lineEditCheck


class PasswordEditBone(BoneEditInterface):
	def __init__(
			self,
			moduleName: str,
			boneName: str,
			readOnly: bool,
			required: bool,
			editWidget: QtWidgets.QWidget = None,
			*args: Any,
			**kwargs: Any):
		super().__init__(moduleName, boneName, readOnly, required, editWidget, *args, **kwargs)
		layout = QtWidgets.QVBoxLayout(self.editWidget)
		self.editWidget.setLayout(layout)
		self.lineEdit = QtWidgets.QLineEdit(self.editWidget)
		self.lineEdit.setEchoMode(QtWidgets.QLineEdit.Password)
		layout.addWidget(self.lineEdit)
		self.lineEdit.show()
		if not self.readOnly:
			self.lineEditCheck = QtWidgets.QLineEdit(self)
			self.lineEditCheck.setEchoMode(QtWidgets.QLineEdit.Password)
			self.lineEditCheck.show()
			# self.lineEditCheck.setValidator(PasswordValidator(self.lineEdit, self.lineEditCheck, self))
			self.lineEdit.textChanged.connect(self.validate)
			self.lineEditCheck.textChanged.connect(self.validate)
			self.validatorResult = QtWidgets.QLabel("", self)
			layout.addWidget(self.lineEditCheck)
			layout.addWidget(self.validatorResult)
		else:
			self.lineEdit.setReadOnly(True)

	def validate(self, payload: str) -> None:
		# FIXME: Prevent saving of form in this case?
		if self.lineEdit.text() == self.lineEditCheck.text():
			self.validatorResult.clear()
		else:
			self.validatorResult.setText("Passwords do not not match")


	@classmethod
	def fromSkelStructure(
			cls,
			moduleName: str,
			boneName: str,
			boneStructure: dict,
			**kwargs: Any) -> Any:
		readOnly = "readonly" in boneStructure and boneStructure["readonly"]
		required = "required" in boneStructure and boneStructure["required"]
		return PasswordEditBone(moduleName, boneName, readOnly, required, **kwargs)

	def onTabLanguageChanged(self, lang: str) -> None:
		if lang in self.langEdits:
			self.tabWidget.blockSignals(True)
			self.tabWidget.setCurrentWidget(self.langEdits[lang])
			self.tabWidget.blockSignals(False)

	def unserialize(self, data: dict, errors: List[Dict]) -> None:
		self.setErrors(errors)
		if not data:
			return
		self.lineEdit.setText(str(data))

	def serializeForPost(self) -> dict:
		text = self.lineEdit.text()
		if text:
			return self.lineEdit.text()
		return ""

	def serializeForDocument(self) -> dict:
		return self.serialize()


def CheckForPasswordBone(
		moduleName: str,
		boneName: str,
		boneStructure: Dict[str, Any]) -> bool:
	return boneStructure["type"] == "password"


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForPasswordBone, PasswordEditBone)
viewDelegateSelector.insert(2, CheckForPasswordBone, PasswordViewBoneDelegate)
