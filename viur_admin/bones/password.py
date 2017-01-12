# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets, QtGui
from viur_admin.bones.bone_interface import BoneEditInterface

from viur_admin.bones.base import BaseViewBoneDelegate
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector


class PasswordViewBoneDelegate(BaseViewBoneDelegate):
	def displayText(self, value, locale):
		return ""


class PasswordValidator(QtGui.QValidator):
	def __init__(self, lineEdit, lineEditCheck, parent):
		super().__init__(parent)
		self.lineEdit = lineEdit
		self.lineEditCheck = lineEditCheck


class PasswordEditBone(BoneEditInterface):
	def __init__(self, moduleName, boneName, readOnly, editWidget=None, *args, **kwargs):
		super().__init__(moduleName, boneName, readOnly, editWidget, *args, **kwargs)
		layout = QtWidgets.QVBoxLayout(self)
		self.setLayout(layout)
		self.lineEdit = QtWidgets.QLineEdit(self)
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

	def validate(self, payload):
		if self.lineEdit.text() == self.lineEditCheck.text():
			self.validatorResult.clear()
			if self.editWidget:
				self.editWidget.ui.btnSaveContinue.setEnabled(True)
				self.editWidget.ui.btnSaveClose.setEnabled(True)
		else:
			self.validatorResult.setText("Passwords do not not match")
			if self.editWidget:
				self.editWidget.ui.btnSaveContinue.setEnabled(False)
				self.editWidget.ui.btnSaveClose.setEnabled(False)

	@staticmethod
	def fromSkelStructure(moduleName, boneName, skelStructure, **kwargs):
		readOnly = "readonly" in skelStructure[boneName].keys() and skelStructure[boneName]["readonly"]
		return PasswordEditBone(moduleName, boneName, readOnly, **kwargs)

	def onTabLanguageChanged(self, lang):
		if lang in self.langEdits.keys():
			self.tabWidget.blockSignals(True)
			self.tabWidget.setCurrentWidget(self.langEdits[lang])
			self.tabWidget.blockSignals(False)

	def unserialize(self, data):
		if self.boneName not in data.keys():
			return
		data = data[self.boneName]
		if not data:
			return
		self.lineEdit.setText(str(data))

	def serializeForPost(self):
		text = self.lineEdit.text()
		if text:
			return {self.boneName: self.lineEdit.text()}
		return {}

	def serializeForDocument(self):
		return self.serialize()


def CheckForPasswordBone(moduleName, boneName, skelStucture):
	return skelStucture[boneName]["type"] == "password"


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForPasswordBone, PasswordEditBone)
viewDelegateSelector.insert(2, CheckForPasswordBone, PasswordViewBoneDelegate)
