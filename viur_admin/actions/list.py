# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.network import NetworkService
from viur_admin.priorityqueue import protocolWrapperInstanceSelector, actionDelegateSelector
from viur_admin.widgets.edit import EditWidget
from viur_admin.utils import WidgetHandler
from viur_admin.config import conf
from viur_admin.widgets.list import CsvExportWidget
from viur_admin.ui.editpreviewUI import Ui_BasePreview


class ListAddAction(QtWidgets.QAction):
	def __init__(self, parent, *args, **kwargs):
		super(ListAddAction, self).__init__(QtGui.QIcon(":icons/actions/add.svg"),
		                                    QtCore.QCoreApplication.translate("ListHandler", "Add entry"), parent)

		# self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.New)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self, e=None):
		if self.parentWidget().list.modul in conf.serverConfig["modules"].keys() and "name" in \
				conf.serverConfig["modules"][self.parentWidget().list.modul].keys():
			name = conf.serverConfig["modules"][self.parentWidget().list.modul]["name"]
		else:
			name = self.parentWidget().list.modul
		descr = QtCore.QCoreApplication.translate("ListHandler", "Add entry: %s") % name
		modul = self.parentWidget().list.modul
		handler = WidgetHandler(lambda: EditWidget(modul, EditWidget.appList, 0), descr,
		                        QtGui.QIcon(":icons/actions/add.svg"))
		handler.stackHandler()

	# event.emit( QtCore.SIGNAL('stackHandler(PyQt_PyObject)'), handler )

	@staticmethod
	def isSuitableFor(modul, actionName):
		return ((modul == "list" or modul.startswith("list.") and actionName == "add"))


actionDelegateSelector.insert(1, ListAddAction.isSuitableFor, ListAddAction)


class ListReloadAction(QtWidgets.QAction):
	def __init__(self, parent, *args, **kwargs):
		super(ListReloadAction, self).__init__(QtGui.QIcon(":icons/actions/refresh.svg"),
		                                       QtCore.QCoreApplication.translate("ListHandler", "Reload"), parent)

		# self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.New)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self, e=None):
		self.parentWidget().list.model().reload()

	@staticmethod
	def isSuitableFor(modul, actionName):
		return ((modul == "list" or modul.startswith("list.") and actionName == "reload"))


actionDelegateSelector.insert(1, ListReloadAction.isSuitableFor, ListReloadAction)


class ListEditAction(QtWidgets.QAction):
	def __init__(self, parent, *args, **kwargs):
		super(ListEditAction, self).__init__(QtGui.QIcon(":icons/actions/edit.svg"),
		                                     QtCore.QCoreApplication.translate("ListHandler", "Edit entry"), parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.Open)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self, e):
		numAccounts = len(set([x.row() for x in self.parentWidget().list.selectionModel().selection().indexes()]))
		if numAccounts == 0:
			return
		if numAccounts > 1:
			reply = QtWidgets.QMessageBox.question(self.parent(),
			                                       QtCore.QCoreApplication.translate("ListHandler",
			                                                                         "Edit multiple Entries"),
			                                       QtCore.QCoreApplication.translate("ListHandler",
			                                                                         "Edit all %s accounts?") % numAccounts,
			                                       QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
			                                       QtWidgets.QMessageBox.No)
			if reply != QtWidgets.QMessageBox.Yes:
				return
		for data in self.parent().getSelection():
			self.parentWidget().openEditor(data, clone=False)

	@staticmethod
	def isSuitableFor(modul, actionName):
		return ((modul == "list" or modul.startswith("list.") and actionName == "edit"))


actionDelegateSelector.insert(1, ListEditAction.isSuitableFor, ListEditAction)


class ListCloneAction(QtWidgets.QAction):
	def __init__(self, parent, *args, **kwargs):
		super(ListCloneAction, self).__init__(QtGui.QIcon(":icons/actions/clone.svg"),
		                                      QtCore.QCoreApplication.translate("ListHandler", "Clone entry"), parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.SaveAs)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self, e):
		if len(self.parentWidget().list.selectionModel().selection().indexes()) == 0:
			return
		data = self.parentWidget().list.model().getData()[
			self.parentWidget().list.selectionModel().selection().indexes()[0].row()]
		self.parentWidget().openEditor(data, clone=True)

	@staticmethod
	def isSuitableFor(modul, actionName):
		return ((modul == "list" or modul.startswith("list.") and actionName == "clone"))


actionDelegateSelector.insert(1, ListCloneAction.isSuitableFor, ListCloneAction)


class ListDeleteAction(QtWidgets.QAction):
	def __init__(self, parent, *args, **kwargs):
		super(ListDeleteAction, self).__init__(QtGui.QIcon(":icons/actions/delete.svg"),
		                                       QtCore.QCoreApplication.translate("ListHandler", "Delete"), parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.Delete)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	# self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )

	def onTriggered(self, e=None):
		indexes = self.parentWidget().list.selectedIndexes()
		rows = []
		for index in indexes:
			row = index.row()
			if not row in rows:
				rows.append(row)
		deleteData = [self.parentWidget().list.model().getData()[row] for row in rows]
		reqWrap = protocolWrapperInstanceSelector.select(self.parent().list.modul)
		self.parent().requestDelete([x["id"] for x in deleteData])

	@staticmethod
	def isSuitableFor(modul, actionName):
		return ((modul == "list" or modul.startswith("list.") and actionName == "delete"))


actionDelegateSelector.insert(1, ListDeleteAction.isSuitableFor, ListDeleteAction)


class Preview(QtWidgets.QDialog):
	def __init__(self, urls, modul, data, *args, **kwargs):
		super(Preview, self).__init__(*args, **kwargs)
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
		self.modul = modul
		self.data = data
		self.request = None
		self.cbUrls.addItems([x[0] for x in self.urls])
		if "actiondescr" in data.keys():
			self.setWindowTitle("%s: %s" % (data["actiondescr"], data["name"]))
		elif "name" in data.keys():
			self.setWindowTitle(QtCore.QCoreApplication.translate("ListHandler", "Preview: %s") % data["name"])
		else:
			self.setWindowTitle(QtCore.QCoreApplication.translate("ListHandler", "Preview"))
		self.cbUrls.currentIndexChanged.connect(self.onCbUrlsCurrentIndexChanged)
		# self.ui.btnReload.released.connect(self.onBtnReloadReleased)
		if len(self.urls) > 0:
			self.onCbUrlsCurrentIndexChanged(0)
		self.show()

	def onCbUrlsCurrentIndexChanged(self, idx):
		if not isinstance(idx, int):
			return
		baseurl = NetworkService.url.replace("/admin", "")
		url = self.urls[idx][1]
		url = url.replace("{{id}}", self.data["id"]).replace("{{modul}}", self.modul)
		QtGui.QDesktopServices.openUrl(QtCore.QUrl(baseurl + url))


class ListPreviewAction(QtWidgets.QAction):
	def __init__(self, parent, *args, **kwargs):
		super(ListPreviewAction, self).__init__(QtGui.QIcon(":icons/actions/preview.svg"),
		                                        QtCore.QCoreApplication.translate("ListHandler", "Preview"), parent)
		self.modul = self.parentWidget().list.modul
		self.widget = None
		if self.modul in conf.serverConfig["modules"].keys():
			modulConfig = conf.serverConfig["modules"][self.modul]
			if "previewurls" in modulConfig.keys() and modulConfig["previewurls"]:
				self.setEnabled(True)
				self.previewURLs = modulConfig["previewurls"]
			else:
				self.setEnabled(False)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.Print)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self, e):
		indexes = self.parentWidget().list.selectionModel().selection().indexes()
		rows = []
		for index in indexes:
			row = index.row()
			if not row in rows:
				rows.append(row)
		if len(rows) > 0:
			data = self.parentWidget().list.model().getData()[rows[0]]
			self.widget = Preview(self.previewURLs, self.modul, data)

	@staticmethod
	def isSuitableFor(modul, actionName):
		return ((modul == "list" or modul.startswith("list.") and actionName == "preview"))


actionDelegateSelector.insert(1, ListPreviewAction.isSuitableFor, ListPreviewAction)


class CsvExportAction(QtWidgets.QAction):
	def __init__(self, parent, *args, **kwargs):
		super(CsvExportAction, self).__init__(QtGui.QIcon(":icons/actions/download.svg"),
		                                      QtCore.QCoreApplication.translate("ListHandler", "CSV Export"), parent)
		self.triggered.connect(self.onTriggered)
		self.modul = self.parentWidget().list.modul
		# self.setShortcut(QtGui.QKeySequence.SaveAs)
		# self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self, e):
		icon = QtGui.QIcon(":icons/actions/download.svg")
		myHandler = WidgetHandler.mainWindow.handlerForWidget(self.parentWidget())  # Always stack them as my child
		assert myHandler is not None
		handler = WidgetHandler(lambda: CsvExportWidget(self.modul, self.parentWidget().list.model()), "CSV Export", icon)

		handler.mainWindow.addHandler(handler, myHandler)
		handler.focus()

	@staticmethod
	def isSuitableFor(modul, actionName):
		return ((modul == "list" or modul.startswith("list.") and actionName == "exportcsv"))


actionDelegateSelector.insert(1, CsvExportAction.isSuitableFor, CsvExportAction)
