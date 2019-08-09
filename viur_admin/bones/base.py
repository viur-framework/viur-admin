# -*- coding: utf-8 -*-
from typing import Any, Dict, List

from PyQt5 import QtCore, QtWidgets

from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector


class BaseViewBoneDelegate(QtWidgets.QStyledItemDelegate):
	request_repaint = QtCore.pyqtSignal()

	def __init__(
			self,
			moduleName: str,
			boneName: str,
			skelStructure: dict,
			*args: Any,
			**kwargs: Any):
		super().__init__(**kwargs)
		self.skelStructure = skelStructure
		self.boneName = boneName
		self.moduleName = moduleName


class BaseEditBone(BoneEditInterface):
	def __init__(
			self,
			moduleName: str,
			boneName: str,
			readOnly: bool,
			editWidget: QtWidgets.QWidget = None,
			*args: Any,
			**kwargs: Any):
		super(BaseEditBone, self).__init__(moduleName, boneName, readOnly, editWidget, *args, **kwargs)
		self.layout = QtWidgets.QHBoxLayout(self)
		self.lineEdit = QtWidgets.QLineEdit()
		self.layout.addWidget(self.lineEdit)
		self.setParams()
		self.lineEdit.show()

	def setParams(self) -> None:
		self.setEnabled(not self.readOnly)

	@staticmethod
	def fromSkelStructure(
			moduleName: str,
			boneName: str,
			skelStructure: dict,
			**kwargs: Any) -> Any:
		readOnly = "readonly" in skelStructure[boneName] and skelStructure[boneName]["readonly"]
		return BaseEditBone(moduleName, boneName, readOnly, **kwargs)

	def unserialize(self, data: dict) -> None:
		if self.boneName in data:
			self.lineEdit.setText(str(data[self.boneName]) if data[self.boneName] else "")

	def serializeForPost(self) -> dict:
		return {self.boneName: self.lineEdit.displayText()}

	def serializeForDocument(self) -> dict:
		return self.serialize()


# Register this Bone in the global queue
editBoneSelector.insert(0, lambda *args, **kwargs: True, BaseEditBone)
viewDelegateSelector.insert(0, lambda *args, **kwargs: True, BaseViewBoneDelegate)
