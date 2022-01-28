#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import copy
import logging
from typing import Sequence, Mapping, Union, Tuple, List, Any, Dict

from viur_admin.log import getLogger, logToUser

logger = getLogger(__name__)

from collections import OrderedDict

from PyQt5 import QtCore, QtGui
from viur_admin.protocolwrapper.base import ProtocolWrapper
from time import time
from viur_admin.network import NetworkService, RequestGroup, RequestWrapper
from viur_admin.priorityqueue import protocolWrapperClassSelector, protocolWrapperInstanceSelector
from enum import Enum
from dataclasses import dataclass
from weakref import WeakSet

class RequestWrapperState(Enum):
	idle = 0
	bussy = 1
	initializing = 2

@dataclass
class QueryResult:
	entries: List[str]
	partial: bool
	cursorList: List[str]

class ListView():
	def __init__(self, callbackMap, listWrapper, filterDict):
		super().__init__()
		self.callbackMap = callbackMap
		self.listWrapper = listWrapper
		self.filterDict = filterDict
		self._hasQueryRunning = False
		self._cursorList = []
		self._keys = []
		self._canFetchMore = True  # Whereever there might be additional pages to fetch

	def fetchMore(self):
		if not self._hasQueryRunning:
			self.listWrapper.requestNextBatch(self)

	def getRow(self, row: int):
		if not (0 <= row < len(self._keys)):
			return None
		return self.listWrapper._entityCache[self._keys[row]]

	def emitEntityUpdated(self, key: str):
		if key in self._keys:
			cb = self.callbackMap.get("rowChanged")
			if cb:
				cb(self._keys.index(key), 1)

	@property
	def canFetchMore(self):
		return self._canFetchMore

class ListWrapper(ProtocolWrapper):
	insertRowsEvent = QtCore.pyqtSignal((int, int))  # New rows have been inserted (index, num-rows)
	removeRowsEvent = QtCore.pyqtSignal((int, int))  # Rows have been removed (index, num-rows)
	changeRowsEvent = QtCore.pyqtSignal((int, int))  # Rows have been changed (index, num-rows)

	def __init__(self, module: str, *args: Any, **kwargs: Any):
		super(ListWrapper, self).__init__()
		logging.error(("XXX LIST WRAP", module, args ))
		self.module = module
		self.status: RequestWrapperState = RequestWrapperState.initializing
		#self._filterIdMap = {}
		#self._entities: Dict[int, QueryResult] = {}
		self._entityCache = {}
		#self._runningRequests = {}
		self.busy = False ##FIXME - alt - nur für lade-bildschirm
		self.views = WeakSet()
		#self.queryCache: Mapping[str, dict] = {}  # Map of URL-Request params to a /list request to the entities returned
		#self.entryCache: Mapping[str, dict] = {}  # Map of str()-Keys of entries to their contents
		self.pendingDeletes = set()  # Set of database keys we've queued for deletion
		#self.viewStructure = None
		#self.addStructure = None
		#self.editStructure = None
		#self.busy = False
		protocolWrapperInstanceSelector.insert(1, self.checkForOurModul, self)
		req = NetworkService.request(
			"/getStructure/%s" % self.module,
			successHandler=self.onStructureAvailable)
		#protocolWrapperInstanceSelector.insert(1, self.checkForOurModul, self)
		#self.deferredTaskQueue: List[Tuple[str, str]] = []
		#self.checkBusyStatus()

	def onStructureAvailable(self, req: RequestWrapper) -> None:
		self.status: RequestWrapperState = RequestWrapperState.idle
		tmp = NetworkService.decode(req)
		if tmp is None:
			# FIXME : Error state?
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

	def registerView(self, queryDict, callbackMap):
		listView = ListView(callbackMap, self, queryDict)
		self.views.add(listView)
		return listView
		#for key, filterDict in self._filterIdMap.items():
		#	if filterDict == queryDict:
		#		return key
		#key = id(queryDict)
		#self._filterIdMap[key] = copy.deepcopy(queryDict)
		#self._entities[key] = QueryResult([], True, [])
		#return key

	def getRow(self, queryId, rowNumber):
		qResult = self._entities.get(queryId, None)
		if not qResult:
			return None
		if len(qResult.entries) > rowNumber:
			return self._entityCache[qResult.entries[rowNumber]]
		if qResult.partial:
			self.requestNextBatch(queryId)
		return None

	def requestNextBatch(self, listView):
		print("requestNextBatch", listView)
		queryDict = copy.deepcopy(listView.filterDict)
		if listView._cursorList:
			queryDict["cursor"] = listView._cursorList[-1]
		r = NetworkService.request("/%s/list" % self.module, queryDict, successHandler=self.addCacheData, failureHandler=self.fetchFailed)
		r.listView = listView

	def addCacheData(self, req: RequestWrapper) -> None:
		listView = req.listView
		listView._hasQueryRunning = False
		data = NetworkService.decode(req)
		cursor = None
		if "cursor" in data:
			cursor = data["cursor"]
			listView._cursorList.append(cursor)
		if data["action"] == "list":
			oldLength = len(listView._keys)
			if 0 and not oldLength:
				self.timer1 = QtCore.QTimer()
				self.timer1.timeout.connect(self.onTimer1)
				self.timer1.start(1000)
				self.remKey = [x["key"] for x in data["skellist"] if x["key"] not in self.pendingDeletes][3]
				self.remQuery = listView
			extLength = len(data["skellist"])
			preCb = listView.callbackMap.get("beforeInsertRows")
			if preCb:
				preCb(oldLength, extLength)
			listView._keys.extend([x["key"] for x in data["skellist"] if x["key"] not in self.pendingDeletes])
			for skel in data["skellist"]:
				if skel["key"] in self.pendingDeletes:
					continue
				self._entityCache[skel["key"]] = skel
			postCb = listView.callbackMap.get("afterInsertRows")
			if postCb:
				postCb(oldLength, extLength)
			if extLength == 0 and not cursor:
				listView._canFetchMore = False
		elif data["action"] == "view":
			assert False
			self.entryCache[data["values"]["key"]] = data["values"]
			self.entityAvailable.emit(data["values"])

	def onTimer1(self, *args, **kwargs):
		print("onTimer1")
		qResult = self.remQuery

		"""
		entry = self._entityCache[self.remKey]
		if "1111" in entry["name"]["de"]:
			entry["name"]["de"] = entry["name"]["de"].replace("1111", "")
		else:
			entry["name"]["de"] += "1111"
		changedCb = qResult.callbackMap.get("rowChanged")
		if changedCb:
			changedCb(qResult._keys.index(self.remKey), 1)
		"""
		if self.remKey in qResult._keys:
			remIndex = qResult._keys.index(self.remKey)
			changedCb = qResult.callbackMap.get("beforeRemovetRows")
			if changedCb:
				changedCb(remIndex, 1)
			qResult._keys.remove(self.remKey)
			changedCb = qResult.callbackMap.get("afterRemoveRows")
			if changedCb:
				changedCb(remIndex, 1)
		else:
			changedCb = qResult.callbackMap.get("beforeInsertRows")
			if changedCb:
				changedCb(3, 1)
			qResult._keys.insert(3, self.remKey)
			changedCb = qResult.callbackMap.get("afterInsertRows")
			if changedCb:
				changedCb(3, 1)

	def fetchFailed(self, req: RequestWrapper, *args, **kwargs):
		print("FETCH FAILED !!!!!!")
		listView = req.listView
		listView._hasQueryRunning = False

	def checkForOurModul(self, moduleName: str) -> bool:
		return self.module == moduleName


	def add(self, callback, **kwargs: Any) -> str:
		print(("IN add,", kwargs))
		req = NetworkService.request(
			"/%s/add/" % (self.module), kwargs, secure=(len(kwargs) > 0),
			finishedHandler=self.onSaveResult)
		if not kwargs:
			# This is our first request to fetch the data, dont show a missing hint
			req.wasInitial = True
		else:
			req.wasInitial = False
		req.callback = callback
		print(("INITIAL", req.wasInitial))
		addTaskId = str(id(req))
		logger.debug("proto list add id: %r", addTaskId)
		return addTaskId

	def edit(self, key: str, callback, **kwargs: Any) -> str:
		print("XXX IN EDIT", key)
		req = NetworkService.request(
			"/%s/edit/%s" % (self.module, key), kwargs, secure=(len(kwargs) > 0),
			finishedHandler=self.onSaveResult)
		if not kwargs:
			# This is our first request to fetch the data, dont show a missing hint
			req.wasInitial = True
		else:
			req.wasInitial = False
			#self.entityChanging.emit(key)
		req.callback = callback
		#self.checkBusyStatus()
		editTaskId = str(id(req))
		logger.debug("proto list edit id: %r", editTaskId)
		return editTaskId

	def onSaveResult(self, req: RequestWrapper) -> None:
		try:
			data = NetworkService.decode(req)
		except:  # Something went wrong, call ErrorHandler
			self.updatingFailedError.emit(str(id(req)))
			QtCore.QTimer.singleShot(self.updateDelay, self.emitEntriesChanged)
			return
		if data["action"] == "editSuccess":
			self._entityCache[data["values"]["key"]] = data["values"]
			self.emitEntityUpdated(data["values"]["key"])
			req.callback(data)
			#self.updatingSucceeded.emit(str(id(req)))
			#self.entityChanged.emit(data["values"])
		elif data["action"] in ["addSuccess", "deleteSuccess", "setSortIndexSuccess"]:  # Saving succeeded
			#QtCore.QTimer.singleShot(self.updateDelay, self.emitEntriesChanged)
			#self.updatingSucceeded.emit(str(id(req)))
			req.callback(data)
		else:  # There were missing fields
			req.callback(data)
			#self.updatingDataAvailable.emit(str(id(req)), data, req.wasInitial)


	def emitEntityUpdated(self, key:str):
		for view in self.views:
			view.emitEntityUpdated(key)


# self.emit( QtCore.SIGNAL("entitiesChanged()") )


def CheckForListModul(moduleName: str, moduleList: dict) -> bool:
	modulData = moduleList[moduleName]
	if "handler" in modulData and (
			modulData["handler"] == "base" or
			modulData["handler"] == "list" or modulData["handler"].startswith("list.")):
		return True
	return False


protocolWrapperClassSelector.insert(0, CheckForListModul, ListWrapper)
