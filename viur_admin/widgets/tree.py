# -*- coding: utf-8 -*-
import json
from typing import Union, Sequence, Any, Dict, List

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QModelIndex
from viur_admin import utils
from viur_admin.config import conf
from viur_admin.log import getLogger
from viur_admin.network import NetworkService, RequestWrapper
from viur_admin.priorityqueue import protocolWrapperInstanceSelector, actionDelegateSelector
from viur_admin.ui.treeUI import Ui_Tree
from viur_admin.utils import Overlay, WidgetHandler, loadIcon
from viur_admin.widgets.edit import EditWidget, ApplicationType
from viur_admin.priorityqueue import viewDelegateSelector

logger = getLogger(__name__)


class NodeItem(QtWidgets.QListWidgetItem):
	"""
		Displayes one subfolder inside a QListWidget
	"""

	def __init__(
			self,
			data: Dict[str, Any],
			parent: Union[QtWidgets.QListWidget, None] = None):
		super(NodeItem, self).__init__(
			loadIcon("folder"), str(data["name"]), parent=parent,
			type=1200)
		self.entryData = data
		self.setToolTip('<strong>{0}</strong>'.format(data["name"]))

	def __gt__(self, other: Any) -> bool:
		if isinstance(other, self.listWidget().leafItem):
			return False
		elif isinstance(other, self.listWidget().nodeItem):
			return (self.entryData["name"] or "") > (other.entryData["name"] or "")
		else:
			return str(self) > str(other)

	def __lt__(self, other: Any) -> bool:
		if isinstance(other, self.listWidget().leafItem):
			return True
		elif isinstance(other, self.listWidget().nodeItem):
			return (self.entryData["name"] or "") < (other.entryData["name"] or "")
		else:
			return str(self) < str(other)


class LeafItem(QtWidgets.QListWidgetItem):
	"""
		Displayes one generic entry inside a QListWidget.
		Can be overriden for a more accurate representation of the element.
	"""

	def __init__(
			self,
			data: Dict[str, Any],
			parent: Union[QtWidgets.QListWidget, None] = None):
		if isinstance(data, dict) and "name" in data:
			name = str(data["name"])
		else:
			name = " - "
		super(LeafItem, self).__init__(
			loadIcon("file"),
			str(name),
			parent=parent,
			type=1100)

		self.entryData = data
		self._parent = parent

	def __gt__(self, other: Any) -> bool:
		if isinstance(other, self.listWidget().nodeItem):
			return True
		elif isinstance(other, self.listWidget().leafItem):
			return self.entryData["name"] > other.entryData["name"]
		else:
			return str(self) > str(other)

	def __lt__(self, other: Any) -> bool:
		if isinstance(other, self.listWidget().nodeItem):
			return False
		elif isinstance(other, self.listWidget().leafItem) and "name" in self.entryData and "name" in other.entryData["name"]:
			return self.entryData["name"] < other.entryData["name"]
		else:
			return str(self) < str(other)




class TreeListView(QtWidgets.QTreeView):
	gridSizeIcon = (128, 128)
	gridSizeList = (32, 32)

	leafItem = LeafItem
	nodeItem = NodeItem

	rootNodeChanged = QtCore.pyqtSignal((str,))
	nodeChanged = QtCore.pyqtSignal((str,))
	itemSelectionChanged = QtCore.pyqtSignal((list, list))
	itemDoubleClicked = QtCore.pyqtSignal((dict,))

	def __init__(
			self,
			module: str,
			rootNode: Union[str, None] = None,
			node: Union[str, None] = None,
			*args: Any,
			**kwargs: Any):
		"""
			@param module: Name of the module to show the elements for
			@type module: str
			@param rootNode: key of the rootNode which data should be displayed. If None, this widget tries to choose
			one.
			@type rootNode: str | None
			@param path: If given, displaying starts in this path
			@type path: String or None
		"""
		super(TreeListView, self).__init__(*args, **kwargs)
		self.module = self.realModule = module
		if module.endswith("_rootNode"):
			self.realModule = module[:-9]
		self.rootNode = rootNode
		self.node = node or rootNode
		self.customQueryKey = None  # As loading is performed in background, they might return results for a dataset
		# which isnt displayed anymore
		self.delegates = []
		protoWrap = protocolWrapperInstanceSelector.select(self.realModule)
		assert protoWrap is not None

		model = protoWrap.registerView(self)
		self.setModel(model)
		model.setRootNode(self.rootNode)
		model.rebuildDelegates.connect(self.rebuildDelegates)
		model.setDisplayedFields(["name", "active", "levelLimit"])

		self.setItemsExpandable(True)
		self.setUniformRowHeights(True)
		self.setSortingEnabled(False)
		self.setSelectionMode(self.ExtendedSelection)
		#self.setSelectionBehavior(self.SelectRows)
		self.setDragDropMode(self.DragDrop)
		self.setDragEnabled(True)
		self.setAcceptDrops(True)


	def rebuildDelegates(self, bones: Dict[str, Dict[str, Any]]) -> None:
		"""(Re)Attach the viewdelegates to the table.

		:param bones: Skeleton-structure send from the server
		"""
		#logger.debug("ListTableView.rebuildDelegates - bones: %r", bones)
		self.structureCache = bones
		modelHeaders = self.model().headers = []
		modulFields = self.model().fields
		# logger.debug("rebuildDelegates: %r, %r", bones, modulFields)
		#if not modulFields or modulFields == ["name"]:
		#	self.model()._validFields = fields = [key for key, value in bones.items()]
		#else:
		#	fields = [x for x in modulFields if x in bones]
		editableFields = set()
		self.defaultSortColumn = None
		self.header().setSortIndicatorShown(False)
		for colum, field in enumerate(modulFields):
			if isinstance(bones[field], list):
				if bones[field][0]["descr"] != bones[field][1]["descr"]:
					descr = "%s / %s" % (bones[field][0]["descr"], bones[field][1]["descr"])
				else:
					descr = bones[field][0]["descr"]
			else:
				descr = bones[field]["descr"]
			modelHeaders.append(descr)
			# Locate the best ViewDeleate for this colum
			delegateFactory = viewDelegateSelector.select(self.module, field, self.structureCache)
			delegate = delegateFactory(self.module, field, self.structureCache)
			self.setItemDelegateForColumn(colum, delegate)
			self.delegates.append(delegate)
			#delegate.request_repaint.connect(self.repaint)
			if delegate.isEditable():
				editableFields.add(field)
			#if self.defaultFilter.get("orderby") == field:
			#	self.defaultSortColumn = (colum, self.defaultFilter.get("orderdir")=="1")
			#	self.horizontalHeader().setSortIndicatorShown(True)
			#	qtSortOrder = QtCore.Qt.AscendingOrder if not self.defaultSortColumn[ 1] else QtCore.Qt.DescendingOrder
			#	self.horizontalHeader().setSortIndicator(self.defaultSortColumn[0], qtSortOrder)
		self.model().editableFields = editableFields

	## Getters & Setters

	def selectionChanged(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection) -> None:
		super().selectionChanged(selected, deselected)
		newSelection = []
		oldSelection = []
		model = self.model()
		for idx in selected.indexes():
			newSelection.append(model.data(idx, QtCore.Qt.UserRole))
		for idx in deselected.indexes():
			oldSelection.append(model.data(idx, QtCore.Qt.UserRole))
		self.itemSelectionChanged.emit(newSelection, oldSelection)

	def getNode(self) -> str:
		return self.node

	def getRootNode(self) -> str:
		return self.rootNode

	def getModul(self) -> str:
		return self.module

	@QtCore.pyqtSlot(str)
	def setNode(self, node: str, isInitialCall: bool = False) -> None:
		self.customQueryKey = None
		self.node = node
		self.loadData()
		if isInitialCall:
			self.nodeChanged.emit(self.node)

	def setRootNode(self, rootNode: str, isInitialCall: bool = False) -> None:
		"""Switch to the given RootNode of our module and start displaying these items.

		@param rootNode: Key of the new rootNode.
		@type rootNode: str
		@param isInitialCall: If this is the initial call, we remit the signal
		@type isInitialCall: bool
		"""

		self.customQueryKey = None
		if rootNode == self.rootNode:
			return
		self.rootNode = rootNode
		self.node = rootNode
		self.model().setRootNode(rootNode)
		#self.loadData()
		if isInitialCall:
			self.rootNodeChanged.emit(self.rootNode)

	def search(self, searchStr: str) -> None:
		"""Starts searching for the given string in the current repository.

		@param searchStr: Token to search for
		@type searchStr: str
		"""

		self.node = self.rootNode
		#self.nodeChanged.emit(self.node)
		if searchStr:
			protoWrap = protocolWrapperInstanceSelector.select(self.module)
			assert protoWrap is not None
			self.customQueryKey = protoWrap.queryData(self.rootNode, search=searchStr)
		else:
			self.customQueryKey = None
			self.loadData()

	def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
		super().mouseDoubleClickEvent(event)
		destItem = self.model().data(self.indexAt(event.pos()), QtCore.Qt.UserRole)
		if destItem["key"] != self.model()._rootNode:
			self.itemDoubleClicked.emit(destItem)

	def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
		"""
			Allow Drag&Drop inside this widget (ie. moving files to subdirs)
		"""
		logger.error("TreeListWidget.dragEnterEvent")
		if event.source() == self:
			event.accept()
			nodes = []
			leafs = []
			for itemIndex in self.selectionModel().selection().indexes():
				print(itemIndex)
				print(itemIndex.isValid(), itemIndex.row(), itemIndex.column(), itemIndex.parent())
				item = self.model().data(itemIndex, QtCore.Qt.UserRole)
				item["dataPosition"] = itemIndex.row()
				if item["_type"] == "node":
					nodes.append(item)
				else:
					leafs.append(item)
			event.mimeData().setData("viur/treeDragData", json.dumps({"nodes": [x["key"] for x in nodes],
			                                                          "leafs": [x["key"] for x in leafs]}).encode(
				"utf-8"))
			event.mimeData().setUrls(
				[utils.urlForItem(self.getModul(), x) for x in nodes] + [utils.urlForItem(self.getModul(), x) for x
				                                                         in
				                                                         leafs])

	def dropEvent(self, event: QtGui.QDropEvent) -> None:
		logger.error("TreeListWidget.dropEvent")
		dataDict = json.loads(event.mimeData().data("viur/treeDragData").data().decode("UTF-8"))
		protoWrap = protocolWrapperInstanceSelector.select(self.realModule)
		assert protoWrap is not None
		destItem = self.model().data(self.indexAt(event.pos()), QtCore.Qt.UserRole)
		if destItem["_type"] != "node":
			# Entries have no childs, only nodeItems can have children
			return
		protoWrap.move(dataDict["nodes"],
		               dataDict["leafs"],
		               destItem["key"]
		               )
		self.selectionModel().clearSelection()

	def setDefaultRootNode(self) -> None:
		logger.debug("setDefaultRootNode")
		NetworkService.request("/%s/listRootNodes" % self.module, successHandler=self.onSetDefaultRootNode)

	def onSetDefaultRootNode(self, request: RequestWrapper) -> None:
		data = NetworkService.decode(request)
		logger.debug("onSetDefaultRootNode: %r", data)
		self.rootNodes = data
		if not self.rootNode:
			try:
				self.rootNode = self.rootNodes[0]["key"]
			except:
				self.rootNode = None
				return
			self.loadData()

	def loadData(self) -> None:
		logger.debug("loadData")
		try:
			self.itemCache.clear()
		except:
			pass
		self.clear()
		protoWrap = protocolWrapperInstanceSelector.select(self.realModule)
		protoWrap.queryData(self.node)

	def onTreeChanged(self, node: str) -> None:
		logger.debug("onTreeChanged: %r", node)
		if not node:
			self.loadData()
		if node != self.node:  # Not our part of that tree
			return
		if self.customQueryKey is not None:  # We currently display a searchresult:
			return
		protoWrap = protocolWrapperInstanceSelector.select(self.realModule)
		assert protoWrap is not None
		res = protoWrap.childrenForNode(self.node)
		raise NotImplementedError("check this out again!!!")
		self.setDisplayData(res)

	def onCustomQueryFinished(self, queryKey: str) -> None:
		print("onCustomQueryFinished", queryKey)
		self.clear()
		if queryKey != self.customQueryKey:
			return
		protoWrap = protocolWrapperInstanceSelector.select(self.realModule)
		assert protoWrap is not None
		self.setDisplayData(protoWrap.getNodesForCustomQuery(queryKey))

	def setDisplayData(self, nodes: List[Dict[str, Any]]) -> None:
		"""Clear the current view and display the items in nodes

		@param nodes: List of Nodes which we shall display
		@type nodes: list of dict
		"""
		print("setDisplayData", nodes)
		self.setSortingEnabled(False)
		lenNodes = len(nodes)
		logger.debug("TreeListView.setDisplayData: sort off: %r", len(nodes))
		for entry in nodes:
			if entry["_type"] == "node":
				self.addItem(self.nodeItem(entry, self))
			elif entry["_type"] == "leaf":
				self.addItem(self.leafItem(entry, self))
			else:
				raise NotImplementedError()
		self.setSortingEnabled(True)
		logger.debug("TreeListView.setDisplayData: sort on: %r", len(nodes))
		self.sortItems()

	def onAppendedData(self, node: str, items: List[Dict[str, Any]]) -> None:
		"""Clear the current view and display the items in nodes

		@param nodes: List of Nodes which we shall display
		@type nodes: list of dict
		"""

		self.setSortingEnabled(False)
		lenItems = len(items)
		logger.debug("TreeListView.onAppendedData: sort off: %r, %r", node, lenItems)
		for entry in items:
			if entry["_type"] == "node":
				self.addItem(self.nodeItem(entry, self))
			elif entry["_type"] == "leaf":
				self.addItem(self.leafItem(entry, self))
			else:
				raise NotImplementedError()
		self.setSortingEnabled(True)
		logger.debug("TreeListView.onAppendedData: sort on: %r, %r", node, lenItems)
		self.sortItems()

	def onCustomContextMenuRequested(self, point: QtCore.QPoint) -> None:
		menu = QtWidgets.QMenu(self)
		if self.itemAt(point):
			actionMove = menu.addAction(QtCore.QCoreApplication.translate("TreeWidget", "Cut"))
			actionMove.task = "move"
			actionDelete = menu.addAction(QtCore.QCoreApplication.translate("TreeWidget", "Delete"))
			actionDelete.task = "delete"
		elif QtWidgets.QApplication.clipboard().mimeData().hasFormat("viur/treeDragData"):
			actionPaste = menu.addAction(QtCore.QCoreApplication.translate("TreeWidget", "Insert"))
			actionPaste.task = "paste"
		menu.triggered.connect(self.onContextMenuTriggered)
		menu.popup(self.mapToGlobal(point))

	def onContextMenuTriggered(self, action: QtWidgets.QAction) -> None:
		protoWrap = protocolWrapperInstanceSelector.select(self.realModule)
		assert protoWrap is not None
		if action.task == "move":
			nodes = []
			leafs = []
			for item in self.selectedItems():
				if isinstance(item, self.nodeItem):
					nodes.append(item.entryData["key"])
				else:
					leafs.append(item.entryData["key"])
			doMove = (action.task == "move")
			mimeData = QtCore.QMimeData()
			mimeData.setData("viur/treeDragData", json.dumps(
				{
					"nodes": nodes,
					"leafs": leafs,
					"domove": doMove}).encode("utf-8"))
			QtWidgets.QApplication.clipboard().setMimeData(mimeData)
		elif action.task == "delete":
			nodes = []
			leafs = []
			for item in self.selectedItems():
				if isinstance(item, self.nodeItem):
					nodes.append(item.entryData["key"])
				else:
					leafs.append(item.entryData["key"])
			self.requestDelete(nodes, leafs)
		elif action.task == "paste":
			# self.currentItem() ):
			data = json.loads(
				QtWidgets.QApplication.clipboard().mimeData().data("viur/treeDragData").data().decode("UTF-8"))
			# srcRootNode, srcPath, files, dirs, destRootNode, destPath, doMove ):
			protoWrap.move(data["nodes"], data["leafs"], self.getNode())

	# self.copy( self.clipboard, self.rootNode, self.getPath() )

	def requestDelete(self, nodes: Sequence[dict], leafs: Sequence[dict]) -> bool:
		self.requestDeleteBox = QtWidgets.QMessageBox(
			QtWidgets.QMessageBox.Question,
			QtCore.QCoreApplication.translate("ListTableView", "Confirm delete"),
			QtCore.QCoreApplication.translate(
				"TreeListView", "Delete %s nodes and %s leafs?") % (len(nodes), len(leafs)),
			(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No),
			self
		)
		self.requestDeleteBox.buttonClicked.connect(self.reqDeleteCallback)
		self.requestDeleteBox.open()
		QtGui.QGuiApplication.processEvents()
		self.requestDeleteBox.adjustSize()
		self.requestDeleteBox.deleteNode = nodes
		self.requestDeleteBox.deleteLeafs = leafs

	def reqDeleteCallback(self, clickedBtn, *args, **kwargs):
		if clickedBtn == self.requestDeleteBox.button(self.requestDeleteBox.Yes):
			protoWrap = protocolWrapperInstanceSelector.select(self.realModule)
			assert protoWrap is not None
			protoWrap.deleteEntities(self.requestDeleteBox.deleteNode, self.requestDeleteBox.deleteLeafs)
			self.requestDeleteBox = None
		return True

	def getLeafItemClass(self) -> Any:
		return self.leafItem

	def getNodeItemClass(self) -> Any:
		return self.nodeItem



class TreeWidget(QtWidgets.QWidget):
	"""
		Provides an interface for Data structured as a tree on the server.

		@emits treeChanged(PyQt_PyObject=emitter,PyQt_PyObject=module,PyQt_PyObject=rootNode,PyQt_PyObject=itemID)
		@emits onItemClicked(PyQt_PyObject=item.data)
		@emits onItemDoubleClicked(PyQt_PyObject=item.data)
	"""
	treeWidget = TreeListView

	# pathChanged = QtCore.pyqtSignal((list,))
	rootNodeChanged = QtCore.pyqtSignal((str,))
	nodeChanged = QtCore.pyqtSignal((str,))
	currentItemChanged = QtCore.pyqtSignal((QtWidgets.QListWidgetItem, QtWidgets.QListWidgetItem))
	itemSelectionChanged = QtCore.pyqtSignal(list, list)
	itemDoubleClicked = QtCore.pyqtSignal((dict,))
	itemClicked = QtCore.pyqtSignal((QtWidgets.QListWidgetItem))
	lastSeenNode: Dict[str, Any] = dict()  # allow opening the last viewed node again

	def __init__(
			self,
			module: str,
			rootNode: str = None,
			node: str = None,
			actions: Union[str, list, None] = None,
			editOnDoubleClick: bool = False,
			*args: Any,
			**kwargs: Any):

		"""Foo Bar
			@param parent: Parent widget.
			@type parent: QWidget
			@param module: Name of the module to show the elements for
			@type module: String
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
		logger.debug("TreeWidget(): %r, %r, %r, %r, %r, %r", module, rootNode, node, actions, args, kwargs)
		super(TreeWidget, self).__init__(*args, **kwargs)
		self._currentActions = None
		self.path: List[str] = list()
		self.ui = Ui_Tree()
		self.ui.setupUi(self)
		self.module = self.realModule = module
		if module.endswith("_rootNode"):
			self.realModule = module[:-9]
		self.editOnDoubleClick = editOnDoubleClick
		self.tree = self.treeWidget(module, rootNode, node, parent=self)
		self.ui.listWidgetBox.layout().addWidget(self.tree)

		# Inbound Signals
		#self.pathList.nodeChanged.connect(self.nodeChanged)
		self.tree.nodeChanged.connect(self.nodeChanged)
		#self.pathList.rootNodeChanged.connect(self.rootNodeChanged)
		self.tree.rootNodeChanged.connect(self.rootNodeChanged)
		self.tree.itemSelectionChanged.connect(self.itemSelectionChanged)# - FIXME11

		# Outbound Signals
		self.nodeChanged.connect(self.tree.setNode)
		#self.nodeChanged.connect(self.pathList.setNode)
		self.rootNodeChanged.connect(self.tree.setRootNode)
		#self.rootNodeChanged.connect(self.pathList.setRootNode)

		# Internal Signals
		self.nodeChanged.connect(self.setNode)
		self.rootNodeChanged.connect(self.setRootNode)

		self.overlay = Overlay(self)

		self.clipboard = None  # (str repo,str path, bool doMove, list files, list dirs )
		self.startDrag = False

		# self.connect( event, QtCore.SIGNAL("treeChanged(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"),
		# self.onTreeChanged )

		self.toolBar = QtWidgets.QToolBar(self)
		self.toolBar.setIconSize(QtCore.QSize(32, 32))
		self.ui.boxActions.addWidget(self.toolBar)
		self.setActions(
			actions if actions is not None else [ "mkdir", "add", "addleaf", "edit", "clone",
												  "preview", "delete", "selecttablerows"])

		self.ui.btnSearch.released.connect(self.onBtnSearchReleased)
		self.ui.editSearch.returnPressed.connect(self.onEditSearchReturnPressed)
		self.tree.itemDoubleClicked.connect(self.itemDoubleClicked)
		self.tree.itemDoubleClicked.connect(self.listWidgetItemDoubleClicked)  # To allow double-click to edit


		protoWrap = protocolWrapperInstanceSelector.select(self.realModule)

		assert protoWrap is not None
		protoWrap.busyStateChanged.connect(self.onBusyStateChanged)
		if not rootNode and protoWrap.rootNodes:
			rootNode = protoWrap.rootNodes[0]["key"]
		if rootNode in self.lastSeenNode:
			lastSeenNode = self.lastSeenNode[rootNode]
		else:
			lastSeenNode = None
		self.setRootNode(rootNode, isInitialCall=True)
		if node:
			self.setNode(node, isInitialCall=True)
		elif lastSeenNode:
			self.setNode(lastSeenNode, isInitialCall=True)
		# Allow switching rootNodes if there's more than one
		if len(protoWrap.rootNodes) > 1:
			selectComboBox = QtWidgets.QComboBox(self)
			for nodeData in protoWrap.rootNodes:
				selectComboBox.addItem(nodeData["name"])
			selectComboBox.currentIndexChanged.connect(self.rootNodeChangeRequested)
			self.ui.boxActions.addWidget(selectComboBox)

	def rootNodeChangeRequested(self, index):
		# Called from the root node select combobox on change
		protoWrap = protocolWrapperInstanceSelector.select(self.realModule)
		self.setRootNode(protoWrap.rootNodes[index]["key"], True)


	def onPathChanged(self, path: list) -> None:
		self.path = path

	def onBusyStateChanged(self, busy: bool) -> None:
		if busy:
			self.setDisabled(True)
			self.overlay.inform(self.overlay.BUSY)
		else:
			self.setDisabled(False)
			self.overlay.clear()
			#self.pathList.rebuild()

	def onBtnSearchReleased(self, *args: Any, **kwargs: Any) -> None:
		self.tree.search(self.ui.editSearch.text())

	def onEditSearchReturnPressed(self) -> None:
		self.search(self.ui.editSearch.text())

	def listWidgetItemDoubleClicked(self, item: QtWidgets.QListWidgetItem) -> None:
		if self.editOnDoubleClick:
			widget = lambda: EditWidget(self.module, ApplicationType.TREE, item["key"], skelType=item["_type"])
			handler = WidgetHandler(widget, descr=QtCore.QCoreApplication.translate("TreeHandler", "Add entry"), icon=loadIcon("edit"))
			handler.stackHandler()


	def setActions(self, actions: Union[Sequence[str], None]) -> None:
		"""Sets the actions available for this widget (ie. its toolBar contents).

		Setting None removes all existing actions
		@param actions: List of action names
		"""
		self.toolBar.clear()
		for a in self.actions():
			self.removeAction(a)

		if not actions:
			self._currentActions = []
			return

		self._currentActions = actions[:]

		for action in actions:
			modulCfg = conf.serverConfig["modules"][self.module]
			actionWdg = actionDelegateSelector.select("%s.%s" % (modulCfg["handler"], self.getModul()), action)
			if actionWdg is not None:
				actionWdg = actionWdg(self)
				if isinstance(actionWdg, QtWidgets.QAction):
					self.toolBar.addAction(actionWdg)
					self.addAction(actionWdg)
				else:
					self.toolBar.addWidget(actionWdg)

	def getActions(self) -> List[str]:
		"""
			Returns a list of the currently activated actions on this tree.
		"""
		return self._currentActions

	def selectedItems(self) -> List[QtWidgets.QListWidgetItem]:
		"""
			Returns the currently selected items.
			Dont mix these with the selectedItems from relationalBones.
			@returns: List
		"""
		res = []
		model = self.tree.model()
		for idx in self.tree.selectionModel().selection().indexes():
			res.append(model.data(idx, QtCore.Qt.UserRole))
		return res

	def setRootNode(self, rootNode: str, isInitialCall: bool = False) -> None:
		"""
			Switch to the given RootNode of our module and start displaying these items.
			@param rootNode: Key of the new rootNode.
			@type rootNode: String
		"""
		if isInitialCall:
			self.rootNodeChanged.emit(rootNode)

	# self.pathChanged.emit( self.path )

	def getNode(self) -> str:
		return self.tree.getNode()

	def setNode(self, node: str, isInitialCall: bool = False) -> None:
		self.lastSeenNode[self.getRootNode()] = node
		if isInitialCall:
			self.nodeChanged.emit(node)

	def getRootNode(self) -> str:
		return self.tree.getRootNode()

	def getModul(self) -> str:
		return self.module

	def getNodeItemClass(self) -> str:
		return self.tree.getNodeItemClass()

	def getLeafItemClass(self) -> Any:
		return self.tree.getLeafItemClass()

	def search(self, searchStr: str) -> None:
		"""
			Start a search for the given string.
			If searchStr is None, it ends a currently active search.
			@param searchStr: Token to search for
			@type searchStr: String or None
		"""
		# befoire = {"rootNode": self.rootNode, "path": "", "name$lk": self.searchStr}
		self.tree.model().search(searchStr)
		#self.tree.search(searchStr)

	def requestDelete(self, nodes: List[str], leafs: List[str]) -> None:
		"""
			Delete files and/or directories from the server.
			Directories dont need to be empty, the server handles that case internally.

			@param nodes: List of node keys.
			@param leafs: List of leaf keys.
		"""
		self.tree.requestDelete(nodes, leafs)

	def onProgressUpdate(self, request: RequestWrapper, done: bool, maximum: int) -> None:
		if request.queryType == "move":
			descr = QtCore.QCoreApplication.translate("TreeWidget", "Moving: %s of %s finished.")
		elif request.queryType == "copy":
			descr = QtCore.QCoreApplication.translate("TreeWidget", "Copying: %s of %s finished.")
		elif request.queryType == "delete":
			descr = QtCore.QCoreApplication.translate("TreeWidget", "Deleting: %s of %s removed.")
		else:
			logger.error("Error in TreeWidget.onProgressUpdate", request.queryType == "move")
			raise NotImplementedError()
		self.overlay.inform(self.overlay.BUSY, descr % (done, maximum))

	def showError(self, req: RequestWrapper, error: Any) -> None:
		self.overlay.inform(self.overlay.ERROR, str(error))

