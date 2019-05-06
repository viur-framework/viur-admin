# -*- coding: utf-8 -*-                                                                                                                                                                                                                                                        

import sys

from viur_admin.log import getLogger

logger = getLogger(__name__)

from collections import OrderedDict

from PyQt5 import QtCore, QtGui, QtWidgets
from viur_admin.bones.bone_interface import BoneEditInterface

from viur_admin.utils import formatString, Overlay
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector
from viur_admin.bones.base import BaseViewBoneDelegate
from viur_admin import config


class BaseBone:
	pass


class RecordViewBoneDelegate(BaseViewBoneDelegate):
	cantSort = True

	def __init__(self, module, boneName, structure):
		super(RecordViewBoneDelegate, self).__init__(module, boneName, structure)
		logger.debug("RecordViewBoneDelegate.init: %r, %r, %r", module, boneName, structure[self.boneName])
		self.format = "$(name)"
		if "format" in structure[boneName]:
			self.format = structure[boneName]["format"]
		self.module = module
		self.structure = structure
		self.boneName = boneName

	def displayText(self, value, locale):
		logger.debug("RecordViewBoneDeleaget - value: %r, structure: %r", value, self.structure[self.boneName])
		relStructList = self.structure[self.boneName]["using"]
		try:
			if isinstance(value, list):
				if relStructList:
					# logger.debug("RecordViewBoneDelegate.displayText: %r, %r, %r", self.boneName, self.format, self.structure.keys())
					value = "\n".join([(formatString(
						formatString(self.format, x, self.structure[self.boneName],
						             language=config.conf.adminConfig["language"]),
						x, x, language=config.conf.adminConfig["language"]) or x[
						                    "key"]) for x in value])
				else:
					value = ", ".join([formatString(self.format, x, self.structure,
					                                language=config.conf.adminConfig["language"]) for x in value])
			elif isinstance(value, dict):
				value = formatString(
					formatString(self.format, value["dest"], self.structure[self.boneName]["relskel"], prefix=["dest"],
					             language=config.conf.adminConfig["language"]),
					value, value, language=config.conf.adminConfig["language"]) or value[
					        "key"]
		except Exception as err:
			logger.exception(err)
			# We probably received some garbage
			value = ""
		return value


class RecordBoneInternalEdit(QtWidgets.QWidget):
	def __init__(self, parent, using, values, errorInformation=None):
		super(RecordBoneInternalEdit, self).__init__(parent)
		self.layout = QtWidgets.QVBoxLayout(self)
		self.setLayout(self.layout)
		# self.groupBox = QtWidgets.QGroupBox("", self)
		# self.groupBox.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
		# self.groupBoxLayout = QtWidgets.QVBoxLayout(self)
		# self.groupBox.setLayout(self.groupBoxLayout)
		# self.layout.addWidget(self.groupBox)
		self.bonesLayout = QtWidgets.QFormLayout()
		self.bonesLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
		self.bonesLayout.setLabelAlignment(QtCore.Qt.AlignLeft)
		self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
		self.bones = OrderedDict()
		self.modul = "poll"
		self.values = values
		ignoreMissing = True
		tmpDict = dict()
		for key, bone in using:
			tmpDict[key] = bone

			if not bone["visible"]:
				continue
			wdgGen = editBoneSelector.select(self.modul, key, tmpDict)
			widget = wdgGen.fromSkelStructure(self.modul, key, tmpDict)
			if bone["error"] and not ignoreMissing:
				dataWidget = QtWidgets.QWidget()
				layout = QtWidgets.QHBoxLayout(dataWidget)
				dataWidget.setLayout(layout)
				layout.addWidget(widget, stretch=1)
				iconLbl = QtWidgets.QLabel(dataWidget)
				if bone["required"]:
					iconLbl.setPixmap(QtGui.QPixmap(":icons/status/error.png"))
				else:
					iconLbl.setPixmap(QtGui.QPixmap(":icons/status/incomplete.png"))
				layout.addWidget(iconLbl, stretch=0)
				iconLbl.setToolTip(str(bone["error"]))
			else:
				dataWidget = widget

			# TODO: Temporary MacOS Fix
			if sys.platform.startswith("darwin"):
				dataWidget.setMaximumWidth(500)
				dataWidget.setMinimumWidth(500)
			# TODO: Temporary MacOS Fix

			lblWidget = QtWidgets.QWidget(self)
			layout = QtWidgets.QHBoxLayout(lblWidget)
			if "params" in bone.keys() and isinstance(bone["params"], dict) and "tooltip" in bone["params"].keys():
				lblWidget.setToolTip(self.parseHelpText(bone["params"]["tooltip"]))
			descrLbl = QtWidgets.QLabel(bone["descr"], lblWidget)
			descrLbl.setWordWrap(True)

			if bone["required"]:
				font = descrLbl.font()
				font.setBold(True)
				font.setUnderline(True)
				descrLbl.setFont(font)
			layout.addWidget(descrLbl)
			self.bonesLayout.addRow(lblWidget, dataWidget)
			dataWidget.show()
			self.bones[key] = widget
		icon6 = QtGui.QIcon()
		icon6.addPixmap(QtGui.QPixmap(":icons/actions/cancel.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		buttonLabelWidget = QtWidgets.QWidget(self)
		buttonLabelLayout = QtWidgets.QHBoxLayout(buttonLabelWidget)
		buttonTrayWidget = QtWidgets.QWidget(self)
		buttonTrayLayout = QtWidgets.QHBoxLayout(buttonTrayWidget)
		self.delBtn = QtWidgets.QPushButton(QtCore.QCoreApplication.translate("InteralEdit", "Remove"), parent=self)
		self.delBtn.setIcon(icon6)
		self.delBtn.released.connect(self.onDelBtnReleased)
		spacerItem = QtWidgets.QSpacerItem(254, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
		buttonTrayLayout.addWidget(self.delBtn)
		buttonTrayLayout.addItem(spacerItem)
		self.bonesLayout.addRow(buttonLabelWidget, buttonTrayWidget)
		self.layout.addLayout(self.bonesLayout)
		self.unserialize(values)

	def unserialize(self, data):
		logger.debug("RecordBone.unserialize: %r", data)
		try:
			for bone in self.bones.values():
				logger.debug("RecordBoneInternalEdit.unserialize bone: %r", bone)
				bone.unserialize(data)
		except AssertionError as err:
			pass

	def serializeForPost(self):
		res = {}
		for key, bone in self.bones.items():
			data = bone.serializeForPost()
			# print("RecordBoneInternalEdit.serializeForPost: key, value", key, data)
			res.update(data)
		return res

	def onDelBtnReleased(self):
		pass


class RecordEditBone(BoneEditInterface):
	GarbageTypeName = "RecordEditBone"
	skelType = None

	def __init__(
			self,
			moduleName,
			boneName,
			readOnly,
			multiple,
			using=None,
			format="$(name)",
			*args,
			**kwargs):
		super(RecordEditBone, self).__init__(moduleName, boneName, readOnly, *args, **kwargs)
		logger.debug("RecordEditBone: %r, %r, %r", moduleName, boneName, readOnly)
		self.multiple = multiple
		self.using = using
		self.format = format
		self.overlay = Overlay(self)
		self.recordBoneInternalEdits = list()
		if not self.multiple:
			self.layout = QtWidgets.QHBoxLayout(self)
			self.previewIcon = None
		else:
			self.layout = QtWidgets.QVBoxLayout(self)
			self.previewWidget = QtWidgets.QListWidget(self)
			# self.previewWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
			self.previewWidget.setResizeMode(QtWidgets.QListView.Adjust)
			self.previewWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
			self.previewWidget.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
			self.previewWidget.setDefaultDropAction(QtCore.Qt.MoveAction)
			sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
			self.setSizePolicy(sizePolicy)
			self.previewWidget.setSizePolicy(sizePolicy)
			self.previewLayout = QtWidgets.QVBoxLayout(self.previewWidget)
			self.layout.addWidget(self.previewWidget)
		self.addBtn = QtWidgets.QPushButton(
			QtCore.QCoreApplication.translate("RecordEditBone", "Add Entry"),
			parent=self)
		iconadd = QtGui.QIcon()
		iconadd.addPixmap(QtGui.QPixmap(":icons/actions/add.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.addBtn.setIcon(iconadd)
		self.addBtn.released.connect(self.onAddBtnReleased)
		if not self.multiple:
			self.entry = QtWidgets.QLineEdit(self)
			self.layout.addWidget(self.entry)
			icon6 = QtGui.QIcon()
			icon6.addPixmap(QtGui.QPixmap(":icons/actions/cancel.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
			self.delBtn = QtWidgets.QPushButton("", parent=self)
			self.delBtn.setIcon(icon6)
			self.delBtn.released.connect(self.onDelBtnReleased)
			self.layout.addWidget(self.addBtn)
			self.layout.addWidget(self.delBtn)
			self.selection = None
		else:
			self.selection = []
			self.layout.addWidget(self.addBtn)

	@classmethod
	def fromSkelStructure(cls, moduleName, boneName, skelStructure, **kwargs):
		logger.debug("Recordbone.fromSkelStructure: %r, %r, %r", moduleName, boneName, skelStructure)
		readOnly = "readonly" in skelStructure[boneName].keys() and skelStructure[boneName]["readonly"]
		using = skelStructure[boneName]["using"]
		return cls(moduleName, boneName, readOnly, multiple=True, using=using,
		           format=skelStructure[boneName].get("format", "$(name)"))

	def updateVisiblePreview(self):
		logger.debug("updateVisiblePreview - start")
		if self.multiple:
			self.previewWidget.clear()
			logger.debug("updateVisiblePreview: record bone entries: %r, %r", len(self.selection), self.selection)
			if self.selection:
				if isinstance(self.selection, dict):
					self.selection = [self.selection]
				heightSum = 0
				for entry in self.selection:
					logger.debug("updateVisiblePreview item: %r, %r", self.using, entry)
					item = RecordBoneInternalEdit(self, self.using, entry)
					item.show()
					listItem = QtWidgets.QListWidgetItem(self.previewWidget)
					listItem.setSizeHint(item.sizeHint())
					self.previewWidget.addItem(listItem)
					self.previewLayout.addWidget(item)
					self.recordBoneInternalEdits.append(item)
					self.previewWidget.setItemWidget(listItem, item)
					heightSum += item.sizeHint().height()

				# itemHeight = heightSum / len(self.selection)
				# heightSum += itemHeight
				self.previewWidget.setFixedHeight(heightSum)
				self.addBtn.setText(QtCore.QCoreApplication.translate("RecordEditBone", "Add Entry"))
			logger.debug("updateVisiblePreview - end")

	def setSelection(self, selection):
		logger.debug("setSelection - start")
		if self.multiple:
			if isinstance(selection, dict):
				self.selection = [selection]
			else:
				self.selection = selection
		elif len(selection) > 0:
			self.selection = selection[0]
		else:
			self.selection = None
		logger.debug("setSelection - before called updateVisiblePreview")
		self.updateVisiblePreview()
		logger.debug("setSelection - end")

	def onAddBtnReleased(self, *args, **kwargs):
		newEntry = dict()
		for key, bone in self.using:
			newEntry[key] = None
			logger.debug("add new entry: %r, %r", key, bone)
		if isinstance(self.selection, dict):
			self.selection = [self.selection]
		self.selection.append(newEntry)
		self.updateVisiblePreview()

	def onDelBtnReleased(self, *args, **kwargs):
		if self.multiple:
			self.selection = []
		else:
			self.selection = None
		logger.debug("onDelBtnReleased - before called updateVisiblePreview")
		self.updateVisiblePreview()

	def unserialize(self, data):
		logger.debug("unserialize start")
		self.selection = data[self.boneName]
		logger.debug("unserialize: before calling updateVisiblePreview")
		self.updateVisiblePreview()
		logger.debug("unserialize end")

	def serializeForPost(self):
		if not self.selection:
			return {self.boneName: None}
		res = {}
		for ix, item in enumerate(self.recordBoneInternalEdits):
			entry = item.serializeForPost()
			if isinstance(entry, dict):
				for k, v in entry.items():
					res["{0}.{1}.{2}".format(self.boneName, ix, k)] = v
			else:
				res["{0}.{1}.key".format(self.boneName, ix)] = entry

		return res


def CheckForRecordBoneBone(moduleName, boneName, skelStucture):
	return skelStucture[boneName]["type"] == "record" or skelStucture[boneName]["type"].startswith("record.")


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForRecordBoneBone, RecordEditBone)
viewDelegateSelector.insert(2, CheckForRecordBoneBone, RecordViewBoneDelegate)