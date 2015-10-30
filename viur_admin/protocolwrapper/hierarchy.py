#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import OrderedDict

from PyQt5 import QtCore

from time import time
from viur_admin.network import NetworkService, RequestGroup, RequestWrapper
from viur_admin.priorityqueue import protocolWrapperClassSelector, protocolWrapperInstanceSelector


class HierarchyWrapper(QtCore.QObject):
	maxCacheTime = 60  # Cache results for max. 60 Seconds
	updateDelay = 1500  # 1,5 Seconds gracetime before reloading

	entitiesChanged = QtCore.pyqtSignal()
	childrenAvailable = QtCore.pyqtSignal((object,))  # A recently queried entity was fetched and is now avaiable
	entityAvailable = QtCore.pyqtSignal((object,))  # We recieved informations about that entry
	busyStateChanged = QtCore.pyqtSignal((bool,))  # If true, im busy right now
	updatingSucceeded = QtCore.pyqtSignal((str,))  # Adding/Editing an entry succeeded
	updatingFailedError = QtCore.pyqtSignal((str,))  # Adding/Editing an entry failed due to network/server error
	updatingDataAvaiable = QtCore.pyqtSignal((str, dict, bool))  # Adding/Editing an entry failed due to missing fields
	modulStructureAvaiable = QtCore.pyqtSignal()  # We fetched the structure for this modul and that data is now
	# avaiable
	rootNodesAvaiable = QtCore.pyqtSignal()  # We fetched the list of rootNodes for this modul and that data is now
	# avaiable

	def __init__(self, modul, *args, **kwargs):
		super(HierarchyWrapper, self).__init__()
		self.modul = modul
		self.dataCache = {}
		self.rootNodes = None
		self.viewStructure = None
		self.addStructure = None
		self.editStructure = None
		self.busy = True
		self.deferedTaskQueue = []
		NetworkService.request("/%s/listRootNodes" % self.modul, successHandler=self.onRootNodesAvaiable)
		req = NetworkService.request("/getStructure/%s" % (self.modul), successHandler=self.onStructureAvaiable)
		protocolWrapperInstanceSelector.insert(1, self.checkForOurModul, self)

	def checkBusyStatus(self):
		busy = False
		for child in self.children():
			if isinstance(child, RequestWrapper) and not child.hasFinished:
				busy = True
				break
		if busy != self.busy:
			self.busy = busy
			self.busyStateChanged.emit(busy)

	def checkForOurModul(self, modulName):
		return (self.modul == modulName)

	def onStructureAvaiable(self, req):
		tmp = NetworkService.decode(req)
		if tmp is None:
			self.checkBusyStatus()
			return
		for stype, structlist in tmp.items():
			structure = OrderedDict()
			for k, v in structlist:
				structure[k] = v
			if stype == "viewSkel":
				self.viewStructure = structure
			elif stype == "editSkel":
				self.editStructure = structure
			elif stype == "addSkel":
				self.addStructure = structure
		self.modulStructureAvaiable.emit()
		self.checkBusyStatus()

	def onRootNodesAvaiable(self, req):
		tmp = NetworkService.decode(req)
		if isinstance(tmp, list):
			self.rootNodes = tmp
		else:
			self.rootNodes = []
		self.rootNodesAvaiable.emit()
		self.checkBusyStatus()

	def cacheKeyFromFilter(self, node, filters):
		tmpList = list(filters.items())
		tmpList.append(("node", node))
		tmpList.sort(key=lambda x: x[0])
		return ("&".join(["%s=%s" % (k, v) for (k, v) in tmpList]))

	def queryData(self, node, **kwargs):
		"""
			Fetches the *children* of that node
		"""
		key = self.cacheKeyFromFilter(node, kwargs)
		if key in self.dataCache.keys():
			self.deferedTaskQueue.append(("childrenAvailable", node))
			QtCore.QTimer.singleShot(25, self.execDefered)
			return (key)
		# Its a cache-miss or cache too old
		r = NetworkService.request("/%s/list/%s" % (self.modul, node), kwargs, successHandler=self.addCacheData)
		r.wrapperCbCacheKey = key
		r.node = node
		self.checkBusyStatus()
		return (key)

	def queryEntry(self, key):
		"""
			Fetches *that* specific entry, not its children
		"""
		if key in self.dataCache.keys():
			QtCore.QTimer.singleShot(25, lambda *args, **kwargs: self.entityAvailable.emit(self.dataCache[key]))
			return (key)
		r = NetworkService.request("/%s/view/%s" % (self.modul, key), successHandler=self.addCacheData)
		return (key)

	def execDefered(self, *args, **kwargs):
		action, node = self.deferedTaskQueue.pop(0)
		if action == "childrenAvailable":
			self.childrenAvailable.emit(node)

	def doCallDefered(self, *args, **kwargs):
		weakSelf, callName, fargs, fkwargs = self.deferedTaskQueue.pop(0)
		callFunc = weakSelf()
		if callFunc is not None:
			targetFunc = getattr(callFunc, callName)
			targetFunc(*fargs, **fkwargs)
		self.checkBusyStatus()

	def addCacheData(self, req):
		data = NetworkService.decode(req)
		cursor = None
		if "cursor" in data.keys():
			cursor = data["cursor"]
		if data["action"] == "list":
			self.dataCache[req.wrapperCbCacheKey] = (time(), data["skellist"], cursor)
			for skel in data["skellist"]:
				self.dataCache[skel["id"]] = skel
			self.childrenAvailable.emit(req.node)
		elif data["action"] == "view":
			self.dataCache[data["values"]["id"]] = data["values"]
			self.entityAvailable.emit(data["values"])
		self.checkBusyStatus()

	def childrenForNode(self, node):
		assert isinstance(node, str)
		res = []
		for item in self.dataCache.values():
			if isinstance(item, dict):  # Its a "normal" item, not a customQuery result
				if item["parententry"] == node:
					res.append(item)
		return (res)

	def add(self, parent, **kwargs):
		tmp = {k: v for (k, v) in kwargs.items()}
		tmp["parent"] = parent
		req = NetworkService.request("/%s/add/" % (self.modul), tmp, secure=(len(kwargs) > 0),
		                             finishedHandler=self.onSaveResult)
		if not kwargs:
			# This is our first request to fetch the data, dont show a missing hint
			req.wasInitial = True
		else:
			req.wasInitial = False
		self.checkBusyStatus()
		return (str(id(req)))

	def edit(self, key, **kwargs):
		req = NetworkService.request("/%s/edit/%s" % (self.modul, key), kwargs, secure=(len(kwargs.keys()) > 0),
		                             finishedHandler=self.onSaveResult)
		if not kwargs:
			# This is our first request to fetch the data, dont show a missing hint
			req.wasInitial = True
		else:
			req.wasInitial = False
		self.checkBusyStatus()
		return (str(id(req)))

	def delete(self, ids):
		if isinstance(ids, list):
			req = RequestGroup(finishedHandler=self.delayEmitEntriesChanged)
			for id in ids:
				r = NetworkService.request("/%s/delete/%s" % (self.modul, id), secure=True)
				req.addQuery(r)
		else:  # We just delete one
			NetworkService.request("/%s/delete/%s" % (self.modul, ids), secure=True,
			                       finishedHandler=self.delayEmitEntriesChanged)
		self.checkBusyStatus()

	def updateSortIndex(self, itemKey, newIndex):
		self.request = NetworkService.request("/%s/setIndex" % self.modul, {"item": itemKey, "index": newIndex}, True,
		                                      finishedHandler=self.delayEmitEntriesChanged)
		self.checkBusyStatus()

	def reparent(self, itemKey, destParent):
		NetworkService.request("/%s/reparent" % self.modul, {"item": itemKey, "dest": destParent}, True,
		                       finishedHandler=self.delayEmitEntriesChanged)
		self.checkBusyStatus()

	def delayEmitEntriesChanged(self, *args, **kwargs):
		"""
			Give the GAE a chance to apply recent changes and then
			force all open views of that modul to reload its data
		"""
		QtCore.QTimer.singleShot(self.updateDelay, self.emitEntriesChanged)
		self.checkBusyStatus()

	def onSaveResult(self, req):
		try:
			data = NetworkService.decode(req)
		except:  # Something went wrong, call ErrorHandler
			self.updatingFailedError.emit(str(id(req)))
			return
		if data["action"] in ["addSuccess", "editSuccess", "deleteSuccess"]:  # Saving succeeded
			QtCore.QTimer.singleShot(self.updateDelay, self.emitEntriesChanged)
			self.updatingSucceeded.emit(str(id(req)))
		else:  # There were missing fields
			self.updatingDataAvaiable.emit(str(id(req)), data, req.wasInitial)
		self.checkBusyStatus()

	def emitEntriesChanged(self, *args, **kwargs):
		self.dataCache = {}
		# for k,v in self.dataCache.items():
		#	# Invalidate the cache. We dont clear that dict sothat execDefered calls dont fail
		#	ctime, data, cursor = v
		#	self.dataCache[ k ] = (1, data, cursor )
		# self.emit( QtCore.SIGNAL("entitiesChanged()") )
		self.entitiesChanged.emit()
		self.checkBusyStatus()


def CheckForHierarchyModul(modulName, modulList):
	modulData = modulList[modulName]
	if "handler" in modulData.keys() and (
					modulData["handler"] == "hierarchy" or modulData["handler"].startswith("hierarchy.")):
		return (True)
	return (False)


protocolWrapperClassSelector.insert(2, CheckForHierarchyModul, HierarchyWrapper)
