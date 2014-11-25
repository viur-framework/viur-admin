# -*- coding: utf-8 -*-
import time
import os
import logging

from ui.adminUI import Ui_MainWindow
from ui.preloaderUI import Ui_Preloader
from PyQt5 import QtCore, QtGui, QtWebKit, QtWidgets
from event import event
from config import conf
from utils import RegisterQueue, showAbout, Overlay, WidgetHandler, GroupHandler
from tasks import TaskViewer, TaskEntryHandler
import startpages
from network import NetworkService, RemoteFile
from priorityqueue import protocolWrapperClassSelector, protocolWrapperInstanceSelector


class Preloader(QtWidgets.QWidget):
    finished = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(Preloader, self).__init__(*args, **kwargs)
        self.ui = Ui_Preloader()
        self.ui.setupUi(self)
        self.timerID = None
        self.ui.progressBar.setMinimum(0)
        self.ui.progressBar.setMaximum(110)
        self.ui.progressBar.setValue(0)
        event.connectWithPriority("configDownloaded", self.configDownloaded, event.lowPriority)


    def configDownloaded(self):
        self.ui.progressBar.setValue(10)
        self.timerID = self.startTimer(100)


    def timerEvent(self, e):
        total = 0
        missing = 0
        for modul in conf.serverConfig["modules"].keys():
            total += 1
            protoWrap = protocolWrapperInstanceSelector.select(modul)
            if protoWrap is None:
                continue
            if protoWrap.busy:
                missing += 1
        self.ui.progressBar.setValue(10 + int(100.0 * ((total - missing) / total)))
        if not missing:
            event.emit("preloadingFinished")
            self.finished.emit()
            self.killTimer(self.timerID)
            self.timerID = None


class MainWindow(QtWidgets.QMainWindow):
    """
    The main window.
    Holds the code for loading and processing the config (from the server) and
    mannaging the viewport
    """

    def __init__(self, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
        self.logger = logging.getLogger("MainWindow")
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.treeWidget.setColumnWidth(0, 266)
        self.ui.treeWidget.setColumnWidth(1, 25)
        event.connectWithPriority('loginSucceeded', self.loadConfig, event.lowPriority)
        # event.connectWithPriority( QtCore.SIGNAL('addHandler(PyQt_PyObject,PyQt_PyObject)'), self.addHandler,
        # event.lowestPriority )
        #event.connectWithPriority( QtCore.SIGNAL('stackHandler(PyQt_PyObject)'), self.stackHandler,
        # event.lowestPriority )
        #event.connectWithPriority( QtCore.SIGNAL('focusHandler(PyQt_PyObject)'), self.focusHandler, event.lowPriority )
        #event.connectWithPriority( QtCore.SIGNAL('unfocusHandler(PyQt_PyObject)'), self.unfocusHandler,
        # event.lowPriority )
        #event.connectWithPriority( QtCore.SIGNAL('removeHandler(PyQt_PyObject)'), self.removeHandler,
        # event.lowPriority )
        event.connectWithPriority('stackWidget', self.stackWidget, event.lowPriority)
        event.connectWithPriority('popWidget', self.popWidget, event.lowPriority)
        #event.connectWithPriority( QtCore.SIGNAL('addWidget(PyQt_PyObject)'), self.addWidget, event.lowPriority )
        #event.connectWithPriority( QtCore.SIGNAL('removeWidget(PyQt_PyObject)'), self.removeWidget, event.lowPriority )
        event.connectWithPriority('rebuildBreadCrumbs', self.rebuildBreadCrumbs, event.lowPriority)
        WidgetHandler.mainWindow = self
        self.ui.treeWidget.itemClicked.connect(self.onTreeWidgetItemClicked)
        self.ui.actionTasks.triggered.connect(self.onActionTasksTriggered)
        self.currentWidget = None
        self.helpBrowser = None
        self.startPage = None
        self.rebuildBreadCrumbs()

    def loadConfig(self, request=None):
        # self.show()
        self.preloader = Preloader()
        self.preloader.show()
        self.preloader.finished.connect(self.onPreloaderFinished)
        self.logger.debug("Checkpoint: loadConfig")
        NetworkService.request("/config", successHandler=self.onLoadConfig, failureHandler=self.onError)

    def onPreloaderFinished(self):
        self.preloader.deleteLater()
        self.preloader = None
        self.show()

    def onLoadConfig(self, request):
        self.logger.debug("Checkpoint: onLoadConfig")
        try:
            conf.serverConfig = NetworkService.decode(request)
        except:

            self.onError(msg="Unable to parse portalconfig!")
            return
        event.emit("configDownloaded")
        self.setup()

    # event.emit( "loginSucceeded()" )

    def onError(self, msg=""):
        """
            Called if something went wrong while loading or parsing the
            portalconfig requested from the server.
        """
        self.logger.error(msg)
        QtCore.QTimer.singleShot(3000, self.resetLoginWindow)


    def handlerForWidget(self, wdg=None):
        def findRekursive(wdg, node):
            if "widgets" in dir(node) and isinstance(node.widgets, list):
                for w in node.widgets:
                    if w == wdg:
                        return ( node )
            for x in range(0, node.childCount()):
                res = findRekursive(wdg, node.child(x))
                if res is not None:
                    return ( res )
            return ( None )

        if wdg is None:
            wdg = self.ui.stackedWidget.currentWidget()
            if wdg is None:
                return ( None )
        return ( findRekursive(wdg, self.ui.treeWidget.invisibleRootItem()) )

    def addHandler(self, handler, parent=None):
        """
        Adds an handler as child of parent.
        If parent is None, handler is added to the toplevel.

        @param handler: Handler to add
        @type handler: BaseHandler
        @param parent: Parent to stack handler to. If None, stack it to the toplevel
        @type handler: BaseHandler or None
        """
        if parent:
            parent.addChild(handler)
            self.ui.treeWidget.expandItem(parent)
        else:
            self.ui.treeWidget.addTopLevelItem(handler)
        self.ui.treeWidget.sortItems(0, QtCore.Qt.AscendingOrder)


    def focusHandler(self, handler):
        """
        Ensures that the widget gains focus.

        @type handler: BaseHandler
        @param handler: Handler requesting the focus
        """
        currentHandler = self.handlerForWidget()
        if currentHandler:
            self.ui.treeWidget.setItemSelected(currentHandler, False)
        if handler.parent():
            self.ui.treeWidget.expandItem(handler.parent())
        self.ui.treeWidget.setItemSelected(handler, True)
        assert self.ui.stackedWidget.indexOf(handler.widgets[-1]) != -1
        self.ui.stackedWidget.setCurrentWidget(handler.widgets[-1])
        self.rebuildBreadCrumbs()

    def stackHandler(self, handler):
        """
            Stacks a new handler to the current handler

            @param handler: handler to stack
            @type handler: BaseHandler
        """
        currentHandler = self.handlerForWidget()
        assert currentHandler
        currentHandler.addChild(handler)
        handler.focus()

    def stackWidget(self, widget):
        """
            Stacks a new widget to the current handler.
            This widget doesnt have its own handler, so it wont appear in the QTreeWidget.
            The last widget on a handler's stack allways hides all other widgets of that handler.

            @param widget: Widget to stack on the current handler
            @type widget: QWidget
        """
        currentHandler = self.handlerForWidget()
        assert currentHandler
        currentHandler.widgets.append(widget)
        self.addWidget(widget)
        currentHandler.focus()

    def addWidget(self, widget):
        assert self.ui.stackedWidget.indexOf(widget) == -1
        event.emit("addWidget", widget)
        self.ui.stackedWidget.addWidget(widget)

    def removeWidget(self, widget):
        assert self.ui.stackedWidget.indexOf(widget) != -1
        self.ui.stackedWidget.removeWidget(widget)
        try:
            widget.prepareDeletion()
        except AttributeError:
            pass
        #widget.setParent( None )
        widget.deleteLater()
        del widget

    def popWidget(self, widget):
        """
            Removes a widget from the currentHandler's stack.
            The widget looses focus and gets detached from that handler.
            If no more referents are left to that widget, its garbarge-collected.

            @type widget: QWidget
            @param widget: Widget to remove. Must be on the current handler's stack.
        """
        currentHandler = self.handlerForWidget(widget)
        if currentHandler is None:
            logging.error("Stale widget: " + str(widget))
            assert False
            return
        currentHandler.close()
        self.rebuildBreadCrumbs()

    def unfocusHandler(self, handler):
        """
            Moves the focus to the next handler on our stack (if any).

            @param handler: The handler requesting the unfocus. *Must* be the last on the stack.
            @type handler: BaseHandler
        """
        currentHandler = self.handlerForWidget()
        if currentHandler:
            self.focusHandler(currentHandler)

    def removeHandler(self, handler):
        """
            Removes a handler added by addHandler or stackHandler.
            @type handler: EntryHandler
        """

        def removeRecursive(handler, parent):
            for subIdx in range(0, parent.childCount()):
                child = parent.child(subIdx)
                if id(child) == id(handler):
                    parent.removeChild(handler)
                    return
                removeRecursive(handler, child)

        parent = handler.parent()
        removeRecursive(handler, self.ui.treeWidget.invisibleRootItem())
        for widget in handler.widgets:
            if self.ui.stackedWidget.indexOf(widget) != -1:
                self.ui.stackedWidget.removeWidget(widget)
        if parent and parent != self.ui.treeWidget.invisibleRootItem():
            parent.focus()
        else:
            currentHandler = self.handlerForWidget()
            if currentHandler:
                self.focusHandler(currentHandler)
        self.rebuildBreadCrumbs()

    def onTreeWidgetItemClicked(self, item, colum):
        if colum == 0:
            item.clicked()
        elif colum == 1:  #Close
            item.close()

    def rebuildBreadCrumbs(self):
        """
            Rebuilds the breadcrump-path.
            Currently, it displayes the current modul, its icon and
            stacks the path as children to its handler
        """
        self.ui.modulLbl.setText(QtCore.QCoreApplication.translate("MainWindow", "Welcome to ViUR!"))
        self.ui.iconLbl.setPixmap(QtGui.QPixmap("icons/viur_logo.png").scaled(64, 64, QtCore.Qt.IgnoreAspectRatio))
        currentHandler = self.handlerForWidget()
        if currentHandler:
            try:
                txt, icon = currentHandler.getBreadCrumb()
            except:
                return
            self.ui.modulLbl.setText(txt[: 35])
            if icon:
                sizes = icon.availableSizes()
                if len(sizes):
                    pixmap = icon.pixmap(sizes[0])
                    self.ui.iconLbl.setPixmap(pixmap.scaled(64, 64, QtCore.Qt.IgnoreAspectRatio))

    def resetLoginWindow(self):
        """
        Emits QtCore.SIGNAL('resetLoginWindow()')
        """
        event.emit('resetLoginWindow')
        self.hide()

    def setup(self):
        """
        Initializes everything based on the config recived from the server.
        It
            - Resets the ui to sane defaults.
            - Selects a startPage for the application
            - Selects Protocollwrapper and Module-Handler for each modul
            - Requests a toplevel handler for each modul
            - Finnaly emits modulHandlerInitialized and mainWindowInitialized
        """
        if not self.startPage:
            if "configuration" in conf.serverConfig.keys():
                if "analyticsKey" in conf.serverConfig["configuration"].keys():
                    self.startPage = startpages.AnalytisWidget()
                elif "startPage" in conf.serverConfig["configuration"].keys():
                    self.startPage = startpages.WebWidget()
            if not self.startPage:  #Still not
                self.startPage = startpages.DefaultWidget()
            self.ui.stackedWidget.addWidget(self.startPage)
        self.ui.treeWidget.clear()
        data = conf.serverConfig
        handlers = []
        groupHandlers = {}
        if "configuration" in data.keys() and "modulGroups" in data["configuration"].keys():
            for group in data["configuration"]["modulGroups"]:
                if not all([x in group.keys() for x in
                            ["name", "prefix", "icon"]]):  #Assert that all required properties are there
                    continue
                groupHandlers[group["prefix"]] = GroupHandler(None, group["name"], group["icon"])
                self.ui.treeWidget.addTopLevelItem(groupHandlers[group["prefix"]])
        if not "modules" in conf.portal.keys():
            conf.portal["modules"] = {}
        for modul, cfg in data["modules"].items():
            queue = RegisterQueue()
            event.emit('requestModulHandler', queue, modul)
            handler = queue.getBest()()
            if "name" in cfg.keys() and groupHandlers:
                parent = None
                for groupName in groupHandlers.keys():
                    if cfg["name"].startswith(groupName):
                        parent = groupHandlers[groupName]
                if parent:
                    parent.addChild(handler)
                else:
                    self.ui.treeWidget.addTopLevelItem(handler)
            else:
                self.ui.treeWidget.addTopLevelItem(handler)
            handlers.append(handler)
            wrapperClass = protocolWrapperClassSelector.select(modul, data["modules"])
            if wrapperClass is not None:
                wrapperClass(modul)
            event.emit('modulHandlerInitialized', modul)
        self.ui.treeWidget.sortItems(0, QtCore.Qt.AscendingOrder)
        event.emit('mainWindowInitialized')
        QtGui.QApplication.restoreOverrideCursor()


    def onActionAboutTriggered(self, checked=None):
        if checked is None: return
        showAbout(self)

    def onActionHelpTriggered(self):
        if self.helpBrowser:
            self.helpBrowser.deleteLater()
        self.helpBrowser = QtWebKit.QWebView()
        self.helpBrowser.setUrl(QtCore.QUrl("http://www.viur.is/site/Admin-Dokumentation"))
        self.helpBrowser.setWindowTitle(QtCore.QCoreApplication.translate("Help", "Help"))
        self.helpBrowser.setWindowIcon(QtGui.QIcon(QtGui.QPixmap("icons/menu/help.png")))
        self.helpBrowser.show()

    def onActionTasksTriggered(self, checked=None):
        """
            Creates a WidgetHandler for the TaskView and displayed the taskHandler
        """
        taskHandler = TaskEntryHandler(lambda *args, **kwargs: TaskViewer())
        self.addHandler(taskHandler)
        taskHandler.focus()
	
