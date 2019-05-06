# -*- coding: utf-8 -*-
from time import time

import csv
import json
from PyQt5.QtCore import QModelIndex

from viur_admin.log import getLogger

logger = getLogger(__name__)

import os.path
from datetime import datetime
from PyQt5 import QtCore, QtGui, QtWidgets
from viur_admin.utils import Overlay, urlForItem
from viur_admin.event import event
from viur_admin.priorityqueue import viewDelegateSelector, protocolWrapperInstanceSelector, actionDelegateSelector, \
	extendedSearchWidgetSelector
from viur_admin.widgets.edit import EditWidget
from viur_admin.utils import WidgetHandler
from viur_admin.ui.listUI import Ui_List
from viur_admin.ui.csvexportUI import Ui_CsvExport
from viur_admin.config import conf
from viur_admin.network import nam


class ListTableModel(QtCore.QAbstractTableModel):
	"""Model for displaying data within a listView"""
	GarbageTypeName = "ListTableModel"
	_chunkSize = 25

	rebuildDelegates = QtCore.pyqtSignal((object,))
	listIsComplete = QtCore.pyqtSignal()

	def __init__(self, modul, fields=None, filter=None, parent=None, *args):
		logger.debug("ListTableModel.init: %r, %r, %r, %r, %r", modul, fields, filter, parent, args)
		QtCore.QAbstractTableModel.__init__(self, parent, *args)
		self.modul = modul
		self.fields = fields or ["name"]
		self._validFields = []  # Due to miss-use, someone might request displaying fields which dont exists. These
		# are the fields that are valid
		self.filter = filter or {}
		self.skippedkeys = []
		self.dataCache = []
		self.headers = []
		self.completeList = False  # Have we all items?
		self.isLoading = 0
		self.cursor = None
		self.loadingKey = None  # As loading is performed in background, they might return results for a dataset which
		#  isnt displayed anymore
		protoWrap = protocolWrapperInstanceSelector.select(self.modul)
		assert protoWrap is not None
		protoWrap.entitiesChanged.connect(self.reload)
		try:
			protoWrap.queryResultAvailable.connect(self.addData)
		except Exception as err:
			logger.error("Error: here we should look again, what queryResultAvailable provides us...")
			logger.exception(err)
		self.reload()

	def insertRows(self, row: int, count: int, parent: QModelIndex = QModelIndex()):
		# logger.debug("insertRows: %r, %r, %r", row, count, parent)
		self.beginInsertRows(QModelIndex(), row, row + count - 1)
		for rowIndex in range(row, row + count):
			self.dataCache.insert(rowIndex, dict.fromkeys(["key"] + self._validFields))
		self.endInsertRows()
		return True

	def removeRows(self, row, count, parent=QModelIndex()):
		# logger.debug("removeRows: %r, %r, %r", row, count, parent)
		self.beginRemoveRows(QModelIndex(), row, row + count - 1)

		for rowIndex in range(row, row + count):
			self.dataCache.pop(rowIndex)

		self.endRemoveRows()
		return True

	def supportedDropActions(self):
		return QtCore.Qt.MoveAction | QtCore.Qt.TargetMoveAction

	def setDisplayedFields(self, fields):
		self.fields = fields
		self.reload()

	def setFilterbyName(self, filterName):
		self.name = filterName
		config = None  # getListConfig( self.module, filterName )
		if config:
			if "columns" in config.keys():
				self.fields = config["columns"]
			if "filter" in config.keys():
				self.filter = config["filter"]

	def setFilter(self, filter):
		self.filter = filter
		self.reload()

	def getFilter(self):
		return self.filter

	def getFields(self):
		return self.fields

	def getModul(self):
		return self.modul

	def reload(self):
		self.modelAboutToBeReset.emit()
		self.dataCache = []
		self.completeList = False
		self.cursor = False
		self.modelReset.emit()
		self.loadNext(True)

	def rowCount(self, parent):
		if self.completeList:
			return len(self.dataCache)
		else:
			return len(self.dataCache) + 1

	def columnCount(self, parent):
		try:
			return len(self.headers)
		except:
			return 0

	def setData(self, index, value, role):
		rowIndex = index.row()
		colIndex = index.column()
		lenDataCache = len(self.dataCache)
		# logger.debug("setData: value=%r", value)
		# logger.debug("indexes and length: %r, %r, %r", rowIndex, colIndex, lenDataCache)
		destDataCacheEntry = self.dataCache[rowIndex]
		fieldNameByIndex = self._validFields[colIndex]
		# logger.debug("destCacheEntry: %r, fieldNameByIndex: %r", destDataCacheEntry, fieldNameByIndex)
		if index.isValid():
			destDataCacheEntry[fieldNameByIndex] = value
			# logger.debug("data before emitting change: %r", destDataCacheEntry[fieldNameByIndex])
			self.dataChanged.emit(index, index)
			return True
		return False

	def data(self, index, role):
		if not index.isValid():
			return None
		elif role != QtCore.Qt.DisplayRole:
			return None
		if index.row() >= 0 and (index.row() < len(self.dataCache)):
			try:
				# logger.debug("data role: %r, %r, %r", index.row(), index.column(), self._validFields)
				return self.dataCache[index.row()][self._validFields[index.column()]]
			except Exception as err:
				logger.exception(err)
				return ""
		else:
			if not self.completeList:
				self.loadNext()
			return "-Lade-"

	def headerData(self, col, orientation, role):
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			return self.headers[col]
		return None

	def loadNext(self, forceLoading=False):
		logger.debug("loadNext - cookies: %r", [i.toRawForm() for i in nam.cookieJar().allCookies()])
		if self.isLoading and not forceLoading:
			# print("stopped loadNext")
			return
		self.isLoading += 1
		logger.debug("loadNext.filter, %r", self.filter)
		rawFilter = self.filter.copy() or {}
		if self.cursor:
			rawFilter["cursor"] = self.cursor
		elif self.dataCache:
			invertedOrderDir = False
			if "orderdir" in rawFilter.keys() and str(rawFilter["orderdir"]) == "1":
				invertedOrderDir = True
			if rawFilter["orderby"] in self.dataCache[-1].keys():
				if invertedOrderDir:
					rawFilter[rawFilter["orderby"] + "$lt"] = self.dataCache[-1][rawFilter["orderby"]]
				else:
					rawFilter[rawFilter["orderby"] + "$gt"] = self.dataCache[-1][rawFilter["orderby"]]
		protoWrap = protocolWrapperInstanceSelector.select(self.modul)
		assert protoWrap is not None
		logger.debug("loadNext.chunk: %r, %r, %r", rawFilter, type(rawFilter), self._chunkSize)
		rawFilter["amount"] = self._chunkSize
		self.loadingKey = protoWrap.queryData(**rawFilter)

	def addData(self, queryKey):
		# print("addData")
		self.isLoading -= 1
		if queryKey is not None and queryKey != self.loadingKey:  # The Data is for a list we dont display anymore
			return
		protoWrap = protocolWrapperInstanceSelector.select(self.modul)
		assert protoWrap is not None
		cacheTime, skellist, cursor = protoWrap.dataCache[queryKey]
		# logger.debug("ListTableModule.addData: %r", len(skellist))
		self.layoutAboutToBeChanged.emit()

		# Rebuild our local cache of valid fields
		bones = {}
		for key, bone in protoWrap.viewStructure.items():
			bones[key] = bone
		self._validFields = [x for x in self.fields if x in bones.keys()]
		self.rebuildDelegates.emit(protoWrap.viewStructure)
		self.dataCache.extend(skellist)
		if len(skellist) < self._chunkSize:
			self.completeList = True
		self.cursor = cursor
		self.layoutChanged.emit()
		self.loadingKey = None

	# self.emit(QtCore.SIGNAL("dataRecived()"))

	def repaint(self):  # Currently an ugly hack to redraw the table
		self.layoutAboutToBeChanged.emit()
		self.layoutChanged.emit()

	def getData(self):
		return self.dataCache

	def sort(self, p_int, order=None):
		if (self.fields[p_int] == "key" or (
				"cantSort" in dir(self.delegates[p_int]) and self.delegates[p_int].cantSort)):
			return
		filter = self.filter
		filter["orderby"] = self.fields[p_int]
		if order == QtCore.Qt.DescendingOrder:
			filter["orderdir"] = "1"
		else:
			filter["orderdir"] = "0"
		self.setFilter(filter)

	def search(self, searchStr):
		"""
			Start a search for the given string.
			If searchStr is None, it ends any currently active search.
			@param searchStr: Token to search for
			@type searchStr: String or None
		"""
		if searchStr:
			if "name$lk" in self.filter.keys():
				del self.filter["name$lk"]
			self.filter["search"] = searchStr
			self.reload()
		else:
			if "search" in self.filter.keys():
				del self.filter["search"]
			self.reload()

	def prefixSearch(self, searchStr):
		"""
			Merge the prefix search in our filter dict if possible.
			Does noting if the list isn't sorted by name.
		"""
		if "orderby" not in self.filter.keys() or not self.filter["orderby"] == "name":
			return
		if "search" in self.filter.keys():
			del self.filter["search"]
		if not searchStr and "name$lk" in self.filter.keys():
			del self.filter["name$lk"]
		if searchStr:
			self.filter["name$lk"] = searchStr
		self.reload()

	def flags(self, index):
		defaultFlags = super(ListTableModel, self).flags(index)
		# logger.debug("flags row and col: %r, %r", index.row(), index.column())
		if not index.isValid():
			# lenData = len(self.dataCache)
			# if index.row() == -1 and index.column() == -1:
			# 	return defaultFlags
			return defaultFlags
		return defaultFlags

	def setSortIndex(self, index: QModelIndex, sortindex: float):
		protoWrap = protocolWrapperInstanceSelector.select(self.modul)
		assert protoWrap is not None
		key = self.dataCache[index.row()]["key"]
		protoWrap.setSortIndex(key, sortindex)


class ListTableView(QtWidgets.QTableView):
	"""
		Provides an interface for Data structured as a simple list.

		@emits hierarchyChanged( PyQt_PyObject=emitter, PyQt_PyObject=module, PyQt_PyObject=rootNode,
		PyQt_PyObject=itemID )
		@emits onItemClicked(PyQt_PyObject=item.data)
		@emits onItemDoubleClicked(PyQt_PyObject=item.data)
		@emits onItemActivated(PyQt_PyObject=item.data)

	"""
	GarbageTypeName = "ListTableView"

	itemClicked = QtCore.pyqtSignal((object,))
	itemDoubleClicked = QtCore.pyqtSignal((object,))
	itemActivated = QtCore.pyqtSignal((object,))

	def __init__(self, parent, modul, fields=None, filter=None, *args, **kwargs):
		super(ListTableView, self).__init__(parent, *args, **kwargs)
		logger.debug("ListTableView.init: %r, %r, %r, %r", parent, modul, fields, filter)
		self.missingImage = QtGui.QImage(":icons/status/missing.png")
		self.modul = modul
		filter = filter or {}
		self.structureCache = None
		model = ListTableModel(self.modul, fields or ["name"], filter)
		self.setDragEnabled(True)
		self.setAcceptDrops(True)  # Needed to receive dragEnterEvent, not actually wanted
		self.setSelectionBehavior(self.SelectRows)
		# self.setDragDropMode(self.InternalMove)
		# self.setDragDropOverwriteMode(False)
		self.setWordWrap(True)
		# self.setDropIndicatorShown(True)
		# self.setSelectionMode(self.SingleSelection)
		# self.setDefaultDropAction(QtCore.Qt.MoveAction)
		self.setModel(model)
		# self.setContentsMargins(0, 0, 0, 0)

		header = self.horizontalHeader()
		header.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		header.customContextMenuRequested.connect(self.tableHeaderContextMenuEvent)
		self.verticalHeader().hide()
		# self.connect( event, QtCore.SIGNAL("listChanged(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"),
		# self.onListChanged )
		model.rebuildDelegates.connect(self.rebuildDelegates)
		model.layoutChanged.connect(self.realignHeaders)
		self.clicked.connect(self.onItemClicked)
		self.doubleClicked.connect(self.onItemDoubleClicked)

	def onItemClicked(self, index):
		try:
			self.itemClicked.emit(self.model().getData()[index.row()])
		except IndexError:
			# someone probably clicked on the 'loading more' row - but why the the row stays so long
			pass

	def onItemDoubleClicked(self, index):
		self.itemDoubleClicked.emit(self.model().getData()[index.row()])

	# self.emit( QtCore.SIGNAL("onItemDoubleClicked(PyQt_PyObject)"), self.model().getData()[index.row()] )
	# self.emit( QtCore.SIGNAL("onItemActivated(PyQt_PyObject)"), self.model().getData()[index.row()] )

	def onListChanged(self, emitter, modul, itemID):
		"""
			Respond to changed Data - refresh our view
		"""
		if emitter == self:  # We issued this event - ignore it as we allready knew
			return
		if modul and modul != self.modul:  # Not our module
			return
		# Well, seems to affect us, refresh our view
		self.model().reload()

	def realignHeaders(self):
		"""
			Distribute space evenly through all displayed columns.
		"""
		width = self.size().width()
		for x in range(0, len(self.model().headers)):
			self.setColumnWidth(x, int(width / len(self.model().headers)))

	def rebuildDelegates(self, bones):
		"""
			(Re)Attach the viewdelegates to the table.
			@param data: Skeleton-structure send from the server
			@type data: dict
		"""
		logger.debug("ListTableView.rebuildDelegates - bones: %r", bones)
		self.delegates = []  # Qt doesn't take ownership of view delegates -> garbarge collected
		self.structureCache = bones
		modelHeaders = self.model().headers = []
		colum = 0
		modulFields = self.model().fields
		# logger.debug("rebuildDelegates: %r, %r", bones, modulFields)
		if not modulFields or modulFields == ["name"]:
			self.model()._validFields = fields = [key for key, value in bones.items()]
		else:
			fields = [x for x in modulFields if x in bones.keys()]
		for field in fields:
			modelHeaders.append(bones[field]["descr"])
			# Locate the best ViewDeleate for this colum
			delegateFactory = viewDelegateSelector.select(self.modul, field, self.structureCache)
			delegate = delegateFactory(self.modul, field, self.structureCache)
			self.setItemDelegateForColumn(colum, delegate)
			self.delegates.append(delegate)
			delegate.request_repaint.connect(self.repaint)
			colum += 1

	# logger.debug("ListTableModule.rebuildDelegates headers and fields: %r, %r, %r", modelHeaders, fields, colum)

	def keyPressEvent(self, e):
		if e.matches(QtGui.QKeySequence.Delete):
			rows = []
			for index in self.selectedIndexes():
				row = index.row()
				if row not in rows:
					rows.append(row)
			idList = []
			for row in rows:
				data = self.model().getData()[row]
				idList.append(data["key"])
			self.requestDelete(idList)
		elif e.key() == QtCore.Qt.Key_Return:
			for index in self.selectedIndexes():
				self.itemActivated.emit(self.model().getData()[index.row()])
		else:
			super(ListTableView, self).keyPressEvent(e)

	def tableHeaderContextMenuEvent(self, point):
		class FieldAction(QtWidgets.QAction):
			def __init__(self, key, name, *args, **kwargs):
				super(FieldAction, self).__init__(*args, **kwargs)
				self.key = key
				self.name = name
				self.setText(self.name)

		menu = QtWidgets.QMenu(self)
		activeFields = self.model().fields
		actions = []
		if not self.structureCache:
			return
		for key in self.structureCache.keys():
			action = FieldAction(key, self.structureCache[key]["descr"], self)
			action.setCheckable(True)
			action.setChecked(key in activeFields)
			menu.addAction(action)
			actions.append(action)
		selection = menu.exec_(self.mapToGlobal(point))
		if selection:
			self.model().setDisplayedFields([x.key for x in actions if x.isChecked()])

	def requestDelete(self, ids):
		if QtWidgets.QMessageBox.question(
				self,
				QtCore.QCoreApplication.translate("ListTableView", "Confirm delete"),
				QtCore.QCoreApplication.translate("ListTableView", "Delete %s entries?") % len(ids),
				QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
				QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.No:
			return
		protoWrap = protocolWrapperInstanceSelector.select(self.model().modul)
		assert protoWrap is not None
		protoWrap.deleteEntities(ids)

	def onProgessUpdate(self, request, done, maximum):
		if request.queryType == "delete":
			descr = QtCore.QCoreApplication.translate("ListTableView", "Deleting: %s of %s removed.")
		else:
			raise NotImplementedError()
		self.overlay.inform(self.overlay.BUSY, descr % (done, maximum))

	def onQuerySuccess(self, query):
		self.model().reload()
		event.emit(QtCore.SIGNAL("listChanged(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self, self.modul, None)
		self.overlay.inform(self.overlay.SUCCESS)

	def dragEnterEvent(self, event):
		"""Allow Drag&Drop to the outside (ie relationalBone)
		"""
		if event.source() == self:
			event.accept()
			tmpList = []
			for itemIndex in self.selectionModel().selection().indexes():
				tmpList.append(self.model().getData()[itemIndex.row()])
				tmpList[-1]["dataPosition"] = itemIndex.row()
			event.mimeData().setData("viur/listDragData", json.dumps({"entities": tmpList}).encode("utf-8"))
			event.mimeData().setUrls([urlForItem(self.model().modul, x) for x in tmpList])
		return super(ListTableView, self).dragEnterEvent(event)

	def dragMoveEvent(self, event):
		"""We need to have drops enabled to receive dragEnterEvents, so we can add our mimeData.

		Here we also check if we have a valid item as a drop target for internal move aka reordering for sortindex bones.
		"""
		if self.rowAt(event.pos().y()) is not -1:
			event.accept()
		else:
			event.ignore()

	def dropEvent(self, drop_event: QtGui.QDropEvent):
		try:
			model = self.model()
			totalItems = model.rowCount(None)
			srcModelIndex = self.currentIndex()
			sortIndexDataIndex = model._validFields.index("sortindex")
			srcModelIndex = model.index(srcModelIndex.row(), sortIndexDataIndex)
			destRowIndex = self.rowAt(drop_event.pos().y())
			destModelIndex = model.index(destRowIndex, sortIndexDataIndex)
			destRowSortIndex = model.data(destModelIndex, QtCore.Qt.DisplayRole)
			srcRowSortIndex = model.data(srcModelIndex, QtCore.Qt.DisplayRole)

			if (destRowIndex == totalItems - 1):
				# drop to last
				newSortIndex = time() + destRowSortIndex
				logger.debug("drop to last item: %r, %r, %r", totalItems, destRowIndex, destRowSortIndex)
			elif destRowIndex == 0:
				newSortIndex = destRowSortIndex
				logger.debug("drop to first item: %r, %r, %r", totalItems, destRowIndex, destRowSortIndex)
			else:
				if srcModelIndex.row() < destRowIndex:
					idx = -1
				else:
					idx = 1

				currentModelIndex = model.index(destRowIndex - idx, sortIndexDataIndex)
				currentSortIndex = model.data(currentModelIndex, QtCore.Qt.DisplayRole)
				newSortIndex = currentSortIndex + destRowSortIndex
				logger.debug("before item dropped: %r, %r", destRowIndex - idx, currentSortIndex)
			newSortIndex /= 2.0
			model.setSortIndex(srcModelIndex, newSortIndex)
			logger.debug("dropEvent: %r, %r, %r, %r", destRowIndex, destRowSortIndex, srcRowSortIndex, newSortIndex)
		except Exception as err:
			logger.exception(err)
		return super(ListTableView, self).dropEvent(drop_event)

	def getFilter(self):
		return self.model().getFilter()

	def setFilter(self, filter):
		self.model().setFilter(filter)

	def getModul(self):
		return self.model().getModul()

	def getSelection(self):
		"""
			Returns a list of items currently selected.
		"""
		return (
			[self.model().getData()[x] for x in set([x.row() for x in self.selectionModel().selection().indexes()])])

	def paintEvent(self, event):
		super(ListTableView, self).paintEvent(event)
		if not len(self.model().getData()):
			painter = QtGui.QPainter(self.viewport())
			painter.setRenderHint(QtGui.QPainter.Antialiasing)
			painter.drawImage((self.width() / 2 - self.missingImage.width() / 2),
			                  (self.height() / 2 - self.missingImage.height() / 2), self.missingImage)
			painter.pen().setWidth(1)
			painter.setPen(QtGui.QColor(0, 0, 0, 255))
			fm = QtGui.QFontMetrics(painter.font())
			msg = QtCore.QCoreApplication.translate("List", "No items in the current selection")
			fontWidth = fm.width(msg)
			painter.drawText(self.width() / 2 - fontWidth / 2, (self.height() / 2) + 55, msg)
			painter.end()


class ListWidget(QtWidgets.QWidget):
	itemClicked = QtCore.pyqtSignal((object,))
	itemDoubleClicked = QtCore.pyqtSignal((object,))
	itemActivated = QtCore.pyqtSignal((object,))

	defaultActions = {
		"list": [
			"add",
			"edit",
			"clone",
			"preview",
			"delete",
			"reload"],
		"list.order": [
			"add",
			"edit",
			"delete",
			"markpayed",
			"marksend",
			"markcanceled"
			"downloadbill",
			"downloaddeliverynote"]
	}

	def __init__(self, modul, config=None, fields=None, filter=None, actions=None, editOnDoubleClick=True, *args, **kwargs):
		super(ListWidget, self).__init__(*args, **kwargs)
		logger.debug("ListWidget.init: modul: %r, fields: %r, filter: %r", modul, fields, filter)
		self.modul = modul
		self.ui = Ui_List()
		self.ui.setupUi(self)
		layout = QtWidgets.QHBoxLayout(self.ui.tableWidget)
		layout.setContentsMargins(0, 0, 0, 0)
		self.ui.tableWidget.setLayout(layout)
		self.list = ListTableView(self.ui.tableWidget, modul, fields, filter)
		layout.addWidget(self.list)
		self.setContentsMargins(0,0,0,0)
		self.list.show()
		self.toolBar = QtWidgets.QToolBar(self)
		self.toolBar.setIconSize(QtCore.QSize(16, 16))
		self.ui.boxActions.addWidget(self.toolBar)
		# FIXME: testing changing to placeholder text
		# if filter is not None and "search" in filter.keys():
		# 	self.ui.editSearch.setText(filter["search"])
		self.config = config
		handler = self.config["handler"]
		try:
			handler = handler.split(".", 1)[0]
		except ValueError:
			pass
		all_actions = list()
		if handler in self.defaultActions.keys():
			all_actions.extend(self.defaultActions[handler])
		if actions is not None:
			all_actions.extend(actions)
		if not all_actions:  # Still None
			all_actions = self.defaultActions["list"]
		self.setActions(all_actions)
		if editOnDoubleClick:
			self.list.itemDoubleClicked.connect(self.openEditor)
		self.list.itemClicked.connect(self.itemClicked)
		self.list.itemDoubleClicked.connect(self.itemDoubleClicked)
		self.list.itemActivated.connect(self.itemActivated)
		# self.ui.splitter.setSizes([])
		# self.ui.splitter.splitterMoved.connect(self.list.realignHeaders)
		self.ui.extendedSearchArea.setVisible(False)
		self.ui.extendedSearchBTN.toggled.connect(self.toggleExtendedSearchArea)
		self.overlay = Overlay(self)
		protoWrap = protocolWrapperInstanceSelector.select(self.modul)
		assert protoWrap is not None
		protoWrap.busyStateChanged.connect(self.onBusyStateChanged)
		self.ui.searchBTN.released.connect(self.search)
		self.ui.editSearch.returnPressed.connect(self.search)
		self.ui.btnPrefixSearch.released.connect(self.doPrefixSearch)
		self.ui.btnPrefixSearch.setEnabled(
			"orderby" in self.list.model().getFilter().keys() and self.list.model().getFilter()["orderby"] == "name")
		self.ui.editSearch.textEdited.connect(self.prefixSearch)
		self.prefixSearchTimer = None
		self.extendedSearchPlugins = list()
		self.initExtendedSearchPlugins()

	# self.overlay.inform( self.overlay.BUSY )

	@QtCore.pyqtSlot(bool)
	def toggleExtendedSearchArea(self, checked):
		logger.debug("ext search state: %r", checked)
		if checked:
			self.ui.extendedSearchArea.setVisible(True)
		else:
			self.ui.extendedSearchArea.setVisible(False)

	def onBusyStateChanged(self, busy):
		if busy:
			self.overlay.inform(self.overlay.BUSY)
		else:
			self.overlay.clear()

	def setActions(self, actions):
		"""
			Sets the actions avaiable for this widget (ie. its toolBar contents).
			Setting None removes all existing actions
			@param actions: List of actionnames
			@type actions: List or None
		"""
		self.toolBar.clear()
		for a in self.actions():
			self.removeAction(a)
		if not actions:
			self._currentActions = []
			return
		self._currentActions = actions[:]
		for action in actions:
			if action == "|":
				self.toolBar.addSeparator()
			else:
				actionWdg = actionDelegateSelector.select("list.%s" % self.modul, action)
				if actionWdg is not None:
					actionWdg = actionWdg(self)
					if isinstance(actionWdg, QtWidgets.QAction):
						self.toolBar.addAction(actionWdg)
						self.addAction(actionWdg)
					else:
						self.toolBar.addWidget(actionWdg)

	def getActions(self):
		"""
			Returns a list of the currently activated actions on this list.
		"""
		return self._currentActions

	def search(self, *args, **kwargs):
		"""
			Start a search for the given string.
			If searchStr is None, it ends any currently active search.
			@param searchStr: Token to search for
			@type searchStr: String or None
		"""
		if self.prefixSearchTimer:
			self.killTimer(self.prefixSearchTimer)
			self.prefixSearchTimer = None
		self.list.model().search(self.ui.editSearch.text())

	def prefixSearch(self, *args, **kwargs):
		"""
			Trigger a prefix search for the current text is no key is
			pressed within the next 1500ms.
		"""
		if self.prefixSearchTimer:
			self.killTimer(self.prefixSearchTimer)
		self.prefixSearchTimer = self.startTimer(1500)

	def timerEvent(self, QTimerEvent):
		"""
			Perform the actual prefix search
		"""
		if QTimerEvent.timerId() != self.prefixSearchTimer:
			super(ListWidget, self).timerEvent(QTimerEvent)
		else:
			self.doPrefixSearch()

	def doPrefixSearch(self, *args, **kwargs):
		if self.prefixSearchTimer:
			self.killTimer(self.prefixSearchTimer)
			self.prefixSearchTimer = None
		self.list.model().prefixSearch(self.ui.editSearch.text())

	def getFilter(self):
		return self.list.getFilter()

	def setFilter(self, filter):
		self.list.setFilter(filter)

	def getModul(self):
		return self.list.getModul()

	def openEditor(self, item, clone=False):
		"""
			Open a new Editor-Widget for the given entity.
			@param item: Entity to open the editor for
			@type item: Dict
			@param clone: Clone the given entry?
			@type clone: Bool
		"""
		myHandler = WidgetHandler.mainWindow.handlerForWidget(self)  # Always stack them as my child
		assert myHandler is not None
		if clone:
			icon = QtGui.QIcon(":icons/actions/clone.svg")
			if self.list.modul in conf.serverConfig["modules"].keys() and "name" in conf.serverConfig["modules"][
				self.list.modul].keys():
				descr = QtCore.QCoreApplication.translate("List", "Clone: %s") % \
				        conf.serverConfig["modules"][self.list.modul]["name"]
			else:
				descr = QtCore.QCoreApplication.translate("List", "Clone entry")
		else:
			icon = QtGui.QIcon(":icons/actions/edit.png")
			if self.list.modul in conf.serverConfig["modules"].keys() and "name" in conf.serverConfig["modules"][
				self.list.modul].keys():
				descr = QtCore.QCoreApplication.translate("List", "Edit: %s") % \
				        conf.serverConfig["modules"][self.list.modul]["name"]
			else:
				descr = QtCore.QCoreApplication.translate("List", "Edit entry")
		modul = self.list.modul
		key = item["key"]
		handler = WidgetHandler(lambda: EditWidget(modul, EditWidget.appList, key, clone=clone), descr, icon)
		handler.mainWindow.addHandler(handler, myHandler)
		handler.focus()

	def requestDelete(self, ids):
		return self.list.requestDelete(ids)

	def getSelection(self):
		return self.list.getSelection()

	def initExtendedSearchPlugins(self):
		logger.debug("initExtendedSearchPlugins: %r", self.config.get("extendedFilters"))
		extendedSearchLayout = self.ui.extendedSearchArea.layout()
		if "extendedFilters" in self.config:
			for extension in self.config["extendedFilters"]:
				wdg = extendedSearchWidgetSelector.select(extension)
				if wdg:
					self.extendedSearchPlugins.append(wdg(extension, self))
					count = extendedSearchLayout.count()
					extendedSearchLayout.insertWidget(count - 1, self.extendedSearchPlugins[-1])

		self.ui.extendedSearchBTN.setVisible(len(self.extendedSearchPlugins) > 0)


class CsvExportWidget(QtWidgets.QWidget):
	appList = "list"
	appHierarchy = "hierarchy"
	appTree = "tree"
	appSingleton = "singleton"

	def __init__(self, module, model, *args, **kwargs):
		"""
			Initialize a new Edit or Add-Widget for the given module.
			@param module: Name of the module
			@type module: str
			@param model: The ListTableModel instance
			@type model: ListTableModel
		"""
		super(CsvExportWidget, self).__init__(*args, **kwargs)
		self.module = module
		self.model = model
		self.ui = Ui_CsvExport()
		self.ui.setupUi(self)
		_translate = QtCore.QCoreApplication.translate
		oldlang = conf.adminConfig.get("language", "de")
		active = 0
		if "viur.defaultlangsvalues" in conf.serverConfig:
			for ix, (key, lang) in enumerate(conf.serverConfig["viur.defaultlangsvalues"].items()):
				if key == oldlang:
					active = ix
				self.ui.langComboBox.addItem(lang, key)
		else:
			self.ui.langComboBox.addItem("Deutsch", "de")
		self.ui.langComboBox.setCurrentIndex(active)

		protoWrap = protocolWrapperInstanceSelector.select(module)
		assert protoWrap is not None

		self.bones = {}
		self.closeOnSuccess = False
		self._lastData = {}  # Dict of structure and values received
		self.isLoading = 0
		self.cursor = None
		self.completeList = False
		self.dataCache = list()
		self.count = 0
		okButton = self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok)
		okButton.released.connect(self.onTriggered)
		cancelButton = self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel)
		cancelButton.released.connect(self.onBtnCloseReleased)
		self.ui.filenameName.setText(
			os.path.expanduser("~/export-{0}-{1}.csv".format(self.module, datetime.now().strftime("%Y%m%d%H%M"))))
		self.fileAction = QtWidgets.QAction(self)
		self.ui.filenameDialogAction.setDefaultAction(self.fileAction)
		self.ui.filenameDialogAction.setText(_translate("CsvExport", "..."))
		self.ui.filenameDialogAction.triggered.connect(self.onChooseOutputFile)

	def onTriggered(self):
		# self.overlay = Overlay(self)
		# self.overlay.inform(self.overlay.BUSY)
		path = self.ui.filenameName.text()
		logger.debug("path: %r", path)
		if not path:
			return

		protoWrap = protocolWrapperInstanceSelector.select(self.module)
		assert protoWrap is not None
		protoWrap.queryResultAvailable.connect(self.addData)
		self.loadNext()

	def loadNext(self):
		if self.isLoading:
			logger.debug("stopping loadNext since it's already loading")
			return
		self.isLoading += 1
		rawFilter = self.model.filter.copy() or {}
		if self.cursor:
			rawFilter["cursor"] = self.cursor
		elif self.dataCache:
			invertedOrderDir = False
			if "orderdir" in rawFilter.keys() and str(rawFilter["orderdir"]) == "1":
				invertedOrderDir = True
			if rawFilter["orderby"] in self.dataCache[-1].keys():
				if invertedOrderDir:
					rawFilter[rawFilter["orderby"] + "$lt"] = self.dataCache[-1][rawFilter["orderby"]]
				else:
					rawFilter[rawFilter["orderby"] + "$gt"] = self.dataCache[-1][rawFilter["orderby"]]
		protoWrap = protocolWrapperInstanceSelector.select(self.module)
		assert protoWrap is not None
		rawFilter["amount"] = 20
		self.loadingKey = protoWrap.queryData(**rawFilter)

	def addData(self, queryKey):
		self.isLoading -= 1
		if queryKey is not None and queryKey != self.loadingKey:  # The Data is for a list we don't display anymore
			return
		protoWrap = protocolWrapperInstanceSelector.select(self.module)
		assert protoWrap is not None
		cacheTime, skellist, cursor = protoWrap.dataCache[queryKey]
		for item in skellist:  # Insert the new Data at the corresponding Position
			self.dataCache.append(item)
		self.cursor = cursor
		self.loadingKey = None
		count = len(skellist)
		self.count += count
		self.ui.countLabel.setText(str(self.count))
		if count < 20:
			self.completeList = True
			self.serializeToCsv(self.dataCache, protoWrap.viewStructure)
			self.model.dataCache = self.dataCache
			self.model.layoutChanged.emit()
			event.emit('popWidget', self)
		else:
			self.loadNext()

	def onChooseOutputFile(self, action=None):
		logger.debug("onChooseOutputFile %r", action)
		dialog = QtWidgets.QFileDialog(self, directory=os.path.expanduser("~"))
		dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
		dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
		dialog.setDefaultSuffix("csv")
		if dialog.exec_():
			try:
				self.ui.filenameName.setText(dialog.selectedFiles()[0])
			except Exception as err:
				logger.exception(err)

	def serializeToCsv(self, data, bones):
		f = open(self.ui.filenameName.text(), "w")
		writer = csv.writer(f, delimiter=";", quoting=csv.QUOTE_ALL)

		delegates = []
		fields = bones.keys()
		headers = list()
		oldlang = conf.adminConfig.get("language", "de")
		newlang = self.ui.langComboBox.currentData()
		try:
			conf.adminConfig["language"] = newlang
			for field in fields:
				# Locate the best ViewDeleate for this column
				delegateFactory = viewDelegateSelector.select(self.module, field, bones)
				delegate = delegateFactory(self.module, field, bones)
				delegates.append(delegate)
				headers.append(bones[field]["descr"])

			writer.writerow(headers)
			for row in data:
				result = list()
				for column, field in enumerate(fields):
					delegate = delegates[column]
					value = row.get(field, "")
					if value:
						result.append(delegate.displayText(value, QtCore.QLocale()))
					else:
						result.append("")
				writer.writerow(result)
			for i in delegates:
				i.deleteLater()
		except Exception as err:
			logger.exception(err)
		finally:
			if "language" in conf.adminConfig:
				conf.adminConfig["language"] = oldlang

	def onBtnCloseReleased(self, *args, **kwargs):
		event.emit("popWidget", self)
