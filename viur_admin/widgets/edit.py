# -*- coding: utf-8 -*-

import os
import os.path
import sys
from enum import Enum
from hashlib import sha1
from typing import Any, Dict, List, Tuple

from viur_admin.log import getLogger

logger = getLogger(__name__)

from collections import OrderedDict

from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.network import NetworkService, getFileNameForUrl, RequestWrapper
from viur_admin.event import event
from viur_admin.utils import Overlay
from viur_admin.config import conf
from viur_admin.ui.editUI import Ui_Edit
from viur_admin.priorityqueue import editBoneSelector
from viur_admin.priorityqueue import protocolWrapperInstanceSelector
from viur_admin.log import logToUser


class ApplicationType(Enum):
	LIST = 0
	HIERARCHY = 1
	TREE = 2
	SINGLETON = 3


def collectBoneErrors(errorList, currentKey):
	boneErrors = []
	for error in errorList:
		if error["fieldPath"] and error["fieldPath"][0] == currentKey:
			thisError = error.copy()
			thisError["fieldPath"] = error["fieldPath"][1:]
			boneErrors.append(thisError)
	return boneErrors

class EditWidget(QtWidgets.QWidget):

	def __init__(
			self,
			module: str,
			applicationType: ApplicationType,
			key: str = None,
			node: str = None,
			skelType: str = None,
			clone: bool = False,
			*args: Any,
			**kwargs: Any):
		"""
			Initialize a new Edit or Add-Widget for the given module.
			@param module: Name of the module
			@type module: String
			@param applicationType: Defines for what application this Add / Edit should be created. This hides
			additional complexity introduced by the hierarchy / tree-application
			@param key: id/key of the new entry. If None, It's a new entry, if clone it's the key of the entry we will clone
			@type key: str
			@param node: If applicationType==ApplicationType.HIERARCHY, the new entry will be added under this
			node, if ApplicationType.TREE the final node is derived from this and the path-parameter.
			Has no effect if applicationType is not HIERARCHY or TREE or if an id have been set.
			@type node: str
			@param clone: If true, it will load the values from the given key, but will save a new entry (i.e. allows
			"cloning" an existing entry)
			@type clone: bool
		"""
		super(EditWidget, self).__init__(*args, **kwargs)
		self.ui = Ui_Edit()
		self.ui.setupUi(self)
		protoWrap = protocolWrapperInstanceSelector.select(module)
		assert protoWrap is not None
		self.module = module

		# A Bunch of santy-checks, as there is a great chance to mess around with this widget
		if applicationType == ApplicationType.HIERARCHY or applicationType == ApplicationType.TREE:
			assert key or node  # Need either an id or an node

		if clone:
			assert key  # Need an id if we should clone an entry
			assert not applicationType == ApplicationType.SINGLETON  # We can't clone a singleton
			if applicationType == ApplicationType.HIERARCHY or applicationType == ApplicationType.TREE:
				assert node  # We still need a rootNode for cloning
		# End santy-checks
		self.applicationType = applicationType
		self.key = key
		self.node = node
		self.skelType = skelType
		self.clone = clone
		self.bones: Dict[str, Any] = dict()
		self.overlay = Overlay(self)
		self.overlay.inform(self.overlay.BUSY)
		self.dataCache: Dict[str, Any] = dict()
		self.closeOnSuccess = False
		# self._lastData = {}  # Dict of structure and values recived
		self.editTaskID = None
		self.reloadData()
		# Hide Previewbuttons if no PreviewURLs are set
		# if module in conf.serverConfig["modules"]:
		# 	if not "previewurls" in conf.serverConfig["modules"][self.module] \
		# 			or not conf.serverConfig["modules"][self.module]["previewurls"]:
		# 		self.ui.btnPreview.hide()
		if module == "_tasks":
			self.ui.btnSaveClose.setText(QtCore.QCoreApplication.translate("EditWidget", "Execute"))
			self.ui.btnSaveContinue.hide()
			self.ui.btnReset.hide()
		self.ui.btnReset.released.connect(self.onBtnResetReleased)
		self.ui.btnSaveContinue.released.connect(self.onBtnSaveContinueReleased)
		self.ui.btnSaveClose.released.connect(self.onBtnSaveCloseReleased)
		self.ui.btnClose.released.connect(self.onBtnCloseReleased)
		if not self.key and not self.clone:
			self.ui.btnSaveClose.setText(QtCore.QCoreApplication.translate("EditWidget", "Save and Close"))
			self.ui.btnSaveContinue.setText(QtCore.QCoreApplication.translate("EditWidget", "Save and New"))
		else:
			self.ui.btnSaveClose.setText(QtCore.QCoreApplication.translate("EditWidget", "Save and Close"))
			self.ui.btnSaveContinue.setText(QtCore.QCoreApplication.translate("EditWidget", "Save and Continue"))
		protoWrap.busyStateChanged.connect(self.onBusyStateChanged)
		protoWrap.updatingSucceeded.connect(self.onSaveSuccess)
		protoWrap.updatingFailedError.connect(self.onSaveError)
		protoWrap.updatingDataAvailable.connect(self.onDataAvailable)
		self.overlay.inform(self.overlay.BUSY)

	def onBusyStateChanged(self, busy: str) -> None:
		if busy:
			self.overlay.inform(self.overlay.BUSY)
		else:
			self.overlay.clear()

	def getBreadCrumb(self) -> Any:
		if self.clone:
			descr = QtCore.QCoreApplication.translate("EditWidget", "Clone entry")
			icon = QtGui.QIcon(":icons/actions/clone.svg")
		elif self.key or self.applicationType == EditWidget.appSingleton:  # We're editing
			descr = QtCore.QCoreApplication.translate("EditWidget", "Edit entry")
			icon = QtGui.QIcon(":icons/actions/edit.svg")
		else:
			descr = QtCore.QCoreApplication.translate("EditWidget", "Add entry")
			icon = QtGui.QIcon(":icons/actions/add.svg")
		return descr, icon

	def onBtnCloseReleased(
			self,
			*args: Any,
			**kwargs: Any) -> None:
		event.emit("popWidget", self)

	def reloadData(self) -> None:
		# print("--RELOADING--")
		self.save({})
		return

	def save(self, data: dict) -> None:
		protoWrap = protocolWrapperInstanceSelector.select(self.module)
		assert protoWrap is not None
		if self.module == "_tasks":
			self.editTaskID = protoWrap.edit(self.key, **data)
		# request = NetworkService.request("/%s/execute/%s" % ( self.module, self.id ), data, secure=True,
		# successHandler=self.onSaveResult )
		elif self.applicationType == ApplicationType.LIST:  # Application: List
			if self.key and (not self.clone or not data):
				self.editTaskID = protoWrap.edit(self.key, **data)
			else:
				self.editTaskID = protoWrap.add(**data)
		elif self.applicationType == ApplicationType.HIERARCHY:  # Application: Hierarchy
			if self.key and (not self.clone or not data):
				self.editTaskID = protoWrap.edit(self.key, **data)
			else:
				self.editTaskID = protoWrap.add(self.node, **data)
		elif self.applicationType == ApplicationType.TREE:  # Application: Tree
			if self.key and not self.clone:
				self.editTaskID = protoWrap.edit(self.key, self.skelType, **data)
			else:
				self.editTaskID = protoWrap.add(self.node, self.skelType, **data)
		elif self.applicationType == ApplicationType.SINGLETON:  # Application: Singleton
			self.editTaskID = protoWrap.edit(**data)
		else:
			raise NotImplementedError()  # Should never reach this
		self.setDisabled(True)

	def onBtnResetReleased(
			self,
			*args: Any,
			**kwargs: Any) -> None:
		self.requestResetBox = QtWidgets.QMessageBox(
			QtWidgets.QMessageBox.Question,
			QtCore.QCoreApplication.translate("EditWidget", "Confirm reset"),
			QtCore.QCoreApplication.translate( "EditWidget", "Discard all unsaved changes?"),
			(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No),
			self
		)
		self.requestResetBox.buttonClicked.connect(self.reqDeleteCallback)
		self.requestResetBox.open()
		QtGui.QGuiApplication.processEvents()
		self.requestResetBox.adjustSize()

	def reqDeleteCallback(self, clickedBtn, *args, **kwargs):
		if clickedBtn == self.requestResetBox.button(self.requestResetBox.Yes):
			self.setData(data=self.dataCache)
		self.requestResetBox = None

	def parseHelpText(self, txt: str) -> str:
		"""Parses the HTML-Text txt and returns it with remote Images replaced with their local copies

		@type txt: String
		@param txt: HTML-Text
		@return: String
		"""
		res = ""
		while txt:
			idx = txt.find("<img src=")
			if idx == -1:
				res += txt
				return (res)
			startpos = txt.find("\"", idx + 8) + 1
			endpos = txt.find("\"", idx + 13)
			url = txt[startpos:endpos]
			res += txt[: startpos]
			res += getFileNameForUrl(url)  # FIXME: BROKEN
			txt = txt[endpos:]

			fileName = os.path.join(conf.currentPortalConfigDirectory, sha1(url.encode("UTF-8")).hexdigest())
			logger.debug("parseHelpText - url: %r", url)
			if not os.path.isfile(fileName):
				try:
					data = NetworkService.request(url)
				except:
					return None
				open(fileName, "w+b").write(data)
		return txt

	def setData(
			self,
			request: RequestWrapper = None,
			data: Dict[str, Any] = None,
			ignoreMissing: bool = False) -> None:
		"""
		Rebuilds the UI according to the skeleton received from server

		:param request: the request to handle
		:param data: The data received
		:param ignoreMissing: if missing data should be reported as errors
		"""
		assert request or data
		if request:
			data = NetworkService.decode(request)
		# Clear the UI
		while self.ui.tabWidget.count():
			item = self.ui.tabWidget.widget(0)
			if item and item.widget():
				if "remove" in dir(item.widget()):
					item.widget().remove()
			self.ui.tabWidget.removeTab(0)
		self.bones = OrderedDict()
		self.dataCache = data
		tmpDict = {}
		tabs: Dict[str, QtWidgets.QFormLayout] = dict()
		tmpTabs: List[Tuple[QtWidgets.QScrollArea, str]] = list()  # Sort tabs by their description
		tabMaxError: Dict[str, int] = {} # Map of max-error code per tap
		for key, bone in data["structure"]:
			tmpDict[key] = bone
		for key, bone in data["structure"]:
			if not bone["visible"]:
				continue

			if "params" in bone and bone["params"] and "category" in bone["params"]:
				tabName = bone["params"]["category"]
			else:
				tabName = QtCore.QCoreApplication.translate("EditWidget", "General")

			if tabName not in tabs:
				scrollArea = QtWidgets.QScrollArea()
				outerContainer = QtWidgets.QWidget(scrollArea)
				outerLayout = QtWidgets.QVBoxLayout(outerContainer)
				scrollArea.setWidget(outerContainer)
				containerWidget = QtWidgets.QWidget(outerContainer)
				outerLayout.addWidget(containerWidget, 1)
				formLayout = QtWidgets.QFormLayout(containerWidget)
				formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
				formLayout.setLabelAlignment(QtCore.Qt.AlignLeft)
				formLayout.setAlignment(QtCore.Qt.AlignTop)
				tabs[tabName] = formLayout
				containerWidget.setLayout(formLayout)
				containerWidget.setSizePolicy(
					QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred))
				tmpTabs.append((scrollArea, tabName))
				outerLayout.addStretch(100)
				scrollArea.setWidgetResizable(True)
			for error in data["errors"]:
				if error["fieldPath"] and error["fieldPath"][0] == key:
					severity = error["severity"]
					if severity == 2 and bone.get("required"):
						severity = 3
					if severity > tabMaxError.get(tabName, 0):
						tabMaxError[tabName] = severity
		tmpTabs.sort(key=lambda x: x[1])
		for scrollArea, tabName in tmpTabs:
			tabIndex = self.ui.tabWidget.addTab(scrollArea, tabName)
			maxErrCode = tabMaxError.get(tabName, 0)
			if maxErrCode == 1:
				self.ui.tabWidget.setTabIcon(tabIndex, QtGui.QIcon(":icons/status/info_normal.png"))
			elif maxErrCode == 2:
				self.ui.tabWidget.setTabIcon(tabIndex, QtGui.QIcon(":icons/status/info_okay.png"))
			elif maxErrCode == 3:
				self.ui.tabWidget.setTabIcon(tabIndex, QtGui.QIcon(":icons/status/info_bad.png"))
			else:
				self.ui.tabWidget.setTabIcon(tabIndex, QtGui.QIcon(":icons/status/info_good.png"))

		for key, bone in data["structure"]:
			if bone["visible"] == False:
				continue
			if "params" in bone and bone["params"] and "category" in bone["params"]:
				tabName = bone["params"]["category"]
			else:
				tabName = QtCore.QCoreApplication.translate("EditWidget", "General")
			# queue = RegisterQueue()
			# event.emit( QtCore.SIGNAL('requestBoneEditWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,
			# PyQt_PyObject)'),queue, self.module, key, tmpDict )
			# widget = queue.getBest()
			wdgGen = editBoneSelector.select(self.module, key, tmpDict)
			widget = wdgGen.fromSkelStructure(self.module, key, tmpDict, editWidget=self)
			widget.setSizePolicy(
				QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
			if 0 and bone["error"] and not ignoreMissing:
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
			if "params" in bone and isinstance(bone["params"], dict) and "tooltip" in bone["params"]:
				lblWidget.setToolTip(self.parseHelpText(bone["params"]["tooltip"]))
			descrLbl = QtWidgets.QLabel(bone["descr"], lblWidget)
			descrLbl.setWordWrap(True)

			if bone["required"]:
				font = descrLbl.font()
				font.setBold(True)
				font.setUnderline(True)
				descrLbl.setFont(font)
			layout.addWidget(descrLbl)
			tabs[tabName].addRow(lblWidget, dataWidget)
			dataWidget.show()
			self.bones[key] = widget

		self.unserialize(data["values"], data["errors"])
		# self._lastData = data
		# logger.debug("setData _lastData: %r", self._lastData)
		event.emit("rebuildBreadCrumbs()")

	# if self.overlay.status==self.overlay.BUSY:
	#	self.overlay.clear()

	def unserialize(self, data: Dict[str, Any], errors: List[Dict]) -> None:
		logger.debug("EditWidget.unserialize - start")
		try:
			for key, bone in self.bones.items():
				boneErrors = collectBoneErrors(errors, key)
				bone.unserialize(data.get(key), boneErrors)
		except AssertionError as err:
			logger.exception(err)
			self.overlay.inform(self.overlay.ERROR, str(err))
			self.ui.btnSaveClose.setDisabled(True)
			self.ui.btnSaveContinue.setDisabled(True)
		logger.debug("EditWidget.unserialize - end")

	def onBtnSaveContinueReleased(
			self,
			*args: Any,
			**kwargs: Any) -> None:
		self.closeOnSuccess = False
		# self.overlay.inform( self.overlay.BUSY )
		res: Dict[str, Any] = dict()
		for key, bone in self.bones.items():
			res[key] = bone.serializeForPost()
		self.save(res)

	def onBtnSaveCloseReleased(
			self,
			*args: Any,
			**kwargs: Any) -> None:
		self.closeOnSuccess = True
		# self.overlay.inform( self.overlay.BUSY )
		res: Dict[str, Any] = dict()
		for key, bone in self.bones.items():
			res[key] = bone.serializeForPost()
			#res.update(bone.serializeForPost())
		self.save(res)

	def onSaveSuccess(self, editTaskID: int) -> None:
		"""
			Adding/editing an entry just succeeded
		"""
		logger.debug("onSaveSuccess: %r, %r", editTaskID, self.editTaskID)
		if editTaskID != self.editTaskID:  # Not our task
			return
		self.setDisabled(False)
		logToUser(QtCore.QCoreApplication.translate("EditWidget", "Entry saved"))
		#self.overlay.inform(self.overlay.SUCCESS, QtCore.QCoreApplication.translate("EditWidget", "Entry saved"))
		if self.closeOnSuccess:
			event.emit('popWidget', self)
		else:
			self.reloadData()

	def onDataAvailable(self, editTaskID: int, data: dict, wasInitial: bool) -> None:
		"""
			Adding/editing failed, cause some required fields are missing/invalid
		"""
		logger.debug("onDataAvailable: %r, %r", editTaskID, self.editTaskID)
		if editTaskID != self.editTaskID:  # Not our task
			return
		self.setDisabled(False)
		self.setData(data=data, ignoreMissing=wasInitial)
		if not wasInitial:
			self.overlay.inform(self.overlay.MISSING, QtCore.QCoreApplication.translate("EditWidget", "Missing data"))

	def onSaveError(self, error: Any) -> None:
		"""
			Unspecified error on saving/editing
		"""
		#self.overlay.inform(
		#	self.overlay.ERROR,
		#	QtCore.QCoreApplication.translate("EditWidget", "There was an error saving your changes"))
		logToUser(QtCore.QCoreApplication.translate("EditWidget", "There was an error saving your changes"))
		self.setDisabled(False)
		return

	def taskAdded(self) -> None:
		QtWidgets.QMessageBox.information(
			self,
			QtCore.QCoreApplication.translate("EditWidget", "Task created"),
			QtCore.QCoreApplication.translate(
				"EditWidget",
				"The task was sucessfully created."),
			QtCore.QCoreApplication.translate("EditWidget", "Okay"))
		self.parent().deleteLater()
