# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.priorityqueue import actionDelegateSelector
from viur_admin.utils import WidgetHandler
from viur_admin.widgets.edit import EditWidget


class HierarchyAddAction(QtWidgets.QAction):
	def __init__(self, parent, *args, **kwargs):
		super(HierarchyAddAction, self).__init__(
				QtGui.QIcon(":icons/actions/add.svg"),
				QtCore.QCoreApplication.translate("Hierarchy", "Add entry"), parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.New)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self):
		# config = conf.serverConfig["modules"][ self.parent().module ]
		modul = self.parent().getModul()
		node = self.parent().hierarchy.rootNode

		def widgetFactory():
			return EditWidget(modul, EditWidget.appHierarchy, node=node)

		handler = WidgetHandler(
				widgetFactory, descr=QtCore.QCoreApplication.translate("Hierarchy", "Add entry"),
				icon=QtGui.QIcon(":icons/actions/add.svg"))
		handler.stackHandler()
		# event.emit( QtCore.SIGNAL('stackHandler(PyQt_PyObject)'), handler )

	@staticmethod
	def isSuitableFor(modul, actionName):
		return (modul == "hierarchy" or modul.startswith("hierarchy.")) and actionName == "add"


actionDelegateSelector.insert(1, HierarchyAddAction.isSuitableFor, HierarchyAddAction)


class HierarchyCloneAction(QtWidgets.QAction):
	def __init__(self, parent, *args, **kwargs):
		super(HierarchyCloneAction, self).__init__(
				QtGui.QIcon(":icons/actions/clone.svg"),
				QtCore.QCoreApplication.translate("HierarchyHandler", "Clone entry"),
				parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.SaveAs)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self, e):
		parent = self.parent()
		modul = self.parent().getModul()
		for item in parent.hierarchy.selectedItems():
			key = item.entryData["key"]

			def widgetFactory():
				node = parent.getRootNode()
				print("clone factory", modul, key, node)
				return EditWidget(modul, EditWidget.appHierarchy, key, node=node, clone=True)

			handler = WidgetHandler(
					widgetFactory, descr=QtCore.QCoreApplication.translate("Hierarchy", "Clone entry"),
					icon=QtGui.QIcon(":icons/actions/clone.svg"))
			handler.stackHandler()

	@staticmethod
	def isSuitableFor(modul, actionName):
		return modul == "hierarchy" or modul.startswith("hierarchy.") and actionName == "clone"


actionDelegateSelector.insert(1, HierarchyCloneAction.isSuitableFor, HierarchyCloneAction)


class HierarchyEditAction(QtWidgets.QAction):
	def __init__(self, parent, *args, **kwargs):
		super(HierarchyEditAction, self).__init__(
				QtGui.QIcon(":icons/actions/edit.svg"),
				QtCore.QCoreApplication.translate("Hierarchy", "Edit entry"), parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.Open)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self):
		parent = self.parent()
		for item in parent.hierarchy.selectedItems():
			modul = self.parent().getModul()
			key = item.entryData["key"]
			widget = lambda: EditWidget(modul, EditWidget.appHierarchy, key)
			handler = WidgetHandler(
					widget, descr=QtCore.QCoreApplication.translate("Hierarchy", "Edit entry"),
					icon=QtGui.QIcon(":icons/actions/edit.svg"))
			handler.stackHandler()
		# event.emit( QtCore.SIGNAL('stackHandler(PyQt_PyObject)'), handler )

	@staticmethod
	def isSuitableFor(modul, actionName):
		return (modul == "hierarchy" or modul.startswith("hierarchy.")) and actionName == "edit"


actionDelegateSelector.insert(1, HierarchyEditAction.isSuitableFor, HierarchyEditAction)


class HierarchyDeleteAction(QtWidgets.QAction):
	def __init__(self, parent, *args, **kwargs):
		super(HierarchyDeleteAction, self).__init__(QtGui.QIcon(":icons/actions/delete.svg"),
		                                            QtCore.QCoreApplication.translate("Hierarchy", "Delete entry"),
		                                            parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.Delete)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self):
		parent = self.parent()
		for item in parent.hierarchy.selectedItems():
			self.parent().hierarchy.requestDelete(item.entryData["key"])

	@staticmethod
	def isSuitableFor(modul, actionName):
		return (modul == "hierarchy" or modul.startswith("hierarchy.")) and actionName == "delete"


actionDelegateSelector.insert(1, HierarchyDeleteAction.isSuitableFor, HierarchyDeleteAction)
