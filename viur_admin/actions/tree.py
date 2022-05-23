# -*- coding: utf-8 -*-

import time
from typing import List

from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.event import event
from viur_admin.priorityqueue import protocolWrapperInstanceSelector, actionDelegateSelector
from viur_admin.utils import WidgetHandler, loadIcon
from viur_admin.widgets.edit import EditWidget, ApplicationType


class TreeAddAction(QtWidgets.QAction):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(TreeAddAction, self).__init__(
			loadIcon("add-folder"),
			QtCore.QCoreApplication.translate("TreeHandler", "Add entry"), parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.New)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self) -> None:
		name = QtCore.QCoreApplication.translate("TreeHandler", "Add entry")
		modul = self.parent().tree.module
		node = self.parent().getNode()
		widget = lambda: EditWidget(modul, ApplicationType.TREE, node=node, skelType="node")
		handler = WidgetHandler(widget, descr=name, icon=loadIcon("add-folder"))
		#event.emit(QtCore.pyqtSignal('stackHandler(PyQt_PyObject)'), handler)
		handler.stackHandler()

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "tree" or module.startswith("tree.")) and actionName == "add"


actionDelegateSelector.insert(1, TreeAddAction.isSuitableFor, TreeAddAction)


class TreeAddLeafAction(QtWidgets.QAction):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(TreeAddLeafAction, self).__init__(
			loadIcon("add"),
			QtCore.QCoreApplication.translate("TreeHandler", "Add leaf entry"), parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.New)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self) -> None:
		name = QtCore.QCoreApplication.translate("TreeHandler", "Add leaf entry")
		modul = self.parent().tree.module
		node = self.parent().getNode()
		widget = lambda: EditWidget(modul, ApplicationType.TREE, node=node, skelType="leaf")
		handler = WidgetHandler(widget, descr=name, icon=loadIcon("add"))
		#event.emit(QtCore.pyqtSignal('stackHandler(PyQt_PyObject)'), handler)
		handler.stackHandler()

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "tree" or module.startswith("tree.")) and not module.startswith("tree.nodeonly") and actionName == "addleaf"


actionDelegateSelector.insert(1, TreeAddLeafAction.isSuitableFor, TreeAddLeafAction)

class TreeEditAction(QtWidgets.QAction):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(TreeEditAction, self).__init__(
			loadIcon("edit"),
			QtCore.QCoreApplication.translate("TreeHandler", "Edit entry"), parent)
		self.setShortcut(QtGui.QKeySequence.Open)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
		self.triggered.connect(self.onTriggered)

	def onTriggered(self) -> None:
		name = QtCore.QCoreApplication.translate("TreeHandler", "Edit entry")
		nodes = []
		leafs = []
		for item in self.parent().selectedItems():
			if item["_type"] == "leaf":
				leafs.append(item)
			else:
				nodes.append(item)
		for entry in leafs:
			skelType = "leaf"
			modul = self.parent().module
			key = entry["key"]
			widget = lambda: EditWidget(modul, ApplicationType.TREE, key, skelType=skelType)
			handler = WidgetHandler(widget, descr=name, icon=loadIcon("edit"))
			handler.stackHandler()
		for entry in nodes:
			skelType = "node"
			modul = self.parent().module
			key = entry["key"]
			widget = lambda: EditWidget(modul, ApplicationType.TREE, key, skelType=skelType)
			handler = WidgetHandler(widget, descr=name, icon=loadIcon("edit"))
			handler.stackHandler()


	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "tree" or module.startswith("tree.")) and actionName == "edit"


actionDelegateSelector.insert(1, TreeEditAction.isSuitableFor, TreeEditAction)


class TreeDeleteAction(QtWidgets.QAction):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(TreeDeleteAction, self).__init__(
			loadIcon("delete"),
			QtCore.QCoreApplication.translate("TreeHandler", "Delete"),
			parent)
		self.parent().itemSelectionChanged.connect(self.onItemSelectionChanged)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.Delete)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
		self.setEnabled(False)

	def onItemSelectionChanged(self, selected, deselected) -> None:
		if len(selected) == 0:
			self.setEnabled(False)
			return
		self.setEnabled(True)

	def onTriggered(self) -> None:
		nodes: List[dict] = []
		leafs: List[dict] = []
		for item in self.parent().selectedItems():
			if item["_type"] == "node":
				nodes.append(item["key"])
			else:
				leafs.append(item["key"])
		self.parent().requestDelete(nodes, leafs)

	# self.parent().delete( self.parent().rootNode, self.parent().getPath(), [ x["name"] for x in files], dirs )

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "tree" or module.startswith("tree.")) and actionName == "delete"


actionDelegateSelector.insert(1, TreeDeleteAction.isSuitableFor, TreeDeleteAction)


class SelectTreeRowsAction(QtWidgets.QAction):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(SelectTreeRowsAction, self).__init__(
			loadIcon("menu"),
			QtCore.QCoreApplication.translate("ListHandler", "Select table headers"),
			parent)
		self.triggered.connect(self.onTriggered)
		self.module = self.parentWidget().tree.module


	def onTriggered(self) -> None:
		class FieldAction(QtWidgets.QAction):
			def __init__(
					self,
					key: str,
					name: str,
					parent: QtWidgets.QWidget = None):
				super(FieldAction, self).__init__(parent=parent)
				self.key = key
				self.name = name
				self.setText(self.name)

		menu = QtWidgets.QMenu(self.parentWidget())
		activeFields = self.parentWidget().tree.model().fields
		actions: List[FieldAction] = []
		if not self.parentWidget().tree.structureCache:
			return
		structure = self.parentWidget().tree.structureCache
		for key in structure:
			descr = "%s / %s" % (structure[key][0]["descr"], structure[key][1]["descr"]) if \
				isinstance(structure[key], list) else structure[key]["descr"]
			action = FieldAction(
				key,
				descr,
				parent=self.parentWidget())
			action.setCheckable(True)
			action.setChecked(key in activeFields)
			menu.addAction(action)
			actions.append(action)
		selection = menu.exec_(self.parentWidget().mapToGlobal(QtCore.QPoint(50,50)))
		if selection:
			self.parentWidget().tree.model().setDisplayedFields([x.key for x in actions if x.isChecked()])


	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "tree" or module.startswith("tree.")) and actionName == "selecttablerows"


actionDelegateSelector.insert(1, SelectTreeRowsAction.isSuitableFor, SelectTreeRowsAction)