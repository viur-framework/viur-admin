# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets
from viur_admin.utils import Overlay, RegisterQueue, formatString
from viur_admin.network import NetworkService, RequestGroup
from viur_admin.event import event
from viur_admin.priorityqueue import viewDelegateSelector, protocolWrapperInstanceSelector, actionDelegateSelector
from viur_admin.widgets.edit import EditWidget
from viur_admin.utils import WidgetHandler
from viur_admin.ui.editpreviewUI import Ui_BasePreview
from viur_admin.config import conf


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
        return ( (modul == "list" or modul.startswith("list.") and actionName == "add") )


actionDelegateSelector.insert(1, ListAddAction.isSuitableFor, ListAddAction)


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
            reply = QtGui.QMessageBox.question(self.parent(),
                                               QtCore.QCoreApplication.translate("ListHandler",
                                                                                 "Edit multiple Entries"),
                                               QtCore.QCoreApplication.translate("ListHandler",
                                                                                 "Edit all %s accounts?") % numAccounts,
                                               QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
            if reply != QtGui.QMessageBox.Yes:
                return
        for data in self.parent().getSelection():
            self.parentWidget().openEditor(data, clone=False)

    @staticmethod
    def isSuitableFor(modul, actionName):
        return ( (modul == "list" or modul.startswith("list.") and actionName == "edit") )


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
        return ( (modul == "list" or modul.startswith("list.") and actionName == "clone") )


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
        return ( (modul == "list" or modul.startswith("list.") and actionName == "delete") )


actionDelegateSelector.insert(1, ListDeleteAction.isSuitableFor, ListDeleteAction)


class Preview(QtWidgets.QWidget):
    def __init__(self, urls, modul, data, *args, **kwargs):
        super(Preview, self).__init__(*args, **kwargs)
        self.ui = Ui_EditPreview()
        self.ui.setupUi(self)
        self.urls = [(k, v) for (k, v) in urls.items()]
        self.urls.sort(key=lambda x: x[0])
        self.modul = modul
        self.data = data
        self.request = None
        self.ui.cbUrls.addItems([x[0] for x in self.urls])
        if "actiondescr" in data.keys():
            self.setWindowTitle("%s: %s" % (data["actiondescr"], data["name"]))
        elif "name" in data.keys():
            self.setWindowTitle(QtCore.QCoreApplication.translate("ListHandler", "Preview: %s") % data["name"])
        else:
            self.setWindowTitle(QtCore.QCoreApplication.translate("ListHandler", "Preview"))
        self.ui.cbUrls.currentIndexChanged.connect(self.onCbUrlsCurrentIndexChanged)
        self.ui.btnReload.released.connect(self.onBtnReloadReleased)
        if len(self.urls) > 0:
            self.onCbUrlsCurrentIndexChanged(0)
        self.show()

    def onCbUrlsCurrentIndexChanged(self, idx):
        if not isinstance(idx, int):
            return
        url = self.urls[idx][1]
        url = url.replace("{{id}}", self.data["id"]).replace("{{modul}}", self.modul)
        self.currentURL = url
        if url.lower().startswith("http"):
            self.ui.webView.setUrl(QtCore.QUrl(self.currentURL))
        else:
            """Its the originating server - Load the page in our context (cookies!)"""
            if self.request:
                # self.request.deleteLater()
                self.request = None
            request = NetworkService.request(NetworkService.url.replace("/admin", "") + url,
                                             finishedHandler=self.setHTML)

    def setHTML(self, req):
        if 1:  # try:
            html = bytes(req.readAll().data()).decode("UTF8")
        else:  # except:
            html = QtCore.QCoreApplication.translate("ListHandler", "Preview not possible")
        self.ui.webView.setHtml(html, QtCore.QUrl(NetworkService.url.replace("/admin", "") + self.currentURL))

    def onBtnReloadReleased(self, *args, **kwargs):
        self.onCbUrlsCurrentIndexChanged(self.ui.cbUrls.currentIndex())


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
        return ( (modul == "list" or modul.startswith("list.") and actionName == "preview") )


actionDelegateSelector.insert(1, ListPreviewAction.isSuitableFor, ListPreviewAction)
