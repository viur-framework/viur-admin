#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import copy
import logging
from typing import Sequence, Mapping, Union, Tuple, List, Any, Dict

from viur_admin.log import getLogger, logToUser

logger = getLogger(__name__)

from collections import OrderedDict

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QModelIndex
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


class ListTableModel(QtCore.QAbstractTableModel):
	"""Model for displaying data within a listView"""
	GarbageTypeName = "ListTableModel"
	_chunkSize = 25

	rebuildDelegates = QtCore.pyqtSignal((object,))
	listIsComplete = QtCore.pyqtSignal()

	def __init__(self, protoWrap, parent):
		#logger.debug("ListTableModel.init: %r, %r, %r, %r", module, fields, viewFilter, parent)
		QtCore.QAbstractTableModel.__init__(self, parent)
		#self.module = module
		self.fields = ["name"]
		# Due to miss-use, someone might request displaying fields which dont exists. These are the fields that are valid
		self._validFields: List[str] = list()
		self.filter = {}
		self.cursorList = []
		self.displayedKeys: List[str] = []
		#self.dataCache: List[Dict[str, Any]] = list()
		self.headers: List[Any] = []
		self.editableFields = set()
		self.pendingUpdates = set()  # List of keys we know have pending writes to the server
		self.bones = {}
		self._canFetchMore = True  # Have we all items?
		self.isLoading = False
		#self.cursor = None
		self._rowCount = 0
		# As loading is performed in background, they might return results for a dataset which isn't displayed anymore
		self.loadingKey = None
		# Tuple of Sort-Properties we should include in queries (Bonename and ascending/descending)
		self.currentSortBone: Tuple[str, bool] = None
		self.protoWrap = protoWrap
		#self.protoWrap.insertRowsEvent.connect(self.onInsertRows)
		#self.protoWrap.removeRowsEvent.connect(self.onRemoveRows)
		#self.protoWrap.changeRowsEvent.connect(self.onChangeRows)
		#self.queryKey = self.protoWrap.registerQuery(self.filter.copy() or {})
		#self.viewProxy = protoWrap.registerView(
		#	{"orderby": "changedate", "orderdir": "1"},
		#	{
		#		"beforeInsertRows": self.beforeInsertRows,
		#		"afterInsertRows": self.afterInsertRows,
		#		"beforeRemovetRows": self.beforeRemovetRows,
		#		"afterRemoveRows": self.afterRemoveRows,
		#		"rowChanged": self.rowChanged,
		#	}
		#)

	def canFetchMore(self, QModelIndex):
		return self._canFetchMore #self.viewProxy.canFetchMore

	def fetchMore(self, QModelIndex):
		if not self.isLoading:
			self.isLoading = True
			self.protoWrap.requestNextBatch(self)
	#protoWrap = protocolWrapperInstanceSelector.select(self.module)
	#protoWrap.requestNextBatch(self.queryKey)

	def beforeInsertRows(self, index: int, numRows:int):
		print("beforeInsertRows: %r, %r" % (index, numRows))

		if not self.bones:
			for key, bone in self.protoWrap.viewStructure.items():
				self.bones[key] = bone
			self._validFields = [x for x in self.fields if x in self.bones]
			self.fields = [x for x in self.fields if x in self._validFields]
			if not self.fields:  # Select the 10 first bones that do exist to prevent an empty table
				# Don't show these bones by default in the table
				systemBones = {"key","creationdate", "changedate", "viurCurrentSeoKeys"}
				self.fields = [x for x in self.bones if x not in systemBones][:10]
				self._validFields = self.fields[:]
			self.rebuildDelegates.emit(self.protoWrap.viewStructure)
			self.repaint()
		self.beginInsertRows(QModelIndex(), index, index + numRows - 1)
		self._rowCount += numRows
	#for rowIndex in range(row, row + count):
	#	self.dataCache.pop(rowIndex)

	def afterInsertRows(self, index: int, numRows:int):
		print("afterInsertRows: %r, %r" % (index, numRows))
		self.endInsertRows()
		return True

	def beforeRemovetRows(self, index, numRows):
		self.beginRemoveRows(QtCore.QModelIndex(), index, index + numRows - 1)
		self._rowCount -= numRows

	def afterRemoveRows(self, index, numRows):
		self.endRemoveRows()

	def rowChanged(self, index, numRows):
		self.dataChanged.emit(self.index(index, 0), self.index(index + numRows - 1, 999))

	#self.beginRemoveRows(QtCore.QModelIndex(), index, index + numRows - 1)
	#self._rowCount -= numRows
	#self.endRemoveRows()

	def updatingDataAvailable(self, reqId, data, wasInitial):
		"""
			Signal from the protocoll-wrapper that an add/edit request bounced back. Check if we have it
			in our pendingUpdates list and update accordingly
		"""
		print("updatingDataAvailable")
		if wasInitial:
			return
		try:
			errorKey = data["values"]["key"]
		except:
			errorKey = None
		for idx, entry in enumerate(self.dataCache):  # Check if we are displaying it right now
			if entry["key"] == errorKey:
				if idx not in self.pendingUpdates:
					return
				self.pendingUpdates.remove(idx)
				self.dataChanged.emit(self.index(idx, 0), self.index(idx, 999))
				self.msgBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information,
													QtCore.QCoreApplication.translate("ListTableView", "Updating failed"),
													QtCore.QCoreApplication.translate("ListTableView", "Updating of %s failed!") % entry["key"],
													(QtWidgets.QMessageBox.Ok),
													)
				self.msgBox.open()
				#QtWidgets.QMessageBox.warning(self.parent(), "Updating failed", "Updating of %s failed!" % entry["key"])
				print("warning up")


	def updatingFinshed(self, key, *args, **kwargs):
		"""
			Callback from the protocolwrapper that an update finished, so remove it's pending update tag
		"""
		try:
			idx = self.displayedKeys.index(key)
		except ValueError:
			return
		self.pendingUpdates.remove(key)
		self.dataChanged.emit(self.index(idx, 0), self.index(idx, 999))

	def entityChanging(self, key: str):
		"""
			Callback from the protocolwrapper that an entry is about to be edited on the server side.
			Ensure we're only displaying "loading" while it's pending
		"""
		try:
			idx = self.displayedKeys.index(key)
		except ValueError:
			return
		self.pendingUpdates.add(key)
		self.dataChanged.emit(self.index(idx, 0), self.index(idx, 999))

	#def updateSingleEntity(self, entryData: dict):
	#	"""
	#		Callback from the protocol-wrapper that a single entry had been changed.
	#		Check if we actually displaying that entry and if update our data and repaint it's cells
	#		:param entryData: Data of the changed entry as received from the server
	#	"""
	#	for idx, displayedEntry in enumerate(self.dataCache):
	#		if displayedEntry["key"] == entryData["key"]:  # We found that entry
	#			self.dataCache[idx] = entryData
	#			if idx in self.pendingUpdates:
	#				self.pendingUpdates.remove(idx)
	#			self.dataChanged.emit(self.index(idx, 0), self.index(idx, 999))
	#			break

	#def entityDeleted(self, key: str):
	#	"""
	#		Event-Callback from protocolwrapper that the given entry has been deleted
	#	"""
	#	for entry in self.dataCache:
	#		if entry["key"] == key:
	#			idx = self.dataCache.index(entry)
	#			self.beginRemoveRows(QtCore.QModelIndex(), idx, idx)
	#			self.dataCache.remove(entry)
	#			self.endRemoveRows()
	#			break


	#def removeRows__(self, row: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
	#	# logger.debug("removeRows: %r, %r, %r", row, count, parent)
	#	self.beginRemoveRows(QModelIndex(), row, row + count - 1)

	#	for rowIndex in range(row, row + count):
	#		self.dataCache.pop(rowIndex)

	#	self.endRemoveRows()
	#	return True

	def supportedDropActions(self) -> int:
		return QtCore.Qt.MoveAction | QtCore.Qt.TargetMoveAction

	def setDisplayedFields(self, fields: List[str]) -> None:
		"""
			Update the list of bones that are visible in this table.
			New fields are been appended to the right, as it's now possible that the user has rearranged
			the colums - so we can't rely on the bone-order in the skeleton.
		:param fields: The new list of bones to display
		"""
		print("setDisplayedFields")
		for field in self.fields[:]:
			if field not in fields:  # Removed
				self.removeColumn(self.fields.index(field))
				self.fields.remove(field)
		for field in fields:
			if field not in self.fields:
				self.insertColumn(len(self.fields))
				self.fields.append(field)
		self.rebuildDelegates.emit(self.protoWrap.viewStructure)
		self.repaint()


	def setFilterbyName(self, filterName: str) -> None:
		self.name = filterName
		config = None  # getListConfig( self.module, filterName )
		if config:
			if "columns" in config:
				self.fields = config["columns"]
			if "filter" in config:
				self.filter = config["filter"]

	def setFilter(self, queryFilter: Dict[str, Any]) -> None:
		self.filter = queryFilter
		self.reload()

	def getFilter(self) -> None:
		return self.filter

	def getFields(self) -> None:
		return self.fields

	def getModul(self) -> None:
		return self.module

	def setSortColumn(self, boneName:str, descending: bool) -> None:
		if not boneName:
			self.currentSortBone = None
		else:
			self.currentSortBone = (boneName, descending)
		self.reload()

	def reload(self) -> None:
		self.beginRemoveRows(QtCore.QModelIndex(), 0, len(self.displayedKeys))
		self.displayedKeys = []
		self.cursorList = []
		self._canFetchMore = True
		self.isLoading = False
		#self.modelReset.emit()
		self.endRemoveRows()
		self.repaint()

	def rowCount(self, parent: QModelIndex = None, *args: Any, **kwargs: Any) -> int:
		return len(self.displayedKeys)

	def columnCount(self, parent: QModelIndex = None) -> int:
		try:
			return len(self.headers)
		except:
			return 0

	def data(self, index: QModelIndex, role: int = None) -> Any:
		if not index.isValid() or role not in [QtCore.Qt.DisplayRole, QtCore.Qt.UserRole]:
			return None
		elif role != QtCore.Qt.DisplayRole:
			return self.protoWrap._entityCache[self.displayedKeys[index.row()]]
			#return None
			#if role != QtCore.Qt.DisplayRole:
		key = self.displayedKeys[index.row()]
		field = self.fields[index.column()]
		return self.protoWrap._entityCache[key][field]
		#return self.viewProxy.getRow(index.row())[self.fields[index.column()]]


	def headerData(self, col: int, orientation: int, role: int = None) -> Any:
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			return self.headers[col]
		return None


	def addData(self, queryKey: str) -> None:
		self.isLoading -= 1
		if queryKey is not None and queryKey != self.loadingKey:  # The Data is for a list we dont display anymore
			return
		protoWrap = protocolWrapperInstanceSelector.select(self.module)
		assert protoWrap is not None
		#cacheTime, skellist, cursor = protoWrap.dataCache[queryKey]
		skellist = [protoWrap.entryCache[x] for x in protoWrap.queryCache[queryKey]["skelkeys"]]
		cursor = protoWrap.queryCache[queryKey]["cursor"]
		# Rebuild our local cache of valid fields
		if not self.bones:
			for key, bone in protoWrap.viewStructure.items():
				self.bones[key] = bone
			self._validFields = [x for x in self.fields if x in self.bones]
			self.fields = [x for x in self.fields if x in self._validFields]
			if not self.fields:  # Select the 10 first bones that do exist to prevent an empty table
				# Don't show these bones by default in the table
				systemBones = {"key","creationdate", "changedate", "viurCurrentSeoKeys"}
				self.fields = [x for x in self.bones if x not in systemBones][:10]
				self._validFields = self.fields[:]
			self.rebuildDelegates.emit(protoWrap.viewStructure)
			self.repaint()
		self.beginInsertRows(QtCore.QModelIndex(), len(self.dataCache), len(self.dataCache) + len(skellist) - 1)
		self.dataCache.extend(skellist)
		self.endInsertRows()
		if not cursor:
			self.beginRemoveRows(QtCore.QModelIndex(), len(self.dataCache), len(self.dataCache))
			self.completeList = True
			self.endRemoveRows()
		self.cursor = cursor
		self.loadingKey = None
		if protoWrap.queryCache[queryKey].get("failed"):
			QtWidgets.QMessageBox.warning(self.parent(), "Failed", "A Network-Request failed")


	# self.emit(QtCore.SIGNAL("dataRecived()"))

	def repaint(self) -> None:  # Currently an ugly hack to redraw the table
		self.layoutAboutToBeChanged.emit()
		self.layoutChanged.emit()


	def sort(self, p_int: int, order: Any = None) -> None:
		return
		if (self.fields[p_int] == "key" or (
				"cantSort" in dir(self.delegates[p_int]) and self.delegates[p_int].cantSort)):
			return
		filter = self.filter
		filter["orderby"] = self.fields[p_int]
		if order == QtCore.Qt.DescendingOrder:
			filter["orderdir"] = "1"
		else:
			filter["orderdir"] = "0"
		self.setFilter(filter)

	def search(self, searchStr: str) -> None:
		"""
			Start a search for the given string.
			If searchStr is None, it ends any currently active search.
			@param searchStr: Token to search for
			@type searchStr: String or None
		"""
		if searchStr:
			if "name$lk" in self.filter:
				del self.filter["name$lk"]
			self.filter["search"] = searchStr
			self.reload()
		else:
			if "search" in self.filter:
				del self.filter["search"]
			self.reload()

	def prefixSearch(self, searchStr: str) -> None:
		"""
			Merge the prefix search in our filter dict if possible.
			Does noting if the list isn't sorted by name.
		"""
		if "orderby" not in self.filter or not self.filter["orderby"] == "name":
			return
		if "search" in self.filter:
			del self.filter["search"]
		if not searchStr and "name$lk" in self.filter:
			del self.filter["name$lk"]
		if searchStr:
			self.filter["name$lk"] = searchStr
		self.reload()

	def flags(self, index: QModelIndex = None) -> QtCore.Qt.ItemFlags:
		#defaultFlags = super(ListTableModel, self).flags(index)
		defaultFlags = QtCore.Qt.ItemIsEnabled
		try:
			key = self.displayedKeys[index.row()]
		except IndexError:
			key = None
		if key in self.pendingUpdates:
			return QtCore.Qt.NoItemFlags
		try:
			if self.fields[index.column()] in self.editableFields:
				defaultFlags |= QtCore.Qt.ItemIsEditable
		except:
			pass
		return defaultFlags

	def setSortIndex(self, index: QModelIndex, sortindex: float) -> None:
		protoWrap = protocolWrapperInstanceSelector.select(self.module)
		assert protoWrap is not None
		key = self.dataCache[index.row()]["key"]
		protoWrap.setSortIndex(key, sortindex)



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

	def registerView(self, parent):
		listView = ListTableModel(self, parent) # callbackMap, self, queryDict
		self.views.add(listView)
		return listView

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
		queryDict = copy.deepcopy(listView.filter)
		if listView.cursorList:
			queryDict["cursor"] = listView.cursorList[-1]
		if listView.currentSortBone:
			queryDict["orderby"] = listView.currentSortBone[0]
			queryDict["orderdir"] = "1" if listView.currentSortBone[1] else "0"
		r = NetworkService.request("/%s/list" % self.module, queryDict, successHandler=self.addCacheData, failureHandler=self.fetchFailed)
		r.listView = listView

	def addCacheData(self, req: RequestWrapper) -> None:
		listView = req.listView
		listView._hasQueryRunning = False
		data = NetworkService.decode(req)
		cursor = None
		if "cursor" in data:
			cursor = data["cursor"]
			listView.cursorList.append(cursor)
		if data["action"] == "list":
			oldLength = len(listView.displayedKeys)
			if 0 and not oldLength:
				self.timer1 = QtCore.QTimer()
				self.timer1.timeout.connect(self.onTimer1)
				self.timer1.start(1000)
				self.remKey = [x["key"] for x in data["skellist"] if x["key"] not in self.pendingDeletes][3]
				self.remQuery = listView
			extLength = len(data["skellist"])
			listView.beforeInsertRows(oldLength, extLength)
			listView.displayedKeys.extend([x["key"] for x in data["skellist"] if x["key"] not in self.pendingDeletes])
			for skel in data["skellist"]:
				if skel["key"] in self.pendingDeletes:
					continue
				self._entityCache[skel["key"]] = skel
			listView.afterInsertRows(oldLength, extLength)
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

	def edit(self, key: str, callback = None, **kwargs: Any) -> str:
		print("XXX IN EDIT", key)
		for view in self.views:
			view.entityChanging(key)
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
		req.pendingKey = key
		#self.checkBusyStatus()
		editTaskId = str(id(req))
		logger.debug("proto list edit id: %r", editTaskId)
		return editTaskId

	def onSaveResult(self, req: RequestWrapper) -> None:
		for view in self.views:
			view.updatingFinshed(req.pendingKey)
		try:
			data = NetworkService.decode(req)
		except:  # Something went wrong, call ErrorHandler
			self.updatingFailedError.emit(str(id(req)))
			QtCore.QTimer.singleShot(self.updateDelay, self.emitEntriesChanged)
			return
		if data["action"] == "editSuccess":
			self._entityCache[data["values"]["key"]] = data["values"]
			self.emitEntityUpdated(data["values"]["key"])
			#req.callback(data)
			#self.updatingSucceeded.emit(str(id(req)))
			#self.entityChanged.emit(data["values"])
		elif data["action"] in ["addSuccess", "deleteSuccess", "setSortIndexSuccess"]:  # Saving succeeded
			pass
			#QtCore.QTimer.singleShot(self.updateDelay, self.emitEntriesChanged)
			#self.updatingSucceeded.emit(str(id(req)))
			#if req.callback:
			#	req.callback(data)
		else:  # There were missing fields
			pass
			#self.updatingDataAvailable.emit(str(id(req)), data, req.wasInitial)
		if req.callback:
			req.callback(data)


	def emitEntityUpdated(self, key:str):
		for view in self.views:
			try:
				idx = view.displayedKeys.index(key)
			except ValueError:  # This view does not display that key
				continue
			view.rowChanged(idx, 1)

	def reload(self):
		for view in self.views:
			numKeys = len(view.displayedKeys)
			view.beforeRemovetRows(0, numKeys)
			view.displayedKeys = []
			view.cursorList = []
			view.pendingUpdates = set()
			view._canFetchMore = True
			view.isLoading = False
			view.afterRemoveRows(0, numKeys)



# self.emit( QtCore.SIGNAL("entitiesChanged()") )


def CheckForListModul(moduleName: str, moduleList: dict) -> bool:
	modulData = moduleList[moduleName]
	if "handler" in modulData and (
			modulData["handler"] == "base" or
			modulData["handler"] == "list" or modulData["handler"].startswith("list.")):
		return True
	return False


protocolWrapperClassSelector.insert(0, CheckForListModul, ListWrapper)
