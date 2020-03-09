# -*- coding: utf-8 -*-
from typing import List, Any, Dict, Union, Tuple

from PyQt5.QtWidgets import QTreeWidgetItemIterator

from viur_admin.log import getLogger

logger = getLogger(__name__)
from collections import OrderedDict

from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin import startpages
from viur_admin.config import conf
from viur_admin.event import event
from viur_admin.network import NetworkService, RequestWrapper
from viur_admin.priorityqueue import protocolWrapperClassSelector, protocolWrapperInstanceSelector
from viur_admin.startpages.default import DefaultWidget
from viur_admin.tasks import TaskViewer, TaskEntryHandler
from viur_admin.ui.preloaderUI import Ui_Preloader
from viur_admin.utils import RegisterQueue, showAbout, WidgetHandler, GroupHandler
import viur_admin.plugins


class Preloader(QtWidgets.QWidget):
	finished = QtCore.pyqtSignal()

	def __init__(
			self,
			*args: Any,
			**kwargs: Any):
		super(Preloader, self).__init__(*args, **kwargs)
		self.ui = Ui_Preloader()
		self.ui.setupUi(self)
		self.timerID = None
		self.ui.progressBar.setMinimum(0)
		self.ui.progressBar.setMaximum(110)
		self.ui.progressBar.setValue(0)
		event.connectWithPriority("configDownloaded", self.configDownloaded, event.lowPriority)

	def configDownloaded(self) -> None:
		self.ui.progressBar.setValue(10)
		self.timerID = self.startTimer(100)

	def timerEvent(self, e: QtCore.QTimerEvent) -> None:
		total = 0
		missing = 0
		for modul in conf.serverConfig["modules"]:
			total += 1
			protoWrap = protocolWrapperInstanceSelector.select(modul)
			if protoWrap is None:
				continue
			if protoWrap.busy:
				missing += 1
		if not total:
			print("No Modules available!!!")
			total = 1
			missing = 0
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

	def __init__(
			self,
			*args: Any,
			**kwargs: Any):
		super(MainWindow, self).__init__(*args, **kwargs)
		self.setObjectName("MainWindow")
		self.resize(983, 707)
		icon = QtGui.QIcon()
		icon.addPixmap(QtGui.QPixmap(":icons/viur_logo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.setWindowIcon(icon)
		self.setIconSize(QtCore.QSize(32, 32))
		self.centralwidget = QtWidgets.QWidget(self)
		self.centralwidget.setObjectName("centralwidget")
		self.centralwidget.setContentsMargins(0, 0, 0, 0)
		self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.centralwidget)
		self.horizontalLayout_2.setSpacing(0)
		self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
		self.horizontalLayout_2.setObjectName("horizontalLayout_2")
		self.verticalLayout = QtWidgets.QVBoxLayout()
		self.verticalLayout.setObjectName("verticalLayout")
		self.verticalLayout.setContentsMargins(0, 0, 0, 0)
		self._mainWidget = QtWidgets.QWidget(self.centralwidget)
		self._mainWidgetLayout = QtWidgets.QHBoxLayout(self._mainWidget)
		self._mainWidgetLayout.setContentsMargins(0, 0, 0, 0)
		# sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
		# sizePolicy.setHorizontalStretch(0)
		# sizePolicy.setVerticalStretch(0)
		# sizePolicy.setHeightForWidth(self._mainWidget.sizePolicy().hasHeightForWidth())
		# self._mainWidget.setSizePolicy(sizePolicy)
		# self._mainWidget.setMinimumSize(QtCore.QSize(0, 100))
		# self._mainWidget.setMaximumSize(QtCore.QSize(16777215, 100))
		self._mainWidget.setObjectName("mainWindowArea")
		# self.horizontalLayout = QtWidgets.QHBoxLayout(self._mainWidget)
		# self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
		# self.horizontalLayout.setObjectName("horizontalLayout")
		# self.iconLbl = QtWidgets.QLabel(self._mainWidget)
		# self.iconLbl.setObjectName("iconLbl")
		# self.horizontalLayout.addWidget(self.iconLbl)
		# self.modulLbl = QtWidgets.QLabel(self._mainWidget)
		font = QtGui.QFont()
		font.setPointSize(22)
		# font.setBold(False)
		# font.setWeight(50)
		# self.modulLbl.setFont(font)
		# self.modulLbl.setObjectName("modulLbl")
		# self.horizontalLayout.addWidget(self.modulLbl)
		# spacerItem = QtWidgets.QSpacerItem(368, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
		# self.horizontalLayout.addItem(spacerItem)
		self.verticalLayout.addWidget(self._mainWidget)
		self.verticalLayout.setContentsMargins(0, 0, 0, 0)
		self.stackedWidget = QtWidgets.QStackedWidget(self.centralwidget)
		self.stackedWidget.setObjectName("stackedWidget")
		self.stackedWidget.setContentsMargins(0, 0, 0, 0)
		self.verticalLayout.addWidget(self.stackedWidget)
		self.horizontalLayout_2.addLayout(self.verticalLayout)
		self.setCentralWidget(self.centralwidget)

		self.menubar = QtWidgets.QMenuBar(self)
		self.menubar.setEnabled(True)
		# self.menubar.setGeometry(QtCore.QRect(0, 0, 983, 19))
		self.menubar.setObjectName("menubar")
		self.menuInfo = QtWidgets.QMenu(self.menubar)
		self.menuInfo.setObjectName("menuInfo")
		self.menuErweitert = QtWidgets.QMenu(self.menubar)
		self.menuErweitert.setObjectName("menuErweitert")
		self.setMenuBar(self.menubar)
		self.statusbar = QtWidgets.QStatusBar(self)
		self.statusbar.setObjectName("statusbar")
		self.setStatusBar(self.statusbar)
		self.dockWidget = QtWidgets.QDockWidget(self)
		self.dockWidget.setWindowFlags(QtCore.Qt.Window)
		# self.dockWidget.setMinimumSize(QtCore.QSize(300, 35))
		self.dockWidget.setObjectName("dockWidget")
		self.treeWidget = QtWidgets.QTreeWidget(self)
		self.treeWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
		self.treeWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
		self.treeWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self.treeWidget.setColumnCount(2)
		self.treeWidget.setObjectName("treeWidget")
		self.treeWidget.headerItem().setText(1, "2")
		self.treeWidget.header().setVisible(False)

		# for handler search
		self.handlerWidget = QtWidgets.QWidget(self)
		self.handlerLayout = QtWidgets.QVBoxLayout(self.handlerWidget)
		_translate = QtCore.QCoreApplication.translate

		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
		sizePolicy.setHorizontalStretch(0)
		sizePolicy.setVerticalStretch(0)
		sizePolicy.setHeightForWidth(self.handlerWidget.sizePolicy().hasHeightForWidth())
		self.handlerWidget.setSizePolicy(sizePolicy)
		self.handlerSearchLayout = QtWidgets.QHBoxLayout()
		self.handlerSearchLayout.setObjectName("handlerSearchLayout")
		self.moduleSearch = QtWidgets.QLineEdit(self)
		# self.moduleSearch.setMinimumSize(QtCore.QSize(0, 32))
		self.moduleSearch.setObjectName("moduleSearch")
		self.moduleSearch.textChanged.connect(self.searchHandler)
		self.handlerSearchLayout.addWidget(self.moduleSearch)
		icon = QtGui.QIcon()
		icon.addPixmap(QtGui.QPixmap(":icons/actions/search.svg"), QtGui.QIcon.Normal, QtGui.QIcon.On)
		self.searchAction = QtWidgets.QAction(icon, _translate("MainWindow", "Handler Search"), self)
		self.searchAction.setShortcut(QtGui.QKeySequence.Find)
		self.searchAction.triggered.connect(self.moduleSearch.setFocus)
		# self.searchBTN = QtWidgets.QPushButton(self)
		# self.searchBTN.setMinimumSize(QtCore.QSize(0, 32))
		# self.searchBTN.setIcon(icon)
		# self.searchBTN.setObjectName("searchBTN")
		# self.handlerSearchLayout.addWidget(self.searchBTN)

		self.handlerLayout.addWidget(self.treeWidget)
		self.handlerLayout.addLayout(self.handlerSearchLayout)
		self.dockWidget.setWidget(self.handlerWidget)

		self.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.dockWidget)
		self.actionQuit = QtWidgets.QAction(self)
		icon = QtGui.QIcon.fromTheme("application-exit")
		self.actionQuit.setIcon(icon)
		self.actionQuit.setObjectName("actionQuit")
		self.actionErste_Schritte = QtWidgets.QAction(self)
		icon = QtGui.QIcon.fromTheme("help-contents")
		self.actionErste_Schritte.setIcon(icon)
		self.actionErste_Schritte.setObjectName("actionErste_Schritte")
		self.actionHelp = QtWidgets.QAction(self)
		icon = QtGui.QIcon.fromTheme("help-contents")
		self.actionHelp.setIcon(icon)
		self.actionHelp.setShortcut("")
		self.actionHelp.setObjectName("actionHelp")
		self.actionAbout = QtWidgets.QAction(self)
		icon = QtGui.QIcon.fromTheme("help-about")
		self.actionAbout.setIcon(icon)
		self.actionAbout.setObjectName("actionAbout")
		self.actionLogout = QtWidgets.QAction(self)
		icon = QtGui.QIcon.fromTheme("system-log-out")
		self.actionLogout.setIcon(icon)
		self.actionLogout.setObjectName("actionLogout")
		self.actionTasks = QtWidgets.QAction(self)
		icon1 = QtGui.QIcon()
		icon1.addPixmap(QtGui.QPixmap(":icons/settings.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.actionTasks.setIcon(icon1)
		self.actionTasks.setObjectName("actionTasks")
		self.toggleModuleViewTasks = QtWidgets.QAction(self)
		self.menuInfo.addAction(self.actionHelp)
		self.menuInfo.addSeparator()
		self.menuInfo.addAction(self.actionAbout)
		self.menuErweitert.addAction(self.actionTasks)
		self.menubar.addAction(self.menuInfo.menuAction())
		self.menubar.addAction(self.menuErweitert.menuAction())
		self.menuErweitert.addAction(self.searchAction)

		self.setWindowTitle(_translate("MainWindow", "ViUR Admin"))
		# self.iconLbl.setText(_translate("MainWindow", "TextLabel"))
		# self.modulLbl.setText(_translate("MainWindow", "TextLabel"))
		self.menuInfo.setTitle(_translate("MainWindow", "Info"))
		self.menuErweitert.setTitle(_translate("MainWindow", "Advanced"))
		self.dockWidget.setFeatures(self.dockWidget.NoDockWidgetFeatures)
		self.dockWidget.setFloating(False)

		self.dockWidget.setWindowTitle(_translate("MainWindow", "Modules"))
		self.treeWidget.setSortingEnabled(False)
		self.treeWidget.headerItem().setText(0, _translate("MainWindow", "Module"))
		self.actionQuit.setText(_translate("MainWindow", "Exit"))
		self.actionErste_Schritte.setText(_translate("MainWindow", "First steps"))
		self.actionHelp.setText(_translate("MainWindow", "Help"))
		self.actionAbout.setText(_translate("MainWindow", "About"))
		self.actionLogout.setText(_translate("MainWindow", "Log out"))
		self.actionTasks.setText(_translate("MainWindow", "Tasks"))
		self.moduleSearch.setPlaceholderText(_translate("MainWindow", "Handler Search"))
		self.stackedWidget.setCurrentIndex(-1)
		QtCore.QMetaObject.connectSlotsByName(self)

		self.treeWidget.setColumnWidth(0, 266)
		self.treeWidget.setColumnWidth(1, 25)
		event.connectWithPriority('loginSucceeded', self.loadConfig, event.lowPriority)
		# event.connectWithPriority( QtCore.SIGNAL('addHandler(PyQt_PyObject,PyQt_PyObject)'), self.addHandler,
		# event.lowestPriority )
		# event.connectWithPriority( QtCore.SIGNAL('stackHandler(PyQt_PyObject)'), self.stackHandler,
		# event.lowestPriority )
		# event.connectWithPriority( QtCore.SIGNAL('focusHandler(PyQt_PyObject)'), self.focusHandler, event.lowPriority )
		# event.connectWithPriority( QtCore.SIGNAL('unfocusHandler(PyQt_PyObject)'), self.unfocusHandler,
		# event.lowPriority )
		# event.connectWithPriority( QtCore.SIGNAL('removeHandler(PyQt_PyObject)'), self.removeHandler,
		# event.lowPriority )
		event.connectWithPriority('stackWidget', self.stackWidget, event.lowPriority)
		event.connectWithPriority('popWidget', self.popWidget, event.lowPriority)
		# event.connectWithPriority( QtCore.SIGNAL('addWidget(PyQt_PyObject)'), self.addWidget, event.lowPriority )
		# event.connectWithPriority( QtCore.SIGNAL('removeWidget(PyQt_PyObject)'), self.removeWidget, event.lowPriority )
		event.connectWithPriority('rebuildBreadCrumbs', self.rebuildBreadCrumbs, event.lowPriority)
		WidgetHandler.mainWindow = self
		self.actionAbout.triggered.connect(self.onActionAboutTriggered)
		self.actionHelp.triggered.connect(self.onActionHelpTriggered)
		self.treeWidget.itemClicked.connect(self.onTreeWidgetItemClicked)
		self.actionTasks.triggered.connect(self.onActionTasksTriggered)
		self.menuErweitert.addAction(self.dockWidget.toggleViewAction())
		# self.searchBTN.released.connect(self.searchHandler)
		self.moduleSearch.returnPressed.connect(self.searchHandler)
		self.currentWidget = None
		self.helpBrowser = None
		self.startPage = None
		self.rebuildBreadCrumbs()
		settings = QtCore.QSettings("Mausbrand", "ViurAdmin")
		try:
			self.restoreGeometry(settings.value("geometry"))
			self.restoreState(settings.value("windowState"))
		except Exception as err:
			# print(err)
			pass

		if self.dockWidget.isFloating():
			self.dockWidget.hide()

	def loadConfig(self, request: RequestWrapper = None) -> None:
		# self.show()
		self.preloader = Preloader()
		self.preloader.show()
		self.preloader.finished.connect(self.onPreloaderFinished)
		# logger.debug("Checkpoint: loadConfig")
		NetworkService.request("/user/view/self", successHandler=self.onLoadUser, failureHandler=self.onError)
		NetworkService.request("/config", successHandler=self.onLoadConfig, failureHandler=self.onError)
		if self.dockWidget.isFloating():
			self.dockWidget.show()

	def onPreloaderFinished(self) -> None:
		self.preloader.deleteLater()
		self.preloader = None
		self.show()

	def onLoadConfig(self, request: RequestWrapper) -> None:
		logger.debug("Checkpoint: onLoadConfig")
		try:
			conf.serverConfig = NetworkService.decode(request)
		except:
			self.onError(msg="Unable to parse portalconfig!")
			return
		event.emit("configDownloaded")
		if conf.currentUserEntry is not None:
			self.setup()

	def onLoadUser(self, request: RequestWrapper) -> None:
		try:
			conf.currentUserEntry = NetworkService.decode(request)["values"]
			logger.debug(repr(conf.currentUserEntry))
		except Exception as err:
			logger.exception(err)
			self.onError(msg="Unable to parse user entry!")
			return
		else:
			if conf.serverConfig is not None:
				self.setup()

	# event.emit( "loginSucceeded()" )

	def onError(self, msg: str = "") -> None:
		"""
			Called if something went wrong while loading or parsing the
			portalconfig requested from the server.
		"""
		logger.error("OnError msg: %r", msg)
		QtCore.QTimer.singleShot(3000, self.resetLoginWindow)

	def handlerForWidget(self, wdg: QtWidgets.QWidget = None) -> Union[QtWidgets.QTreeWidgetItem, None]:
		def findRekursive(currentWidget: QtWidgets.QWidget, node: Union[WidgetHandler, GroupHandler]) -> Union[WidgetHandler, GroupHandler, QtWidgets.QWidget, None]:
			if "widgets" in dir(node) and isinstance(node.widgets, list):
				for w in node.widgets:
					if w == currentWidget:
						return node
			for x in range(0, node.childCount()):
				res = findRekursive(currentWidget, node.child(x))
				if res is not None:
					return res
			return None

		if wdg is None:
			wdg = self.stackedWidget.currentWidget()
			if wdg is None:
				return None
		return findRekursive(wdg, self.treeWidget.invisibleRootItem())

	def addHandler(
			self,
			handler: Union[WidgetHandler, GroupHandler],
			parent: QtWidgets.QTreeWidgetItem = None) -> None:
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
			self.treeWidget.expandItem(parent)
		else:
			self.treeWidget.addTopLevelItem(handler)

	def focusHandler(self, handler: Any) -> None:
		"""
		Ensures that the widget gains focus.

		@type handler: BaseHandler
		@param handler: Handler requesting the focus
		"""
		currentHandler = self.handlerForWidget()
		if currentHandler:
			self.treeWidget.setCurrentItem(currentHandler)
		if handler.parent():
			self.treeWidget.expandItem(handler.parent())
		self.treeWidget.setCurrentItem(handler)
		assert self.stackedWidget.indexOf(handler.widgets[-1]) != -1
		self.stackedWidget.setCurrentWidget(handler.widgets[-1])
		self.rebuildBreadCrumbs()

	def stackHandler(self, handler: Any) -> None:
		"""
			Stacks a new handler to the current handler

			@param handler: handler to stack
			@type handler: BaseHandler
		"""
		currentHandler = self.handlerForWidget()
		assert currentHandler
		currentHandler.addChild(handler)
		handler.focus()

	def stackWidget(self, widget: Any) -> None:
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

	def addWidget(self, widget: Any) -> None:
		assert self.stackedWidget.indexOf(widget) == -1
		event.emit("addWidget", widget)
		self.stackedWidget.addWidget(widget)

	def removeWidget(self, widget: Any) -> None:
		logger.debug("removeWidget: %r", widget)
		assert self.stackedWidget.indexOf(widget) != -1
		self.stackedWidget.removeWidget(widget)
		try:
			widget.prepareDeletion()
		except AttributeError:
			pass
		widget.deleteLater()
		del widget

	def popWidget(self, widget: Any) -> None:
		"""
			Removes a widget from the currentHandler's stack.
			The widget looses focus and gets detached from that handler.
			If no more referents are left to that widget, its garbarge-collected.

			@type widget: QWidget
			@param widget: Widget to remove. Must be on the current handler's stack.
		"""
		logger.debug("popWidget: %r", widget)
		currentHandler = self.handlerForWidget(widget)
		if currentHandler is None:
			logger.error("Stale widget: " + str(widget))
			# TODO: why the former raise here without Exception instance?
			raise Exception("stale Widget: %r", widget)
		currentHandler.close()
		self.rebuildBreadCrumbs()

	def unfocusHandler(self, handler: Any) -> None:
		"""
			Moves the focus to the next handler on our stack (if any).

			@param handler: The handler requesting the unfocus. *Must* be the last on the stack.
			@type handler: BaseHandler
		"""
		currentHandler = self.handlerForWidget()
		if currentHandler:
			self.focusHandler(currentHandler)

	def removeHandler(self, handler: Any) -> None:
		"""
			Removes a handler added by addHandler or stackHandler.
			@type handler: EntryHandler
		"""

		logger.debug("MainWindow.removeHandler: %r", handler)

		def removeRecursive(handler: Any, parent: Any) -> Any:
			for subIdx in range(0, parent.childCount()):
				child = parent.child(subIdx)
				if id(child) == id(handler):
					parent.removeChild(handler)
					return
				removeRecursive(handler, child)

		parent = handler.parent()
		removeRecursive(handler, self.treeWidget.invisibleRootItem())
		for widget in handler.widgets:
			if self.stackedWidget.indexOf(widget) != -1:
				self.stackedWidget.removeWidget(widget)
		if parent and parent != self.treeWidget.invisibleRootItem():
			parent.focus()
		else:
			currentHandler = self.handlerForWidget()
			if currentHandler:
				self.focusHandler(currentHandler)
		self.rebuildBreadCrumbs()

	def onTreeWidgetItemClicked(self, item: Any, column: Any) -> None:
		logger.debug("item, column: %r, %r", item, column)
		if column == 0:
			item.clicked()
		elif column == 1 and not isinstance(item, GroupHandler):
			# Close only if we don't clicked on column 2 of a group
			item.close()

	def rebuildBreadCrumbs(self) -> None:
		"""
			Rebuilds the breadcrump-path.
			Currently, it displays the current module, its icon and
			stacks the path as children to its handler
		"""
		# self.modulLbl.setText(QtCore.QCoreApplication.translate("MainWindow", "Welcome to ViUR!"))
		# self.iconLbl.setPixmap(QtGui.QPixmap(":icons/viur_logo.png").scaled(32, 32, QtCore.Qt.IgnoreAspectRatio))
		currentHandler = self.handlerForWidget()
		if currentHandler:
			try:
				txt, icon = currentHandler.getBreadCrumb()
			except:
				return
			# self.modulLbl.setText(txt[:35])
			# if icon:
			# 	sizes = icon.availableSizes()
			# 	if len(sizes):
			# 		pixmap = icon.pixmap(sizes[0])
			# 		self.iconLbl.setPixmap(pixmap.scaled(32, 32, QtCore.Qt.IgnoreAspectRatio))

	def resetLoginWindow(self) -> None:
		"""
		Emits QtCore.SIGNAL('resetLoginWindow()')
		"""
		event.emit('resetLoginWindow')
		self.hide()

	def setup(self) -> None:
		"""
		Initializes everything based on the config received from the server.
		It
			- Resets the ui to sane defaults.
			- Selects a startPage for the application
			- Selects Protocolwrapper and Module-Handler for each module
			- Requests a toplevel handler for each module
			- Finally emits modulHandlerInitialized and mainWindowInitialized
		"""
		if not self.startPage:
			if "configuration" in conf.serverConfig:
				if "analyticsKey" in conf.serverConfig["configuration"]:
					logger.debug("setting analytics widget as startpage")
					self.startPage = startpages.AnalytisWidget()
				elif "startPage" in conf.serverConfig["configuration"]:
					logger.debug("retrieving startpage from server")
					self.startPage = startpages.WebWidget()
			if not self.startPage:  # Still not
				logger.debug("setting default startpage")
				self.startPage = DefaultWidget()
			self.stackedWidget.addWidget(self.startPage)
		self.treeWidget.clear()
		data = conf.serverConfig
		handlers = []
		groupHandlers = {}
		by_group: Dict[str, List[Any]] = dict()
		if "configuration" in data and "moduleGroups" in data["configuration"]:
			for group in data["configuration"]["moduleGroups"]:
				if not all([x in group for x in
				            ["name", "prefix", "icon"]]):  # Assert that all required properties are there
					continue
				group_handler = GroupHandler(None, group["name"], group["icon"], sortIndex=group.get("sortIndex", 0))
				group_prefix = group["prefix"]
				groupHandlers[group_prefix] = group_handler
				by_group[group_prefix] = list()
				# self.treeWidget.addTopLevelItem(groupHandlers[group["prefix"]])
		if "modules" not in conf.portal:
			conf.portal["modules"] = {}

		def sortItemHandlers(pair: Tuple[Any, Any]) -> Any:
			return pair[1].sortIndex

		groupHandlers = OrderedDict(sorted(groupHandlers.items(), key=sortItemHandlers))

		access = conf.currentUserEntry["access"]
		for module, cfg in data["modules"].items():
			logger.debug("starting to load module %r", module)
			if "root" not in access and not "{0}-view".format(module) in access:
				continue
			queue = RegisterQueue()
			event.emit('requestModuleHandler', queue, module)
			handler = queue.getBest()()
			if "name" in cfg and groupHandlers:
				parent = None
				for groupName in groupHandlers:
					if cfg["name"].startswith(groupName):
						parent = groupHandlers[groupName]
						break
				if parent:
					# parent.addChild(handler)
					by_group[groupName].append(handler)
				else:
					self.treeWidget.addTopLevelItem(handler)
			else:
				self.treeWidget.addTopLevelItem(handler)
			handlers.append(handler)
			wrapperClass = protocolWrapperClassSelector.select(module, data["modules"])
			if wrapperClass is not None:
				wrapperClass(module)
			event.emit('modulHandlerInitialized', module)

		def subhandlerSorter(x: Any) -> int:
			return x.sortIndex

		emptyGroups = list()
		for group, handlers in by_group.items():
			handlers.sort(key=subhandlerSorter, reverse=True)
			for handler in handlers:
				groupHandlers[group].addChild(handler)
			if handlers:
				self.treeWidget.addTopLevelItem(groupHandlers[group])
			else:
				emptyGroups.append((group, groupHandlers[group]))

		for prefix, groupHandler in emptyGroups:
			groupHandlers.pop(prefix)
			del by_group[prefix]

		self.treeWidget.sortItems(1, QtCore.Qt.DescendingOrder)

		event.emit('mainWindowInitialized')
		QtWidgets.QApplication.restoreOverrideCursor()

	def onActionAboutTriggered(self, checked: bool = None) -> None:
		if checked is None:
			return
		showAbout(self)

	def onActionHelpTriggered(self) -> None:
		QtGui.QDesktopServices.openUrl(QtCore.QUrl("http://www.viur.is/site/Admin-Dokumentation"))

	def onActionTasksTriggered(self, checked: bool = None) -> None:
		"""
			Creates a WidgetHandler for the TaskView and displayed the taskHandler
		"""
		taskHandler = TaskEntryHandler(lambda *args, **kwargs: TaskViewer())
		self.addHandler(taskHandler)
		taskHandler.focus()

	def prepareCloseEverywhere(self):
		stackedWidgetCount = self.stackedWidget.count()
		for i in range(stackedWidgetCount - 1, -1, -1):
			widget = self.stackedWidget.widget(i)
			self.stackedWidget.removeWidget(widget)
			try:
				widget.prepareDeletion()
			except AttributeError:
				pass
			widget.deleteLater()
			del widget

	def closeEvent(self, event: QtGui.QCloseEvent) -> None:
		logger.debug("closeEvent: %r", event)
		self.prepareCloseEverywhere()
		settings = QtCore.QSettings("Mausbrand", "ViurAdmin")
		settings.setValue("geometry", self.saveGeometry())
		settings.setValue("windowState", self.saveState())
		super(MainWindow, self).closeEvent(event)

	def _setAllHidden(self, hidden: bool = True) -> None:
		it = QtWidgets.QTreeWidgetItemIterator(self.treeWidget)
		item = it.value()
		while item:
			item.setHidden(hidden)
			it += 1
			item = it.value()


	def searchHandler(self) -> None:
		self.dockWidget.setFloating(False)
		text = self.moduleSearch.text()
		if text and len(text) > 2:
			self._setAllHidden()
		else:
			self._setAllHidden(False)
			return

		foundItems = list()
		for i in range(2):
			for item in self.treeWidget.findItems(text, QtCore.Qt.MatchFlags(
							QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive), i):
				foundItems.append(item)

		for item in foundItems:
			item.setHidden(False)
			parent = item.parent()
			while parent:
				parent.setHidden(False)
				self.treeWidget.expandItem(parent)
				parent = parent.parent()
