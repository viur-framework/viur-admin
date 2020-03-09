from datetime import datetime
from typing import Union, Any, Dict, List

from PyQt5 import QtCore, QtWidgets, QtGui

from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.priorityqueue import editBoneSelector, extendedSearchWidgetSelector
from viur_admin.ui.extendedDateRangeFilterPluginUI import Ui_Form
from viur_admin.utils import wheelEventFilter

try:
	_fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
	_fromUtf8 = lambda s: s


class FixedDateTimeEdit(QtWidgets.QDateTimeEdit):
	"""Subclass of SpinBox which doesn't accept QWheelEvents if it doesnt have focus
	"""

	def __init__(self, *args: Any, **kwargs: Any):
		super(FixedDateTimeEdit, self).__init__(*args, **kwargs)
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		self.installEventFilter(wheelEventFilter)

	def focusInEvent(self, e: QtGui.QFocusEvent) -> None:
		self.setFocusPolicy(QtCore.Qt.WheelFocus)
		super(FixedDateTimeEdit, self).focusInEvent(e)

	def focusOutEvent(self, e: QtGui.QFocusEvent) -> None:
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		super(FixedDateTimeEdit, self).focusOutEvent(e)


class FixedDateEdit(QtWidgets.QDateEdit):
	"""
		Subclass of SpinBox which doesn't accept QWheelEvents if it doesnt have focus
	"""

	def __init__(self, *args: Any, **kwargs: Any):
		super(FixedDateEdit, self).__init__(*args, **kwargs)
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		self.installEventFilter(wheelEventFilter)

	def focusInEvent(self, e: QtGui.QFocusEvent) -> None:
		self.setFocusPolicy(QtCore.Qt.WheelFocus)
		super(FixedDateEdit, self).focusInEvent(e)

	def focusOutEvent(self, e: QtGui.QFocusEvent) -> None:
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		super(FixedDateEdit, self).focusOutEvent(e)


class FixedTimeEdit(QtWidgets.QTimeEdit):
	"""Subclass of SpinBox which doesn't accept QWheelEvents if it does not have focus

	"""

	def __init__(self, *args: Any, **kwargs: Any):
		super(FixedTimeEdit, self).__init__(*args, **kwargs)
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		self.installEventFilter(wheelEventFilter)

	def focusInEvent(self, e: QtGui.QFocusEvent) -> None:
		self.setFocusPolicy(QtCore.Qt.WheelFocus)
		super(FixedTimeEdit, self).focusInEvent(e)

	def focusOutEvent(self, e: QtGui.QFocusEvent) -> None:
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		super(FixedTimeEdit, self).focusOutEvent(e)


class DateRangeFilterPlugin(QtWidgets.QGroupBox):
	def __init__(self, extension: Dict[Any, Any], parent: QtWidgets.QWidget = None):
		super(DateRangeFilterPlugin, self).__init__(parent)
		self.extension = extension
		# self.view = view
		# self.module = module
		self.ui = Ui_Form()
		self.ui.setupUi(self)
		self.setTitle(extension["name"])
		self.mutualExclusiveGroupTarget = "daterange-filter"
		self.mutualExclusiveGroupKey = extension["target"]

	@staticmethod
	def canHandleExtension(extension: Dict[Any, Any]) -> bool:
		return isinstance(extension, dict) and "type" in extension and (
				extension["type"] == "date" or extension["type"].startswith("date."))


class DateEditBone(BoneEditInterface):
	def __init__(
			self,
			moduleName: str,
			boneName: str,
			readOnly: bool,
			hasDate: bool,
			hasTime: bool,
			editWidget: Union[QtWidgets.QWidget, None] = None,
			*args: Any,
			**kwargs: Any):
		super(DateEditBone, self).__init__(moduleName, boneName, readOnly, editWidget=editWidget, *args, **kwargs)

		self.editWidget = editWidget
		self.boneName = boneName
		self.layout = QtWidgets.QHBoxLayout(self)

		self.time = hasTime
		self.date = hasDate

		# builds inputspecific Widgets
		if self.time and self.date:
			self.lineEdit = FixedDateTimeEdit(self)
			self.lineEdit.setGeometry(QtCore.QRect(170, 50, 250, 20))
			self.lineEdit.setAccelerated(False)
			self.lineEdit.setCalendarPopup(True)
		elif self.date:
			self.lineEdit = FixedDateEdit(self)
			self.lineEdit.setGeometry(QtCore.QRect(190, 90, 250, 22))
			self.lineEdit.setCalendarPopup(True)
		else:
			self.lineEdit = FixedTimeEdit(self)
			self.lineEdit.setGeometry(QtCore.QRect(190, 190, 250, 22))

		self.lineEdit.setObjectName(_fromUtf8(boneName))
		self.layout.addWidget(self.lineEdit)
		self.lineEdit.show()

	@classmethod
	def fromSkelStructure(
			cls,
			moduleName: str,
			boneName: str,
			skelStructure: dict,
			**kwargs: Any) -> Any:
		readOnly = "readonly" in skelStructure[boneName] and skelStructure[boneName]["readonly"]
		hasDate = skelStructure[boneName]["date"]
		hasTime = skelStructure[boneName]["time"]
		return DateEditBone(moduleName, boneName, readOnly, hasDate, hasTime, **kwargs)

	def unserialize(self, data: dict) -> None:
		value = None
		if self.boneName in data:
			value = str(data[self.boneName])
		self.dt = datetime.now()
		if self.time and self.date:  # date AND time
			try:
				self.dt = datetime.strptime(value, "%d.%m.%Y %H:%M:%S")
			except:
				pass
			self.lineEdit.setDateTime(
				QtCore.QDateTime(
					QtCore.QDate(self.dt.year, self.dt.month, self.dt.day),
					QtCore.QTime(self.dt.hour, self.dt.minute, self.dt.second)))
		elif self.date:  # date only
			try:
				self.dt = datetime.strptime(value, "%d.%m.%Y")
			except:
				pass
			self.lineEdit.setDate(QtCore.QDate(self.dt.year, self.dt.month, self.dt.day))
		else:  # time only
			try:
				self.dt = datetime.strptime(value, "%H:%M:%S")
			except:
				pass
			self.lineEdit.setTime(QtCore.QTime(self.dt.hour, self.dt.minute, self.dt.second))

	def serializeForPost(self) -> dict:
		# FIXME: what's about deleted or not set date / times?
		if self.time and self.date:  # date AND time
			arg = self.lineEdit.dateTime().toString("dd.MM.yyyy hh:mm:ss")
		elif self.date:  # date only
			arg = self.lineEdit.date().toString("dd.MM.yyyy")
		else:  # time only
			arg = self.lineEdit.time().toString("hh:mm:ss")

		return {self.boneName: arg}

	def serializeForDocument(self) -> dict:
		return self.serialize()


def CheckForDateBone(moduleName: str, boneName: str, skelStucture: Dict[str, Any]) -> bool:
	return skelStucture[boneName]["type"] == "date"


editBoneSelector.insert(2, CheckForDateBone, DateEditBone)
extendedSearchWidgetSelector.insert(1, DateRangeFilterPlugin.canHandleExtension, DateRangeFilterPlugin)
