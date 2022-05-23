#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Union, Any, List, Dict, Tuple

from PyQt5 import QtWidgets, QtGui, QtCore
from viur_admin.bones.bone_interface import BoneEditInterface

from viur_admin.priorityqueue import editBoneSelector


class AccessPushButton(QtWidgets.QPushButton):
	def __init__(self, bone: str, module: str, state: bool, parent: QtWidgets.QWidget = None):
		super(AccessPushButton, self).__init__(parent)
		self.setCheckable(True)
		self.bone = bone
		self.module = module
		self.state = state
		self.toggled.connect(self.onToggled)

	def onToggled(self, checked: bool) -> None:
		# self.bone.modules[self.module][self.state][1] = checked
		if checked and self.state != "view":
			self.bone.modules[self.module]["view"][0].setChecked(True)

		if not checked and self.state == "view":
			for item, isEnabled in self.bone.modules[self.module].values():
				if isEnabled:
					item.setChecked(False)
		self.bone.checkmodulesbox(self.module)


class AccessCheckBox(QtWidgets.QCheckBox):
	def __init__(self, bone: str, module: str, parent: QtWidgets.QWidget = None):
		super(AccessCheckBox, self).__init__(parent)
		self.bone = bone
		self.module = module
		self.clicked.connect(self.onStateChanged)

	def onStateChanged(self, clicked: bool) -> None:
		state = self.checkState()
		if state == QtCore.Qt.Checked:
			for item, isEnabled in self.bone.modules[self.module].values():
				if isEnabled:
					item.setChecked(True)
		elif state == QtCore.Qt.Unchecked:
			for item, isEnabled in self.bone.modules[self.module].values():
				if isEnabled:
					item.setChecked(False)


class AccessSelectMultiEditBone(BoneEditInterface):
	states = ["view", "edit", "add", "delete"]

	def __init__(
			self,
			moduleName: str,
			boneName: str,
			readOnly: bool,
			required: bool,
			values: list,
			sortBy: str = "keys",
			editWidget: Union[QtWidgets.QWidget, None] = None,
			*args: Any,
			**kwargs: Any):
		super(AccessSelectMultiEditBone, self).__init__(moduleName, boneName, readOnly, required, editWidget, *args, **kwargs)
		layout = QtWidgets.QVBoxLayout(self.editWidget)
		self.checkboxes: Dict[Any, Any] = dict()
		self.flags: Dict[Any, Any] = dict()
		self.modules: Dict[Any, Any] = dict()
		self.moduleBoxes: Dict[Any, Any] = dict()
		tmpList = values
		if sortBy == "keys":
			tmpList.sort(key=lambda x: x[0])  # Sort by keys
		else:
			tmpList.sort(key=lambda x: x[1])  # Values

		self.values = defaultValues = dict(tmpList)
		for key, value in tmpList:
			module = self.parseskelaccess(key)
			if not module:
				self.flags[value] = None
			elif module[0] not in self.modules:
				self.modules[module[0]] = {}

		for flag in sorted(self.flags):
			try:
				descr = defaultValues[flag]
			except KeyError:
				descr = flag
			cb = QtWidgets.QCheckBox(descr, self.editWidget)
			layout.addWidget(cb)
			cb.show()
			self.checkboxes[flag] = cb

		for module in sorted(self.modules):
			groupBox = QtWidgets.QGroupBox(module, self.editWidget)
			groupBoxLayout = QtWidgets.QHBoxLayout(groupBox)
			for ix, state in enumerate(self.states):
				key = "{0}-{1}".format(module, state)
				try:
					descr = defaultValues[key]
				except:
					descr = key
				cb = AccessPushButton(self, module, state, self.editWidget)
				if state == "view":
					iconName = "preview"
				else:
					iconName = state
				cb.setIcon(QtGui.QIcon(":icons/actions/{0}".format(iconName)))
				if key not in defaultValues:
					cb.setEnabled(False)

				cb.show()
				self.checkboxes[key] = cb
				self.modules[module][state] = [cb, key in defaultValues]
				groupBoxLayout.addWidget(cb)
			cb = AccessCheckBox(self, module, self)
			cb.setTristate(True)
			self.layout.addWidget(cb)
			cb.show()
			self.moduleBoxes[module] = cb
			groupBoxLayout.addWidget(cb)
			self.layout.addWidget(groupBox)

	def parseskelaccess(self, value: str) -> Union[Tuple[str, str], bool]:
		for state in self.states:
			if value.endswith(state):
				return value[0: -(len(state) + 1)], state

		return False

	def checkmodulesbox(self, module: str) -> None:
		on = 0
		all = 0

		for item, isEnabled in self.modules[module].values():
			if isEnabled:
				all += 1

			if item.isChecked():
				on += 1

		if on == 0 or on == all:
			self.moduleBoxes[module].setCheckState(on == all and QtCore.Qt.Checked or QtCore.Qt.Unchecked)
		else:
			self.moduleBoxes[module].setCheckState(QtCore.Qt.PartiallyChecked)

	@classmethod
	def fromSkelStructure(
			cls,
			moduleName: str,
			boneName: str,
			boneStructure: dict,
			**kwargs: Any) -> Any:
		readOnly = "readonly" in boneStructure and boneStructure["readonly"]
		required = "required" in boneStructure and boneStructure["required"]
		if "sortBy" in boneStructure:
			sortBy = boneStructure["sortBy"]
		else:
			sortBy = "keys"
		values = list(boneStructure["values"])
		return cls(
			moduleName,
			boneName,
			readOnly,
			required,
			values=values,
			sortBy=sortBy,
			**kwargs)

	def unserialize(self, data: Dict[str, Any], errors: List[Dict]) -> None:
		self.setErrors(errors)
		if self.boneName not in data:
			return
		for key, checkbox in self.checkboxes.items():
			checkbox.setChecked(key in data[self.boneName])

		for module in self.modules:
			self.checkmodulesbox(module)

	def serializeForPost(self) -> Dict[str, Any]:
		ret = []

		for name in self.flags:
			if self.checkboxes[name].isChecked():
				ret.append(name)

		for module in self.modules:
			for state in self.states:
				if self.modules[module][state][0].isChecked():
					ret.append("%s-%s" % (module, state))

		return {self.boneName: ret}

	def serializeForDocument(self) -> Dict[str, Any]:
		return self.serialize()


def CheckForAccessSelectMultiBone(moduleName: str, boneName: str, boneStructure: Dict[str, Any]) -> bool:
	return boneStructure["type"] in ("select.access", "selectmulti.access")


# Register this Bone in the global queue
editBoneSelector.insert(4, CheckForAccessSelectMultiBone, AccessSelectMultiEditBone)
