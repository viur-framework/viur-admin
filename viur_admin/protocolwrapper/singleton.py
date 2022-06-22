#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import OrderedDict
from typing import Tuple, Sequence, Dict, List, Any

from PyQt5 import QtCore

from viur_admin.network import NetworkService, RequestGroup, RequestWrapper
from viur_admin.priorityqueue import protocolWrapperClassSelector, protocolWrapperInstanceSelector


class SingletonWrapper(QtCore.QObject):
	maxCacheTime = 60  # Cache results for max. 60 Seconds
	updateDelay = 1500  # 1,5 Seconds gracetime before reloading

	updatingSucceeded = QtCore.pyqtSignal((str,))  # Adding/Editing an entry succeeded
	updatingFailedError = QtCore.pyqtSignal((str,))  # Adding/Editing an entry failed due to network/server error
	updatingDataAvailable = QtCore.pyqtSignal((str, dict, bool))  # Adding/Editing an entry failed due to missing fields
	modulStructureAvailable = QtCore.pyqtSignal()  # We fetched the structure for this module and that data is now
	# available
	busyStateChanged = QtCore.pyqtSignal((bool,))  # If true, im busy right now

	def __init__(self, module: str, *args: Any, **kwargs: Any):
		super(SingletonWrapper, self).__init__()
		self.module = module
		self.busy = True
		self.editStructure: Dict[str, Any] = None
		self.viewStructure: Dict[str, Any] = None
		protocolWrapperInstanceSelector.insert(1, self.checkForOurModul, self)
		self.deferredTaskQueue: Sequence[Tuple[str, str]] = list()
		req = NetworkService.request(
			"/getStructure/%s" % self.module,
			successHandler=self.onStructureAvailable)

	def checkForOurModul(self, moduleName: str) -> bool:
		return self.module == moduleName

	def onStructureAvailable(self, req: RequestWrapper) -> None:
		tmp = NetworkService.decode(req)
		if tmp is None:
			self.checkBusyStatus()
			return
		for stype, structlist in tmp.items():
			structure: OrderedDict = OrderedDict()
			for k, v in structlist:
				structure[k] = v
			if stype == "viewSkel":
				self.viewStructure = structure
			elif stype == "editSkel":
				self.editStructure = structure
		self.modulStructureAvailable.emit()
		self.checkBusyStatus()

	def edit(self, callback, **kwargs: Any) -> str:
		req = NetworkService.request(
			"/%s/edit" % self.module,
			kwargs, secure=(len(kwargs) > 0),
			finishedHandler=self.onSaveResult)
		if not kwargs:
			# This is our first request to fetch the data, dont show a missing hint
			req.wasInitial = True
		else:
			req.wasInitial = False
		req.callback = callback
		self.checkBusyStatus()
		return str(id(req))

	def onSaveResult(self, req: RequestWrapper) -> None:
		try:
			data = NetworkService.decode(req)
		except:  # Something went wrong, call ErrorHandler
			self.updatingFailedError.emit(str(id(req)))
			return
		if data["action"] in ["editSuccess", "deleteSuccess"]:  # Saving succeeded
			req.callback(data)
			#self.updatingSucceeded.emit(str(id(req)))
			#self.checkBusyStatus()
		else:  # There were missing fields
			req.callback(data)
			#self.updatingDataAvailable.emit(str(id(req)), data, req.wasInitial)
		self.checkBusyStatus()

	def checkBusyStatus(self) -> None:
		busy = False
		for child in self.children():
			if isinstance(child, RequestWrapper) or isinstance(child, RequestGroup):
				if not child.hasFinished:
					busy = True
					break
		if busy != self.busy:
			self.busy = busy
			self.busyStateChanged.emit(busy)


def CheckForSingletonModul(moduleName: str, moduleList: dict) -> bool:
	modulData = moduleList[moduleName]
	if "handler" in modulData and (
			modulData["handler"] == "singleton" or modulData["handler"].startswith("singleton.")):
		return True
	return False


protocolWrapperClassSelector.insert(0, CheckForSingletonModul, SingletonWrapper)
