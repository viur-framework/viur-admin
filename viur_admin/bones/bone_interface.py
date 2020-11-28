# -*- coding: utf-8 -*-
from typing import Union, Any, Dict, List

from PyQt5 import QtWidgets, QtGui, QtCore


class BoneEditInterface(QtWidgets.QWidget):
	def __init__(
			self,
			moduleName: str,
			boneName: str,
			readOnly: bool,
			editWidget: Union[QtWidgets.QWidget, None] = None,
			*args: Any,
			**kwargs: Any):
		super(BoneEditInterface, self).__init__(*args, **kwargs)
		self.moduleName = moduleName
		self.boneName = boneName
		self.readOnly = readOnly
		self.editForm = editWidget  # Reference to Edit-Form
		self.editWidget =QtWidgets.QWidget()
		self.setLayout(QtWidgets.QVBoxLayout(self))
		self.layout().addWidget(self.editWidget)
		self.errorLabels = QtWidgets.QWidget()
		self.layout().addWidget(self.errorLabels)
		self.errorLabels.setLayout(QtWidgets.QVBoxLayout(self.errorLabels))
		#lbl = QtWidgets.QLabel("Test Error")
		#self.errorLabels.layout().addWidget(lbl)


	def setErrors(self, errorList):
		for i in reversed(range(self.errorLabels.layout().count())):
			self.errorLabels.layout().itemAt(i).widget().setParent(None)
		for error in errorList:
			dataWidget = QtWidgets.QWidget()
			layout = QtWidgets.QHBoxLayout(dataWidget)
			dataWidget.setLayout(layout)
			iconLbl = QtWidgets.QLabel(dataWidget)
			if 1 or error["severity"] >= 2:
				iconLbl.setPixmap(QtGui.QIcon(":icons/status/error.svg").pixmap(QtCore.QSize(32,32)))
			else:
				iconLbl.setPixmap(QtGui.QPixmap(":icons/status/incomplete.svg"))
			layout.addWidget(iconLbl, stretch=0)
			lbl = QtWidgets.QLabel(error["errorMessage"])
			layout.addWidget(lbl, stretch=1)
			self.errorLabels.layout().addWidget(dataWidget)

	@classmethod
	def fromSkelStructure(
			cls,
			moduleName: str,
			boneName: str,
			skelStructure: Dict[str, Any],
			**kwargs: Any) -> Any:
		raise NotImplementedError()

	def showDialog(self) -> None:
		raise NotImplementedError()

	def unserialize(self, data: Dict[str, Any], errors: List[Dict]) -> None:
		raise NotImplementedError()

	def serializeForPost(self) -> Dict[str, Any]:
		raise NotImplementedError()

	def serializeForDocument(self) -> Dict[str, Any]:
		return self.serializeForPost()
