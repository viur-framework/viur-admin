#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import OrderedDict

from PyQt5 import QtCore
from network import NetworkService, RequestGroup, RequestWrapper
from priorityqueue import protocolWrapperClassSelector, protocolWrapperInstanceSelector


class TreeWrapper(QtCore.QObject):
    maxCacheTime = 60  # Cache results for max. 60 Seconds
    updateDelay = 1500  # 1,5 Seconds gracetime before reloading
    batchSize = 30  # Fetch 30 entries at once
    protocolWrapperInstancePriority = 1

    entitiesChanged = QtCore.pyqtSignal((str,))  # Node,
    entityAvailable = QtCore.pyqtSignal((object,))  # A recently queried entity was fetched and is now avaiable
    customQueryFinished = QtCore.pyqtSignal((str,))  # RequestID,
    rootNodesAvaiable = QtCore.pyqtSignal()
    busyStateChanged = QtCore.pyqtSignal((bool,))  # If true, im busy right now
    updatingSucceeded = QtCore.pyqtSignal((str,))  # Adding/Editing an entry succeeded
    updatingFailedError = QtCore.pyqtSignal((str,))  # Adding/Editing an entry failed due to network/server error
    updatingDataAvaiable = QtCore.pyqtSignal((str, dict, bool))  # Adding/Editing an entry failed due to missing fields

    def __init__(self, modul, *args, **kwargs):
        super(TreeWrapper, self).__init__()
        self.modul = modul
        self.dataCache = {}
        # self.parentMap = {} #Stores references from child -> parent
        self.viewLeafStructure = None
        self.viewNodeStructure = None
        self.addLeafStructure = None
        self.addNodeStructure = None
        self.editStructure = None
        self.editLeafStructure = None
        self.editNodeStructure = None
        self.rootNodes = None
        self.busy = True
        req = NetworkService.request("/getStructure/%s" % (self.modul), successHandler=self.onStructureAvaiable)
        NetworkService.request("/%s/listRootNodes" % self.modul, successHandler=self.onRootNodesAvaiable)
        print("Initializing TreeWrapper for modul %s" % self.modul)
        protocolWrapperInstanceSelector.insert(self.protocolWrapperInstancePriority, self.checkForOurModul, self)
        self.deferedTaskQueue = []

    def checkBusyStatus(self):
        busy = False
        for child in self.children():
            if isinstance(child, RequestWrapper) or isinstance(child, RequestGroup):
                if not child.hasFinished:
                    busy = True
                    break
        if busy != self.busy:
            self.busy = busy
            self.busyStateChanged.emit(busy)


    def checkForOurModul(self, modulName):
        return ( self.modul == modulName )


    def clearCache(self):
        """
            Resets our Cache.
            Does not emit entitiesChanged!
        """
        self.dataCache = {}
        for node in self.rootNodes:
            node = node.copy()
            node["_type"] = "node"
            node["id"] = node["key"]
            node["_isRootNode"] = 1
            node["parentdir"] = None
            self.dataCache[node["key"]] = node

    def onStructureAvaiable(self, req):
        tmp = NetworkService.decode(req)
        if tmp is None:
            self.checkBusyStatus()
            return
        for stype, structlist in tmp.items():
            structure = OrderedDict()
            for k, v in structlist:
                structure[k] = v
            if stype == "viewNodeSkel":
                self.viewNodeStructure = structure
            elif stype == "viewLeafSkel":
                self.viewLeafStructure = structure
            elif stype == "editNodeSkel":
                self.editNodeStructure = structure
            elif stype == "editLeafSkel":
                self.editLeafStructure = structure
            elif stype == "addNodeSkel":
                self.addNodeStructure = structure
            elif stype == "addLeafSkel":
                self.addLeafStructure = structure
        self.emit(QtCore.SIGNAL("onModulStructureAvaiable()"))
        self.checkBusyStatus()

    def onRootNodesAvaiable(self, req):
        tmp = NetworkService.decode(req)
        if isinstance(tmp, list):
            self.rootNodes = tmp
        self.clearCache()
        self.rootNodesAvaiable.emit()
        self.checkBusyStatus()

    def childrenForNode(self, node):
        assert isinstance(node, str)
        res = []
        for item in self.dataCache.values():
            if isinstance(item, dict):  # Its a "normal" item, not a customQuery result
                if item["parentdir"] == node:
                    res.append(item)
        return ( res )


    def cacheKeyFromFilter(self, node, filters):
        tmp = {k: v for k, v in filters.items()}
        tmp["node"] = node
        tmpList = list(tmp.items())
        tmpList.sort(key=lambda x: x[0])
        return ( "&".join(["%s=%s" % (k, v) for (k, v) in tmpList]) )

    def queryData(self, node, **kwargs):
        key = self.cacheKeyFromFilter(node, kwargs)
        if key in self.dataCache.keys():
            if self.dataCache[key] is None:
                # We allready started fetching that key
                return ( key )
            self.deferedTaskQueue.append(( "entitiesChanged", key ))
            QtCore.QTimer.singleShot(25, self.execDefered)
            # callback( None, data, cursor )
            return ( key )
        # Its a cache-miss or cache too old
        self.dataCache[key] = None
        tmp = {k: v for k, v in kwargs.items()}
        tmp["node"] = node
        for skelType in ["node", "leaf"]:
            tmp["skelType"] = skelType
            tmp["amount"] = self.batchSize
            r = NetworkService.request("/%s/list" % self.modul, tmp, successHandler=self.addCacheData)
            r.wrapperCacheKey = key
            r.skelType = skelType
            r.node = node
            r.queryArgs = kwargs
        if not node in [x["key"] for x in self.rootNodes]:  #Dont query rootNodes again..
            r = NetworkService.request("/%s/view/node/%s" % (self.modul, node), successHandler=self.addCacheData)
            r.wrapperCacheKey = node
            r.skelType = "node"
            r.node = node
            r.queryArgs = kwargs
        self.checkBusyStatus()
        return ( key )

    def queryEntry(self, key, skelType):
        if key in self.dataCache.keys():
            self.deferedTaskQueue.append(("entityAvailable", key))
            QtCore.QTimer.singleShot(25, self.execDefered)
            return ( key )
        r = NetworkService.request("/%s/view/%s/%s" % (self.modul, skelType, key ), successHandler=self.addCacheData)
        r.wrapperCacheKey = key
        r.queryArgs = None
        r.skelType = skelType
        r.node = key
        return ( key )

    def execDefered(self, *args, **kwargs):
        m, key = self.deferedTaskQueue.pop(0)
        if m == "entitiesChanged":
            self.entitiesChanged.emit(key)
        elif m == "entityAvailable":
            self.entityAvailable.emit(self.dataCache[key])
        self.checkBusyStatus()

    def getNode(self, node):
        if node in self.dataCache.keys():
            return ( self.dataCache[node] )
        return ( None )


    def getNodesForCustomQuery(self, key):
        if not key in self.dataCache or self.dataCache[key] is None:
            return ( [] )
        else:
            return ( self.dataCache[key] )

    def addCacheData(self, req):
        data = NetworkService.decode(req)
        if req.queryArgs:  # This was a custom request
            key = self.cacheKeyFromFilter(req.node, req.queryArgs)
            if not key in self.dataCache.keys():
                self.dataCache[key] = []
            assert data["action"] == "list"
            for skel in data["skellist"]:
                if not skel["id"] in [x["id"] for x in self.dataCache[key]]:
                    skel["_type"] = req.skelType
                    self.dataCache[key].append(skel)
            self.customQueryFinished.emit(key)
        cursor = None
        if "cursor" in data.keys():
            cursor = data["cursor"]
        if data["action"] == "list":
            for skel in data["skellist"]:
                skel["_type"] = req.skelType
                self.dataCache[skel["id"]] = skel
            if len(data["skellist"]) == self.batchSize:  # There might be more results
                if "cursor" in data.keys() and data["cursor"]:  #We have a cursor (we can continue this query)
                    # Fetch the next batch
                    tmp = {k: v for k, v in req.queryArgs.items()}
                    tmp["node"] = req.node
                    tmp["cursor"] = data["cursor"]
                    tmp["skelType"] = req.skelType
                    tmp["amount"] = self.batchSize
                    r = NetworkService.request("/%s/list" % self.modul, tmp, successHandler=self.addCacheData)
                    r.wrapperCacheKey = req.wrapperCacheKey
                    r.skelType = req.skelType
                    r.node = req.node
                    r.queryArgs = req.queryArgs
        elif data["action"] == "view":
            skel = data["values"]
            skel["_type"] = req.skelType
            self.dataCache[skel["id"]] = skel
            self.entityAvailable.emit(skel)
        if req.wrapperCacheKey in self.dataCache.keys() and self.dataCache[req.wrapperCacheKey] is None:
            del self.dataCache[req.wrapperCacheKey]
        self.entitiesChanged.emit(req.node)
        self.checkBusyStatus()

    def add(self, node, skelType, **kwargs):
        tmp = {k: v for (k, v) in kwargs.items()}
        tmp["node"] = node
        tmp["skelType"] = skelType
        req = NetworkService.request("/%s/add/" % ( self.modul ), tmp, secure=(len(kwargs) > 0),
                                     finishedHandler=self.onSaveResult)
        if not kwargs:
            # This is our first request to fetch the data, dont show a missing hint
            req.wasInitial = True
        else:
            req.wasInitial = False
        self.checkBusyStatus()
        return ( str(id(req)) )

    def edit(self, key, skelType, **kwargs):
        req = NetworkService.request("/%s/edit/%s/%s" % ( self.modul, skelType, key ), kwargs, secure=(len(kwargs) > 0),
                                     finishedHandler=self.onSaveResult)
        if not kwargs:
            # This is our first request to fetch the data, dont show a missing hint
            req.wasInitial = True
        else:
            req.wasInitial = False
        self.checkBusyStatus()
        return ( str(id(req)) )


    def deleteEntities(self, nodes, leafs):
        """
            Delete files and/or directories from the server.
            Directories dont need to be empty, the server handles that case internally.

            @param rootNode: rootNode to delete from
            @type rootNode: String
            @param path: Path (relative to the rootNode) which contains the elements which should be deleted.
            @type path: String
            @param entries: List of filenames in that directory.
            @type entries: List
            @param dirs: List of directories in that directory.
            @type dirs: List
        """
        request = RequestGroup(finishedHandler=self.delayEmitEntriesChanged)
        for leaf in leafs:
            request.addQuery(NetworkService.request("/%s/delete" % self.modul, {"id": leaf,
                                                                                "skelType": "leaf"}, parent=self))
        for node in nodes:
            request.addQuery(NetworkService.request("/%s/delete" % self.modul, {"id": node,
                                                                                "skelType": "node"}, parent=self))
        # request.flushList = [ lambda *args, **kwargs:  self.flushCache( rootNode, path ) ]
        request.queryType = "delete"
        self.checkBusyStatus()
        return ( str(id(request)) )


    def move(self, nodes, leafs, destNode):
        """
            Copy or move elements to the given rootNode/path.

            @param clipboard: Tuple holding all informations about the elements which get moved/copied
            @type clipboard: (srcRepo, srcPath, doMove, entities, dirs)
            @param rootNode: Destination rootNode
            @type rootNode: String
            @param path: Destination path
            @type path: String
        """
        request = RequestGroup(finishedHandler=self.delayEmitEntriesChanged)
        for node in nodes:
            request.addQuery(NetworkService.request("/%s/move" % self.modul, {"id": node,
                                                                              "skelType": "node",
                                                                              "destNode": destNode
            }
                                                    , parent=self))
        for leaf in leafs:
            request.addQuery(NetworkService.request("/%s/move" % self.modul, {"id": leaf,
                                                                              "skelType": "leaf",
                                                                              "destNode": destNode
            }
                                                    , parent=self))
        request.queryType = "move"
        self.checkBusyStatus()
        return ( str(id(request)) )


    def delayEmitEntriesChanged(self, req=None, *args, **kwargs):
        """
            Give the GAE a chance to apply recent changes and then
            force all open views of that modul to reload its data
        """
        if req is not None:
            try:
                print(NetworkService.decode(req))
            except:
                print("error decoding response")
        QtCore.QTimer.singleShot(self.updateDelay, self.emitEntriesChanged)


    def onSaveResult(self, req):
        try:
            data = NetworkService.decode(req)
        except:  # Something went wrong, call ErrorHandler
            self.updatingFailedError.emit(str(id(req)))
            QtCore.QTimer.singleShot(self.updateDelay, self.resetOnError)
            return
        if data["action"] in ["addSuccess", "editSuccess", "deleteSuccess"]:  # Saving succeeded
            QtCore.QTimer.singleShot(self.updateDelay, self.emitEntriesChanged)
            self.updatingSucceeded.emit(str(id(req)))
        else:  # There were missing fields
            self.updatingDataAvaiable.emit(str(id(req)), data, req.wasInitial)
        self.checkBusyStatus()

    def emitEntriesChanged(self, *args, **kwargs):
        self.clearCache()
        self.entitiesChanged.emit(None)
        self.checkBusyStatus()

    def resetOnError(self, *args, **kwargs):
        """
            If one or more requests fail, flush our cache and force
            all listening widgets to reload.
        """
        self.emitEntriesChanged()


def CheckForTreeModul(modulName, modulList):
    modulData = modulList[modulName]
    if "handler" in modulData.keys() and ( modulData["handler"] == "tree" or modulData["handler"].startswith("tree.")):
        return ( True )
    return ( False )


protocolWrapperClassSelector.insert(0, CheckForTreeModul, TreeWrapper)
