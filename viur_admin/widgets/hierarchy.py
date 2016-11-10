# -*- coding: utf-8 -*-
import json

from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin import utils
from viur_admin.config import conf
from viur_admin.network import NetworkService
from viur_admin.priorityqueue import protocolWrapperInstanceSelector, actionDelegateSelector
from viur_admin.ui.hierarchyUI import Ui_Hierarchy
from viur_admin.utils import Overlay
from viur_admin.widgets.edit import EditWidget


class HierarchyItem(QtWidgets.QTreeWidgetItem):
	""" Displays one entry in a QTreeWidget.

	Its comparison-methods have been overridden to reflect the sort-order on the server.
	"""

	def __init__(self, modul, data):
		config = conf.serverConfig["modules"][modul]
		if "format" in config.keys():
			fmt = config["format"]
		else:
			fmt = "$(name)"
		protoWrap = protocolWrapperInstanceSelector.select(modul)
		assert protoWrap is not None
		itemName = utils.formatString(fmt, protoWrap.viewStructure, data)
		# print("HierarchyItem format", format, protoWrap.viewStructure, data.keys(), repr(itemName))
		super(HierarchyItem, self).__init__([str(itemName)])
		self.loaded = False
		self.entryData = data
		self.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.ShowIndicator)

	def __gt__(self, other):
		if isinstance(other, HierarchyItem) and \
						"sortindex" in self.entryData.keys() and \
						"sortindex" in other.entryData.keys():
			return self.entryData["sortindex"] > other.entryData["sortindex"]
		else:
			return super(HierarchyItem, self).__gt__(other)

	def __lt__(self, other):
		if isinstance(other, HierarchyItem) and \
						"sortindex" in self.entryData.keys() and \
						"sortindex" in other.entryData.keys():
			return self.entryData["sortindex"] < other.entryData["sortindex"]
		else:
			return super(HierarchyItem, self).__lt__(other)


class HierarchyTreeWidget(QtWidgets.QTreeWidget):
	""" Provides an interface for Data structured as a hierarchy on the server.

	@emits hierarchyChanged( PyQt_PyObject=emitter, PyQt_PyObject=modul, PyQt_PyObject=rootNode,
	PyQt_PyObject=itemID )
	@emits onItemClicked(PyQt_PyObject=item.data)
	@emits onItemDoubleClicked(PyQt_PyObject=item.data)
	"""

	def __init__(self, parent, modul, rootNode=None, *args, **kwargs):
		""" CTOR

		:param parent: Parent widget
		:type parent: QWidgets.QWidget
		:param modul: Name of the modul to show the elements for
		:type modul: str
		:param rootNode: Key of the rootNode which data should be displayed. If None, this widget tries to choose
		one.
		:type rootNode: str or None
		"""
		super(HierarchyTreeWidget, self).__init__(parent=parent)
		self.modul = modul
		self.rootNode = rootNode
		self.loadingKey = None
		self.overlay = Overlay(self)
		self.expandList = []
		self.setHeaderHidden(True)
		self.setAcceptDrops(True)
		self.setDragDropMode(self.DragDrop)
		self.rootNodes = None
		protoWrap = protocolWrapperInstanceSelector.select(self.modul)
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

	def onHierarchyChanged(self):
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

	def setRootNode(self, rootNode, repoName=None):
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

	def getRootNode(self):
		return self.rootNode

	def onItemExpanded(self, item, *args, **kwargs):
		""" An item has just been expanded.

		Check, if we already have information about the elements beneath, otherwise load them.

		:param item: our item which has expanded
		:type item: HierarchyItem
		"""
		if not item.loaded:
			while item.takeChild(0):
				pass
			self.loadData(item.entryData["key"])

	def loadData(self, parent=None):
		self.overlay.inform(self.overlay.BUSY)
		protoWrap = protocolWrapperInstanceSelector.select(self.modul)
		assert protoWrap is not None
		protoWrap.queryData((parent or self.rootNode))

	def setData(self, node):
		"""
			Information about a node we recently queried got avaiable
		"""
		protoWrap = protocolWrapperInstanceSelector.select(self.modul)
		assert protoWrap is not None
		if node == self.rootNode:
			self.clear()
		for itemData in protoWrap.childrenForNode(node):
			tvItem = HierarchyItem(self.modul, itemData)
			if (itemData["parententry"] == self.rootNode):
				self.addTopLevelItem(tvItem)
			else:
				self.insertItem(tvItem)
			if tvItem.entryData["key"] in self.expandList:
				tvItem.setExpanded(True)
		self.sortItems(0, QtCore.Qt.AscendingOrder)
		self.setSortingEnabled(False)
		self.overlay.clear()

	def insertItem(self, newItem, fromChildren=None):
		"""
			New data got avaiable - insert it into the corresponding locations.
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

	def dragEnterEvent(self, event):
		""""
			Add URL-Mimedata to the dragevent, so it can be dropped outside.
		"""
		if event.source() == self:
			mimeData = event.mimeData()
			urls = []
			for item in self.selectedItems():
				urls.append(utils.urlForItem(self.modul, item.entryData))
			mimeData.setUrls(urls)
			event.mimeData().setData(
					"viur/hierarchyDragData",
					json.dumps({"entities": [x.entryData for x in self.selectedItems()]}).encode("utf-8"))
		# event.accept()
		# event.acceptProposedAction()
		# self.emitDataChanged.emit(event.mimeData)
		super(HierarchyTreeWidget, self).dragEnterEvent(event)

	def dropEvent(self, event):
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
			self.reparent(draggedItem.entryData["key"], self.rootNode)
			if self.topLevelItemCount() > 1:
				self.updateSortIndex(draggedItem.entryData["key"],
				                     self.topLevelItem(self.topLevelItemCount() - 2).entryData["sortindex"] + 1)
		else:
			if draggedItem.parent() is targetItem:  # Moved to subitem
				self.reparent(draggedItem.entryData["key"], targetItem.entryData["key"])
			else:  # Moved within its parent list
				while targetItem:
					childIndex = 0
					while childIndex < targetItem.childCount():
						currChild = targetItem.child(childIndex)
						if currChild is draggedItem:
							self.reparent(draggedItem.entryData["key"], targetItem.entryData["key"])
							if childIndex == 0 and targetItem.childCount() > 1:  # is now 1st item
								self.updateSortIndex(draggedItem.entryData["key"],
								                     targetItem.child(1).entryData["sortindex"] - 1)
							elif childIndex == (targetItem.childCount() - 1) and childIndex > 0:  # is now lastitem
								self.updateSortIndex(draggedItem.entryData["key"],
								                     targetItem.child(childIndex - 1).entryData["sortindex"] + 1)
							elif childIndex > 0 and childIndex < (targetItem.childCount() - 1):  # in between
								newSortIndex = (targetItem.child(childIndex - 1).entryData["sortindex"] +
								                targetItem.child(childIndex + 1).entryData["sortindex"]) / 2.0
								self.updateSortIndex(draggedItem.entryData["key"], newSortIndex)
							else:  # We are the only one in this layer
								pass
							return
						childIndex += 1
					targetItem = targetItem.parent()
				childIndex = 0
				currChild = self.topLevelItem(childIndex)
				while currChild:
					if currChild is draggedItem:
						self.reparent(draggedItem.entryData["key"], self.rootNode)
						if childIndex == 0 and self.topLevelItemCount() > 1:  # is now 1st item
							self.updateSortIndex(draggedItem.entryData["key"],
							                     self.topLevelItem(1).entryData["sortindex"] - 1)
						elif childIndex == (self.topLevelItemCount() - 1) and childIndex > 0:  # is now lastitem
							self.updateSortIndex(draggedItem.entryData["key"],
							                     self.topLevelItem(childIndex - 1).entryData["sortindex"] + 1)
						elif childIndex > 0 and childIndex < (self.topLevelItemCount() - 1):  # in between
							newSortIndex = (self.topLevelItem(childIndex - 1).entryData["sortindex"] +
							                self.topLevelItem(childIndex + 1).entryData["sortindex"]) / 2.0
							self.updateSortIndex(draggedItem.entryData["key"], newSortIndex)
						else:  # We are the only one in this layer
							pass
						return
					childIndex += 1
					currChild = self.topLevelItem(childIndex)

	def reparent(self, itemKey, destParent):
		protoWrap = protocolWrapperInstanceSelector.select(self.modul)
		assert protoWrap is not None
		protoWrap.reparent(itemKey, destParent)
		self.overlay.inform(self.overlay.BUSY)

	def updateSortIndex(self, itemKey, newIndex):
		protoWrap = protocolWrapperInstanceSelector.select(self.modul)
		assert protoWrap is not None
		protoWrap.updateSortIndex(itemKey, newIndex)
		self.overlay.inform(self.overlay.BUSY)

	def requestDelete(self, id):
		"""
			Delete the entity with the given id
		"""
		if QtWidgets.QMessageBox.question(
				self,
				QtCore.QCoreApplication.translate("HierarchyTreeWidget", "Confirm delete"),
						QtCore.QCoreApplication.translate(
								"HierarchyTreeWidget",
								"Delete %s entries and everything below?") % 1,
						QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
				QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.No:
			return
		protoWrap = protocolWrapperInstanceSelector.select(self.modul)
		assert protoWrap is not None
		protoWrap.delete(id)
		self.overlay.inform(self.overlay.BUSY)


class HierarchyWidget(QtWidgets.QWidget):
	itemClicked = QtCore.pyqtSignal((QtWidgets.QTreeWidgetItem, int))
	itemDoubleClicked = QtCore.pyqtSignal((QtWidgets.QTreeWidgetItem, int))

	def __init__(self, modul, repoID=None, actions=None, editOnDoubleClick=True, *args, **kwargs):
		super(HierarchyWidget, self).__init__(*args, **kwargs)
		self.ui = Ui_Hierarchy()
		self.ui.setupUi(self)
		layout = QtWidgets.QHBoxLayout(self.ui.treeWidget)
		self.ui.treeWidget.setLayout(layout)
		self.hierarchy = HierarchyTreeWidget(self, modul, rootNode=repoID)
		layout.addWidget(self.hierarchy)
		# self.ui.treeWidget.addChild( self.hierarchy )
		self.hierarchy.show()
		self.toolBar = QtWidgets.QToolBar(self)
		self.toolBar.setIconSize(QtCore.QSize(32, 32))
		self.ui.boxActions.addWidget(self.toolBar)
		self.modul = modul
		self.page = 0
		self.rootNodes = {}
		config = conf.serverConfig["modules"][modul]
		self.rootNode = None
		self.isSorting = False
		self.path = []
		self.request = None
		self.overlay = Overlay(self)
		self.setAcceptDrops(True)
		self.ui.webView.hide()
		self._currentActions = None
		self.setActions(actions if actions is not None else ["add", "edit", "clone", "preview", "delete"])
		self.hierarchy.itemClicked.connect(self.onItemClicked)
		self.hierarchy.itemClicked.connect(self.itemClicked)
		self.hierarchy.itemDoubleClicked.connect(self.itemDoubleClicked)
		if editOnDoubleClick:
			self.hierarchy.itemDoubleClicked.connect(self.onItemDoubleClicked)

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
			actionWdg = actionDelegateSelector.select("hierarchy.%s" % self.modul, action)
			if actionWdg is not None:
				actionWdg = actionWdg(self)
				if isinstance(actionWdg, QtWidgets.QAction):
					self.toolBar.addAction(actionWdg)
					self.addAction(actionWdg)
				else:
					self.toolBar.addWidget(actionWdg)

	def getActions(self):
		"""
			Returns a list of the currently activated actions on this widget.
		"""
		return self._currentActions

	def onItemClicked(self, item, col):
		""" An item has been selected. If we have a previewURL -> show it

		:param item: the item which was clicked
		:type item: HierarchyItem
		:param col: the column index
		:type col: int
		"""

		config = conf.serverConfig["modules"][self.modul]
		if "previewURL" in config.keys() and config["previewURL"]:
			previewURL = config["previewURL"].replace("{{key}}", item.entryData["key"])
			if not previewURL.lower().startswith("http"):
				previewURL = NetworkService.url.replace("/admin", "") + previewURL
			self.loadPreview(previewURL)

	def onItemDoubleClicked(self, item, col):
		""" Open a editor for this entry.

		:param item: the item which was clicked
		:type item: HierarchyItem
		:param col: the column index
		:type col: int
		"""

		handler = utils.WidgetHandler(
				lambda: EditWidget(self.modul, EditWidget.appHierarchy, item.entryData["key"]),
				descr=QtCore.QCoreApplication.translate("Hierarchy", "Edit entry"),
				icon=QtGui.QIcon(":icons/actions/edit.svg"))
		handler.stackHandler()

	def loadPreview(self, url):
		""" Tries to fetch the entry specified by url and shows it on success

		Take a look in self.setHTML for the view part

		:param url: the url of the item to preview in our webview
		:type url: str
		"""
		NetworkService.request(url, successHandler=self.setHTML)

	def setHTML(self, req=None):
		try:  # This request might got canceled meanwhile..
			html = bytes(req.readAll())
		except:
			return
		self.ui.webView.setHtml(html.decode("UTF-8"), QtCore.QUrl(NetworkService.url.replace("/admin", "")))
		self.ui.webView.show()

	def getModul(self):
		return self.modul

	def getRootNode(self):
		return self.hierarchy.getRootNode()
