# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.priorityqueue import actionDelegateSelector
from viur_admin.utils import WidgetHandler, loadIcon
from viur_admin.widgets.edit import EditWidget, ApplicationType


class HierarchyAddAction(QtWidgets.QAction):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(HierarchyAddAction, self).__init__(
			loadIcon("add"),
			QtCore.QCoreApplication.translate("Hierarchy", "Add entry"),
			parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.New)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self) -> None:
		# config = conf.serverConfig["modules"][ self.parent().module ]
		modul = self.parent().getModul()
		node = self.parent().hierarchy.rootNode

		def widgetFactory() -> EditWidget:
			return EditWidget(modul, ApplicationType.HIERARCHY, node=node)

		handler = WidgetHandler(
			widgetFactory, descr=QtCore.QCoreApplication.translate("Hierarchy", "Add entry"),
			icon=loadIcon("add"))
		handler.stackHandler()

	# event.emit( QtCore.SIGNAL('stackHandler(PyQt_PyObject)'), handler )

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "tree.nodeonly" or module.startswith("tree.nodeonly.")) and actionName == "add"


actionDelegateSelector.insert(2, HierarchyAddAction.isSuitableFor, HierarchyAddAction)


class HierarchyCloneAction(QtWidgets.QAction):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(HierarchyCloneAction, self).__init__(
			loadIcon("clone"),
			QtCore.QCoreApplication.translate("HierarchyHandler", "Clone entry"),
			parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.SaveAs)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self, result: bool) -> None:
		parent = self.parent()
		modul = self.parent().getModul()
		for item in parent.hierarchy.selectedItems():
			key = item.entryData["key"]

			def widgetFactory() -> EditWidget:
				node = parent.getRootNode()
				print("clone factory", modul, key, node)
				return EditWidget(modul, ApplicationType.HIERARCHY, key, node=node, clone=True)

			handler = WidgetHandler(
				widgetFactory, descr=QtCore.QCoreApplication.translate("Hierarchy", "Clone entry"),
				icon=loadIcon("clone"))
			handler.stackHandler()

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return module == "tree.nodeonly" or module.startswith("tree.nodeonly.") and actionName == "clone"


actionDelegateSelector.insert(2, HierarchyCloneAction.isSuitableFor, HierarchyCloneAction)


class HierarchyEditAction(QtWidgets.QAction):
	def __init__(self, parent: QtCore.QObject = None):
		super(HierarchyEditAction, self).__init__(
			loadIcon("edit"),
			QtCore.QCoreApplication.translate("Hierarchy", "Edit entry"),
			parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.Open)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self) -> None:
		parent = self.parent()
		for item in parent.hierarchy.selectedItems():
			modul = self.parent().getModul()
			key = item.entryData["key"]
			widget = lambda: EditWidget(modul, ApplicationType.HIERARCHY, key)
			handler = WidgetHandler(
				widget, descr=QtCore.QCoreApplication.translate("Hierarchy", "Edit entry"),
				icon=loadIcon("edit"))
			handler.stackHandler()

	# event.emit( QtCore.SIGNAL('stackHandler(PyQt_PyObject)'), handler )

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "tree.nodeonly" or module.startswith("tree.nodeonly.")) and actionName == "edit"


actionDelegateSelector.insert(2, HierarchyEditAction.isSuitableFor, HierarchyEditAction)


class HierarchyDeleteAction(QtWidgets.QAction):
	def __init__(self, parent: QtCore.QObject = None):
		super(HierarchyDeleteAction, self).__init__(
			loadIcon("delete"),
			QtCore.QCoreApplication.translate("Hierarchy", "Delete entry"),
			parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.Delete)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self) -> None:
		parent = self.parent()
		for item in parent.hierarchy.selectedItems():
			self.parent().hierarchy.requestDelete(item.entryData["key"])

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "tree.nodeonly" or module.startswith("tree.nodeonly.")) and actionName == "delete"


actionDelegateSelector.insert(2, HierarchyDeleteAction.isSuitableFor, HierarchyDeleteAction)
