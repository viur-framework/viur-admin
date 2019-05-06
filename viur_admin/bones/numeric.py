# -*- coding: utf-8 -*-
from math import pow

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QIcon

from viur_admin.bones.bone_interface import BoneEditInterface

from viur_admin.bones.base import BaseViewBoneDelegate
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector
from viur_admin.utils import wheelEventFilter


class FixedQSpinBox(QtWidgets.QSpinBox):
	"""
		Subclass of SpinBox which doesn't accept QWheelEvents if it doesnt have focus
	"""

	def __init__(self, *args, **kwargs):
		super(FixedQSpinBox, self).__init__(*args, **kwargs)
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		self.installEventFilter(wheelEventFilter)

	def focusInEvent(self, e):
		self.setFocusPolicy(QtCore.Qt.WheelFocus)
		super(FixedQSpinBox, self).focusInEvent(e)

	def focusOutEvent(self, e):
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		super(FixedQSpinBox, self).focusOutEvent(e)


class FixedQDoubleSpinBox(QtWidgets.QDoubleSpinBox):
	"""
		Subclass of QDoubleSpinBox which doesn't accept QWheelEvents if it doesnt have focus
	"""

	def __init__(self, *args, **kwargs):
		super(FixedQDoubleSpinBox, self).__init__(*args, **kwargs)
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		self.installEventFilter(wheelEventFilter)

	def focusInEvent(self, e):
		self.setFocusPolicy(QtCore.Qt.WheelFocus)
		super(FixedQDoubleSpinBox, self).focusInEvent(e)

	def focusOutEvent(self, e):
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		super(FixedQDoubleSpinBox, self).focusOutEvent(e)


class NumericViewBoneDelegate(BaseViewBoneDelegate):
	def displayText(self, value, locale):
		if self.boneName in self.skelStructure.keys() and "precision" in self.skelStructure[self.boneName].keys():
			try:
				if not self.skelStructure[self.boneName]["precision"]:  # Its an int:
					value = str(int(value))
				else:
					value = ("%#." + str(int(self.skelStructure[self.boneName]["precision"])) + "f") % value
			except:
				value = str(value)
		return super(NumericViewBoneDelegate, self).displayText(value, locale)


class IndexSortViewBoneDelegate(BaseViewBoneDelegate):
	def __init__(self, moduleName, boneName, skelStructure, *args, **kwargs):
		super(IndexSortViewBoneDelegate, self).__init__(moduleName, boneName, skelStructure, *args, **kwargs)
		self.icon = QIcon(":icons/actions/icon-draggable.svg")
		self.margin = 20
		self.mode = QIcon.Normal
		self.state = QIcon.On
		# logger.debug("IndexSortColumnDelegate")

	def displayText(self, value, locale):
		if self.boneName in self.skelStructure.keys() and "precision" in self.skelStructure[self.boneName].keys():
			try:
				if not self.skelStructure[self.boneName]["precision"]:  # Its an int:
					value = str(int(value))
				else:
					value = ("%#." + str(int(self.skelStructure[self.boneName]["precision"])) + "f") % value
			except:
				value = str(value)
		return super(IndexSortViewBoneDelegate, self).displayText(value, locale)

	def paint(self, painter, option, index):
		# logger.debug("paint: %r, %r, %r", painter, option, index)
		super(self.__class__, self).paint(painter, option, index)

		# if option.state & QtWidgets.QStyle.State_MouseOver:
		# 	painter.fillRect(option.rect, option.palette.highlight())
		# if option.state & QtWidgets.QStyle.State_Selected:
		# 	painter.fillRect(option.rect, option.palette.highlight())
		actualSize = self.icon.actualSize(option.decorationSize, self.mode, self.state)
		option.decorationSize = QtCore.QSize(min(option.decorationSize.width(), actualSize.width()), min(option.decorationSize.height(), actualSize.height()))
		# logger.debug("in delegate paint: %r, %r", actualSize, option)
		r = QtCore.QRect(QtCore.QPoint(), option.decorationSize)
		r.moveCenter(option.rect.center())
		r.setRight(option.rect.right() - self.margin)
		self.icon.paint(painter, r, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter, self.mode, self.state)

	def sizeHint(self, option, index):
		return QtCore.QSize(20, 20)


class NumericEditBone(BoneEditInterface):
	def __init__(self, moduleName, boneName, readOnly, precision=0, min=-pow(2, 30), max=pow(2, 30), *args, **kwargs):
		super(NumericEditBone, self).__init__(moduleName, boneName, readOnly, *args, **kwargs)
		self.precision = precision
		self.min = min
		self.max = max
		lineLayout = QtWidgets.QHBoxLayout(self)
		if self.precision:
			self.lineEdit = FixedQDoubleSpinBox(self)
			self.lineEdit.setDecimals(self.precision)
		else:  # Just ints
			self.lineEdit = FixedQSpinBox(self)
		self.lineEdit.setRange(self.min, self.max)
		lineLayout.addWidget(self.lineEdit)

	@staticmethod
	def fromSkelStructure(moduleName, boneName, skelStructure, **kwargs):
		readOnly = "readonly" in skelStructure[boneName].keys() and skelStructure[boneName]["readonly"]
		precision = int(skelStructure[boneName]["precision"]) if "precision" in skelStructure[boneName].keys() else 0
		if "min" in skelStructure[boneName].keys() and "max" in skelStructure[boneName].keys():
			minVal = skelStructure[boneName]["min"]
			maxVal = skelStructure[boneName]["max"]
		else:
			minVal = -pow(2, 30)
			maxVal = pow(2, 30)
		return NumericEditBone(moduleName, boneName, readOnly, precision=precision, min=minVal, max=maxVal, **kwargs)

	def unserialize(self, data):
		if self.boneName not in data.keys():
			return
		if not self.precision:
			self.lineEdit.setValue(int(data[self.boneName]) if data[self.boneName] else 0)
		else:
			self.lineEdit.setValue(float(data[self.boneName]) if data[self.boneName] else 0)

	def serializeForPost(self):
		return {self.boneName: str(self.lineEdit.value())}

	def serializeForDocument(self):
		return self.serialize()


def CheckForNumericBone(moduleName, boneName, skelStucture):
	return (skelStucture[boneName]["type"] == "numeric")


# def CheckForSortIndexBone(moduleName, boneName, skelStucture):
# 	return (skelStucture[boneName]["type"] == "numeric" and boneName == "sortindex")


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForNumericBone, NumericEditBone)
viewDelegateSelector.insert(2, CheckForNumericBone, NumericViewBoneDelegate)
# viewDelegateSelector.insert(3, CheckForSortIndexBone, IndexSortViewBoneDelegate)
