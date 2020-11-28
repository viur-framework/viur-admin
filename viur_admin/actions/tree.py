# -*- coding: utf-8 -*-

import time
from typing import List

from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.event import event
from viur_admin.priorityqueue import protocolWrapperInstanceSelector, actionDelegateSelector
from viur_admin.utils import WidgetHandler
from viur_admin.widgets.edit import EditWidget, ApplicationType


class TreeAddAction(QtWidgets.QAction):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(TreeAddAction, self).__init__(
			QtGui.QIcon(":icons/actions/add.svg"),
			QtCore.QCoreApplication.translate("TreeHandler", "Add entry"), parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.New)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self) -> None:
		name = QtCore.QCoreApplication.translate("TreeHandler", "Add entry")
		modul = self.parent().tree.modul
		node = self.parent().getNode()
		widget = lambda: EditWidget(modul, ApplicationType.TREE, node=node)
		handler = WidgetHandler(widget, descr=name, icon=QtGui.QIcon(":icons/actions/add.svg"))
		event.emit(QtCore.pyqtSignal('stackHandler(PyQt_PyObject)'), handler)

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "tree" or module.startswith("tree.")) and actionName == "add"


actionDelegateSelector.insert(1, TreeAddAction.isSuitableFor, TreeAddAction)


class TreeEditAction(QtWidgets.QAction):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(TreeEditAction, self).__init__(
			QtGui.QIcon(":icons/actions/edit.svg"),
			QtCore.QCoreApplication.translate("TreeHandler", "Edit entry"), parent)
		self.setShortcut(QtGui.QKeySequence.Open)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
		self.triggered.connect(self.onTriggered)

	def onTriggered(self) -> None:
		name = QtCore.QCoreApplication.translate("TreeHandler", "Edit entry")
		entries = []
		for item in self.parent().selectedItems():
			if isinstance(item, self.parent().getLeafItemClass()):
				entries.append(item.entryData)

		for entry in entries:
			if isinstance(entry, self.parent().getLeafItemClass()):
				skelType = "leaf"
			else:
				skelType = "node"
			modul = self.parent().modul
			key = entry["key"]
			widget = lambda: EditWidget(modul, EditWidget.appTree, key, skelType=skelType)
			handler = WidgetHandler(widget, descr=name, icon=QtGui.QIcon(":icons/actions/edit.svg"))
			handler.stackHandler()

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "tree" or module.startswith("tree.")) and actionName == "edit"


actionDelegateSelector.insert(1, TreeEditAction.isSuitableFor, TreeEditAction)


class TreeDirUpAction(QtWidgets.QAction):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(TreeDirUpAction, self).__init__(
			QtGui.QIcon(":icons/actions/folder_back.svg"),
			QtCore.QCoreApplication.translate("TreeHandler", "Directory up"),
			parent)
		self.parent().nodeChanged.connect(self.onNodeChanged)
		self.realModule = self.parent().realModule
		reqWrap = protocolWrapperInstanceSelector.select(self.realModule)
		assert reqWrap is not None
		x = 3
		while x:
			if reqWrap.rootNodes is None:
				# print("rootNones is still None - waiting...", reqWrap)
				time.sleep(0.2)
				x -= 1
			else:
				break
		if reqWrap.rootNodes and self.parent().getNode() in [x["key"] for x in reqWrap.rootNodes]:
			self.setEnabled(False)
		self.triggered.connect(self.onTriggered)

	def onNodeChanged(self, node: str) -> None:
		reqWrap = protocolWrapperInstanceSelector.select(self.realModule)
		assert reqWrap is not None
		node = reqWrap.getNode(self.parent().getNode())
		if not node["parententry"]:
			self.setEnabled(False)
		else:
			self.setEnabled(True)

	def onTriggered(self) -> None:
		reqWrap = protocolWrapperInstanceSelector.select(self.realModule)
		assert reqWrap is not None
		node = reqWrap.getNode(self.parent().getNode())
		if node:
			if node["parententry"]:
				self.parent().setNode(node["parententry"], isInitialCall=True)

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "tree" or module.startswith("tree.")) and actionName == "dirup"


actionDelegateSelector.insert(1, TreeDirUpAction.isSuitableFor, TreeDirUpAction)


class TreeDeleteAction(QtWidgets.QAction):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(TreeDeleteAction, self).__init__(
			QtGui.QIcon(":icons/actions/delete.svg"),
			QtCore.QCoreApplication.translate("TreeHandler", "Delete"),
			parent)
		self.parent().itemSelectionChanged.connect(self.onItemSelectionChanged)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.Delete)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
		self.setEnabled(False)

	def onItemSelectionChanged(self) -> None:
		entries = self.parent().selectedItems()
		if len(entries) == 0:
			self.setEnabled(False)
			return
		self.setEnabled(True)

	def onTriggered(self) -> None:
		nodes: List[dict] = []
		leafs: List[dict] = []
		for item in self.parent().selectedItems():
			if isinstance(item, self.parent().getNodeItemClass()):
				nodes.append(item.entryData["key"])
			else:
				leafs.append(item.entryData["key"])
		self.parent().requestDelete(nodes, leafs)

	# self.parent().delete( self.parent().rootNode, self.parent().getPath(), [ x["name"] for x in files], dirs )

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "tree" or module.startswith("tree.")) and actionName == "delete"


actionDelegateSelector.insert(1, TreeDeleteAction.isSuitableFor, TreeDeleteAction)


class TreeSwitchViewAction(QtWidgets.QAction):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(TreeSwitchViewAction, self).__init__(
			QtGui.QIcon(":icons/actions/switch_list.png"),
			QtCore.QCoreApplication.translate("TreeHandler", "Switch View"),
			parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut("F8")
		if not self.parent().isIconMode():
			self.setIcon(QtGui.QIcon(":icons/actions/switch_icon.svg"))
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self) -> None:
		self.parent().setIconMode(not self.parent().isIconMode())
		if not self.parent().isIconMode():
			self.setIcon(QtGui.QIcon(":icons/actions/switch_icon.png"))
		else:
			self.setIcon(QtGui.QIcon(":icons/actions/switch_list.png"))

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "tree" or module.startswith("tree.")) and actionName == "switchview"


actionDelegateSelector.insert(1, TreeSwitchViewAction.isSuitableFor, TreeSwitchViewAction)
