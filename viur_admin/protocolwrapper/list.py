#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Sequence, Mapping, Union, Tuple, List, Any, Dict

from viur_admin.log import getLogger

logger = getLogger(__name__)

from collections import OrderedDict

from PyQt5 import QtCore, QtGui

from time import time
from viur_admin.network import NetworkService, RequestGroup, RequestWrapper
from viur_admin.priorityqueue import protocolWrapperClassSelector, protocolWrapperInstanceSelector


class ListWrapper(QtCore.QObject):
	maxCacheTime = 60  # Cache results for max. 60 Seconds
	updateDelay = 0  # Refresh instantly
	entitiesChanged = QtCore.pyqtSignal()
	entityAvailable = QtCore.pyqtSignal((object,))
	queryResultAvailable = QtCore.pyqtSignal((str,))
	busyStateChanged = QtCore.pyqtSignal((bool,))  # If true, im busy right now
	updatingSucceeded = QtCore.pyqtSignal((str,))  # Adding/Editing an entry succeeded
	updatingFailedError = QtCore.pyqtSignal((str,))  # Adding/Editing an entry failed due to network/server error
	updatingDataAvailable = QtCore.pyqtSignal((str, dict, bool))  # Adding/Editing an entry failed due to missing fields
	modulStructureAvailable = QtCore.pyqtSignal()  # We fetched the structure for this module and that data is now

	# avaiable

	def __init__(self, module: str, *args: Any, **kwargs: Any):
		super(ListWrapper, self).__init__()
		self.module = module
		self.dataCache: Mapping[str, dict] = {}
		self.viewStructure = None
		self.addStructure = None
		self.editStructure = None
		self.busy = True
		req = NetworkService.request(
			"/getStructure/%s" % self.module,
			successHandler=self.onStructureAvailable)
		protocolWrapperInstanceSelector.insert(1, self.checkForOurModul, self)
		self.deferredTaskQueue: List[Tuple[str, str]] = []
		self.checkBusyStatus()

	def checkBusyStatus(self) -> None:
		busy = False
		for child in self.children():
			if (isinstance(child, RequestWrapper) or isinstance(child, RequestGroup)) and not child.hasFinished:
				busy = True
				break
		if busy != self.busy:
			self.busy = busy
			self.busyStateChanged.emit(busy)
		QtGui.QGuiApplication.processEvents()
		QtCore.QCoreApplication.processEvents()

	def execNetworkAction(self, *args: Any, **kwargs: Any) -> RequestWrapper:
		"""
			Starts a QNetworkRequest in this context.
			All arguments are passed directly to NetworkService.request.
			This function ensures that all childs show the correct bussy-status
			and refresh their data if this request finishes.
		"""
		req = NetworkService.request(*args, parent=self, **kwargs)
		req.finished.connect(self.emitEntriesChanged)
		self.checkBusyStatus()
		return req

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
			elif stype == "addSkel":
				self.addStructure = structure
		self.modulStructureAvailable.emit()
		self.checkBusyStatus()

	def cacheKeyFromFilter(self, filters: dict) -> str:
		tmpList = list(filters.items())
		tmpList.sort(key=lambda x: x[0])
		return "&".join(["%s=%s" % (k, v) for (k, v) in tmpList])

	def queryData(self, **kwargs: Any) -> str:
		key = self.cacheKeyFromFilter(kwargs)
		if key in self.dataCache:
			if self.dataCache[key] is None:
				# We already started querying that key
				return key
			ctime, data, cursor = self.dataCache[key]
			if ctime + self.maxCacheTime > time():  # This cache-entry is still valid
				self.deferredTaskQueue.append(("queryResultAvailable", key))
				QtCore.QTimer.singleShot(25, self.execDefered)
				# callback( None, data, cursor )
				return key
		# Its a cache-miss or cache too old
		self.dataCache[key] = None
		r = NetworkService.request("/%s/list" % self.module, kwargs, successHandler=self.addCacheData)
		r.wrapperCbCacheKey = key
		self.checkBusyStatus()
		return key

	def queryEntry(self, key: str) -> str:
		if key in self.dataCache:
			QtCore.QTimer.singleShot(25, lambda *args, **kwargs: self.entityAvailable.emit(self.dataCache[key]))
			return key
		r = NetworkService.request("/%s/view/%s" % (self.module, key), successHandler=self.addCacheData)
		return key

	def execDefered(self, *args: Any, **kwargs: Any) -> None:
		action, key = self.deferredTaskQueue.pop(0)
		if action == "queryResultAvailable":
			self.queryResultAvailable.emit(key)
		self.checkBusyStatus()

	def addCacheData(self, req: RequestWrapper) -> None:
		data = NetworkService.decode(req)
		cursor = None
		if "cursor" in data:
			cursor = data["cursor"]
		if data["action"] == "list":
			self.dataCache[req.wrapperCbCacheKey] = (time(), data["skellist"], cursor)
			for skel in data["skellist"]:
				self.dataCache[skel["key"]] = skel
		elif data["action"] == "view":
			self.dataCache[data["values"]["key"]] = data["values"]
			self.entityAvailable.emit(data["values"])
		if hasattr(req, "wrapperCbCacheKey"):
			self.queryResultAvailable.emit(req.wrapperCbCacheKey)
		self.checkBusyStatus()

	def setSortIndex(self, key: str, sortIndex: Union[float, int]) -> str:
		req = NetworkService.request(
			"/{0}/setSortIndex/".format(self.module), params={"key": key, "index": sortIndex},
			secure=True,
			finishedHandler=self.onSaveResult)
		self.checkBusyStatus()
		setSortIndexTaskId = str(id(req))
		logger.debug("proto list setSortIndex task id: %r", setSortIndexTaskId)
		return setSortIndexTaskId

	def add(self, **kwargs: Any) -> str:
		req = NetworkService.request(
			"/%s/add/" % (self.module), kwargs, secure=(len(kwargs) > 0),
			finishedHandler=self.onSaveResult)
		if not kwargs:
			# This is our first request to fetch the data, dont show a missing hint
			req.wasInitial = True
		else:
			req.wasInitial = False
		self.checkBusyStatus()
		addTaskId = str(id(req))
		logger.debug("proto list add id: %r", addTaskId)
		return addTaskId

	def edit(self, key: str, **kwargs: Any) -> str:
		req = NetworkService.request(
			"/%s/edit/%s" % (self.module, key), kwargs, secure=(len(kwargs) > 0),
			finishedHandler=self.onSaveResult)
		if not kwargs:
			# This is our first request to fetch the data, dont show a missing hint
			req.wasInitial = True
		else:
			req.wasInitial = False
		self.checkBusyStatus()
		editTaskId = str(id(req))
		logger.debug("proto list edit id: %r", editTaskId)
		return editTaskId

	def deleteEntities(self, keys: Sequence[str]) -> None:
		if isinstance(keys, list):
			req = RequestGroup(finishedHandler=self.delayEmitEntriesChanged)
			for key in keys:
				r = NetworkService.request("/%s/delete" % self.module, {"key": key}, secure=True, parent=req)
				req.addQuery(r)
		else:  # We just delete one
			NetworkService.request(
				"/%s/delete/%s" % (self.module, id), secure=True,
				finishedHandler=self.delayEmitEntriesChanged)
		self.checkBusyStatus()

	def delayEmitEntriesChanged(self, *args: Any, **kwargs: Any) -> None:
		"""
			Give the GAE a chance to apply recent changes and then
			force all open views of that module to reload its data
		"""
		QtCore.QTimer.singleShot(self.updateDelay, self.emitEntriesChanged)
		self.checkBusyStatus()

	def resetOnError(self, *args: Any, **kwargs: Any) -> None:
		"""
			If one or more requests fail, flush our cache and force
			all listening widgets to reload.
		"""
		self.dataCache = {}
		self.entitiesChanged.emit()
		self.checkBusyStatus()

	def onSaveResult(self, req: RequestWrapper) -> None:
		try:
			data = NetworkService.decode(req)
		except:  # Something went wrong, call ErrorHandler
			self.updatingFailedError.emit(str(id(req)))
			QtCore.QTimer.singleShot(self.updateDelay, self.resetOnError)
			return
		if data["action"] in ["addSuccess", "editSuccess", "deleteSuccess", "setSortIndexSuccess"]:  # Saving succeeded
			QtCore.QTimer.singleShot(self.updateDelay, self.emitEntriesChanged)
			self.updatingSucceeded.emit(str(id(req)))
		else:  # There were missing fields
			self.updatingDataAvailable.emit(str(id(req)), data, req.wasInitial)
		self.checkBusyStatus()

	def emitEntriesChanged(self, *args: Any, **kwargs: Any) -> None:
		self.dataCache = {}
		self.entitiesChanged.emit()
		self.checkBusyStatus()


# self.emit( QtCore.SIGNAL("entitiesChanged()") )


def CheckForListModul(moduleName: str, moduleList: dict) -> bool:
	modulData = moduleList[moduleName]
	if "handler" in modulData and (
			modulData["handler"] == "base" or
			modulData["handler"] == "list" or modulData["handler"].startswith("list.")):
		return True
	return False


protocolWrapperClassSelector.insert(0, CheckForListModul, ListWrapper)
