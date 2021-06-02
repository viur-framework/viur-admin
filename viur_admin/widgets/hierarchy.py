# -*- coding: utf-8 -*-
import json

from typing import Sequence, Any, List, Dict, Callable, Union

from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin import utils
from viur_admin.config import conf
from viur_admin.network import NetworkService, RequestWrapper
from viur_admin.priorityqueue import protocolWrapperInstanceSelector, actionDelegateSelector
from viur_admin.ui.hierarchyUI import Ui_Hierarchy
from viur_admin.utils import Overlay, loadIcon
from viur_admin.widgets.edit import EditWidget, ApplicationType


class HierarchyItem(QtWidgets.QTreeWidgetItem):
	""" Displays one entry in a QTreeWidget.

	Its comparison-methods have been overridden to reflect the sort-order on the server.
	"""

	def __init__(self, module: str, data: Dict[str, Any]):
		config = conf.serverConfig["modules"][module]
		if "format" in config:
			fmt = config["format"]
		else:
			fmt = "$(name)"
		protoWrap = protocolWrapperInstanceSelector.select(module)
		assert protoWrap is not None
		itemName = utils.formatString(fmt, data, protoWrap.viewStructure)
		# print("HierarchyItem format", format, protoWrap.viewStructure, data, repr(itemName))
		super(HierarchyItem, self).__init__([str(itemName)])
		self.loaded = False
		self.entryData = data
		self.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.ShowIndicator)

	def __gt__(self, other: Any) -> bool:
		if isinstance(other, HierarchyItem) and \
						"sortindex" in self.entryData and \
						"sortindex" in other.entryData:
			return self.entryData["sortindex"] > other.entryData["sortindex"]
		else:
			return super(HierarchyItem, self).__gt__(other)

	def __lt__(self, other: Any) -> bool:
		if isinstance(other, HierarchyItem) and \
						"sortindex" in self.entryData and \
						"sortindex" in other.entryData:
			return self.entryData["sortindex"] < other.entryData["sortindex"]
		else:
			return super(HierarchyItem, self).__lt__(other)


class HierarchyTreeWidget(QtWidgets.QTreeWidget):
	""" Provides an interface for Data structured as a hierarchy on the server.

	@emits hierarchyChanged( PyQt_PyObject=emitter, PyQt_PyObject=module, PyQt_PyObject=rootNode,
	PyQt_PyObject=itemID )
	@emits onItemClicked(PyQt_PyObject=item.data)
	@emits onItemDoubleClicked(PyQt_PyObject=item.data)
	"""

	def __init__(self, parent: QtWidgets.QWidget, module: str, rootNode: Union[str, None] = None, *args: Any, **kwargs: Any):
		""" CTOR

		:param parent: Parent widget
		:param module: Name of the module to show the elements for
		:param rootNode: Key of the rootNode which data should be displayed. If None, this widget tries to choose
		one.
		"""
		super(HierarchyTreeWidget, self).__init__(parent=parent)
		self.module = module
		self.rootNode = rootNode
		self.loadingKey = None
		self.overlay = Overlay(self)
		self.expandList: List[str] = list()
		self.setHeaderHidden(True)
		self.setAcceptDrops(True)
		self.setDragDropMode(self.DragDrop)
		self.rootNodes = None
		protoWrap = protocolWrapperInstanceSelector.select(self.module)
		assert protoWrap is not None
		if not self.rootNode:
			if protoWrap.rootNodes:
				self.rootNode = protoWrap.rootNodes[0]["key"]
		protoWrap.entitiesChanged.connect(self.onHierarchyChanged)
		protoWrap.childrenAvailable.connect(self.setData)
		# self.connect( protoWrap, QtCore.SIGNAL("entitiesChanged()"), self.onHierarchyChanged )
		# self.connect( self, QtCore.SIGNAL("itemExpanded(QTreeWidgetItem *)"), self.onItemExpanded )
		self.itemExpanded.connect(self.onItemExpanded)
		if self.rootNode:
			self.loadData()
		protoWrap.busyStateChanged.connect(self.onBusyStateChanged)

	def onBusyStateChanged(self, busy: bool) -> None:
		if busy:
			self.setDisabled(True)
		else:
			self.setDisabled(False)

	def onHierarchyChanged(self) -> None:
		"""
			Respond to changed Data - refresh our view
		"""
		# Well, seems to affect us, refresh our view
		# First, save all expanded items
		self.expandList = []
		it = QtWidgets.QTreeWidgetItemIterator(self)
		while it.value():
			if it.value().isExpanded():
				self.expandList.append(it.value().entryData["key"])
			it += 1
		# Now clear the treeview and reload data
		self.clear()
		self.loadData()

	def setRootNode(self, rootNode: str, repoName: str = None) -> None:
		"""
			Set the current rootNode.
			(A Modul might have several independent hierarchies)
			@param rootNode: Key of the RootNode.
			@type rootNode: String
			@param repoName: Displayed name of the rootNode (currently unused)
			@param repoName: String or None
		"""
		self.rootNode = rootNode
		self.clear()
		self.loadData()

	def getRootNode(self) -> str:
		return self.rootNode

	def onItemExpanded(self, item: HierarchyItem) -> None:
		""" An item has just been expanded.

		Check, if we already have information about the elements beneath, otherwise load them.

		:param item: our item which has expanded
		"""
		if not item.loaded:
			while item.takeChild(0):
				pass
			self.loadData(item.entryData["key"])

	def loadData(self, parent: HierarchyItem = None) -> None:
		self.overlay.inform(self.overlay.BUSY)
		protoWrap = protocolWrapperInstanceSelector.select(self.module)
		assert protoWrap is not None
		protoWrap.queryData((parent or self.rootNode))

	def setData(self, node: HierarchyItem) -> None:
		"""
			Information about a node we recently queried got available
		"""
		protoWrap = protocolWrapperInstanceSelector.select(self.module)
		assert protoWrap is not None
		if node == self.rootNode:
			self.clear()
		for itemData in protoWrap.childrenForNode(node):
			tvItem = HierarchyItem(self.module, itemData)
			if (itemData["parententry"] == self.rootNode):
				self.addTopLevelItem(tvItem)
			else:
				self.insertItem(tvItem)
			if tvItem.entryData["key"] in self.expandList:
				tvItem.setExpanded(True)
		self.sortItems(0, QtCore.Qt.AscendingOrder)
		self.setSortingEnabled(False)
		self.overlay.clear()

	def insertItem(self, newItem: HierarchyItem, fromChildren: HierarchyItem = None) -> None:
		"""
			New data got available - insert it into the corresponding locations.
		"""
		if not fromChildren:
			idx = 0
			item = self.topLevelItem(idx)
			while item:
				if item.entryData["key"] == newItem.entryData["parententry"]:
					item.addChild(newItem)
					item.loaded = True
					return
				self.insertItem(newItem, item)
				idx += 1
				item = self.topLevelItem(idx)
		else:
			idx = 0
			child = fromChildren.child(idx)
			while child:
				if child.entryData["key"] == newItem.entryData["parententry"]:
					child.addChild(newItem)
					child.loaded = True
					return
				self.insertItem(newItem, child)
				idx += 1
				child = fromChildren.child(idx)

	def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
		""""
			Add URL-Mimedata to the dragevent, so it can be dropped outside.
		"""
		if event.source() == self:
			mimeData = event.mimeData()
			urls = []
			for item in self.selectedItems():
				urls.append(utils.urlForItem(self.module, item.entryData))
			mimeData.setUrls(urls)
			event.mimeData().setData(
					"viur/hierarchyDragData",
					json.dumps({"entities": [x.entryData for x in self.selectedItems()]}).encode("utf-8"))
		# event.accept()
		# event.acceptProposedAction()
		# self.emitDataChanged.emit(event.mimeData)
		super(HierarchyTreeWidget, self).dragEnterEvent(event)

	def dropEvent(self, event: QtGui.QDropEvent) -> None:
		"""
			An Item has been moved inside our HierarchyWidget,
			Move it to the correct location on the server.
		"""
		try:
			draggedItem = self.selectedItems()[0]
		except:
			return
		targetItem = self.itemAt(event.pos())
		event.setDropAction(QtCore.Qt.MoveAction)
		# event.accept()
		super(HierarchyTreeWidget, self).dropEvent(event)
		if not targetItem:  # Moved to the end of the list
			if self.topLevelItemCount() > 1:
				newSortIndex = self.topLevelItem(self.topLevelItemCount() - 2).entryData["sortindex"] + 1
			else:
				newSortIndex = None
			self.reparent(draggedItem.entryData["key"], self.rootNode, sortIndex=newSortIndex)
		else:
			if draggedItem.parent() is targetItem:  # Moved to subitem
				self.reparent(draggedItem.entryData["key"], targetItem.entryData["key"])
			else:  # Moved within its parent list
				while targetItem:
					childIndex = 0
					while childIndex < targetItem.childCount():
						currChild = targetItem.child(childIndex)
						if currChild is draggedItem:
							if childIndex == 0 and targetItem.childCount() > 1:  # is now 1st item
								newSortIndex = targetItem.child(1).entryData["sortindex"] - 1
							elif childIndex == (targetItem.childCount() - 1) and childIndex > 0:  # is now lastitem
								newSortIndex = targetItem.child(childIndex - 1).entryData["sortindex"] + 1
							elif childIndex > 0 and childIndex < (targetItem.childCount() - 1):  # in between
								newSortIndex = (targetItem.child(childIndex - 1).entryData["sortindex"] +
								                targetItem.child(childIndex + 1).entryData["sortindex"]) / 2.0
							else:  # We are the only one in this layer
								newSortIndex = None
							self.reparent(draggedItem.entryData["key"], targetItem.entryData["key"], newSortIndex)
							return
						childIndex += 1
					targetItem = targetItem.parent()
				childIndex = 0
				currChild = self.topLevelItem(childIndex)
				while currChild:
					if currChild is draggedItem:
						if childIndex == 0 and self.topLevelItemCount() > 1:  # is now 1st item
							newSortIndex = self.topLevelItem(1).entryData["sortindex"] - 1
						elif childIndex == (self.topLevelItemCount() - 1) and childIndex > 0:  # is now lastitem
							newSortIndex = self.topLevelItem(childIndex - 1).entryData["sortindex"] + 1
						elif childIndex > 0 and childIndex < (self.topLevelItemCount() - 1):  # in between
							newSortIndex = (self.topLevelItem(childIndex - 1).entryData["sortindex"] +
							                self.topLevelItem(childIndex + 1).entryData["sortindex"]) / 2.0
						else:  # We are the only one in this layer
							newSortIndex = None
						self.reparent(draggedItem.entryData["key"], self.rootNode, newSortIndex)
						return
					childIndex += 1
					currChild = self.topLevelItem(childIndex)

	def reparent(self, itemKey: str, destParent: str, sortIndex: int = None) -> None:
		protoWrap = protocolWrapperInstanceSelector.select(self.module)
		assert protoWrap is not None
		self.setDisabled(True)
		protoWrap.reparent(itemKey, destParent, sortIndex)
		self.overlay.inform(self.overlay.BUSY)


	def updateSortIndex(self, itemKey: str, newIndex: str) -> None:
		protoWrap = protocolWrapperInstanceSelector.select(self.module)
		assert protoWrap is not None
		self.setDisabled(True)
		protoWrap.updateSortIndex(itemKey, newIndex)
		self.overlay.inform(self.overlay.BUSY)


	def requestDelete(self, key: str) -> None:
		self.requestDeleteBox = QtWidgets.QMessageBox(
			QtWidgets.QMessageBox.Question,
			QtCore.QCoreApplication.translate("HierarchyTreeWidget", "Confirm delete"),
			QtCore.QCoreApplication.translate("HierarchyTreeWidget", "Delete %s entries and everything below?") % 1,
			(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No),
			self
		)
		self.requestDeleteBox.buttonClicked.connect(self.reqDeleteCallback)
		self.requestDeleteBox.open()
		QtGui.QGuiApplication.processEvents()
		self.requestDeleteBox.adjustSize()
		self.requestDeleteBox.deleteList = key

	def reqDeleteCallback(self, clickedBtn, *args, **kwargs):
		if clickedBtn == self.requestDeleteBox.button(self.requestDeleteBox.Yes):
			protoWrap = protocolWrapperInstanceSelector.select(self.module)
			assert protoWrap is not None
			self.setDisabled(True)
			protoWrap.delete(self.requestDeleteBox.deleteList)
		self.requestDeleteBox = None



class HierarchyWidget(QtWidgets.QWidget):
	itemClicked = QtCore.pyqtSignal((QtWidgets.QTreeWidgetItem, int))
	itemDoubleClicked = QtCore.pyqtSignal((QtWidgets.QTreeWidgetItem, int))

	def __init__(
			self,
			module: str,
			repoID: str = None,
			actions: List[str] = None,
			editOnDoubleClick: bool = True,
			*args: Any,
			**kwargs: Any):
		super(HierarchyWidget, self).__init__(*args, **kwargs)
		self.ui = Ui_Hierarchy()
		self.ui.setupUi(self)
		layout = QtWidgets.QHBoxLayout(self.ui.treeWidget)
		self.ui.treeWidget.setLayout(layout)
		self.hierarchy = HierarchyTreeWidget(self, module, rootNode=repoID)
		layout.addWidget(self.hierarchy)
		# self.ui.treeWidget.addChild( self.hierarchy )
		self.hierarchy.show()
		self.toolBar = QtWidgets.QToolBar(self)
		self.toolBar.setIconSize(QtCore.QSize(32, 32))
		self.ui.boxActions.addWidget(self.toolBar)
		self.module = module
		self.page = 0
		self.rootNodes: Dict[str, Any] = dict()
		config = conf.serverConfig["modules"][module]
		self.rootNode = None
		self.isSorting = False
		self.path: List[str] = list()
		self.request = None
		self.overlay = Overlay(self)
		self.setAcceptDrops(True)
		#self.ui.webView.hide()
		self._currentActions: List[str] = None
		self.setActions(actions if actions is not None else ["add", "edit", "clone", "preview", "delete"])
		self.hierarchy.itemClicked.connect(self.onItemClicked)
		self.hierarchy.itemClicked.connect(self.itemClicked)
		self.hierarchy.itemDoubleClicked.connect(self.itemDoubleClicked)
		if editOnDoubleClick:
			self.hierarchy.itemDoubleClicked.connect(self.onItemDoubleClicked)

	def setActions(self, actions: List[str]) -> None:
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
			actionWdg = actionDelegateSelector.select("tree.nodeonly.%s" % self.module, action)
			if actionWdg is not None:
				actionWdg = actionWdg(self)
				if isinstance(actionWdg, QtWidgets.QAction):
					self.toolBar.addAction(actionWdg)
					self.addAction(actionWdg)
				else:
					self.toolBar.addWidget(actionWdg)

	def getActions(self) -> List[str]:
		"""
			Returns a list of the currently activated actions on this widget.
		"""
		return self._currentActions

	def onItemClicked(self, item: HierarchyItem, col: int) -> None:
		""" An item has been selected. If we have a previewURL -> show it

		:param item: the item which was clicked
		:param col: the column index
		"""

		config = conf.serverConfig["modules"][self.module]
		if "previewURL" in config and config["previewURL"]:
			previewURL = config["previewURL"].replace("{{key}}", item.entryData["key"])
			if not previewURL.lower().startswith("http"):
				previewURL = NetworkService.url.replace("/admin", "") + previewURL
			self.loadPreview(previewURL)

	def onItemDoubleClicked(self, item: HierarchyItem, col: int) -> None:
		""" Open a editor for this entry.

		:param item: the item which was clicked
		:param col: the column index
		"""

		handler = utils.WidgetHandler(
				lambda: EditWidget(self.module, ApplicationType.HIERARCHY, item.entryData["key"]),
				descr=QtCore.QCoreApplication.translate("Hierarchy", "Edit entry"),
				icon=loadIcon("edit"))
		handler.stackHandler()

	def loadPreview(self, url: str) -> None:
		""" Tries to fetch the entry specified by url and shows it on success

		Take a look in self.setHTML for the view part

		:param url: the url of the item to preview in our webview
		"""
		NetworkService.request(url, successHandler=self.setHTML)

	def setHTML(self, req: RequestWrapper = None) -> None:
		try:  # This request might got canceled meanwhile..
			html = bytes(req.readAll())
		except:
			return
		self.ui.webView.setHtml(html.decode("UTF-8"), QtCore.QUrl(NetworkService.url.replace("/admin", "")))
		self.ui.webView.show()

	def getModul(self) -> str:
		return self.module

	def getRootNode(self) -> str:
		return self.hierarchy.getRootNode()
