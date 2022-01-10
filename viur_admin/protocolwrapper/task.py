#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Any, Dict, List

from PyQt5 import QtCore

from viur_admin.network import NetworkService, RequestGroup, RequestWrapper
from viur_admin.priorityqueue import protocolWrapperInstanceSelector


class TaskWrapper(QtCore.QObject):
	maxCacheTime = 60  # Cache results for max. 60 Seconds
	updateDelay = 1500  # 1,5 seconds grace time before reloading

	updatingSucceeded = QtCore.pyqtSignal((str,))  # Adding/Editing an entry succeeded
	updatingFailedError = QtCore.pyqtSignal((str,))  # Adding/Editing an entry failed due to network/server error
	updatingDataAvailable = QtCore.pyqtSignal((str, dict, bool))  # Adding/Editing an entry failed due to missing fields
	modulStructureAvailable = QtCore.pyqtSignal()  # We fetched the structure for this module and that data is now available
	busyStateChanged = QtCore.pyqtSignal((bool,))  # If true, im busy right now

	def __init__(self, module: str, *args: Any, **kwargs: Any):
		super(TaskWrapper, self).__init__()
		self.module = module
		self.busy = False
		# self.editStructure = None # Warning: This depends on the currently edited task!!
		protocolWrapperInstanceSelector.insert(1, self.checkForOurModul, self)

	def checkForOurModul(self, moduleName: str) -> bool:
		return self.module == moduleName

	def edit(self, key: str, callback, **kwargs: Any) -> str:
		req = NetworkService.request(
			"/%s/execute/%s" % (self.module, key),
			kwargs,
			secure=(len(kwargs) > 0),
			finishedHandler=self.onSaveResult)
		if not kwargs:
			# This is our first request to fetch the data, dont show a missing hint
			req.wasInitial = True
		else:
			req.wasInitial = False
		req.callback = callback
		self.checkBusyStatus()
		return str(id(req))

	def editPreflight(self, key: str, data, callback) -> None:
		data["bounce"] = "1"
		data["skey"] = "-"
		url = "/%s/execute/%s" % (self.module, key)
		req = NetworkService.request(url, data, finishedHandler=callback)

	def onSaveResult(self, req: RequestWrapper) -> None:
		try:
			data = NetworkService.decode(req)
		except:  # Something went wrong, call ErrorHandler
			self.updatingFailedError.emit(str(id(req)))
			return
		if data["action"] in ["addSuccess"]:  # Saving succeeded
			#self.updatingSucceeded.emit(str(id(req)))
			#self.checkBusyStatus()
			req.callback(data)
		else:  # There were missing fields
			#self.updatingDataAvailable.emit(str(id(req)), data, req.wasInitial)
			req.callback(data)
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


TaskWrapper("_tasks")  # We statically instance exactly one taskWrapper
