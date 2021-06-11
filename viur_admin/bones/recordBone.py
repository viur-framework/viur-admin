# -*- coding: utf-8 -*-                                                                                                                                                                                                                                                        

import sys
from typing import Any, Dict, List, Union

from viur_admin.log import getLogger

logger = getLogger(__name__)

from collections import OrderedDict

from PyQt5 import QtCore, QtGui, QtWidgets
from viur_admin.bones.bone_interface import BoneEditInterface

from viur_admin.utils import Overlay
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
			structure: Dict[str, Any]):
		super(RecordViewBoneDelegate, self).__init__(module, boneName, structure)
		logger.debug("RecordViewBoneDelegate.init: %r, %r, %r", module, boneName, structure[self.boneName])
		self.format = "value['name']"
		if "format" in structure[boneName]:
			self.format = structure[boneName]["format"]
		self.module = module
		self.structure = structure
		self.boneName = boneName
		self.safeEval = safeeval.SafeEval()
		try:
			self.ast = self.safeEval.compile(self.format)
		except:
			self.ast = self.safeEval.compile("value['name']")

	def displayText(self, value: str, locale: QtCore.QLocale) -> str:
		logger.debug("RecordViewBoneDeleaget - value: %r, structure: %r", value, self.structure[self.boneName])
		relStructList = self.structure[self.boneName]["using"]
		try:
			if isinstance(value, list):
				tmpList = []
				for v in value:
					try:
						tmpList.append(self.safeEval.execute(self.ast, {
							"value": v,
							"structure": self.structure,
							"language": config.conf.adminConfig["language"]
						}))
					except Exception as e:
						logger.exception(e)
						tmpList.append("(invalid format string)")
				value = ", ".join(tmpList)
			elif isinstance(value, dict):
				try:
					value = self.safeEval.execute(self.ast, {
						"value": value,
						"structure": self.structure,
						"language": config.conf.adminConfig["language"]
					})
				except Exception as e:
					logger.exception(e)
					value = "(invalid format string)"
		except Exception as err:
			logger.exception(err)
			# We probably received some garbage
			value = ""
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
			skelStructure: dict,
			**kwargs: Any) -> Any:
		#logger.debug("Recordbone.fromSkelStructure: %r, %r, %r", moduleName, boneName, skelStructure)
		myStruct = skelStructure[boneName]
		readOnly = "readonly" in skelStructure[boneName] and skelStructure[boneName]["readonly"]
		required = "required" in skelStructure[boneName] and skelStructure[boneName]["required"]
		widgetGen = lambda: cls(
			moduleName,
			boneName,
			readOnly,
			required,
			skelStructure[boneName]["multiple"],
			using=skelStructure[boneName]["using"],
			format=skelStructure[boneName].get("format", "$(name)")
		)
		if myStruct.get("multiple"):
			viewDeleate = RecordViewBoneDelegate(moduleName, boneName, skelStructure)
			textFormatFunc = lambda x: viewDeleate.displayText(x, None)
			preMultiWidgetGen = widgetGen
			widgetGen = lambda: TabMultiContainer(preMultiWidgetGen, textFormatFunc)
		if myStruct.get("languages"):
			preLangWidgetGen = widgetGen
			widgetGen = lambda: LanguageContainer(myStruct["languages"], preLangWidgetGen)
		return widgetGen()


	def unserialize(self, data: Dict[str, Any], errors: List[Dict]) -> None:
		self.setErrors(errors)
		return self.internalEdit.unserialize(data, errors)

	def serializeForPost(self) -> dict:
		return self.internalEdit.serializeForPost()

	def setErrors(self, errorList):  # Just forward to internalEdit
		self.internalEdit.setErrors(errorList)

	def getEffectiveMaximumBoneError(self, inOptionalContainer: bool = False) -> int:  # Just forward to internalEdit
		return self.internalEdit.getEffectiveMaximumBoneError(inOptionalContainer or not self.required)

def CheckForRecordBoneBone(
		moduleName: str,
		boneName: str,
		skelStucture: Dict[str, Any]) -> bool:
	return skelStucture[boneName]["type"] == "record" or skelStucture[boneName]["type"].startswith("record.")


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForRecordBoneBone, RecordEditBone)
viewDelegateSelector.insert(2, CheckForRecordBoneBone, RecordViewBoneDelegate)
