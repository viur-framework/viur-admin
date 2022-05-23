#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import OrderedDict
from typing import Union, Sequence, Tuple, List, Dict, Any, Optional, Set
from PyQt5.QtCore import QModelIndex
from PyQt5 import QtCore, QtWidgets

from viur_admin.log import getLogger
from viur_admin.network import NetworkService, RequestGroup, RequestWrapper
from viur_admin.priorityqueue import protocolWrapperClassSelector, protocolWrapperInstanceSelector
from viur_admin.log import getLogger, getStatusBar, logToUser
from weakref import WeakSet, ref as weakRef
from viur_admin.protocolwrapper.base import Task, ProtocolWrapper
import copy

logger = getLogger(__name__)



class MoveItemsTask(Task):
	def __init__(self, protoWrap, nodeType: str, movedKey: str, targetKey:str):
		super(MoveItemsTask, self).__init__()
		self.protoWrap = protoWrap
		self.nodeType = nodeType
		self.movedKey = movedKey
		self.targetKey = targetKey

	def run(self):
		if self.protoWrap.isTemporaryKey(self.movedKey):
			# Our parent directory might have just been created
			self.movedKey = self.protoWrap.lookupTemporaryKey(self.movedKey)
			assert self.movedKey is not None, "Temporary key did not resolve!"
		if self.protoWrap.isTemporaryKey(self.targetKey):
			# Our parent directory might have just been created
			self.targetKey = self.protoWrap.lookupTemporaryKey(self.targetKey)
			assert self.targetKey is not None, "Temporary key did not resolve!"
		NetworkService.request("/%s/move/" % self.protoWrap.module,
							   {"key": self.movedKey,
								"skelType": self.nodeType,
								"parentNode": self.targetKey},
							   secure=True,
							   successHandler=self.onMoveSuccess,
							   failureHandler=self.onMoveFailed)

	def onMoveSuccess(self, req):
		data = NetworkService.decode(req)
		try:
			newKey = data["values"]["key"]
		except:
			self.finish(success=False)
			return
		self.finish(success=True)

	def onMoveFailed(self, req):
		self.finish(success=False)


class DeleteItemsTask(Task):
	def __init__(self, protoWrap, nodeType: str, deleteKey: str):
		super(DeleteItemsTask, self).__init__()
		self.protoWrap = protoWrap
		self.nodeType = nodeType
		self.deleteKey = deleteKey

	def run(self):
		if self.protoWrap.isTemporaryKey(self.deleteKey):
			# Our parent directory might have just been created
			self.deleteKey = self.protoWrap.lookupTemporaryKey(self.deleteKey)
			assert self.deleteKey is not None, "Temporary key did not resolve!"
		NetworkService.request("/%s/delete/" % self.protoWrap.module,
							   {"key": self.deleteKey,
								"skelType": self.nodeType},
							   secure=True,
							   successHandler=self.onDeleteSuccess,
							   failureHandler=self.onDeleteFailed)

	def onDeleteSuccess(self, req):
		data = NetworkService.decode(req)
		self.finish(success=data == "OKAY")

	def onDeleteFailed(self, req):
		self.finish(success=False)

class AddItemTask(Task):
	def __init__(self, protoWrap, nodeType: str, parentKey: str, isInitial:bool, data: dict[str,str]):
		super(AddItemTask, self).__init__()
		self.protoWrap = protoWrap
		self.nodeType = nodeType
		self.parentKey = parentKey
		self.isInitial = isInitial
		self.data = data

	def run(self):
		if self.protoWrap.isTemporaryKey(self.parentKey):
			# Our parent directory might have just been created
			self.parentKey = self.protoWrap.lookupTemporaryKey(self.parentKey)
			assert self.parentKey is not None, "Temporary key did not resolve!"
		dataDict = {"node": self.parentKey, "skelType": self.nodeType}
		dataDict.update(self.data)
		NetworkService.request("/%s/add" % self.protoWrap.module,
							   dataDict,
							   secure=True,
							   successHandler=self.onAddSuccess,
							   failureHandler=self.onAddFailed)

	def onAddSuccess(self, req):
		data = NetworkService.decode(req)
		self.finish(success=data == "OKAY")

	def onAddFailed(self, req):
		self.finish(success=False)

class TreeView(QtCore.QAbstractItemModel):
	rebuildDelegates = QtCore.pyqtSignal((object,))

	def __init__(self, treeWrapper, parent):
		QtCore.QAbstractItemModel.__init__(self, parent)
		#self.callbackMap = callbackMap
		self.treeWrapper = treeWrapper
		self._rootNode = None
		self._dataDict = {}
		self._nextDataIndex = 1
		self._sortOrder = ("name", "0")
		self._searchStr = ""
		self.fields = ["name"]
		# Due to miss-use, someone might request displaying fields which dont exists. These are the fields that are valid
		self._validFields: List[str] = list()
		self.displayedKeys: List[str] = []

	def headerData(self, col: int, orientation: int, role: int = None) -> Any:
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			return self.headers[col]
		return None

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
		self.rebuildDelegates.emit(self.treeWrapper.viewStructure)


	def search(self, searchStr:str):
		self.setRootNode(self._rootNode)  # This will clear this model
		self._searchStr = searchStr



	def resolveParentDataForIndex(self, index: QModelIndex) -> dict:
		internalIndex = index.internalId() if index.isValid() else 0
		return self._dataDict[internalIndex]

	def resolveInternalDataForIndex(self, index: QModelIndex) -> dict:
		internalIndex = index.internalId() if index.isValid() else 0
		res = self._dataDict[internalIndex]
		if index.isValid():
			if index.row() < len(res["nodeKeys"]):
				return self.resolveInternalDataForNodeKey(res["nodeKeys"][index.row()])
			else:
				return None  # That index points to a leaf
		return res

	def resolveInternalDataForNodeKey(self, nodeKey: str) -> dict:
		for v in self._dataDict.values():
			if v["nodeKey"] == nodeKey:
				return v


	def resolveParentIndexForNodeKey(self, nodeKey: str) -> Optional[QModelIndex]:
		data = self.resolveInternalDataForNodeKey(nodeKey)
		if not data:
			return None
		if not data["parentNodeKey"]:
			return QModelIndex()
		data = self.resolveInternalDataForNodeKey(data["parentNodeKey"])
		return self.createIndex(data["nodeKeys"].index(nodeKey),0, data["internalIndex"])

	def resolveParentIndexForLeafKey(self, leafKey: str) -> QModelIndex:
		for data in self._dataDict.values():
			if leafKey in data["leafKeys"]:
				return self.createIndex(data["leafKeys"].index(leafKey)+len(data["nodeKeys"]),0, data["internalIndex"])

	def resolveInternalDataForLeafKey(self, leafKey: str) -> dict:
		for data in self._dataDict.values():
			if leafKey in data["leafKeys"]:
				return data

	def removeInternalDataForNodeKey(self, nodeKey:str):
		"""
			Removes our internal data for the given nodeKey.
			Must be used in delete, to ensure this node does not pop up as valid for this view anymore.
		"""
		for k, v in list(self._dataDict.items()):
			if v["nodeKey"] == nodeKey:
				del self._dataDict[k]
				for node in v["nodeKeys"]:
					self.removeInternalDataForNodeKey(node)

	def createInternalNodeStructure(self, nodeKey, parentKey):
		idx = self._nextDataIndex
		self._nextDataIndex += 1
		self._dataDict[idx] = {
			"internalIndex": idx,
			"rowCount": 0,
			"hasQueryRunning": False,
			"nodeCursorList": [],
			"nodeListComplete": False,
			"nodeKeys": [],
			"leafCursorList": [],
			"leafListComplete": self.treeWrapper.nodesOnly,
			"leafKeys": [],
			"parentNodeKey" : parentKey,
			"nodeKey": nodeKey,
		}
		return self._dataDict[idx]
		#self.beginInsertRows(self.createIndex(0,0,idx) if idx else QModelIndex(), 0, 30)
		#self.endInsertRows()

	def setRootNode(self, node:str):
		print("---- SET ROOT NODE", node)
		self.beginResetModel()
		self._rootNode = node
		self._nextDataIndex = 0
		self._dataDict = {}
		self.createInternalNodeStructure(node, None)
		self.endResetModel()


	def beforeInsertRows(self, nodeKey:str, index: int, numRows:int, treeType):
		logger.debug("beforeInsertRows: %r, %r" % (index, numRows))
		parentModelIndex = self.resolveParentIndexForNodeKey(nodeKey)
		dataDict = self.resolveInternalDataForNodeKey(nodeKey)
		self.beginInsertRows(parentModelIndex, index, index + numRows - 1)
		dataDict["rowCount"] += numRows


	def afterInsertRows(self, nodeKey:str, index: int, numRows:int, treeType):
		print("afterInsertRows: %r, %r" % (index, numRows))
		self.endInsertRows()
		return True

	def beforeRemoveRows(self, nodeKey:str, index:int, numRows:int, treeType):
		parentModelIndex = self.resolveParentIndexForNodeKey(nodeKey)
		dataDict = self.resolveInternalDataForNodeKey(nodeKey)
		self.beginRemoveRows(parentModelIndex, index, index +numRows)
		dataDict["rowCount"] -= numRows

	def afterRemoveRows(self, nodeKey:str, index, numRows, treeType):
		self.endRemoveRows()

	def rowChanged(self, index, numRows):
		# Indicates, that numRows (starting from index) have been changed and have to be redrawn
		parent = self.parent(index)
		self.dataChanged.emit(self.index(index.row(), 0, parent), self.index(index.row() + numRows - 1, 999, parent))

	def rowCount(self, parent: QModelIndex = None, *args: Any, **kwargs: Any) -> int:
		dataDict = self.resolveInternalDataForIndex(parent)
		if not dataDict:  # It's a node
			return 0
		return dataDict["rowCount"]

	def columnCount(self, parent: QModelIndex = None) -> int:
		try:
			return len(self.headers)
		except:
			return 0

	def data(self, index: QModelIndex, role: int = None) -> Any:
		if role not in [QtCore.Qt.DisplayRole, QtCore.Qt.UserRole]:
			return None
		if index.isValid():
			dataDict = self.resolveParentDataForIndex(index)
			row = index.row()
			if row < len(dataDict["nodeKeys"]):
				key = dataDict["nodeKeys"][row]
			else:
				row -= len(dataDict["nodeKeys"])
				if row < len(dataDict["leafKeys"]):
					key = dataDict["leafKeys"][row]
				else:
					#print(row, "?")
					return {"_type": "invalid"}
		else:
			key = self._rootNode
		return self.treeWrapper._entityCache[key]

		if entry.get("_pending"):
			return "[Syncing] %s" % entry.get("name")
		field = self.fields[index.column()]
		return entry.get(field)

	def canFetchMore(self, parent: QModelIndex) -> bool:
		dataDict = self.resolveInternalDataForIndex(parent)
		return bool(self._rootNode) and (not dataDict["nodeListComplete"] or not dataDict["leafListComplete"])

	def fetchMore(self, parent: QModelIndex) -> None:
		dataDict = self.resolveInternalDataForIndex(parent)
		if dataDict["hasQueryRunning"]:
			return
		dataDict["hasQueryRunning"] = True
		if not dataDict["nodeListComplete"]:
			if self._searchStr and dataDict["nodeKey"] == self._rootNode:
				self.treeWrapper.search(self, dataDict["nodeKey"], "node", self._searchStr)
			else:
				self.treeWrapper.queryNode(self, dataDict["nodeKey"], "node", self._sortOrder, dataDict["nodeCursorList"][-1] if dataDict["nodeCursorList"] else None)
		elif not dataDict["leafListComplete"]:
			if self._searchStr and dataDict["nodeKey"] == self._rootNode:
				self.treeWrapper.search(self, dataDict["nodeKey"], "leaf", self._searchStr)
			else:
				self.treeWrapper.queryNode(self, dataDict["nodeKey"], "leaf", self._sortOrder, dataDict["leafCursorList"][-1] if dataDict["leafCursorList"] else None)

	def index(self, row: int, column: int, parent: QModelIndex = ...) -> QModelIndex:
		dataDict = self.resolveInternalDataForIndex(parent)
		# If that index points to a leaf, we have no datadict; so we can use the current parent as parent
		return self.createIndex(row, column, dataDict["internalIndex"] if dataDict else parent.internalId())

	def parent(self, child: QModelIndex) -> QModelIndex:
		dataDict = self.resolveParentDataForIndex(child)
		return self.resolveParentIndexForNodeKey(dataDict["nodeKey"])

	def hasChildren(self, parent: QModelIndex = ...) -> bool:
		return self.resolveInternalDataForIndex(parent) is not None

	def flags(self, index: QModelIndex) -> QtCore.Qt.ItemFlags:
		if not index.isValid():
			return QtCore.Qt.ItemIsDropEnabled  # Allow dropping on root-node
		if self.resolveInternalDataForIndex(index): # Allow drops only on nodes
			return QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
		return QtCore.Qt.ItemIsDragEnabled| QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemNeverHasChildren



class TreeWrapper(ProtocolWrapper):
	maxCacheTime = 60  # Cache results for max. 60 Seconds
	updateDelay = 0  # 1,5 Seconds grace time before reloading
	batchSize = 30  # Fetch 30 entries at once
	protocolWrapperInstancePriority = 1

	entitiesChanged = QtCore.pyqtSignal((str,))  # Node,
	entitiesAppended = QtCore.pyqtSignal((str, list))  # Node,
	entityAvailable = QtCore.pyqtSignal((object,))  # A recently queried entity was fetched and is now available
	customQueryFinished = QtCore.pyqtSignal((str,))  # RequestID,
	rootNodesAvailable = QtCore.pyqtSignal()
	busyStateChanged = QtCore.pyqtSignal((bool,))  # If true, I'm busy right now
	updatingSucceeded = QtCore.pyqtSignal((str,))  # Adding/Editing an entry succeeded
	updatingFailedError = QtCore.pyqtSignal((str,))  # Adding/Editing an entry failed due to network/server error
	updatingDataAvailable = QtCore.pyqtSignal((str, dict, bool))  # Adding/Editing an entry failed due to missing fields
	onModulStructureAvailable = QtCore.pyqtSignal()

	def __init__(self, module: str, *args: Any, **kwargs: Any):
		super(TreeWrapper, self).__init__()
		self.module = module
		req = NetworkService.request("/getStructure/%s" % self.module, successHandler=self.onStructureAvailable)
		NetworkService.request("/%s/listRootNodes" % self.module, successHandler=self.onRootNodesAvailable)
		protocolWrapperInstanceSelector.insert(self.protocolWrapperInstancePriority, self.checkForOurModul, self)
		self.busy = True
		self.views: WeakSet[TreeView] = WeakSet()
		self.rootNodes = []
		self.headers = []
		self.pendingDeletes = set()
		self.nodesOnly: bool = False  # If true, there's no leaf skel defined
		# Map of pending inserts (uploads / adds that have not yet been synced to the server).
		# Format: parent (root?)node key (str) -> List of keys that should be inserted on this node (0: Nodes, 1: Leafs)
		self.pendingInserts: dict[str, Tuple[List[str],List[str]]] = {}
		self._entityCache: dict[str, dict] = {}  # Map of database-key -> entity data
		self.temporaryKeyIndex: int = 0  # We'll assign temp. keys using this index
		self.temporaryKeyMap: dict[str, str] = {}  # Map of temp key -> finally assignend key from the server
		self.viewNodeStructure = self.viewLeafStructure = self.viewStructure = None


	def resolveTemporaryKey(self, tempKey, finalKey):
		"""
			Sets the final, server-assigned key for the given temporary key. Must be called if the entry has been
			successfully created on the server and we got it's final key in addSuccess or the like.
		"""
		print("resolveTemporaryKey", tempKey, finalKey)
		super().resolveTemporaryKey(tempKey, finalKey)
		self._entityCache[finalKey] = self._entityCache[tempKey]
		self._entityCache[tempKey]["_pending"] = False
		isNode = "%s_rootNode" % self.module in tempKey
		for view in self.views:
			# Insert these items into the destination node
			if isNode:
				data = view.resolveInternalDataForNodeKey(tempKey)
				if data:  # This view also has the destination node
					assert data["nodeKey"] == tempKey
					parentData = view.resolveInternalDataForNodeKey(data["parentNodeKey"])
					data["nodeKey"] = finalKey
					assert tempKey in parentData["nodeKeys"]
					# Replate the temporary node key with it's final one
					parentData["nodeKeys"] = [(finalKey if x==tempKey else x) for x in parentData["nodeKeys"]]
					for subNodeKey in data["nodeKeys"]:
						subNodeData = view.resolveInternalDataForNodeKey(subNodeKey)
						subNodeData["parentNodeKey"] = finalKey
			else:
				data = view.resolveInternalDataForLeafKey(tempKey)
				if data:  # This view also has the destination node
					assert tempKey in data["leafKeys"]
					# Replate the temporary node key with it's final one
					data["leafKeys"] = [(finalKey if x==tempKey else x) for x in data["leafKeys"]]
		if tempKey in self.pendingInserts:
			self.pendingInserts[finalKey] = self.pendingInserts[tempKey]
			del self.pendingInserts[tempKey]
		r = NetworkService.request("/%s/view/%s/%s" % (self.module, "node" if isNode else "leaf", finalKey), successHandler=self.updateEntry)
		r.isNode = isNode

	def updateEntry(self, req):
		data = NetworkService.decode(req)
		key = data["values"]["key"]
		self._entityCache[key].update(data["values"])
		for view in self.views:
			# Check which views may display that node/leaf
			if req.isNode:
				parentIndex = view.resolveParentIndexForNodeKey(key)
				if parentIndex:
					data = view.resolveInternalDataForNodeKey(view.resolveInternalDataForNodeKey(key)["parentNodeKey"])
					idx = view.index(data["nodeKeys"].index(key), 0, parentIndex)
					idx2 = view.index(data["nodeKeys"].index(key), 99, parentIndex)
					view.dataChanged.emit(idx, idx2)
			else:
				parentIndex = view.resolveParentIndexForLeafKey(key)
				data = view.resolveInternalDataForLeafKey(key)
				if data:
					idx = view.index(data["leafKeys"].index(key), 0, parentIndex)
					idx2 = view.index(data["leafKeys"].index(key), 99, parentIndex)
					view.dataChanged.emit(idx, idx2)

	def onStructureAvailable(self, req: RequestWrapper) -> None:
		tmp = NetworkService.decode(req)
		if tmp is None:
			self.checkBusyStatus()
			return
		self.nodesOnly = True
		for stype, structlist in tmp.items():
			structure: OrderedDict = OrderedDict()
			for k, v in structlist:
				structure[k] = v
			if stype == "viewNodeSkel":
				self.viewNodeStructure = structure
			elif stype == "viewLeafSkel":
				self.nodesOnly = False
				self.viewLeafStructure = structure
			elif stype == "editNodeSkel":
				self.editNodeStructure = structure
			elif stype == "editLeafSkel":
				self.nodesOnly = False
				self.editLeafStructure = structure
			elif stype == "addNodeSkel":
				self.addNodeStructure = structure
			elif stype == "addLeafSkel":
				self.nodesOnly = False
				self.addLeafStructure = structure
			else:
				raise ValueError("onStructureAvailable: unknown node type: {0}".format(stype))
		print(self.module, self.nodesOnly)
		if self.viewNodeStructure and self.viewLeafStructure:
			self.viewStructure = copy.deepcopy(self.viewNodeStructure)
			for k, v in self.viewLeafStructure.items():
				if k not in self.viewStructure:
					self.viewStructure[k] = copy.deepcopy(v)
				elif self.viewStructure[k]["type"] == v["type"]:
					if self.viewStructure[k]["descr"] != v["descr"]:
						self.viewStructure[k]["descr"] = "%s / %s" % (self.viewStructure[k]["descr"], v["descr"])
				else:
					self.viewStructure[k] = [self.viewStructure[k], v]
			#print("xxxx", self.viewLeafStructure)
		self.onModulStructureAvailable.emit()


	def onRootNodesAvailable(self, req: RequestWrapper) -> None:
		tmp = NetworkService.decode(req)
		if isinstance(tmp, list):
			self.rootNodes = tmp
		#self.clearCache()
		for node in self.rootNodes:
			self._entityCache[node["key"]] = node
			self._entityCache[node["key"]]["_type"] = "node"
		self.rootNodesAvailable.emit()
		logger.debug("TreeWrapper.onRootNodesAvailable: %r", tmp)
		self.busy = False


	def checkForOurModul(self, moduleName: str) -> bool:
		return self.module == moduleName

	def registerView(self, parent):
		listView = TreeView(self, parent)
		self.views.add(listView)
		return listView


	def queryNode(self, treeView, node, treeType, sortOrder, cursor=None):
		if self.isTemporaryKey(node) and not self.lookupTemporaryKey(node):
			dataDict = treeView.resolveInternalDataForNodeKey(node)
			# Nothing to fetch here, it's still awaiting upload
			if treeType == "node":
				dataDict["nodeListComplete"] = True
				dataDict["hasQueryRunning"] = False
				self.injectPendingInsertsIfNeeded(treeView, "node", node)
			else:
				dataDict["leafListComplete"] = True
				dataDict["hasQueryRunning"] = False
				self.injectPendingInsertsIfNeeded(treeView, "leaf", node)
		else:
			queryDict = {"orderby": sortOrder[0], "orderdir": sortOrder[1], "parententry": node}
			if cursor:
				queryDict["cursor"] = cursor
			r = NetworkService.request("/%s/list/%s" % (self.module, treeType), queryDict, successHandler=self.addCacheData, failureHandler=self.fetchFailed)
			r.treeType = treeType
			r.treeView = weakRef(treeView)
			r.node = node

	def search(self, treeView, node, treeType, searchStr):
		queryDict = {"search": searchStr, "parentrepo": node}
		r = NetworkService.request("/%s/list/%s" % (self.module, treeType), queryDict, successHandler=self.addCacheData, failureHandler=self.fetchFailed)
		r.treeType = treeType
		r.treeView = weakRef(treeView)
		r.node = node


	def addCacheData(self, req: RequestWrapper) -> None:
		data = NetworkService.decode(req)
		cursor = None
		if data["action"] == "list":
			treeView = req.treeView()
			if not treeView:  # The treeView has been deleted in the meanwhile, we do not need to process the response
				return
			dataDict = treeView.resolveInternalDataForNodeKey(req.node)
			dataDict["hasQueryRunning"] = False
			if "cursor" in data and data["cursor"]:
				cursor = data["cursor"]
				if req.treeType == "node":
					dataDict["nodeCursorList"].append(cursor)
				else:
					dataDict["leafCursorList"].append(cursor)
			# Prevent re-adding items scheduled for deletion
			filteredSkelList = [x for x in data["skellist"] if x["key"] not in self.pendingDeletes]
			# Don't add items already present (might be an item that just finished uploading)
			filteredSkelList = [x for x in filteredSkelList if x["key"] not in dataDict["nodeKeys"]]
			filteredSkelList = [x for x in filteredSkelList if x["key"] not in dataDict["leafKeys"]]
			oldLength = len(dataDict["nodeKeys"]) + len(dataDict["leafKeys"])
			extLength = len(filteredSkelList)
			treeView.beforeInsertRows(req.node, oldLength, extLength, req.treeType)
			if req.treeType == "node":
				for skel in data["skellist"]:
					treeView.createInternalNodeStructure(skel["key"], req.node)
				dataDict["nodeKeys"].extend([x["key"] for x in filteredSkelList])
			else:
				dataDict["leafKeys"].extend([x["key"] for x in filteredSkelList])
			for skel in filteredSkelList:
				if skel["key"] in self.pendingDeletes:
					continue
				if req.treeType == "node":
					skel["_type"] = "node"
				else:
					skel["_type"] = "leaf"
				self._entityCache[skel["key"]] = skel
			treeView.afterInsertRows(req.node, oldLength, extLength, req.treeType)
			if not cursor:
				if req.treeType == "node":
					dataDict["nodeListComplete"] = True
					self.injectPendingInsertsIfNeeded(treeView, "node", req.node)
				else:
					dataDict["leafListComplete"] = True
					self.injectPendingInsertsIfNeeded(treeView, "leaf", req.node)
		elif data["action"] == "view":
			assert False
			self.entryCache[data["values"]["key"]] = data["values"]
			self.entityAvailable.emit(data["values"])

	def fetchFailed(self, req: RequestWrapper, *args, **kwargs):
		print("FETCH FAILED !!!!!!")
		req._hasQueryRunning = False

	def injectPendingInsertsIfNeeded(self, view: TreeView, nodeType:str, parentNode: str):
		"""
			A view might request data for a node, for which we have uploads still pending.
			We'll re-inject these pending items into the view, so the data stayes visible.
		"""
		if parentNode not in self.pendingInserts:
			return
		injectList = self.pendingInserts[parentNode][0 if nodeType=="node" else 1]
		if not injectList:
			return
			# Insert these items into the destination node
		data = view.resolveInternalDataForNodeKey(parentNode)
		assert data, "The node disappeared from the view?"
		if nodeType=="node":
			newNodeList = data["nodeKeys"].copy()
			for pendingKey in injectList:
				# If that key has been resolved, use the final key
				pendingKey = self.lookupTemporaryKey(pendingKey) or pendingKey
				if pendingKey not in newNodeList:
					newNodeList.append(pendingKey)
			# Resort nodes according to the views sort order
			sortProp = view._sortOrder[0]
			def getSortProp(skelKey):
				skel = self._entityCache[skelKey]
				return str(skel.get(sortProp))
			newNodeList.sort(key=getSortProp)
			for idx, newKey in enumerate(newNodeList):
				if newKey in data["nodeKeys"]:
					continue
				view.createInternalNodeStructure(newKey, parentNode)
				view.beforeInsertRows(parentNode, idx, 1, "node")
				data["nodeKeys"].insert(idx, newKey)
				view.afterInsertRows(parentNode, idx, 1, "node")
		else:
			newLeafList = data["leafKeys"].copy()
			for pendingKey in injectList:
			# If that key has been resolved, use the final key
				pendingKey = self.lookupTemporaryKey(pendingKey) or pendingKey
				if pendingKey not in newLeafList:
					newLeafList.append(pendingKey)
			# Resort nodes according to the views sort order
			sortProp = view._sortOrder[0]
			def getSortProp(skelKey):
				skel = self._entityCache[skelKey]
				return str(skel.get(sortProp))
			newLeafList.sort(key=getSortProp)
			for idx, newKey in enumerate(newLeafList):
				if newKey in data["leafKeys"]:
					continue
				view.beforeInsertRows(parentNode, idx, 1, "leaf")
				data["leafKeys"].insert(idx, newKey)
				view.afterInsertRows(parentNode, idx, 1, "leaf")

	def onSaveResult(self, req: RequestWrapper = None) -> None:
		try:
			data = NetworkService.decode(req)
		except:  # Something went wrong, call ErrorHandler
			self.updatingFailedError.emit(str(id(req)))
			QtCore.QTimer.singleShot(self.updateDelay, self.resetOnError)
			return
		if data["action"] == "addSuccess":
			self._entityCache[data["values"]["key"]] = data["values"]
			self._entityCache[data["values"]["key"]]["_type"] = req.skelType
			if req.skelType == "node":
				self._injectItemsIntoViews(data["values"]["parententry"], [data["values"]["key"]], [])
			else:
				self._injectItemsIntoViews(data["values"]["parententry"], [], [data["values"]["key"]])
		elif data["action"] == "editSuccess":
			self._entityCache[data["values"]["key"]].update(data["values"])
			if req.skelType == "node":
				self._notifyViewsItemsChanged([data["values"]["key"]], [])
			else:
				self._notifyViewsItemsChanged([], [data["values"]["key"]])
		req.callback(data)

	def add(self, node: str, skelType: str, callback, **kwargs: Any) -> str:
		tmp = kwargs.copy()
		tmp["node"] = node
		tmp["skelType"] = skelType
		req = NetworkService.request(
			"/%s/add/" % self.module, tmp, secure=(len(kwargs) > 0),
			finishedHandler=self.onSaveResult)
		if not kwargs:
			# This is our first request to fetch the data, dont show a missing hint
			req.wasInitial = True
		else:
			req.wasInitial = False
		req.callback = callback
		req.skelType = skelType
		return str(id(req))

	def edit(self, key: str, skelType, callback, **kwargs: Any) -> str:
		print("XXX IN EDIT", key)
		req = NetworkService.request(
			"/%s/edit/%s/%s" % (self.module, skelType, key), kwargs, secure=(len(kwargs) > 0),
			finishedHandler=self.onSaveResult)
		if not kwargs:
			# This is our first request to fetch the data, dont show a missing hint
			req.wasInitial = True
		else:
			req.wasInitial = False
		#self.entityChanging.emit(key)
		req.callback = callback
		req.skelType = skelType
		#self.checkBusyStatus()
		editTaskId = str(id(req))
		logger.debug("proto list edit id: %r", editTaskId)
		return editTaskId

	def _notifyViewsItemsChanged(self, nodes: List[str], leafs: List[str]):
		for view in self.views:
			for node in nodes:
				index = view.resolveParentIndexForNodeKey(node)
				view.rowChanged(index, 1)
			for leaf in leafs:
				index = view.resolveParentIndexForLeafKey(leaf)
				view.rowChanged(index, 1)

	def _deleteItemsFromViews(self, nodes: List[str], leafs: List[str]):
		"""
			This will remove the given nodes and/or leafs from any active views
			:param nodes: The list of keys (of type node) that should be removed.
			:param leafs: The list of keys (of type leaf) that should be removed.
		"""
		for view in self.views:
			# Mark these entities as deleted in the source nodes
			for node in nodes:
				index = view.resolveParentIndexForNodeKey(node)
				data = view.resolveParentDataForIndex(index)
				if data:  # Not all views may display this nodes/leafs
					oldIdx = data["nodeKeys"].index(node)
					view.beforeRemoveRows(data["nodeKey"], oldIdx, 1, "node")
					data["nodeKeys"].remove(node)
					# Also update our parentNode key
					#nodeData = view.resolveInternalDataForNodeKey(node)
					#nodeData["parentNodeKey"] = destNode
					view.afterRemoveRows(data["nodeKey"], oldIdx, 1, "node")
					view.removeInternalDataForNodeKey(node)
			for leaf in leafs:
				data = view.resolveInternalDataForLeafKey(leaf)
				if data:  # Not all views may display this nodes/leafs
					oldIdx = data["leafKeys"].index(leaf) + len(data["nodeKeys"])
					view.beforeRemoveRows(data["nodeKey"], oldIdx, 1, "leaf")
					data["leafKeys"].remove(leaf)
					view.afterRemoveRows(data["nodeKey"], oldIdx, 1, "leaf")

	def _injectItemsIntoViews(self, destNode:str, nodes: List[str], leafs: List[str]):
		"""
			This will propagate the new nodes and/or leafs to all currently active views
			:param destNode: The key of the node (may be a rootNode) under which they should appear
			:param nodes: The list of keys (of type node) that should be injected. Will be ignored if already displayed
			:param leafs: The list of keys (of type leaf) that should be injected. Will be ignored if already displayed
		"""
		for view in self.views:
			data = view.resolveInternalDataForNodeKey(destNode)
			if data:  # This view also has the destination node
				if nodes:
					newNodeList = data["nodeKeys"].copy()
					newNodeList.extend(nodes)
					# Resort nodes according to the views sort order
					sortProp = view._sortOrder[0]
					def getSortProp(skelKey):
						skel = self._entityCache[skelKey]
						return str(skel.get(sortProp))
					newNodeList.sort(key=getSortProp)
					for idx, newKey in enumerate(newNodeList):
						if newKey in data["nodeKeys"]:
							continue
						view.createInternalNodeStructure(newKey, destNode)
						view.beforeInsertRows(destNode, idx, 1, "node")
						data["nodeKeys"].insert(idx, newKey)
						view.afterInsertRows(destNode, idx, 1, "node")
				if leafs:
					newLeafList = data["leafKeys"].copy()
					newLeafList.extend(leafs)
					# Resort nodes according to the views sort order
					sortProp = view._sortOrder[0]
					def getSortProp(skelKey):
						skel = self._entityCache[skelKey]
						return str(skel.get(sortProp))
					newLeafList.sort(key=getSortProp)
					for idx, newKey in enumerate(newLeafList):
						if newKey in data["leafKeys"]:
							continue
						view.beforeInsertRows(destNode, idx, 1, "leaf")
						data["leafKeys"].insert(idx, newKey)
						view.afterInsertRows(destNode, idx, 1, "leaf")

	def move(self, nodes: List[str], leafs: List[str], destNode: str) -> str:
		"""Moves elements to the given rootNode/path.

		:param nodes: Nodes to be removed
		:param leafs: leafs to be removed
		:param destNode: destination node id
		"""
		# Update our internal views
		self._deleteItemsFromViews(nodes, leafs)
		self._injectItemsIntoViews(destNode, nodes, leafs)
		# We'll treat then as deleted, as injectPendingInsertsIfNeeded will add them anyway
		for node in nodes:
			self.pendingDeletes.add(node)
		for leaf in leafs:
			self.pendingDeletes.add(leaf)
		# Update our pending insert map
		for node in nodes:
			parentNodeKey = self._entityCache[node]["parententry"]
			parentNodeKey = self.lookupTemporaryKey(parentNodeKey) or parentNodeKey
			# Remove from the old node if needed (an Upload, thats still pending and is allready being moved)
			if parentNodeKey in self.pendingInserts:
				if node in self.pendingInserts[parentNodeKey][0]:
					self.pendingInserts[parentNodeKey][0].remove(node)
			# Insert into the target node
			if destNode not in self.pendingInserts:
				self.pendingInserts[destNode] = ([], [])
			self.pendingInserts[destNode][0].append(node)
		for leaf in leafs:
			parentLeafKey = self._entityCache[leaf]["parententry"]
			parentLeafKey = self.lookupTemporaryKey(parentLeafKey) or parentLeafKey
			# Remove from the old node if needed (an Upload, thats still pending and is allready being moved)
			if parentLeafKey in self.pendingInserts:
				if leaf in self.pendingInserts[parentLeafKey][1]:
					self.pendingInserts[parentLeafKey][1].remove(leaf)
			# Insert into the target node
			if destNode not in self.pendingInserts:
				self.pendingInserts[destNode] = ([], [])
			self.pendingInserts[destNode][1].append(leaf)
		# Sync the changes to the server
		for node in nodes:
			self.taskqueue.addTask(MoveItemsTask(self, "node", node, destNode))
		for leaf in leafs:
			self.taskqueue.addTask(MoveItemsTask(self, "leaf", leaf, destNode))

	def onSyncFailureOccured(self, reqGroup):
		print("SYNC FAILURE :(")

	def deleteEntities(self, nodes: list, leafs: list) -> None:
		"""Delete files and/or directories from the server.

		Nodes will be deleted recursively

		:param nodes: Nodes to be removed
		:type nodes: list
		:param leafs: leafs to be removed
		:type leafs: list
		:return:
		"""
		# Update our internal views
		self._deleteItemsFromViews(nodes, leafs)
		# We'll treat then as deleted, as injectPendingInsertsIfNeeded will add them anyway
		for node in nodes:
			self.pendingDeletes.add(node)
		for leaf in leafs:
			self.pendingDeletes.add(leaf)
		# Update our pending insert map
		for node in nodes:
			print(self._entityCache[node])
			parentNodeKey = self._entityCache[node]["parententry"]
			parentNodeKey = self.lookupTemporaryKey(parentNodeKey) or parentNodeKey
			# Remove from the old node if needed (an Upload, thats still pending and is allready being moved)
			if parentNodeKey in self.pendingInserts:
				if node in self.pendingInserts[parentNodeKey][0]:
					self.pendingInserts[parentNodeKey][0].remove(node)
		for leaf in leafs:
			parentLeafKey = self._entityCache[leaf]["parententry"]
			parentLeafKey = self.lookupTemporaryKey(parentLeafKey) or parentLeafKey
			# Remove from the old node if needed (an Upload, thats still pending and is allready being moved)
			if parentLeafKey in self.pendingInserts:
				if leaf in self.pendingInserts[parentLeafKey][1]:
					self.pendingInserts[parentLeafKey][1].remove(leaf)
		for leaf in leafs:
			self.taskqueue.addTask(DeleteItemsTask(self, "leaf", leaf))
		for node in nodes:
			self.taskqueue.addTask(DeleteItemsTask(self, "node", node))



def CheckForTreeModul(moduleName: str, moduleList: dict) -> bool:
	modulData = moduleList[moduleName]
	if "handler" in modulData and (modulData["handler"] == "tree" or modulData["handler"].startswith("tree.")):
		return True
	return False


protocolWrapperClassSelector.insert(2, CheckForTreeModul, TreeWrapper)
