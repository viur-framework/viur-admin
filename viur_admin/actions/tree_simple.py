# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.log import getLogger
from viur_admin.mainwindow import WidgetHandler
from viur_admin.priorityqueue import protocolWrapperInstanceSelector, actionDelegateSelector
from viur_admin.widgets.edit import EditWidget

logger = getLogger(__name__)


class TreeSimpleEditAction(QtWidgets.QAction):
	"""
		Overriden edit-action which prevents editing Nodes
	"""

	def __init__(self, parent: QtWidgets.QWidget = None):
		super(TreeSimpleEditAction, self).__init__(
			QtGui.QIcon(":icons/actions/edit.svg"),
			QtCore.QCoreApplication.translate("TreeHandler", "Edit entry"),
			parent)
		self.parent().itemSelectionChanged.connect(self.onItemSelectionChanged)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.Open)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
		self.setEnabled(False)

	def onItemSelectionChanged(self) -> None:
		entries = self.parent().selectedItems()
		if len(entries) != 1:
			self.setEnabled(False)
			return
		if not isinstance(entries[0], self.parent().getLeafItemClass()):
			self.setEnabled(False)
			return
		self.setEnabled(True)

	def onTriggered(self) -> None:
		name = QtCore.QCoreApplication.translate("TreeHandler", "Edit entry")
		entries = []
		for item in self.parent().selectedItems():
			if isinstance(item, self.parent().getLeafItemClass()):
				entries.append(item.entryData)
		for entry in entries:
			if isinstance(item, self.parent().getLeafItemClass()):
				skelType = "leaf"
			else:
				skelType = "node"
			module = self.parent().module
			key = entry["key"]
			widget = lambda: EditWidget(module, EditWidget.appTree, key, skelType=skelType)
			handler = WidgetHandler(widget, descr=name, icon=QtGui.QIcon(":icons/actions/edit.svg"))
			handler.stackHandler()

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "tree.simple" or module.startswith("tree.simple.")) and actionName == "edit"


actionDelegateSelector.insert(3, TreeSimpleEditAction.isSuitableFor, TreeSimpleEditAction)


class TreeMkDirAction(QtWidgets.QAction):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(TreeMkDirAction, self).__init__(
			QtGui.QIcon(":icons/actions/folder_add.svg"),
			QtCore.QCoreApplication.translate("TreeHandler", "New directory"),
			parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut("SHIFT+Ctrl+N")
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self) -> None:
		(dirName, okay) = QtWidgets.QInputDialog.getText(
			self.parent(),
			QtCore.QCoreApplication.translate(
				"TreeHandler",
				"Create "
				"directory"),
			QtCore.QCoreApplication.translate(
				"TreeHandler",
				"Directory name"))
		if dirName and okay:
			logger.debug("TreeMkDirAction.onTriggered: %r, %r", self.parent(), self.parent().realModule)
			reqWrap = protocolWrapperInstanceSelector.select(self.parent().realModule)
			assert reqWrap is not None
			reqWrap.add(self.parent().getNode(), "node", name=dirName)

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "tree.simple" or module.startswith("tree.simple.")) and actionName == "mkdir"


actionDelegateSelector.insert(1, TreeMkDirAction.isSuitableFor, TreeMkDirAction)


class TreeSimpleRenameAction(QtWidgets.QAction):
	"""
		Allow renaming directories
	"""

	def __init__(self, parent: QtWidgets.QWidget = None):
		super(TreeSimpleRenameAction, self).__init__(
			QtGui.QIcon(":icons/actions/rename.svg"),
			QtCore.QCoreApplication.translate("TreeHandler", "Rename entry"),
			parent)
		self.parent().itemSelectionChanged.connect(self.onItemSelectionChanged)
		self.triggered.connect(self.onTriggered)
		self.setShortcut("F2")
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
		self.setEnabled(False)

	def onItemSelectionChanged(self) -> None:
		entries = self.parent().selectedItems()
		if len(entries) != 1:
			self.setEnabled(False)
			return
		if not isinstance(entries[0], self.parent().getNodeItemClass()):
			self.setEnabled(False)
			return
		self.setEnabled(True)

	def onTriggered(self) -> None:
		name = QtCore.QCoreApplication.translate("TreeSimpleRenameAction", "Edit entry")
		entries = self.parent().selectedItems()
		if len(entries) != 1:
			return
		entry = entries[0]
		if not isinstance(entry, self.parent().getNodeItemClass()):  # Cant rename an leaf
			return
		name, res = QtWidgets.QInputDialog.getText(
			self.parent(),
			QtCore.QCoreApplication.translate(
				"TreeSimpleRenameAction",
				"Rename directory"),
			QtCore.QCoreApplication.translate(
				"TreeSimpleRenameAction",
				"New name:"),
			text=entry.entryData["name"]
		)
		if not res:
			return  # Cancel was clicked
		protpWrap = protocolWrapperInstanceSelector.select(self.parent().module)
		assert protpWrap is not None
		data = entry.entryData.copy()
		data["name"] = name
		key = data["key"]
		del data["key"]
		protpWrap.edit(key, "node", **data)

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "tree.simple" or module.startswith("tree.simple.")) and actionName == "rename"


actionDelegateSelector.insert(3, TreeSimpleRenameAction.isSuitableFor, TreeSimpleRenameAction)
