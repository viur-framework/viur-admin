# -*- coding: utf-8 -*-

from html import unescape as unescapeHtml
from typing import Union, List, Dict, Any, Callable

from PyQt5 import QtWidgets, QtGui, QtCore

from viur_admin.bones.base import BaseViewBoneDelegate, LanguageContainer, MultiContainer
from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.config import conf
from viur_admin.event import event
from viur_admin.log import getLogger
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector, extendedSearchWidgetSelector
from viur_admin.ui.extendedStringSearchPluginUI import Ui_Form
from viur_admin.utils import wheelEventFilter, ViurTabBar
from viur_admin.bones.numeric import FixedQDoubleSpinBox

logger = getLogger(__name__)



class SpatialViewBoneDelegate(BaseViewBoneDelegate):
	def displayText(self, value: str, locale: QtCore.QLocale) -> str:
		return str(value)


class SpatialEditBone(BoneEditInterface):
	def __init__(
			self,
			moduleName: str,
			boneName: str,
			readOnly: bool,
			multiple: bool = False,
			languages: List[str] = None,
			editWidget: Union[QtWidgets.QWidget, None] = None,
			*args: Any,
			**kwargs: Any):
		super(SpatialEditBone, self).__init__(moduleName, boneName, readOnly, editWidget=editWidget, *args, **kwargs)
		self.setLayout(QtWidgets.QVBoxLayout(self))
		self.lat = FixedQDoubleSpinBox(self)
		self.lat.setDecimals(10)
		self.layout().addWidget(self.lat)
		self.lat.show()
		self.lat.setReadOnly(self.readOnly)
		self.lng = FixedQDoubleSpinBox(self)
		self.lng.setDecimals(10)
		self.layout().addWidget(self.lng)
		self.lng.show()
		self.lng.setReadOnly(self.readOnly)
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		self.installEventFilter(wheelEventFilter)

	@staticmethod
	def fromSkelStructure(
			moduleName: str,
			boneName: str,
			skelStructure: Dict[str, Any],
			**kwargs: Any) -> Any:
		myStruct = skelStructure[boneName]
		readOnly = bool(myStruct.get("readonly"))
		widgetGen = lambda: SpatialEditBone(
			moduleName,
			boneName,
			readOnly,
			multiple=False,
			languages=None,
			**kwargs)
		if myStruct.get("multiple"):
			preMultiWidgetGen = widgetGen
			widgetGen = lambda: MultiContainer(preMultiWidgetGen)
		if myStruct.get("languages"):
			preLangWidgetGen = widgetGen
			widgetGen = lambda: LanguageContainer(myStruct["languages"], preLangWidgetGen)
		return widgetGen()


	def unserialize(self, data: Dict[str, Any], errors: List[Dict]) -> None:
		if not data:
			return
		try:
			lat, lng = data
		except:
			lat = lng = 0
		self.lat.setValue(lat)
		self.lng.setValue(lng)

	def serializeForPost(self) -> Dict[str, Any]:
		return {"lat": str(self.lat.value()), "lng": str(self.lng.value())}



def CheckForSpatialBone(moduleName: str, boneName: str, skelStucture: Dict[str, Any]) -> bool:
	return (skelStucture[boneName]["type"] == "spatial")


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForSpatialBone, SpatialEditBone)
viewDelegateSelector.insert(2, CheckForSpatialBone, SpatialViewBoneDelegate)
