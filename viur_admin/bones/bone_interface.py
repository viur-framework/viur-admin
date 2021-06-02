# -*- coding: utf-8 -*-
from typing import Union, Any, Dict, List
from PyQt5 import QtWidgets, QtGui, QtCore
from viur_admin.pyodidehelper import isPyodide
from viur_admin.utils import boneErrorCodeToIcon


class ToolTipLabel(QtWidgets.QLabel):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		#self.installEventFilter(self)
		self.qtip = QtWidgets.QToolTip #()
		self.helpText = ""
		self._pixCache = None
		#self.setMouseTracking(True)

	def setPixmap(self, a0: QtGui.QPixmap):
		self._pixCache = a0
		super().setPixmap(a0)

	def setToolTip(self, a0: str):
		self.helpText = a0

	def clear(self):
		self.helpText = ""
		super().clear()

	def enterEvent(self, event):
		if self.helpText:
			self.setText(self.helpText)

	def leaveEvent(self, a0: QtCore.QEvent):
		if self.helpText:
			self.setText("")
		if self._pixCache:
			self.setPixmap(self._pixCache)


class BoneEditInterface(QtWidgets.QWidget):
	def __init__(
			self,
			moduleName: str,
			boneName: str,
			readOnly: bool,
			required: bool,
			editWidget: Union[QtWidgets.QWidget, None] = None,
			*args: Any,
			**kwargs: Any):
		super(BoneEditInterface, self).__init__(*args, **kwargs)
		self.moduleName = moduleName
		self.boneName = boneName
		self.readOnly = readOnly
		self.required = required
		self.editForm = editWidget  # Reference to Edit-Form
		self.setLayout(QtWidgets.QHBoxLayout(self))
		self.editWidget = QtWidgets.QWidget()
		self.layout().addWidget(self.editWidget)
		self.errorLabel = ToolTipLabel() if isPyodide else QtWidgets.QLabel(self)  # Hack for broken Tooltips on WASM
		sp = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
		self.errorLabel.setSizePolicy(sp)
		self.layout().addWidget(self.errorLabel)
		self.errorSeverityList = [-1]
		#self.errorLabels.setLayout(QtWidgets.QVBoxLayout(self.errorLabels))

	def getEffectiveMaximumBoneError(self, inOptionalContainer: bool = False):
		maxErr = max(self.errorSeverityList)
		if maxErr == 2 or maxErr==0:
			if self.required and not inOptionalContainer:
				return 3
			elif 1 in self.errorSeverityList:
				return 1
			else:
				return -1
		else:
			return maxErr

	def setErrors(self, errorList):
		self.errorSeverityList = [-1]
		errorTxt = []
		for error in errorList:
			self.errorSeverityList.append(error["severity"])
			errorTxt.append(error["errorMessage"])
		self.errorLabel.setToolTip("\n".join(errorTxt))
		maxError = self.getEffectiveMaximumBoneError(False)
		if maxError == -1:
			self.errorLabel.clear()
		self.errorLabel.setPixmap(boneErrorCodeToIcon(maxError).pixmap(QtCore.QSize(32, 32)))

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
