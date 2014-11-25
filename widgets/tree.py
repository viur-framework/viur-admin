# -*- coding: utf-8 -*-
import json

from PyQt5 import QtCore, QtGui, QtWidgets
from utils import Overlay
from network import NetworkService, RequestGroup
from event import event
import utils
from priorityqueue import protocolWrapperInstanceSelector, actionDelegateSelector
from ui.treeUI import Ui_Tree
from mainwindow import WidgetHandler
from widgets.edit import EditWidget
from config import conf


class NodeItem(QtWidgets.QListWidgetItem):
    """
        Displayes one subfolder inside a QListWidget
    """

    def __init__(self, data):
        super(NodeItem, self).__init__(QtGui.QIcon("icons/filetypes/folder.png"), str(data["name"]))
        self.entryData = data

    def __gt__(self, other):
        if isinstance(other, self.listWidget().leafItem):
            return ( False )
        elif isinstance(other, self.listWidget().nodeItem):
            return ( self.entryData["name"] > other.entryData["name"] )
        else:
            return ( str(self) > str(other) )

    def __lt__(self, other):
        if isinstance(other, self.listWidget().leafItem):
            return ( True )
        elif isinstance(other, self.listWidget().nodeItem):
            return ( self.entryData["name"] < other.entryData["name"] )
        else:
            return ( str(self) < str(other) )


class LeafItem(QtWidgets.QListWidgetItem):
    """
        Displayes one generic entry inside a QListWidget.
        Can be overriden for a more accurate representation of the element.
    """

    def __init__(self, data):
        if isinstance(data, dict) and "name" in data:
            name = str(data["name"])
        else:
            name = " - "
        super(LeafItem, self).__init__(QtGui.QIcon("icons/filetypes/unknown.png"), str(name))
        self.entryData = data

    def __gt__(self, other):
        if isinstance(other, self.listWidget().nodeItem):
            return ( True )
        elif isinstance(other, self.listWidget().leafItem):
            return ( self.entryData["name"] > other.entryData["name"] )
        else:
            return ( str(self) > str(other) )

    def __lt__(self, other):
        if isinstance(other, self.listWidget().nodeItem):
            return ( False )
        elif isinstance(other, self.listWidget().leafItem):
            return ( self.entryData["name"] < other.entryData["name"] )
        else:
            return ( str(self) < str(other) )


class PathListView(QtWidgets.QListWidget):
    pathChanged = QtCore.pyqtSignal((list,))  # FIXME: DELETE ME
    rootNodeChanged = QtCore.pyqtSignal((str,))
    nodeChanged = QtCore.pyqtSignal((str,))

    def __init__(self, modul, rootNode, node=None, *args, **kwargs):
        super(PathListView, self).__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.modul = modul
        self.rootNode = rootNode
        self.node = node or rootNode
        self.itemClicked.connect(self.pathListItemClicked)
        self.setFlow(self.LeftToRight)
        self.setFixedHeight(35)
        protoWrap = protocolWrapperInstanceSelector.select(self.modul)
        assert protoWrap is not None
        protoWrap.entitiesChanged.connect(self.onEntitiesChanged)

    def onEntitiesChanged(self, node):
        self.rebuild()

    def rebuild(self):
        protoWrap = protocolWrapperInstanceSelector.select(self.modul)
        assert protoWrap is not None
        self.clear()
        node = self.node
        revList = []
        while node:
            if not node in protoWrap.dataCache.keys():
                protoWrap.queryData(node)
                return
            node = protoWrap.dataCache[node].copy()
            revList.append(node)
            node = node["parentdir"]
        for node in revList[:: -1]:
            aitem = NodeItem(node)
            self.addItem(aitem)


    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("viur/treeDragData"):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if self.itemAt(event.pos()):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        dataDict = json.loads(event.mimeData().data("viur/treeDragData").data().decode("UTF-8"))
        protoWrap = protocolWrapperInstanceSelector.select(self.modul)
        assert protoWrap is not None
        destItem = self.itemAt(event.pos())
        protoWrap.move(dataDict["nodes"],
                       dataDict["leafs"],
                       destItem.entryData["id"])

    @QtCore.pyqtSlot(str)
    def setNode(self, node, isInitialCall=False):
        self.node = node
        self.rebuild()
        if isInitialCall:
            self.nodeChanged.emit(self.node)

    @QtCore.pyqtSlot(str)
    def setRootNode(self, rootNode):
        self.rootNode = rootNode
        self.node = rootNode
        self.rebuild()

    def pathListItemClicked(self, item):
        self.setNode(item.entryData["id"], isInitialCall=True)

    # self.setPath( self.path[ : clickeditem.i ] )
    #self.pathChanged.emit( self.path )


class TreeListView(QtWidgets.QListWidget):
    gridSizeIcon = (128, 128)
    gridSizeList = (32, 32)

    leafItem = LeafItem
    nodeItem = NodeItem

    rootNodeChanged = QtCore.pyqtSignal((str,))
    nodeChanged = QtCore.pyqtSignal((str,))


    def __init__(self, modul, rootNode=None, node=None, *args, **kwargs):
        """
            @param parent: Parent widget.
            @type parent: QWidget
            @param modul: Name of the modul to show the elements for
            @type modul: String
            @param rootNode: Key of the rootNode which data should be displayed. If None, this widget tries to choose
            one.
            @type rootNode: String or None
            @param path: If given, displaying starts in this path
            @type path: String or None
        """
        super(TreeListView, self).__init__(*args, **kwargs)
        self.modul = modul
        self.rootNode = rootNode
        self.node = node or rootNode
        self.customQueryKey = None  # As loading is performed in background, they might return results for a dataset
        # which isnt displayed anymore
        protoWrap = protocolWrapperInstanceSelector.select(self.modul)
        assert protoWrap is not None
        protoWrap.entitiesChanged.connect(self.onTreeChanged)
        protoWrap.customQueryFinished.connect(self.onCustomQueryFinished)
        # self.connect( protoWrap, QtCore.SIGNAL("entitiesChanged()"), self.onTreeChanged )
        self.itemDoubleClicked.connect(self.onItemDoubleClicked)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onCustomContextMenuRequested)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setViewMode(self.IconMode)
        self.setSortingEnabled(True)
        self.setIconSize(QtCore.QSize(*[x - 24 for x in self.gridSizeIcon]))
        self.setGridSize(QtCore.QSize(*self.gridSizeIcon))
        self.setSelectionMode(self.ExtendedSelection)
        if self.rootNode is not None:
            print("hAVING ROOTNODE", self.rootNode)
            self.loadData()

    ## Getters & Setters

    def getNode(self):
        return ( self.node )

    def getRootNode(self):
        return ( self.rootNode )

    def getModul(self):
        return ( self.modul )

    @QtCore.pyqtSlot(str)
    def setNode(self, node, isInitialCall=False):
        self.customQueryKey = None
        self.node = node
        self.loadData()
        if isInitialCall:
            self.nodeChanged.emit(self.node)

    def setRootNode(self, rootNode, isInitialCall=False):
        """
            Switch to the given RootNode of our modul and start displaying these items.
            @param rootNode: Key of the new rootNode.
            @type rootNode: String
            @param isInitialCall: If this is the initial call, we remit the signal
            @type repoName: bool
        """
        print("Setting ROOTnode", rootNode)
        self.customQueryKey = None
        if rootNode == self.rootNode:
            return
        self.rootNode = rootNode
        self.node = rootNode
        self.loadData()
        if isInitialCall:
            self.rootNodeChanged.emit(self.rootNode)

    def search(self, searchStr):
        """
            Starts searching for the given string in the current repository.
            @param searchStr: Token to search for
            @type searchStr: string
        """
        self.node = self.rootNode
        self.nodeChanged.emit(self.node)
        if searchStr:
            protoWrap = protocolWrapperInstanceSelector.select(self.modul)
            assert protoWrap is not None
            self.customQueryKey = protoWrap.queryData(self.rootNode, search=searchStr)
        else:
            self.customQueryKey = None
            self.loadData()


    def onItemDoubleClicked(self, item):
        if ( isinstance(item, self.nodeItem) ):
            self.setNode(item.entryData["id"], isInitialCall=True)

    def dragEnterEvent(self, event):
        """
            Allow Drag&Drop inside this widget (ie. moving files to subdirs)
        """
        if event.source() == self:
            event.accept()
            nodes = []
            leafs = []
            for item in self.selectedItems():
                if isinstance(item, self.nodeItem):
                    nodes.append(item.entryData)
                else:
                    leafs.append(item.entryData)
            event.mimeData().setData("viur/treeDragData", json.dumps({"nodes": [x["id"] for x in nodes],
                                                                      "leafs": [x["id"] for x in leafs]}))
            event.mimeData().setUrls(
                [utils.urlForItem(self.getModul(), x) for x in nodes] + [utils.urlForItem(self.getModul(), x) for x in
                                                                         leafs])

    def dragMoveEvent(self, event):
        if isinstance(self.itemAt(event.pos()), self.leafItem):
            event.ignore()
        else:
            event.accept()

    def dropEvent(self, event):
        dataDict = json.loads(event.mimeData().data("viur/treeDragData").data().decode("UTF-8"))
        protoWrap = protocolWrapperInstanceSelector.select(self.modul)
        assert protoWrap is not None
        destItem = self.itemAt(event.pos())
        if not isinstance(destItem, self.nodeItem):
            # Entries have no childs, only nodeItems can have children
            return
        protoWrap.move(dataDict["nodes"],
                       dataDict["leafs"],
                       destItem.entryData["id"]
        )


    def setDefaultRootNode(self):
        NetworkService.request("/%s/listRootNodes" % ( self.modul ), successHandler=self.onSetDefaultRootNode)

    def onSetDefaultRootNode(self, request):
        data = NetworkService.decode(request)
        self.rootNodes = data
        if not self.rootNode:
            try:
                self.rootNode = self.rootNodes[0]["key"]
            except:
                self.rootNode = None
                return
            self.loadData()

    def loadData(self, queryObj=None):
        protoWrap = protocolWrapperInstanceSelector.select(self.modul)
        protoWrap.queryData(self.node)

    def onTreeChanged(self, node):
        if not node:
            self.loadData()
        if node != self.node:  # Not our part of that tree
            return
        if self.customQueryKey is not None:  # We currently display a searchresult:
            return
        protoWrap = protocolWrapperInstanceSelector.select(self.modul)
        assert protoWrap is not None
        res = protoWrap.childrenForNode(self.node)
        self.setDisplayData(res)

    def onCustomQueryFinished(self, queryKey):
        if queryKey != self.customQueryKey:
            return
        protoWrap = protocolWrapperInstanceSelector.select(self.modul)
        assert protoWrap is not None
        self.setDisplayData(protoWrap.getNodesForCustomQuery(queryKey))

    def setDisplayData(self, nodes):
        """
            Clear the current view and display the items in nodes
            @param nodes: List of Nodes which we shall display
            @type nodes: list of dict
        """
        self.clear()
        for entry in nodes:
            if entry["_type"] == "node":
                self.addItem(self.nodeItem(entry))
            elif entry["_type"] == "leaf":
                self.addItem(self.leafItem(entry))
            else:
                raise NotImplementedError()
        self.sortItems()

    def onCustomContextMenuRequested(self, point):
        menu = QtGui.QMenu(self)
        if self.itemAt(point):
            actionMove = menu.addAction(QtCore.QCoreApplication.translate("TreeWidget", "Cut"))
            actionMove.task = "move"
            actionDelete = menu.addAction(QtCore.QCoreApplication.translate("TreeWidget", "Delete"))
            actionDelete.task = "delete"
        elif QtGui.QApplication.clipboard().mimeData().hasFormat("viur/treeDragData"):
            actionPaste = menu.addAction(QtCore.QCoreApplication.translate("TreeWidget", "Insert"))
            actionPaste.task = "paste"
        menu.triggered.connect(self.onContextMenuTriggered)
        menu.popup(self.mapToGlobal(point))

    def onContextMenuTriggered(self, action):
        protoWrap = protocolWrapperInstanceSelector.select(self.modul)
        assert protoWrap is not None
        if action.task == "move":
            nodes = []
            leafs = []
            for item in self.selectedItems():
                if isinstance(item, self.nodeItem):
                    nodes.append(item.entryData["id"])
                else:
                    leafs.append(item.entryData["id"])
            doMove = (action.task == "move")
            mimeData = QtCore.QMimeData()
            mimeData.setData("viur/treeDragData", json.dumps({"nodes": nodes,
                                                              "leafs": leafs,
                                                              "domove": doMove}))
            QtGui.QApplication.clipboard().setMimeData(mimeData)
        elif action.task == "delete":
            nodes = []
            leafs = []
            for item in self.selectedItems():
                if isinstance(item, self.nodeItem):
                    nodes.append(item.entryData["id"])
                else:
                    leafs.append(item.entryData["id"])
            self.requestDelete(nodes, leafs)
        elif action.task == "paste":
            # self.currentItem() ):
            data = json.loads(
                QtGui.QApplication.clipboard().mimeData().data("viur/treeDragData").data().decode("UTF-8"))
            # srcRootNode, srcPath, files, dirs, destRootNode, destPath, doMove ):
            protoWrap.move(data["nodes"], data["leafs"], self.getNode())
        # self.copy( self.clipboard, self.rootNode, self.getPath() )

    def requestDelete(self, nodes, leafs):
        if QtGui.QMessageBox.question(self,
                                      QtCore.QCoreApplication.translate("TreeListView", "Confirm delete"),
                                      QtCore.QCoreApplication.translate("TreeListView",
                                                                        "Delete %s nodes and %s leafs?") % (
                                      len(nodes), len(leafs) ),
                                      QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                      QtGui.QMessageBox.No) == QtGui.QMessageBox.No:
            return ( False )
        protoWrap = protocolWrapperInstanceSelector.select(self.modul)
        assert protoWrap is not None
        protoWrap.deleteEntities(nodes, leafs)
        return ( True )

    def getLeafItemClass(self):
        return ( self.leafItem )

    def getNodeItemClass(self):
        return ( self.nodeItem )

    def isIconMode(self):
        return ( self.viewMode() == self.IconMode )

    def setIconMode(self, iconMode):
        if iconMode:
            self.setViewMode(self.IconMode)
            self.setGridSize(QtCore.QSize(*self.gridSizeIcon))
            self.setIconSize(QtCore.QSize(*[x - 24 for x in self.gridSizeIcon]))
        else:
            self.setViewMode(self.ListMode)
            self.setGridSize(QtCore.QSize(*self.gridSizeList))
            self.setIconSize(QtCore.QSize(*[x - 8 for x in self.gridSizeList]))


class TreeWidget(QtWidgets.QWidget):
    """
        Provides an interface for Data structured as a tree on the server.

        @emits treeChanged(PyQt_PyObject=emitter,PyQt_PyObject=modul,PyQt_PyObject=rootNode,PyQt_PyObject=itemID)
        @emits onItemClicked(PyQt_PyObject=item.data)
        @emits onItemDoubleClicked(PyQt_PyObject=item.data)
    """
    treeWidget = TreeListView

    pathChanged = QtCore.pyqtSignal((list,))
    rootNodeChanged = QtCore.pyqtSignal((str,))
    nodeChanged = QtCore.pyqtSignal((str,))
    currentItemChanged = QtCore.pyqtSignal((QtWidgets.QListWidgetItem, QtWidgets.QListWidgetItem))
    itemSelectionChanged = QtCore.pyqtSignal()
    itemDoubleClicked = QtCore.pyqtSignal((QtWidgets.QListWidgetItem))

    lastSeenNode = {}  # allow opening the last viewed node again

    def __init__(self, modul, rootNode=None, node=None, actions=None, editOnDoubleClick=False, *args, **kwargs):
        """
            @param parent: Parent widget.
            @type parent: QWidget
            @param modul: Name of the modul to show the elements for
            @type modul: String
            @param rootNode: Key of the rootNode which data should be displayed. If None, this widget tries to choose
            one.
            @type rootNode: String or None
            @param path: If given, displaying starts in this path
            @type path: String or None
            @param leafItem: If set, use this class for displaying Entries inside the QListWidget.
            @param leafItem: QListWidgetItem
            @param leafItem: If set, use this class for displaying Directories inside the QListWidget.
            @param leafItem: QListWidgetItem
        """
        super(TreeWidget, self).__init__(*args, **kwargs)
        self.ui = Ui_Tree()
        self.ui.setupUi(self)
        self.modul = modul
        self.editOnDoubleClick = editOnDoubleClick
        self.tree = self.treeWidget(modul, rootNode, node)
        self.ui.listWidgetBox.layout().addWidget(self.tree)
        self.pathList = PathListView(modul, rootNode, [])
        self.ui.pathListBox.layout().addWidget(self.pathList)
        self.editOnDoubleClick = True

        # Inbound Signals
        self.pathList.nodeChanged.connect(self.nodeChanged)
        self.tree.nodeChanged.connect(self.nodeChanged)
        self.pathList.rootNodeChanged.connect(self.rootNodeChanged)
        self.tree.rootNodeChanged.connect(self.rootNodeChanged)
        self.tree.itemSelectionChanged.connect(self.itemSelectionChanged)

        # Outbound Signals
        self.nodeChanged.connect(self.tree.setNode)
        self.nodeChanged.connect(self.pathList.setNode)
        self.rootNodeChanged.connect(self.tree.setRootNode)
        self.rootNodeChanged.connect(self.pathList.setRootNode)

        # Internal Signals
        self.nodeChanged.connect(self.setNode)
        self.rootNodeChanged.connect(self.setRootNode)

        self.overlay = Overlay(self)

        self.clipboard = None  # (str repo,str path, bool doMove, list files, list dirs )
        self.startDrag = False

        # self.connect( event, QtCore.SIGNAL("treeChanged(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"),
        # self.onTreeChanged )

        self.toolBar = QtGui.QToolBar(self)
        self.toolBar.setIconSize(QtCore.QSize(32, 32))
        self.ui.boxActions.addWidget(self.toolBar)
        self.setActions(
            actions if actions is not None else ["dirup", "mkdir", "add", "edit", "clone", "preview", "delete",
                                                 "switchview"])

        self.ui.btnSearch.released.connect(self.onBtnSearchReleased)
        self.tree.itemDoubleClicked.connect(self.itemDoubleClicked)

        protoWrap = protocolWrapperInstanceSelector.select(modul)
        assert protoWrap is not None
        protoWrap.busyStateChanged.connect(self.onBusyStateChanged)
        if not rootNode and protoWrap.rootNodes:
            rootNode = protoWrap.rootNodes[0]["key"]
        if rootNode in self.lastSeenNode.keys():
            lastSeenNode = self.lastSeenNode[rootNode]
        else:
            lastSeenNode = None
        self.setRootNode(rootNode, isInitialCall=True)
        if node:
            self.setNode(node, isInitialCall=True)
        elif lastSeenNode:
            self.setNode(lastSeenNode, isInitialCall=True)

    def onPathChanged(self, path):
        self.path = path

    def onBusyStateChanged(self, busy):
        if busy:
            self.overlay.inform(self.overlay.BUSY)
        else:
            self.overlay.clear()

    def onBtnSearchReleased(self, *args, **kwargs):
        self.tree.search(self.ui.editSearch.text())

    def onEditSearchReturnPressed(self):
        self.search(self.ui.editSearch.text())

    def listWidgetItemDoubleClicked(self, item):
        if ( isinstance(item, self.leafItem) ) and self.editOnDoubleClick:
            descr = QtCore.QCoreApplication.translate("TreeWidget", "Edit entry")
            handler = WidgetHandler(lambda: EditWidget(self.modul, EditWidget.appTree, item.entryData["id"]), descr)
            handler.stackHandler()
        elif ( isinstance(item, NodeItem) ):
            self.path.append(item.dirName)
            self.loadData()

    def setActions(self, actions):
        """
            Sets the actions avaiable for this widget (ie. its toolBar contents).
            Setting None removes all existing actions
            @param actions: List of actionnames
            @type actions: List or None
        """
        self.toolBar.clear()
        for a in self.actions():
            self.removeAction(a)
        if not actions:
            self._currentActions = []
            return
        self._currentActions = actions[:]
        for action in actions:
            modulCfg = conf.serverConfig["modules"][self.modul]
            actionWdg = actionDelegateSelector.select("%s.%s" % ( modulCfg["handler"], self.getModul() ), action)
            if actionWdg is not None:
                actionWdg = actionWdg(self)
                if isinstance(actionWdg, QtWidgets.QAction):
                    self.toolBar.addAction(actionWdg)
                    self.addAction(actionWdg)
                else:
                    self.toolBar.addWidget(actionWdg)

    def getActions(self):
        """
            Returns a list of the currently activated actions on this tree.
        """
        return ( self._currentActions )

    def selectedItems(self):
        """
            Returns the currently selected items.
            Dont mix these with the selectedItems from relationalBones.
            @returns: List
        """
        return ( self.tree.selectedItems() )


    def setRootNode(self, rootNode, isInitialCall=False):
        """
            Switch to the given RootNode of our modul and start displaying these items.
            @param rootNode: Key of the new rootNode.
            @type rootNode: String
            @param repoName: Human-readable description of the given rootNode
            @type repoName: -Currently ignored-
        """
        if isInitialCall:
            self.rootNodeChanged.emit(rootNode)
        # self.pathChanged.emit( self.path )

    def getNode(self):
        return ( self.tree.getNode() )

    def setNode(self, node, isInitialCall=False):
        self.lastSeenNode[self.getRootNode()] = node
        if isInitialCall:
            self.nodeChanged.emit(node)

    def getRootNode(self):
        return ( self.tree.getRootNode() )

    def getModul(self):
        return ( self.modul )

    def getNodeItemClass(self):
        return ( self.tree.getNodeItemClass() )

    def getLeafItemClass(self):
        return ( self.tree.getLeafItemClass() )

    def search(self, searchStr):
        """
            Start a search for the given string.
            If searchStr is None, it ends a currently active search.
            @param searchStr: Token to search for
            @type searchStr: String or None
        """
        if searchStr:
            self.path = None
            self.searchStr = searchStr
            self.loadData({"rootNode": self.rootNode, "path": "", "name$lk": self.searchStr})
        else:
            self.path = []
            self.searchStr = None
            self.loadData()


    def requestDelete(self, nodes, leafs):
        """
            Delete files and/or directories from the server.
            Directories dont need to be empty, the server handles that case internally.

            @param nodes: List of node-ids.
            @type nodes: List
            @param leafs: List of leaf-ids.
            @type leafs: List
        """
        self.tree.requestDelete(nodes, leafs)


    def onProgessUpdate(self, request, done, maximum):
        if request.queryType == "move":
            descr = QtCore.QCoreApplication.translate("TreeWidget", "Moving: %s of %s finished.")
        elif request.queryType == "copy":
            descr = QtCore.QCoreApplication.translate("TreeWidget", "Copying: %s of %s finished.")
        elif request.queryType == "delete":
            descr = QtCore.QCoreApplication.translate("TreeWidget", "Deleting: %s of %s removed.")
        else:
            raise NotImplementedError()
        self.overlay.inform(self.overlay.BUSY, descr % (done, maximum))


    def showError(self, reqWrapper, error):
        self.overlay.inform(self.overlay.ERROR, str(error))

    def isIconMode(self):
        return ( self.tree.isIconMode() )

    def setIconMode(self, iconMode):
        return ( self.tree.setIconMode(iconMode) )
