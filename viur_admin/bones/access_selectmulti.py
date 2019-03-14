#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets, QtGui, QtCore
from viur_admin.bones.bone_interface import BoneEditInterface

from viur_admin.priorityqueue import editBoneSelector


class AccessPushButton(QtWidgets.QPushButton):
	def __init__(self, bone, module, state, parent=None):
		super(AccessPushButton, self).__init__(parent)
		self.setCheckable(True)
		self.bone = bone
		self.module = module
		self.state = state
		self.toggled.connect(self.onToggled)

	def onToggled(self, checked):
		# self.bone.modules[self.module][self.state][1] = checked
		if checked and self.state != "view":
			self.bone.modules[self.module]["view"][0].setChecked(True)

		if not checked and self.state == "view":
			for item, isEnabled in self.bone.modules[self.module].values():
				if isEnabled:
					item.setChecked(False)
		self.bone.checkmodulesbox(self.module)


class AccessCheckBox(QtWidgets.QCheckBox):
	def __init__(self, bone, module, parent=None):
		super(AccessCheckBox, self).__init__(parent)
		self.bone = bone
		self.module = module
		self.clicked.connect(self.onStateChanged)

	def onStateChanged(self, clicked):
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

	def __init__(self, moduleName, boneName, readOnly, values, sortBy="keys", editWidget=None, *args, **kwargs):
		super(AccessSelectMultiEditBone, self).__init__(moduleName, boneName, readOnly, editWidget, *args, **kwargs)
		self.layout = QtWidgets.QVBoxLayout(self)
		self.checkboxes = {}
		self.flags = {}
		self.modules = {}
		self.moduleBoxes = {}
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
			elif module[0] not in self.modules.keys():
				self.modules[module[0]] = {}

		for flag in sorted(self.flags.keys()):
			try:
				descr = defaultValues[flag]
			except KeyError:
				descr = flag
			cb = QtWidgets.QCheckBox(descr, self)
			self.layout.addWidget(cb)
			cb.show()
			self.checkboxes[flag] = cb

		for module in sorted(self.modules.keys()):
			groupBox = QtWidgets.QGroupBox(module, self)
			groupBoxLayout = QtWidgets.QHBoxLayout(groupBox)
			for ix, state in enumerate(self.states):
				key = "{0}-{1}".format(module, state)
				try:
					descr = defaultValues[key]
				except:
					descr = key
				cb = AccessPushButton(self, module, state, self)
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

	def parseskelaccess(self, value):
		for state in self.states:
			if value.endswith(state):
				return value[0: -(len(state) + 1)], state

		return False

	def checkmodulesbox(self, module):
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

	@staticmethod
	def fromSkelStructure(moduleName, boneName, skelStructure, **kwargs):
		readOnly = "readonly" in skelStructure[boneName].keys() and skelStructure[boneName]["readonly"]
		if "sortBy" in skelStructure[boneName].keys():
			sortBy = skelStructure[boneName]["sortBy"]
		else:
			sortBy = "keys"
		values = list(skelStructure[boneName]["values"])
		return AccessSelectMultiEditBone(moduleName, boneName, readOnly, values=values, sortBy=sortBy, **kwargs)

	def unserialize(self, data):
		if self.boneName not in data.keys():
			return
		for key, checkbox in self.checkboxes.items():
			checkbox.setChecked(key in data[self.boneName])

		for module in self.modules.keys():
			self.checkmodulesbox(module)

	def serializeForPost(self):
		ret = []

		for name in self.flags.keys():
			if self.checkboxes[name].isChecked():
				ret.append(name)

		for module in self.modules.keys():
			for state in self.states:
				if self.modules[module][state][0].isChecked():
					ret.append("%s-%s" % (module, state))

		return {self.boneName: ret}

	def serializeForDocument(self):
		return self.serialize()


def CheckForAccessSelectMultiBone(moduleName, boneName, skelStucture):
	return skelStucture[boneName]["type"] in ("select.access", "selectmulti.access")


# Register this Bone in the global queue
editBoneSelector.insert(4, CheckForAccessSelectMultiBone, AccessSelectMultiEditBone)
