# -*- coding: utf-8 -*-
from math import pow
from typing import Union, Dict, Any, List

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QIcon, QFocusEvent

from viur_admin.bones.base import BaseViewBoneDelegate, LanguageContainer, ListMultiContainer
from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.log import getLogger
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector
from viur_admin.utils import wheelEventFilter, loadIcon

logger = getLogger(__name__)


class FixedQSpinBox(QtWidgets.QSpinBox):
	"""
		Subclass of SpinBox which doesn't accept QWheelEvents if it doesnt have focus
	"""

	def __init__(self, *args: Any, **kwargs: Any):
		super(FixedQSpinBox, self).__init__(*args, **kwargs)
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		self.installEventFilter(wheelEventFilter)

	def focusInEvent(self, e: QFocusEvent) -> None:
		self.setFocusPolicy(QtCore.Qt.WheelFocus)
		super(FixedQSpinBox, self).focusInEvent(e)

	def focusOutEvent(self, e: QFocusEvent) -> None:
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		super(FixedQSpinBox, self).focusOutEvent(e)


class FixedQDoubleSpinBox(QtWidgets.QDoubleSpinBox):
	"""
		Subclass of QDoubleSpinBox which doesn't accept QWheelEvents if it doesnt have focus
	"""

	def __init__(self, *args: Any, **kwargs: Any):
		super(FixedQDoubleSpinBox, self).__init__(*args, **kwargs)
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		self.installEventFilter(wheelEventFilter)

	def focusInEvent(self, e: QFocusEvent) -> None:
		self.setFocusPolicy(QtCore.Qt.WheelFocus)
		super(FixedQDoubleSpinBox, self).focusInEvent(e)

	def focusOutEvent(self, e: QFocusEvent) -> None:
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		super(FixedQDoubleSpinBox, self).focusOutEvent(e)


class NumericViewBoneDelegate(BaseViewBoneDelegate):
	def displayText(self, value: dict, locale: QtCore.QLocale) -> None:
		value = value.get(self.boneName)
		if "precision" in self.boneStructure:
			try:
				if not self.boneStructure["precision"]:  # Its an int:
					value = str(int(value))
				else:
					value = ("%#." + str(int(self.boneStructure["precision"])) + "f") % value
			except Exception as err:
				#logger.exception(err)
				value = str(value)
		return value


class IndexSortViewBoneDelegate(BaseViewBoneDelegate):
	def __init__(
			self,
			moduleName: str,
			boneName: str,
			boneStructure: dict,
			*args: Any,
			**kwargs: Any):
		super(IndexSortViewBoneDelegate, self).__init__(moduleName, boneName, boneStructure, *args, **kwargs)
		self.icon = loadIcon("draggable")
		self.margin = 20
		self.mode = QIcon.Normal
		self.state = QIcon.On

	# logger.debug("IndexSortColumnDelegate")

	def displayText(self, value: str, locale: QtCore.QLocale) -> None:
		value = value.get(self.boneName)
		if "precision" in self.boneStructure:
			try:
				if not self.boneStructure["precision"]:  # Its an int:
					value = str(int(value))
				else:
					value = ("%#." + str(int(self.boneStructure["precision"])) + "f") % value
			except:
				value = str(value)
		return value

	def paint(self, painter: Any, option: Any, index: Any) -> None:
		# logger.debug("paint: %r, %r, %r", painter, option, index)
		super(self.__class__, self).paint(painter, option, index)

		# if option.state & QtWidgets.QStyle.State_MouseOver:
		# 	painter.fillRect(option.rect, option.palette.highlight())
		# if option.state & QtWidgets.QStyle.State_Selected:
		# 	painter.fillRect(option.rect, option.palette.highlight())
		actualSize = self.icon.actualSize(option.decorationSize, self.mode, self.state)
		option.decorationSize = QtCore.QSize(min(option.decorationSize.width(), actualSize.width()),
		                                     min(option.decorationSize.height(), actualSize.height()))
		# logger.debug("in delegate paint: %r, %r", actualSize, option)
		r = QtCore.QRect(QtCore.QPoint(), option.decorationSize)
		r.moveCenter(option.rect.center())
		r.setRight(option.rect.right() - self.margin)
		self.icon.paint(painter, r, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter, self.mode, self.state)

	def sizeHint(self, option: Any, index: Any) -> QtCore.QSize:
		return QtCore.QSize(20, 20)


class NumericEditBone(BoneEditInterface):
	def __init__(
			self,
			moduleName: str,
			boneName: str,
			readOnly: bool,
			required: bool,
			precision: int = 0,
			min: Union[int, float] = -pow(2, 30),
			max: Union[int, float] = pow(2, 30),
			*args: Any,
			**kwargs: Any):
		super(NumericEditBone, self).__init__(moduleName, boneName, readOnly, required, *args, **kwargs)
		self.precision = precision
		self.min = min
		self.max = max
		lineLayout = QtWidgets.QHBoxLayout(self.editWidget)
		if self.precision:
			self.lineEdit = FixedQDoubleSpinBox(self.editWidget)
			self.lineEdit.setDecimals(self.precision)
		else:  # Just ints
			self.lineEdit = FixedQSpinBox(self.editWidget)
		self.lineEdit.setRange(self.min, self.max)
		lineLayout.addWidget(self.lineEdit)

	@classmethod
	def fromSkelStructure(
			cls,
			moduleName: str,
			boneName: str,
			boneStructure: dict,
			**kwargs: Any) -> Any:
		readOnly = "readonly" in boneStructure and boneStructure["readonly"]
		precision = int(boneStructure["precision"]) if "precision" in boneStructure else 0
		if "min" in boneStructure and "max" in boneStructure:
			minVal = boneStructure["min"]
			maxVal = boneStructure["max"]
		else:
			minVal = -pow(2, 30)
			maxVal = pow(2, 30)
		myStruct = boneStructure
		readOnly = bool(myStruct.get("readonly"))
		required = bool(myStruct.get("required"))
		widgetGen = lambda: cls(
			moduleName,
			boneName,
			readOnly,
			required,
			precision=precision,
			min=minVal,
			max=maxVal,
			**kwargs)
		if myStruct.get("multiple"):
			preMultiWidgetGen = widgetGen
			widgetGen = lambda: ListMultiContainer(preMultiWidgetGen)
		if myStruct.get("languages"):
			preLangWidgetGen = widgetGen
			widgetGen = lambda: LanguageContainer(myStruct["languages"], preLangWidgetGen)
		return widgetGen()

	def unserialize(self, data: dict, errors: List[Dict]) -> None:
		self.setErrors(errors)
		if not self.precision:
			self.lineEdit.setValue(int(data) if data else 0)
		else:
			self.lineEdit.setValue(float(data) if data else 0)

	def serializeForPost(self) -> dict:
		return str(self.lineEdit.value())

	def serializeForDocument(self) -> dict:
		return self.serializeForPost()


def CheckForNumericBone(
		moduleName: str,
		boneName: str,
		boneStructure: Dict[str, Any]) -> bool:
	return boneStructure["type"] == "numeric"


# def CheckForSortIndexBone(moduleName, boneName, skelStucture):
# 	return (skelStucture[boneName]["type"] == "numeric" and boneName == "sortindex")


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForNumericBone, NumericEditBone)
viewDelegateSelector.insert(2, CheckForNumericBone, NumericViewBoneDelegate)
# viewDelegateSelector.insert(3, CheckForSortIndexBone, IndexSortViewBoneDelegate)
