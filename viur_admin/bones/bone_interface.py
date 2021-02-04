# -*- coding: utf-8 -*-
from typing import Union, Any, Dict, List
from PyQt5 import QtWidgets, QtGui, QtCore
from viur_admin.pyodidehelper import isPyodide


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
		#self.errorLabels.setLayout(QtWidgets.QVBoxLayout(self.errorLabels))



	# lbl = QtWidgets.QLabel("Test Error")
	# self.errorLabels.layout().addWidget(lbl)

	def setErrors(self, errorList):
		maxError = 0
		errorTxt = []
		for error in errorList:
			if error["severity"] > maxError:
				maxError = error["severity"]
			errorTxt.append(error["errorMessage"])
		self.errorLabel.setToolTip("\n".join(errorTxt))
		if maxError == 1:
			self.errorLabel.setPixmap(QtGui.QIcon(":icons/status/info_normal.png").pixmap(QtCore.QSize(32, 32)))
		elif maxError == 3 or (maxError == 2 and self.required):
			self.errorLabel.setPixmap(QtGui.QIcon(":icons/status/info_bad.png").pixmap(QtCore.QSize(32, 32)))
		elif maxError == 2:
			self.errorLabel.setPixmap(QtGui.QIcon(":icons/status/info_okay.png").pixmap(QtCore.QSize(32, 32)))
		else:
			self.errorLabel.clear()

		#for i in reversed(range(self.errorLabels.layout().count())):
		#	self.errorLabels.layout().itemAt(i).widget().setParent(None)
		#for error in errorList:
		#	dataWidget = QtWidgets.QWidget()
		#	layout = QtWidgets.QHBoxLayout(dataWidget)
		#	dataWidget.setLayout(layout)
		#	iconLbl = QtWidgets.QLabel(dataWidget)
		##	if 1 or error["severity"] >= 2:
		#		iconLbl.setPixmap(QtGui.QIcon(":icons/status/error.svg").pixmap(QtCore.QSize(32, 32)))
		#	else:
		#		iconLbl.setPixmap(QtGui.QPixmap(":icons/status/incomplete.svg"))
		#	layout.addWidget(iconLbl, stretch=0)
		#	lbl = QtWidgets.QLabel(error["errorMessage"])
		#	layout.addWidget(lbl, stretch=1)
		#	self.errorLabels.layout().addWidget(dataWidget)

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
