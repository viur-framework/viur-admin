# -*- coding: utf-8 -*-                                                                                                                                                                                                                                                        

import sys
from typing import Any, Dict, List, Union

from viur_admin.log import getLogger

logger = getLogger(__name__)

from collections import OrderedDict

from PyQt5 import QtCore, QtGui, QtWidgets
from viur_admin.bones.bone_interface import BoneEditInterface

from viur_admin.utils import Overlay, formatString
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector
from viur_admin.bones.base import BaseViewBoneDelegate, LanguageContainer, TabMultiContainer
from viur_admin import config
from viur_admin.widgets.edit import collectBoneErrors
from viur_admin.bones.relational import InternalEdit
import safeeval


class BaseBone:
	pass


class RecordViewBoneDelegate(BaseViewBoneDelegate):
	cantSort = True

	def __init__(
			self,
			module: str,
			boneName: str,
			boneStructure: Dict[str, Any]):
		super(RecordViewBoneDelegate, self).__init__(module, boneName, boneStructure)
		logger.debug("RecordViewBoneDelegate.init: %r, %r, %r", module, boneName, boneStructure)
		self.format = "$(name)"
		if "format" in boneStructure:
			self.format = boneStructure["format"]
		self.module = module
		self.boneStructure = boneStructure
		self.boneName = boneName
		self._cache = {}

	def displayText(self, value: dict, locale: QtCore.QLocale) -> str:
		logger.debug("RecordViewBoneDeleaget - value: %r, structure: %r", value, self.boneStructure)
		value = value.get(self.boneName)
		relStructList = self.boneStructure["using"]
		inValue = str(value)
		if inValue in self._cache:
			return self._cache[inValue]
		try:
			if isinstance(value, list):
				if relStructList:
					# logger.debug("RecordViewBoneDelegate.displayText: %r, %r, %r", self.boneName, self.format, self.structure)
					value = ", ".join([(formatString(
						formatString(
							self.format,
							x, self.boneStructure,
							language=config.conf.adminConfig["language"]),
						x, x, language=config.conf.adminConfig["language"]) or x[
											"key"]) for x in value])
				else:
					value = ", ".join([formatString(self.format, x, self.boneStructure,
													language=config.conf.adminConfig["language"]) for x in value])
			elif isinstance(value, dict):
				value = formatString(
					formatString(self.format, value, self.structure[self.boneName], prefix=[],
								 language=config.conf.adminConfig["language"]),
					value, value, language=config.conf.adminConfig["language"]) or value["key"]
		except Exception as err:
			logger.exception(err)
			# We probably received some garbage
			value = ""
		self._cache[inValue] = value
		return value


class RecordEditBone(BoneEditInterface):
	GarbageTypeName = "RecordEditBone"
	skelType = None

	def __init__(
			self,
			moduleName: str,
			boneName: str,
			readOnly: bool,
			required: bool,
			multiple: bool,
			using: Dict[str, Any] = None,
			format: str="$(name)",
			*args: Any,
			**kwargs: Any):
		super(RecordEditBone, self).__init__(moduleName, boneName, readOnly, required, *args, **kwargs)
		self.layout = QtWidgets.QVBoxLayout(self)
		self.setLayout(self.layout)
		logger.debug("RecordEditBone: %r, %r, %r", moduleName, boneName, readOnly)
		self.multiple = multiple
		self.using = using
		self.format = format
		self.overlay = Overlay(self)
		outerLayout = QtWidgets.QVBoxLayout(self.editWidget)
		self.internalEdit = InternalEdit(self.editWidget, self.using, "FIXME", {}, [])
		outerLayout.addWidget(self.internalEdit)
		self.errorLabel.hide()  # We'll display the errors in the TabMultiContainer


	@classmethod
	def fromSkelStructure(
			cls,
			moduleName: str,
			boneName: str,
			boneStructure: dict,
			**kwargs: Any) -> Any:
		#logger.debug("Recordbone.fromSkelStructure: %r, %r, %r", moduleName, boneName, skelStructure)
		myStruct = boneStructure
		readOnly = "readonly" in boneStructure and boneStructure["readonly"]
		required = "required" in boneStructure and boneStructure["required"]
		widgetGen = lambda: cls(
			moduleName,
			boneName,
			readOnly,
			required,
			boneStructure["multiple"],
			using=boneStructure["using"],
			format=boneStructure.get("format", "$(name)")
		)
		if myStruct.get("multiple"):
			viewDeleate = RecordViewBoneDelegate(moduleName, boneName, boneStructure)
			textFormatFunc = lambda x: viewDeleate.displayText(x, None)
			preMultiWidgetGen = widgetGen
			widgetGen = lambda: TabMultiContainer(preMultiWidgetGen, textFormatFunc)
		if myStruct.get("languages"):
			preLangWidgetGen = widgetGen
			widgetGen = lambda: LanguageContainer(myStruct["languages"], preLangWidgetGen)
		return widgetGen()


	def unserialize(self, data: Dict[str, Any], errors: List[Dict]) -> None:
		self.setErrors(errors)
		return self.internalEdit.unserialize(data or {}, errors)  # New, non-multipe record-bones may be none

	def serializeForPost(self) -> dict:
		return self.internalEdit.serializeForPost()

	def setErrors(self, errorList):  # Just forward to internalEdit
		self.internalEdit.setErrors(errorList)

	def getEffectiveMaximumBoneError(self, inOptionalContainer: bool = False) -> int:  # Just forward to internalEdit
		return self.internalEdit.getEffectiveMaximumBoneError(inOptionalContainer or not self.required)

def CheckForRecordBoneBone(
		moduleName: str,
		boneName: str,
		boneStructure: Dict[str, Any]) -> bool:
	return boneStructure["type"] == "record" or boneStructure["type"].startswith("record.")


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForRecordBoneBone, RecordEditBone)
viewDelegateSelector.insert(2, CheckForRecordBoneBone, RecordViewBoneDelegate)
