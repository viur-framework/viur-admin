# -*- coding: utf-8 -*-
import csv
import json
from time import time
from typing import Sequence, Any, List, Dict, Callable

from PyQt5.QtCore import QModelIndex

from viur_admin.log import getLogger

logger = getLogger(__name__)

import os.path
from datetime import datetime
from PyQt5 import QtCore, QtGui, QtWidgets
from viur_admin.utils import Overlay, urlForItem
from viur_admin.event import event
from viur_admin.priorityqueue import viewDelegateSelector, protocolWrapperInstanceSelector, actionDelegateSelector, \
	extendedSearchWidgetSelector, editBoneSelector
from viur_admin.widgets.edit import EditWidget, ApplicationType
from viur_admin.utils import WidgetHandler, loadIcon
from viur_admin.ui.listUI import Ui_List
from viur_admin.ui.csvexportUI import Ui_CsvExport
from viur_admin.config import conf
from viur_admin.network import nam, RequestWrapper
from typing import Tuple


class ListTableModel(QtCore.QAbstractTableModel):
	"""Model for displaying data within a listView"""
	GarbageTypeName = "ListTableModel"
	_chunkSize = 25

	rebuildDelegates = QtCore.pyqtSignal((object,))
	listIsComplete = QtCore.pyqtSignal()

	def __init__(self, module: str, fields: List[str] = None, *, viewFilter: Dict[str, Any] = None,
	             parent: QtWidgets.QWidget = None):
		logger.debug("ListTableModel.init: %r, %r, %r, %r", module, fields, viewFilter, parent)
		QtCore.QAbstractTableModel.__init__(self, parent)
		self.module = module
		self.fields = fields
		# Due to miss-use, someone might request displaying fields which dont exists. These are the fields that are valid
		self._validFields: List[str] = list()
		self.filter = viewFilter or {}
		self.skippedkeys: List[str] = list()
		self.dataCache: List[Dict[str, Any]] = list()
		self.headers: List[Any] = []
		self.editableFields = set()
		self.pendingUpdates = set()  # List of keys we know have pending writes to the server
		self.bones = {}
		self.completeList = False  # Have we all items?
		self.isLoading = 0
		self.cursor = None
		self._rowCount = 0
		# As loading is performed in background, they might return results for a dataset which isn't displayed anymore
		self.loadingKey = None
		# Tuple of Sort-Properties we should include in queries (Bonename and ascending/descending)
		self.currentSortBone: Tuple[str, bool] = None
		protoWrap = protocolWrapperInstanceSelector.select(self.module)
		#self.protoWrap.insertRowsEvent.connect(self.onInsertRows)
		#self.protoWrap.removeRowsEvent.connect(self.onRemoveRows)
		#self.protoWrap.changeRowsEvent.connect(self.onChangeRows)
		#self.queryKey = self.protoWrap.registerQuery(self.filter.copy() or {})
		self.viewProxy = protoWrap.registerView(
			{"orderby": "changedate", "orderdir": "1"},
			{
				"beforeInsertRows": self.beforeInsertRows,
				"afterInsertRows": self.afterInsertRows,
				"beforeRemovetRows": self.beforeRemovetRows,
				"afterRemoveRows": self.afterRemoveRows,
				"rowChanged": self.rowChanged,
			 }
		)

	def canFetchMore(self, QModelIndex):
		return self.viewProxy.canFetchMore

	def fetchMore(self, QModelIndex):
		print("fetchMore")
		self.viewProxy.fetchMore()
		#protoWrap = protocolWrapperInstanceSelector.select(self.module)
		#protoWrap.requestNextBatch(self.queryKey)

	def beforeInsertRows(self, index: int, numRows:int):
		print("beforeInsertRows: %r, %r" % (index, numRows))

		if not self.bones:
			for key, bone in self.viewProxy.listWrapper.viewStructure.items():
				self.bones[key] = bone
			self._validFields = [x for x in self.fields if x in self.bones]
			self.fields = [x for x in self.fields if x in self._validFields]
			if not self.fields:  # Select the 10 first bones that do exist to prevent an empty table
				# Don't show these bones by default in the table
				systemBones = {"key","creationdate", "changedate", "viurCurrentSeoKeys"}
				self.fields = [x for x in self.bones if x not in systemBones][:10]
				self._validFields = self.fields[:]
			self.rebuildDelegates.emit(self.viewProxy.listWrapper.viewStructure)
			self.repaint()
		self.beginInsertRows(QModelIndex(), index, index + numRows - 1)
		self._rowCount += numRows
		#for rowIndex in range(row, row + count):
		#	self.dataCache.pop(rowIndex)

	def afterInsertRows(self, index: int, numRows:int):
		print("afterInsertRows: %r, %r" % (index, numRows))
		self.endInsertRows()
		return True

	def beforeRemovetRows(self, index, numRows):
		self.beginRemoveRows(QtCore.QModelIndex(), index, index + numRows - 1)
		self._rowCount -= numRows

	def afterRemoveRows(self, index, numRows):
		self.endRemoveRows()

	def rowChanged(self, index, numRows):
		self.dataChanged.emit(self.index(index, 0), self.index(index + numRows - 1, 999))

		#self.beginRemoveRows(QtCore.QModelIndex(), index, index + numRows - 1)
		#self._rowCount -= numRows
		#self.endRemoveRows()

	def updatingDataAvailable(self, reqId, data, wasInitial):
		"""
			Signal from the protocoll-wrapper that an add/edit request bounced back. Check if we have it
			in our pendingUpdates list and update accordingly
		"""
		print("updatingDataAvailable")
		if wasInitial:
			return
		try:
			errorKey = data["values"]["key"]
		except:
			errorKey = None
		for idx, entry in enumerate(self.dataCache):  # Check if we are displaying it right now
			if entry["key"] == errorKey:
				if idx not in self.pendingUpdates:
					return
				self.pendingUpdates.remove(idx)
				self.dataChanged.emit(self.index(idx, 0), self.index(idx, 999))
				self.msgBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information,
					QtCore.QCoreApplication.translate("ListTableView", "Updating failed"),
					QtCore.QCoreApplication.translate("ListTableView", "Updating of %s failed!") % entry["key"],
					(QtWidgets.QMessageBox.Ok),
				)
				self.msgBox.open()
				#QtWidgets.QMessageBox.warning(self.parent(), "Updating failed", "Updating of %s failed!" % entry["key"])
				print("warning up")


	def updatingFailed(self, key, *args, **kwargs):
		"""
			Callback from the protocolwrapper that an update failed, so remove it's pending update tag
		"""
		for idx, entry in enumerate(self.dataCache):  # Check if we are displaying it right now
			if entry["key"] == key:
				self.pendingUpdates.remove(idx)
				self.dataChanged.emit(self.index(idx, 0), self.index(idx, 999))

	def entityChanging(self, key: str):
		"""
			Callback from the protocolwrapper that an entry is about to be edited on the server side.
			Ensure we're only displaying "loading" while it's pending
		"""
		for idx, entry in enumerate(self.dataCache):  # Check if we are displaying it right now
			if entry["key"] == key:
				self.pendingUpdates.add(idx)
				self.dataChanged.emit(self.index(idx, 0), self.index(idx, 999))

	def updateSingleEntity(self, entryData: dict):
		"""
			Callback from the protocol-wrapper that a single entry had been changed.
			Check if we actually displaying that entry and if update our data and repaint it's cells
			:param entryData: Data of the changed entry as received from the server
		"""
		for idx, displayedEntry in enumerate(self.dataCache):
			if displayedEntry["key"] == entryData["key"]:  # We found that entry
				self.dataCache[idx] = entryData
				if idx in self.pendingUpdates:
					self.pendingUpdates.remove(idx)
				self.dataChanged.emit(self.index(idx, 0), self.index(idx, 999))
				break

	def entityDeleted(self, key: str):
		"""
			Event-Callback from protocolwrapper that the given entry has been deleted
		"""
		for entry in self.dataCache:
			if entry["key"] == key:
				idx = self.dataCache.index(entry)
				self.beginRemoveRows(QtCore.QModelIndex(), idx, idx)
				self.dataCache.remove(entry)
				self.endRemoveRows()
				break


	def removeRows__(self, row: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
		# logger.debug("removeRows: %r, %r, %r", row, count, parent)
		self.beginRemoveRows(QModelIndex(), row, row + count - 1)

		for rowIndex in range(row, row + count):
			self.dataCache.pop(rowIndex)

		self.endRemoveRows()
		return True

	def supportedDropActions(self) -> int:
		return QtCore.Qt.MoveAction | QtCore.Qt.TargetMoveAction

	def setDisplayedFields(self, fields: List[str]) -> None:
		"""
			Update the list of bones that are visible in this table.
			New fields are been appended to the right, as it's now possible that the user has rearranged
			the colums - so we can't rely on the bone-order in the skeleton.
		:param fields: The new list of bones to display
		"""
		print("setDisplayedFields")
		protoWrap = protocolWrapperInstanceSelector.select(self.module)
		assert protoWrap is not None
		for field in self.fields[:]:
			if field not in fields:  # Removed
				self.removeColumn(self.fields.index(field))
				self.fields.remove(field)
		for field in fields:
			if field not in self.fields:
				self.insertColumn(len(self.fields))
				self.fields.append(field)
		self.rebuildDelegates.emit(protoWrap.viewStructure)
		self.repaint()


	def setFilterbyName(self, filterName: str) -> None:
		self.name = filterName
		config = None  # getListConfig( self.module, filterName )
		if config:
			if "columns" in config:
				self.fields = config["columns"]
			if "filter" in config:
				self.filter = config["filter"]

	def setFilter(self, queryFilter: Dict[str, Any]) -> None:
		self.filter = queryFilter
		self.reload()

	def getFilter(self) -> None:
		return self.filter

	def getFields(self) -> None:
		return self.fields

	def getModul(self) -> None:
		return self.module

	def setSortColumn(self, boneName:str, descending: bool) -> None:
		if not boneName:
			self.currentSortBone = None
		else:
			self.currentSortBone = (boneName, descending)
		self.reload()

	def reload(self) -> None:
		self.beginRemoveRows(QtCore.QModelIndex(), 0, len(self.dataCache))
		self.dataCache = []
		self.completeList = False
		self.cursor = False
		#self.modelReset.emit()
		self.endRemoveRows()
		self.repaint()
		self.loadNext(True)

	def rowCount(self, parent: QModelIndex = None, *args: Any, **kwargs: Any) -> int:
		return self._rowCount

	def columnCount(self, parent: QModelIndex = None) -> int:
		try:
			return len(self.headers)
		except:
			return 0

	def data(self, index: QModelIndex, role: int = None) -> Any:
		if not index.isValid():
			return None
		elif role != QtCore.Qt.DisplayRole:
			return None
		return self.viewProxy.getRow(index.row())[self.fields[index.column()]]


	def headerData(self, col: int, orientation: int, role: int = None) -> Any:
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			return self.headers[col]
		return None

	def loadNext___(self, forceLoading: bool = False) -> None:
		protoWrap = protocolWrapperInstanceSelector.select(self.module)
		protoWrap.requestNextBatch(self.queryKey)
		return
		if self.isLoading and not forceLoading:
			return
		self.isLoading += 1
		rawFilter = self.filter.copy() or {}
		if self.cursor:
			rawFilter["cursor"] = self.cursor
		if self.currentSortBone:
			boneName, descending = self.currentSortBone
			rawFilter["orderby"] = boneName
			rawFilter["orderdir"] = "1" if descending else "0"
		#elif self.dataCache:  # FIXME(): Is this still a thing?
		#	invertedOrderDir = False
		#	if "orderdir" in rawFilter and str(rawFilter["orderdir"]) == "1":
		#		invertedOrderDir = True
		#	if "orderby" in rawFilter and rawFilter["orderby"] in self.dataCache[-1]:
		#		if invertedOrderDir:
		#			rawFilter[rawFilter["orderby"] + "$lt"] = self.dataCache[-1][rawFilter["orderby"]]
		#		else:
		#			rawFilter[rawFilter["orderby"] + "$gt"] = self.dataCache[-1][rawFilter["orderby"]]
		protoWrap = protocolWrapperInstanceSelector.select(self.module)
		assert protoWrap is not None
		# logger.debug("loadNext.chunk: %r, %r, %r", rawFilter, type(rawFilter), self._chunkSize)
		rawFilter["limit"] = self._chunkSize
		self.loadingKey = protoWrap.queryData(**rawFilter)

	def addData(self, queryKey: str) -> None:
		self.isLoading -= 1
		if queryKey is not None and queryKey != self.loadingKey:  # The Data is for a list we dont display anymore
			return
		protoWrap = protocolWrapperInstanceSelector.select(self.module)
		assert protoWrap is not None
		#cacheTime, skellist, cursor = protoWrap.dataCache[queryKey]
		skellist = [protoWrap.entryCache[x] for x in protoWrap.queryCache[queryKey]["skelkeys"]]
		cursor = protoWrap.queryCache[queryKey]["cursor"]
		# Rebuild our local cache of valid fields
		if not self.bones:
			for key, bone in protoWrap.viewStructure.items():
				self.bones[key] = bone
			self._validFields = [x for x in self.fields if x in self.bones]
			self.fields = [x for x in self.fields if x in self._validFields]
			if not self.fields:  # Select the 10 first bones that do exist to prevent an empty table
				# Don't show these bones by default in the table
				systemBones = {"key","creationdate", "changedate", "viurCurrentSeoKeys"}
				self.fields = [x for x in self.bones if x not in systemBones][:10]
				self._validFields = self.fields[:]
			self.rebuildDelegates.emit(protoWrap.viewStructure)
			self.repaint()
		self.beginInsertRows(QtCore.QModelIndex(), len(self.dataCache), len(self.dataCache) + len(skellist) - 1)
		self.dataCache.extend(skellist)
		self.endInsertRows()
		if not cursor:
			self.beginRemoveRows(QtCore.QModelIndex(), len(self.dataCache), len(self.dataCache))
			self.completeList = True
			self.endRemoveRows()
		self.cursor = cursor
		self.loadingKey = None
		if protoWrap.queryCache[queryKey].get("failed"):
			QtWidgets.QMessageBox.warning(self.parent(), "Failed", "A Network-Request failed")


	# self.emit(QtCore.SIGNAL("dataRecived()"))

	def repaint(self) -> None:  # Currently an ugly hack to redraw the table
		self.layoutAboutToBeChanged.emit()
		self.layoutChanged.emit()

	def getData(self, row: int) -> dict:
		return self.viewProxy.getRow(row)

	def sort(self, p_int: int, order: Any = None) -> None:
		return
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

	def search(self, searchStr: str) -> None:
		"""
			Start a search for the given string.
			If searchStr is None, it ends any currently active search.
			@param searchStr: Token to search for
			@type searchStr: String or None
		"""
		if searchStr:
			if "name$lk" in self.filter:
				del self.filter["name$lk"]
			self.filter["search"] = searchStr
			self.reload()
		else:
			if "search" in self.filter:
				del self.filter["search"]
			self.reload()

	def prefixSearch(self, searchStr: str) -> None:
		"""
			Merge the prefix search in our filter dict if possible.
			Does noting if the list isn't sorted by name.
		"""
		if "orderby" not in self.filter or not self.filter["orderby"] == "name":
			return
		if "search" in self.filter:
			del self.filter["search"]
		if not searchStr and "name$lk" in self.filter:
			del self.filter["name$lk"]
		if searchStr:
			self.filter["name$lk"] = searchStr
		self.reload()

	def flags(self, index: QModelIndex = None) -> QtCore.Qt.ItemFlags:
		defaultFlags = super(ListTableModel, self).flags(index)
		try:
			if self.fields[index.column()] in self.editableFields:
				defaultFlags |= QtCore.Qt.ItemIsEditable
		except:
			pass
		return defaultFlags

	def setSortIndex(self, index: QModelIndex, sortindex: float) -> None:
		protoWrap = protocolWrapperInstanceSelector.select(self.module)
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

	def __init__(
			self,
			parent: QtWidgets.QWidget,
			module: str,
			fields: List[str] = None,
			viewFilter: Dict[str, Any] = None,
			sortableBones: List[str] = None,
			*args: Any,
			**kwargs: Any):
		super(ListTableView, self).__init__(parent, *args, **kwargs)
		logger.error("ListTableView.init: %r, %r, %r, %r", parent, module, fields, viewFilter)
		self.missingImage = loadIcon("message-news")  # FIXME: QtGui.QImage(":icons/status/missing.png")
		self.module = module
		self.sortableBones = sortableBones
		# Which (if any) colum the table is sorted by. Tuple of column-index (0-based) and sortOrder (True for descending)
		self.currentSortColumn: Tuple[int, bool] = None
		# The default sort order that should be applied if none is set (can also be none)
		self.defaultSortColumn: Tuple[int, bool] = None
		viewFilter = viewFilter or dict()
		# Ref to the original filter we display as we might have to determine the default sort order provided in there
		self.defaultFilter = viewFilter.copy()
		self.structureCache = None
		self.delegates: List[Callable] = []  # Qt doesn't take ownership of view delegates -> garbarge collected
		model = ListTableModel(
			self.module,
			fields or ["name"],
			viewFilter=viewFilter)
		self.setDragEnabled(True)
		self.setAcceptDrops(True)  # Needed to receive dragEnterEvent, not actually wanted
		self.setSelectionBehavior(self.SelectRows)
		self.setWordWrap(True)
		self.setModel(model)
		header = self.horizontalHeader()
		header.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		header.customContextMenuRequested.connect(self.openContextMenuForColoum)
		self.verticalHeader().hide()
		model.rebuildDelegates.connect(self.rebuildDelegates)
		model.layoutChanged.connect(self.realignHeaders)
		self.clicked.connect(self.onItemClicked)
		self.doubleClicked.connect(self.onItemDoubleClicked)
		self.setEditTriggers(self.EditKeyPressed)
		self.horizontalHeader().setSectionsMovable(True)
		self.horizontalHeader().sectionClicked.connect(self.onHeaderClicked)
		self.editColums = set()  # Column numbers that currently are in always edit mode (clicking into will open the editor)



	def onHeaderClicked(self, idx: int) -> None:
		try:
			delegate = self.delegates[idx]
		except:
			return
		hasChanged = False
		if self.sortableBones and delegate.boneName in self.sortableBones:
			if self.currentSortColumn is None or self.currentSortColumn[0] != idx:
				# Sort by that colum, ascending
				self.currentSortColumn = (idx, False)
				hasChanged = True
			elif self.currentSortColumn[1] == False:
				# Was our colum, ascending; flip to descending
				self.currentSortColumn = (idx, True)
				hasChanged = True
			else: # Was our colum descending, set back to the default if needed
				if self.currentSortColumn and self.defaultSortColumn and \
						self.currentSortColumn[0] == self.defaultSortColumn[0] and self.defaultSortColumn[1]:
					self.currentSortColumn = (idx, False)
				else:
					self.currentSortColumn = None
				hasChanged = True
		if self.currentSortColumn is None and self.defaultSortColumn:
			self.currentSortColumn = self.defaultSortColumn
			if self.defaultSortColumn:
				try:
					delegate = self.delegates[self.defaultSortColumn[0]]
				except:
					return
			hasChanged = True
		if hasChanged:
			QtCore.QTimer.singleShot(1, self.applySortOrder)
			if self.currentSortColumn:
				self.model().setSortColumn(delegate.boneName, self.currentSortColumn[1])
			else:
				self.model().setSortColumn(None, False)
		elif self.sortableBones and delegate.boneName not in self.sortableBones:
			# No change had happen, but we need to reset the sort-indicator as qt deleted it
			QtCore.QTimer.singleShot(1, self.applySortOrder)


	def applySortOrder(self, *args, **kwargs):
		"""
			Pass the currently selected sort-order to the model and update the sort-indicator accordingly.
			Has to run deferred as we can't override the sortIndicator in onHeaderClick for some reason.
		"""
		if self.currentSortColumn:
			idx, descending = self.currentSortColumn
			self.horizontalHeader().setSortIndicatorShown(False)
			self.horizontalHeader().setSortIndicatorShown(True)

			self.horizontalHeader().setSortIndicator(idx, QtCore.Qt.AscendingOrder if not descending else QtCore.Qt.DescendingOrder)
		else:
			self.horizontalHeader().setSortIndicatorShown(False)




	def setColumEditMode(self, fieldName: str, editMode:bool):
		"""
			Sets the column displaying the given bonename to be always editable.
		"""
		if fieldName not in self.model().editableFields:
			return
		try:
			idx = self.model().fields.index(fieldName)
		except:  # That field is currently not on display
			return
		if editMode:
			self.editColums.add(idx)
		else:
			self.editColums.remove(idx)

	def getColumEditMode(self, fieldName: str) -> bool:
		"""
		:return: True if the given bone name is currenty in always edit mode
		"""
		if fieldName not in self.model().editableFields:
			return False
		try:
			idx = self.model().fields.index(fieldName)
		except:  # That field is currently not on display
			return False
		return idx in self.editColums


	def openContextMenuForColoum(self, pos: QtCore.QPoint):
		"""
			Selects the viewDelegate that's handling that colum and ask it to create the context menu
		"""
		self.delegates[self.columnAt(pos.x())].openContextMenu(pos, self)

	def onItemClicked(self, index: QModelIndex) -> None:
		if index.column() in self.editColums:
			self.edit(index)
			return
		try:
			self.itemClicked.emit(self.model().getData(index, QtCore.Qt.UserRole))
		except IndexError:
			# someone probably clicked on the 'loading more' row - but why the the row stays so long
			pass

	def onItemDoubleClicked(self, index: QModelIndex) -> None:
		self.itemDoubleClicked.emit(self.model().getData()[index.row()])

	# self.emit( QtCore.SIGNAL("onItemDoubleClicked(PyQt_PyObject)"), self.model().getData()[index.row()] )
	# self.emit( QtCore.SIGNAL("onItemActivated(PyQt_PyObject)"), self.model().getData()[index.row()] )

	def onListChanged(self, emitter: Any, module: str, itemID: Any) -> None:
		"""
			Respond to changed Data - refresh our view
		"""
		if emitter == self:  # We issued this event - ignore it as we allready knew
			return
		if module and module != self.module:  # Not our module
			return
		# Well, seems to affect us, refresh our view
		self.model().reload()

	def realignHeaders(self) -> None:
		"""Distribute space evenly through all displayed columns.
		"""

		width = self.size().width()
		for x in range(0, len(self.model().headers)):
			self.setColumnWidth(x, int(width / len(self.model().headers)))

	def rebuildDelegates(self, bones: Dict[str, Dict[str, Any]]) -> None:
		"""(Re)Attach the viewdelegates to the table.

		:param bones: Skeleton-structure send from the server
		"""
		#logger.debug("ListTableView.rebuildDelegates - bones: %r", bones)

		self.structureCache = bones
		modelHeaders = self.model().headers = []
		modulFields = self.model().fields
		# logger.debug("rebuildDelegates: %r, %r", bones, modulFields)
		#if not modulFields or modulFields == ["name"]:
		#	self.model()._validFields = fields = [key for key, value in bones.items()]
		#else:
		#	fields = [x for x in modulFields if x in bones]
		editableFields = set()
		self.defaultSortColumn = None
		self.horizontalHeader().setSortIndicatorShown(False)
		for colum, field in enumerate(modulFields):
			modelHeaders.append(bones[field]["descr"])
			# Locate the best ViewDeleate for this colum
			delegateFactory = viewDelegateSelector.select(self.module, field, self.structureCache)
			delegate = delegateFactory(self.module, field, self.structureCache)
			self.setItemDelegateForColumn(colum, delegate)
			self.delegates.append(delegate)
			#delegate.request_repaint.connect(self.repaint)
			if delegate.isEditable():
				editableFields.add(field)
			if self.defaultFilter.get("orderby") == field:
				self.defaultSortColumn = (colum, self.defaultFilter.get("orderdir")=="1")
				self.horizontalHeader().setSortIndicatorShown(True)
				qtSortOrder = QtCore.Qt.AscendingOrder if not self.defaultSortColumn[ 1] else QtCore.Qt.DescendingOrder
				self.horizontalHeader().setSortIndicator(self.defaultSortColumn[0], qtSortOrder)
		self.model().editableFields = editableFields

	# logger.debug("ListTableModule.rebuildDelegates headers and fields: %r, %r, %r", modelHeaders, fields, colum)

	def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
		if e.matches(QtGui.QKeySequence.Delete):
			rows: List[int] = list()
			for index in self.selectedIndexes():
				row = index.row()
				if row not in rows:
					rows.append(row)
			idList = []
			for row in rows:
				data = self.model().getData()[row]
				idList.append(data["key"])
			self.requestDelete(idList)
		#elif e.key() == QtCore.Qt.Key_Return and e.modifiers() == QtCore.Qt.AltModifier:
		#	print("ALT RETURN!!")
		#	for index in self.selectedIndexes():
		#		print(index)
		#		print(index.row())
		#		print(index.column())
		#		self.openPersistentEditor(index)
		#		break
		elif e.key() == QtCore.Qt.Key_Return:
			for index in self.selectedIndexes():
				self.itemActivated.emit(self.model().getData()[index.row()])
		else:
			super(ListTableView, self).keyPressEvent(e)

	def tableHeaderContextMenuEvent(self, point: QtCore.QPoint) -> None:
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

		menu = QtWidgets.QMenu(self)
		activeFields = self.model().fields
		actions: List[FieldAction] = []
		if not self.structureCache:
			return
		for key in self.structureCache:
			action = FieldAction(
				key,
				self.structureCache[key]["descr"],
				parent=self)
			action.setCheckable(True)
			action.setChecked(key in activeFields)
			menu.addAction(action)
			actions.append(action)
		selection = menu.exec_(self.mapToGlobal(point))
		if selection:
			self.model().setDisplayedFields([x.key for x in actions if x.isChecked()])

	def requestDelete(self, ids: Sequence[str]) -> None:
		self.requestDeleteBox = QtWidgets.QMessageBox(
			QtWidgets.QMessageBox.Question,
			QtCore.QCoreApplication.translate("ListTableView", "Confirm delete"),
			QtCore.QCoreApplication.translate("ListTableView", "Delete %s entries?") % len(ids),
			(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No),
			self
		)
		self.requestDeleteBox.buttonClicked.connect(self.reqDeleteCallback)
		self.requestDeleteBox.open()
		QtGui.QGuiApplication.processEvents()
		self.requestDeleteBox.adjustSize()
		self.requestDeleteBox.deleteList = ids

	def reqDeleteCallback(self, clickedBtn, *args, **kwargs):
		if clickedBtn == self.requestDeleteBox.button(self.requestDeleteBox.Yes):
			protoWrap = protocolWrapperInstanceSelector.select(self.model().module)
			assert protoWrap is not None
			protoWrap.deleteEntities(self.requestDeleteBox.deleteList)
		self.requestDeleteBox = None

	def onProgessUpdate(self, request: RequestWrapper, done: bool, maximum: int) -> None:
		if request.queryType == "delete":
			descr = QtCore.QCoreApplication.translate("ListTableView", "Deleting: %s of %s removed.")
		else:
			raise NotImplementedError()
		self.overlay.inform(self.overlay.BUSY, descr % (done, maximum))

	def onQuerySuccess(self, query: Any) -> None:
		self.model().reload()
		event.emit(QtCore.SIGNAL("listChanged(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self, self.module, None)
		self.overlay.inform(self.overlay.SUCCESS)

	def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
		"""Allow Drag&Drop to the outside (ie relationalBone)
		"""
		if event.source() == self:
			event.accept()
			tmpList = []
			for itemIndex in self.selectionModel().selection().indexes():
				tmpList.append(self.model().getData()[itemIndex.row()])
				tmpList[-1]["dataPosition"] = itemIndex.row()
			event.mimeData().setData("viur/listDragData", json.dumps({"entities": tmpList}).encode("utf-8"))
			event.mimeData().setUrls([urlForItem(self.model().module, x) for x in tmpList])
		return super(ListTableView, self).dragEnterEvent(event)

	def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
		"""We need to have drops enabled to receive dragEnterEvents, so we can add our mimeData.

		Here we also check if we have a valid item as a drop target for internal move aka reordering for sortindex bones.
		"""
		if self.rowAt(event.pos().y()) != -1:
			event.accept()
		else:
			event.ignore()

	def dropEvent(self, drop_event: QtGui.QDropEvent) -> None:
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

	def getFilter(self) -> Dict[str, Any]:
		return self.model().getFilter()

	def setFilter(self, filter: Dict[str, Any]) -> None:
		self.model().setFilter(filter)

	def getModul(self) -> str:
		return self.model().getModul()

	def getSelection(self) -> List[Dict[str, Any]]:
		"""
			Returns a list of items currently selected.
		"""
		return [self.model().getData(x) for x in set([x.row() for x in self.selectionModel().selection().indexes()])]

	def paintEvent_(self, event: QtGui.QPaintEvent) -> None:
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
			"reload",
		],
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

	def __init__(
			self,
			module: str,
			config: Any = None,
			fields: List[str] = None,
			filter: Dict[str, Any] = None,
			actions: List[str] = None,
			editOnDoubleClick: bool = True,
			*args: Any,
			**kwargs: Any):
		super(ListWidget, self).__init__(*args, **kwargs)
		logger.error("ListWidget.init: modul: %r, fields: %r, filter: %r", module, fields, filter)
		self.module = module
		if config is None:
			config = conf.serverConfig["modules"][module]
		self.config = config
		self._currentActions: List[str] = list()
		self.ui = Ui_List()
		self.ui.setupUi(self)
		layout = QtWidgets.QHBoxLayout(self.ui.tableWidget)
		layout.setContentsMargins(0, 0, 0, 0)
		self.ui.tableWidget.setLayout(layout)
		self.list = ListTableView(self.ui.tableWidget, module, fields, filter, sortableBones=self.config.get("sortableBones"))
		layout.addWidget(self.list)
		self.setContentsMargins(0, 0, 0, 0)
		self.list.show()
		self.toolBar = QtWidgets.QToolBar(self)
		self.toolBar.setIconSize(QtCore.QSize(32, 32))
		self.ui.boxActions.addWidget(self.toolBar)
		self.customActions = config["customActions"] if isinstance(config.get("customActions"), dict) else None
		# FIXME: testing changing to placeholder text
		# if filter is not None and "search" in filter:
		# 	self.ui.editSearch.setText(filter["search"])
		handler = self.config["handler"]
		try:
			handler = handler.split(".", 1)[0]
		except ValueError:
			pass
		all_actions = list()

		try:
			from viur_admin.module_overwrites import listDefaultActionsOverwrite
			self.defaultActions = listDefaultActionsOverwrite
		except ImportError:
			pass

		if handler in self.defaultActions:
			all_actions.extend(self.defaultActions[handler])
		if actions is not None:
			all_actions.extend(actions)
		if not all_actions:  # Still None
			all_actions = self.defaultActions["list"]
		if "selecttablerows" not in all_actions:
			all_actions.append("|")
			all_actions.append("selecttablerows")
		self.setActions(all_actions)
		try:
			from viur_admin.module_overwrites import listWidgetInstanceFlags
			editOnDoubleClick = listWidgetInstanceFlags["editOnDoubleClick"]
		except ImportError:
			pass

		if editOnDoubleClick:
			self.list.itemDoubleClicked.connect(self.openEditor)
		self.list.itemClicked.connect(self.itemClicked)
		self.list.itemDoubleClicked.connect(self.itemDoubleClicked)
		self.list.itemActivated.connect(self.itemActivated)
		# self.ui.splitter.setSizes([])
		# self.ui.splitter.splitterMoved.connect(self.list.realignHeaders)
		self.ui.extendedSearchArea.setVisible(False)
		self.overlay = Overlay(self)
		#protoWrap = protocolWrapperInstanceSelector.select(self.module)  #FIXME - Noch nötig?
		#assert protoWrap is not None
		#protoWrap.busyStateChanged.connect(self.onBusyStateChanged)
		self.ui.searchBTN.released.connect(self.search)
		self.ui.editSearch.returnPressed.connect(self.search)
		self.ui.editSearch.textEdited.connect(self.prefixSearch)
		self.prefixSearchTimer = None

	# self.overlay.inform( self.overlay.BUSY )

	@QtCore.pyqtSlot(bool)
	def toggleExtendedSearchArea(self, checked: bool) -> None:
		logger.debug("ext search state: %r", checked)
		if checked:
			self.ui.extendedSearchArea.setVisible(True)
		else:
			self.ui.extendedSearchArea.setVisible(False)

	def onBusyStateChanged(self, busy: bool) -> None:
		if busy:
			self.setDisabled(True)
			self.overlay.inform(self.overlay.BUSY)
		else:
			self.setDisabled(False)
			self.overlay.clear()

	def setActions(self, actions: List[str]) -> None:
		"""
			Sets the actions available for this widget (ie. its toolBar contents).
			Setting None removes all existing actions
			@param actions: List of actionnames
			@type actions: List or None
		"""
		self.toolBar.clear()
		for a in self.actions():
			self.removeAction(a)
		if not actions:
			self._currentActions = list()
			return

		self._currentActions = actions[:]
		for action in actions:
			if action == "|":
				self.toolBar.addSeparator()
			else:
				actionWdg = actionDelegateSelector.select("list.%s" % self.module, action)
				if actionWdg is not None:
					actionWdg = actionWdg(self)
					if isinstance(actionWdg, QtWidgets.QAction):
						self.toolBar.addAction(actionWdg)
						self.addAction(actionWdg)
					else:
						self.toolBar.addWidget(actionWdg)
				else:  # It may be a server-side defined action
					if self.customActions and action in self.customActions:
						print(self.customActions[action])
						actionWdg = CustomAction(self.customActions[action], ApplicationType.LIST, self)
						self.toolBar.addAction(actionWdg)
						self.addAction(actionWdg)

	def getActions(self) -> List[str]:
		"""
			Returns a list of the currently activated actions on this list.
		"""
		return self._currentActions

	def search(self, *args: Any, **kwargs: Any) -> None:
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

	def prefixSearch(self, *args: Any, **kwargs: Any) -> None:
		"""
			Trigger a prefix search for the current text is no key is
			pressed within the next 1500ms.
		"""
		if self.prefixSearchTimer:
			self.killTimer(self.prefixSearchTimer)
		self.prefixSearchTimer = self.startTimer(1500)

	def timerEvent(self, e: QtCore.QTimerEvent) -> None:
		"""
			Perform the actual prefix search
		"""
		if e.timerId() != self.prefixSearchTimer:
			super(ListWidget, self).timerEvent(e)
		else:
			self.doPrefixSearch()

	def doPrefixSearch(self, *args: Any, **kwargs: Any) -> None:
		if self.prefixSearchTimer:
			self.killTimer(self.prefixSearchTimer)
			self.prefixSearchTimer = None
		self.list.model().prefixSearch(self.ui.editSearch.text())

	def getFilter(self) -> Dict[str, Any]:
		return self.list.getFilter()

	def setFilter(self, filter: Dict[str, Any]) -> None:
		self.list.setFilter(filter)

	def getModul(self) -> str:
		return self.list.getModul()

	def openEditor(self, item: Dict[str, Any], clone: bool = False) -> None:
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
			icon = loadIcon("clone")
			if self.list.module in conf.serverConfig["modules"] and "name" in conf.serverConfig["modules"][
				self.list.module]:
				descr = QtCore.QCoreApplication.translate("List", "Clone: %s") % \
				        conf.serverConfig["modules"][self.list.module]["name"]
			else:
				descr = QtCore.QCoreApplication.translate("List", "Clone entry")
		else:
			icon = loadIcon("edit")
			if self.list.module in conf.serverConfig["modules"] and "name" in conf.serverConfig["modules"][
				self.list.module]:
				descr = QtCore.QCoreApplication.translate("List", "Edit: %s") % \
				        conf.serverConfig["modules"][self.list.module]["name"]
			else:
				descr = QtCore.QCoreApplication.translate("List", "Edit entry")
		modul = self.list.module
		key = item["key"]
		handler = WidgetHandler(lambda: EditWidget(modul, ApplicationType.LIST, key, clone=clone), descr, icon)
		handler.mainWindow.addHandler(handler, myHandler)
		handler.focus()

	def requestDelete(self, ids: Sequence[str]) -> None:
		logger.debug("requestDelete: %r", ids)
		self.list.requestDelete(ids)

	def prepareDeletion(self) -> None:
		logger.debug("ListWidget.prepareDeletion")
		pass

	def getSelection(self) -> Sequence:
		return self.list.getSelection()



class CsvExportWidget(QtWidgets.QWidget):
	appList = "list"
	appHierarchy = "hierarchy"
	appTree = "tree"
	appSingleton = "singleton"

	def __init__(self, module: str, model: ListTableModel, *args: Any, **kwargs: Any):
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

		# self.bones: Dict[str, Dict[str, Any]] = dict()
		self.closeOnSuccess = False
		# self._lastData = {}  # Dict of structure and values received
		self.isLoading = 0
		self.cursor = None
		self.completeList = False
		self.dataCache: List[Any] = list()
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

	def onTriggered(self) -> None:
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

	def loadNext(self) -> None:
		if self.isLoading:
			logger.debug("stopping loadNext since it's already loading")
			return
		self.isLoading += 1
		rawFilter = self.model.filter.copy() or {}
		if self.cursor:
			rawFilter["cursor"] = self.cursor
		elif self.dataCache:
			invertedOrderDir = False
			if "orderdir" in rawFilter and str(rawFilter["orderdir"]) == "1":
				invertedOrderDir = True
			if rawFilter["orderby"] in self.dataCache[-1]:
				if invertedOrderDir:
					rawFilter[rawFilter["orderby"] + "$lt"] = self.dataCache[-1][rawFilter["orderby"]]
				else:
					rawFilter[rawFilter["orderby"] + "$gt"] = self.dataCache[-1][rawFilter["orderby"]]
		protoWrap = protocolWrapperInstanceSelector.select(self.module)
		assert protoWrap is not None
		rawFilter["limit"] = 20
		self.loadingKey = protoWrap.queryData(**rawFilter)

	def addData(self, queryKey: Any) -> None:
		self.isLoading -= 1
		if queryKey is not None and queryKey != self.loadingKey:  # The Data is for a list we don't display anymore
			return
		protoWrap = protocolWrapperInstanceSelector.select(self.module)
		assert protoWrap is not None
		protoData = protoWrap.queryCache[queryKey]
		skellist = [protoWrap.entryCache[x] for x in protoData["skelkeys"]]
		cursor = protoData["cursor"]
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

	def onChooseOutputFile(self, action: Any = None) -> None:
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

	def serializeToCsv(self, data: List[Dict[str, Any]], bones: Dict[str, Dict[str, str]]) -> None:
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

	def onBtnCloseReleased(self, *args: Any, **kwargs: Any) -> None:
		event.emit("popWidget", self)


# Must be imported last to prevent circular imports
from viur_admin.actions.customAction import CustomAction
