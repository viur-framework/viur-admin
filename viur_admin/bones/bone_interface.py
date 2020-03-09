# -*- coding: utf-8 -*-
from typing import Union, Any, Dict, List

from PyQt5 import QtWidgets


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
		self.editWidget = editWidget

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

	def unserialize(self, data: Dict[str, Any]) -> None:
		raise NotImplementedError()

	def serializeForPost(self) -> Dict[str, Any]:
		raise NotImplementedError()

	def serializeForDocument(self) -> Dict[str, Any]:
		return self.serializeForPost()
