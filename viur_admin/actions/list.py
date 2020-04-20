# -*- coding: utf-8 -*-
from typing import List

from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.config import conf
from viur_admin.network import NetworkService
from viur_admin.priorityqueue import protocolWrapperInstanceSelector, actionDelegateSelector
from viur_admin.utils import WidgetHandler
from viur_admin.widgets.edit import EditWidget, ApplicationType
from viur_admin.widgets.list import CsvExportWidget


class ListAddAction(QtWidgets.QAction):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(ListAddAction, self).__init__(
			QtGui.QIcon(":icons/actions/add.svg"),
			QtCore.QCoreApplication.translate("ListHandler", "Add entry"),
			parent)

		# self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.New)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self) -> None:
		if self.parentWidget().list.module in conf.serverConfig["modules"] and "name" in \
				conf.serverConfig["modules"][self.parentWidget().list.module]:
			name = conf.serverConfig["modules"][self.parentWidget().list.module]["name"]
		else:
			name = self.parentWidget().list.modul
		descr = QtCore.QCoreApplication.translate("ListHandler", "Add entry: %s") % name
		modul = self.parentWidget().list.module
		handler = WidgetHandler(
			lambda: EditWidget(modul, ApplicationType.LIST),
			descr,
			QtGui.QIcon(":icons/actions/add.svg"))
		handler.stackHandler()

	# event.emit( QtCore.SIGNAL('stackHandler(PyQt_PyObject)'), handler )

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "list" or module.startswith("list.")) and actionName == "add"


actionDelegateSelector.insert(1, ListAddAction.isSuitableFor, ListAddAction)


class ListReloadAction(QtWidgets.QAction):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(ListReloadAction, self).__init__(QtGui.QIcon(":icons/actions/refresh.svg"),
		                                       QtCore.QCoreApplication.translate("ListHandler", "Reload"), parent)

		# self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.New)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self) -> None:
		self.parentWidget().list.model().reload()

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "list" or module.startswith("list.")) and actionName == "reload"


actionDelegateSelector.insert(1, ListReloadAction.isSuitableFor, ListReloadAction)


class ListEditAction(QtWidgets.QAction):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(ListEditAction, self).__init__(QtGui.QIcon(":icons/actions/edit.svg"),
		                                     QtCore.QCoreApplication.translate("ListHandler", "Edit entry"), parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.Open)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self) -> None:
		numAccounts = len(set([x.row() for x in self.parentWidget().list.selectionModel().selection().indexes()]))
		if numAccounts == 0:
			return
		if numAccounts > 1:
			reply = QtWidgets.QMessageBox.question(
				self.parent(),
				QtCore.QCoreApplication.translate(
					"ListHandler",
					"Edit multiple Entries"),
				QtCore.QCoreApplication.translate(
					"ListHandler",
					"Edit all %s accounts?") % numAccounts,
				QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
				QtWidgets.QMessageBox.No)
			if reply != QtWidgets.QMessageBox.Yes:
				return
		for data in self.parent().getSelection():
			self.parentWidget().openEditor(data, clone=False)

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "list" or module.startswith("list.")) and actionName == "edit"


actionDelegateSelector.insert(1, ListEditAction.isSuitableFor, ListEditAction)


class ListCloneAction(QtWidgets.QAction):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(ListCloneAction, self).__init__(
			QtGui.QIcon(":icons/actions/clone.svg"),
			QtCore.QCoreApplication.translate("ListHandler", "Clone entry"),
			parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.SaveAs)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self) -> None:
		if len(self.parentWidget().list.selectionModel().selection().indexes()) == 0:
			return
		data = self.parentWidget().list.model().getData()[
			self.parentWidget().list.selectionModel().selection().indexes()[0].row()]
		self.parentWidget().openEditor(data, clone=True)

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "list" or module.startswith("list.")) and actionName == "clone"


actionDelegateSelector.insert(1, ListCloneAction.isSuitableFor, ListCloneAction)


class ListDeleteAction(QtWidgets.QAction):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(ListDeleteAction, self).__init__(
			QtGui.QIcon(":icons/actions/delete.svg"),
			QtCore.QCoreApplication.translate("ListHandler", "Delete"),
			parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.Delete)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	# self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )

	def onTriggered(self) -> None:
		indexes = self.parentWidget().list.selectedIndexes()
		rows: List[dict] = list()
		for index in indexes:
			row = index.row()
			if row not in rows:
				rows.append(row)
		deleteData = [self.parentWidget().list.model().getData()[row] for row in rows]
		reqWrap = protocolWrapperInstanceSelector.select(self.parent().list.module)
		self.parent().requestDelete([x["key"] for x in deleteData])

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "list" or module.startswith("list.")) and actionName == "delete"


actionDelegateSelector.insert(1, ListDeleteAction.isSuitableFor, ListDeleteAction)


class Preview(QtWidgets.QDialog):
	def __init__(self, urls: dict, module: str, data: dict, parent: QtWidgets.QWidget = None):
		super(Preview, self).__init__(parent=parent)
		self.setObjectName("BasePreview")
		# self.resize(300, 482)
		self.setWindowTitle("")
		icon = QtGui.QIcon()
		icon.addPixmap(QtGui.QPixmap(":icons/ViURadmin.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.setWindowIcon(icon)
		self.verticalLayout = QtWidgets.QVBoxLayout(self)
		self.cbUrls = QtWidgets.QComboBox(self)
		self.cbUrls.setObjectName("cbUrls")
		self.verticalLayout.addWidget(self.cbUrls)
		self.urls = [(k, v) for (k, v) in urls.items()]
		self.urls.sort(key=lambda x: x[0])
		self.module = module
		self.data = data
		self.request = None
		self.cbUrls.addItems([x[0] for x in self.urls])
		if "actiondescr" in data:
			self.setWindowTitle("%s: %s" % (data["actiondescr"], data["name"]))
		elif "name" in data:
			self.setWindowTitle(QtCore.QCoreApplication.translate("ListHandler", "Preview: %s") % data["name"])
		else:
			self.setWindowTitle(QtCore.QCoreApplication.translate("ListHandler", "Preview"))
		self.cbUrls.currentIndexChanged.connect(self.onCbUrlsCurrentIndexChanged)
		# self.ui.btnReload.released.connect(self.onBtnReloadReleased)
		if len(self.urls) > 0:
			self.onCbUrlsCurrentIndexChanged(0)
		self.show()

	def onCbUrlsCurrentIndexChanged(self, idx: int) -> None:
		if not isinstance(idx, int):
			return
		baseurl = NetworkService.url.replace("/admin", "")
		url = self.urls[idx][1]
		url = url.replace("{{key}}", self.data["key"]).replace("{{module}}", self.module)
		QtGui.QDesktopServices.openUrl(QtCore.QUrl(baseurl + url))


class ListPreviewAction(QtWidgets.QAction):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(ListPreviewAction, self).__init__(
			QtGui.QIcon(":icons/actions/preview.svg"),
			QtCore.QCoreApplication.translate("ListHandler", "Preview"),
			parent)
		self.module = self.parentWidget().list.module
		self.widget = None
		if self.module in conf.serverConfig["modules"]:
			modulConfig = conf.serverConfig["modules"][self.module]
			if "previewurls" in modulConfig and modulConfig["previewurls"]:
				self.setEnabled(True)
				self.previewURLs = modulConfig["previewurls"]
			else:
				self.setEnabled(False)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.Print)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self) -> None:
		indexes = self.parentWidget().list.selectionModel().selection().indexes()
		rows: List[dict] = list()
		for index in indexes:
			row = index.row()
			if row not in rows:
				rows.append(row)
		if len(rows) > 0:
			data = self.parentWidget().list.model().getData()[rows[0]]
			self.widget = Preview(self.previewURLs, self.module, data)

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "list" or module.startswith("list.")) and actionName == "preview"


actionDelegateSelector.insert(1, ListPreviewAction.isSuitableFor, ListPreviewAction)


class CsvExportAction(QtWidgets.QAction):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(CsvExportAction, self).__init__(
			QtGui.QIcon(":icons/actions/download.svg"),
			QtCore.QCoreApplication.translate("ListHandler", "CSV Export"),
			parent)
		self.triggered.connect(self.onTriggered)
		self.module = self.parentWidget().list.module

	# self.setShortcut(QtGui.QKeySequence.SaveAs)
	# self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self) -> None:
		icon = QtGui.QIcon(":icons/actions/download.svg")
		myHandler = WidgetHandler.mainWindow.handlerForWidget(self.parentWidget())  # Always stack them as my child
		assert myHandler is not None
		handler = WidgetHandler(
			lambda: CsvExportWidget(self.module, self.parentWidget().list.model()),
			"CSV Export",
			icon)

		handler.mainWindow.addHandler(handler, myHandler)
		handler.focus()

	@staticmethod
	def isSuitableFor(module: str, actionName: str) -> bool:
		return (module == "list" or module.startswith("list.")) and actionName == "exportcsv"


actionDelegateSelector.insert(1, CsvExportAction.isSuitableFor, CsvExportAction)
