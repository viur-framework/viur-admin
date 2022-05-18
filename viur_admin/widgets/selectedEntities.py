# -*- coding: utf-8 -*-
import json
from typing import Dict, Any, List, Union

from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.priorityqueue import viewDelegateSelector, protocolWrapperInstanceSelector


from viur_admin.log import getLogger
logger = getLogger(__name__)


class SelectedEntitiesTableModel(QtCore.QAbstractTableModel):
	"""
		The model holding the currently selected entities.
	"""

	def __init__(
			self,
			parent: QtWidgets.QWidget,
			module: str,
			selection: List[Dict[str, Any]],
			skelType: str = None,
			*args: Any,
			**kwargs: Any):
		"""
			:param parent: Our parent widget.
			:param module: Name of the module which items were going to display.
			:param selection: Currently selected items.
		"""
		super(SelectedEntitiesTableModel, self).__init__(parent, *args, **kwargs)
		logger.debug("SelectedEntitiesTableModel.init: %r, %r, %r, %r", parent, module, selection, skelType)
		self.module = self.realModule = module
		if module.endswith("_rootNode"):
			self.realModule = module[:-9]
		self.dataCache: List[Any] = []
		self.fields = ["name", "foo"]
		self.headers: List[Any] = []
		self.skelType = skelType
		self.entryFetches: List[Any] = []  # List of fetch-Tasks we issued
		protoWrap = protocolWrapperInstanceSelector.select(self.realModule)
		assert protoWrap is not None
		#structureCache = protoWrap.editStructure
		# print("model init structure", structureCache)
		protoWrap.entityAvailable.connect(self.onItemDataAvailable)
		for item in (selection or []):
			self.addItem(item)

	def addItem(self, item: Union[Dict[str, Any], str]) -> None:
		"""
			Adds an item to the model.
			The only relevant information is item["key"], the rest is freshly fetched from the server.
			@param item: The new item
			@type item: Dict or String
		"""

		self.layoutAboutToBeChanged.emit()
		self.dataCache.append(item)
		self.layoutChanged.emit()
		return #FIXME? - is the onItemDataAvailable dance still needed?
		protoWrap = protocolWrapperInstanceSelector.select(self.realModule)
		assert protoWrap is not None
		if not item:
			return
		if isinstance(item, dict):
			if "dest" in item:
				key = item["dest"]["key"]
			elif "key" in item:
				key = item["key"]
			else:
				raise NotImplementedError("Unknown item format: %s" % item)
			if "_type" in item:
				self.entryFetches.append(protoWrap.queryEntry(key, item["_type"]))
			else:
				if self.skelType:
					self.entryFetches.append(protoWrap.queryEntry(key, self.skelType))
				else:
					self.entryFetches.append(protoWrap.queryEntry(key))
		elif isinstance(item, str):
			if self.skelType is not None:
				self.entryFetches.append(protoWrap.queryEntry(item, self.skelType))
			else:
				self.entryFetches.append(protoWrap.queryEntry(item))
		else:
			logger.debug("SelectedEntities.addItem: unhandled instance type: %r", item, type(item))
			raise NotImplementedError()
		# self.entryFetches.append( protoWrap.queryEntry( id ) )
		# NetworkService.request("/%s/view/%s" % (self.module, id), successHandler= self.onItemDataAvailable )

	def onItemDataAvailable(self, item: Dict[str, Any]) -> None:
		"""
			Fetching the updated information from the server finished.
			Start displaying that item.
		"""
		protoWrap = protocolWrapperInstanceSelector.select(self.realModule)
		assert protoWrap is not None
		if item is None or not item["key"] in self.entryFetches:
			return
		self.entryFetches.remove(item["key"])
		self.layoutAboutToBeChanged.emit()
		self.dataCache.append(item)
		self.layoutChanged.emit()

	def rowCount(self, parent: QtCore.QModelIndex = None) -> int:
		if not self.dataCache:
			return 0
		return len(self.dataCache)

	def columnCount(self, parent: QtCore.QModelIndex = None) -> int:
		return len(self.headers)

	def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.DisplayRole) -> Any:
		if not index.isValid():
			return None
		elif role != QtCore.Qt.DisplayRole:
			return None
		if 0 <= index.row() < len(self.dataCache):
			return self.dataCache[index.row()][self.fields[index.column()]]

	def headerData(self, col: int, orientation: QtCore.Qt.Orientation, role: int = None) -> Any:
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			return self.headers[col]
		return None

	def removeItemAtIndex(self, index: QtCore.QModelIndex) -> None:
		if not index.isValid() or index.row() >= len(self.dataCache):
			return
		self.layoutAboutToBeChanged.emit()
		self.dataCache.pop(index.row())
		self.layoutChanged.emit()

	def getData(self) -> List[Dict[str, Any]]:
		return self.dataCache

	def clear(self) -> None:
		self.layoutAboutToBeChanged.emit()
		self.dataCache.clear()
		self.layoutChanged.emit()


class SelectedEntitiesWidget(QtWidgets.QTableView):
	"""
		Displayes the currently selected entities of one relationalBone.
	"""
	skelType = None

	def __init__(
			self,
			module: str,
			selection: Dict[str, Any] = None,
			skelType: str = None,
			*args: Any,
			**kwargs: Any):
		"""
			@param parent: Parent-Widget
			@type parent: QWidget
			@param module: Modul which entities we'll display. (usually "file" in this context)
			@type module: String
			@param selection: Currently selected Items.
			@type selection: List-of-Dict, Dict or None
		"""
		logger.debug("SelectedEntitiesWidget.init - start: %r, %r, %r", module, selection, skelType)
		assert skelType in [None, "node", "leaf"]
		super(SelectedEntitiesWidget, self).__init__(*args, **kwargs)
		self.module = self.realModule = module
		if module.endswith("_rootNode"):
			self.realModule = module[:-9]
		self.selection = selection or list()
		self.delegates: List[Any] = list()  # Qt does not take ownership of view delegates -> garbage collected
		# self.skelType = skelType
		if selection and not isinstance(self.selection, list):  # This was a singleSelection before
			self.selection = [self.selection]
		self.setModel(SelectedEntitiesTableModel(self, self.module, self.selection, self.skelType))
		self.setAcceptDrops(True)
		self.doubleClicked.connect(self.onItemDoubleClicked)
		self.rebuildDelegates()

	# self.connect( self, QtCore.SIGNAL("itemDoubleClicked (QListWidgetItem *)"), self.itemDoubleClicked )
	# self.connect( self.model(), QtCore.SIGNAL("rebuildDelegates(PyQt_PyObject)"), self.rebuildDelegates )

	def rebuildDelegates(self) -> None:
		"""(Re)Attach the view delegates to the table.
		"""
		logger.debug("SelectedEntitiesWidget.rebuildDelegates - start:")
		protoWrap = protocolWrapperInstanceSelector.select(self.realModule)
		assert protoWrap is not None
		self.delegates = list()
		if self.skelType is None:
			structureCache = protoWrap.viewStructure
		elif self.skelType == "node":
			structureCache = protoWrap.viewNodeStructure
		elif self.skelType == "leaf":
			structureCache = protoWrap.viewLeafStructure
		else:
			structureCache = dict()
		self.model().headers = []
		colum = 0
		fields = [x for x in self.model().fields if x in structureCache]
		for field in fields:
			self.model().headers.append(structureCache[field]["descr"])
			# Locate the best ViewDeleate for this colum
			delegateFactory = viewDelegateSelector.select(self.realModule, field, structureCache)
			delegate = delegateFactory(self.realModule, field, structureCache)
			self.setItemDelegateForColumn(colum, delegate)
			self.delegates.append(delegate)
			delegate.request_repaint.connect(self.repaint)
			colum += 1

	def onItemDoubleClicked(self, index: QtCore.QModelIndex) -> None:
		"""
			One of our Items has been double-clicked.
			Remove it from the selection
		"""
		self.model().removeItemAtIndex(index)

	def set(self, selection: List[Dict[str, Any]]) -> None:
		"""
			Set our current selection to "selection".
			@param selection: The new selection
			@type selection: List-of-Dict, Dict or None
		"""
		self.model().clear()
		for s in selection:
			self.model().addItem(s)

	def extend(self, selection: List[Dict[str, Any]]) -> None:
		"""
			Append the given items to our selection.
			@param selection: New items
			@type selection: List
		"""
		for s in selection:
			self.model().addItem(s)

	def get(self) -> Any:
		"""
			Returns the currently selected items.
			@returns: List or None
		"""
		return self.model().getData()

	def dropEvent(self, event: QtGui.QDropEvent) -> None:
		"""
			We got a Drop! Add them to the selection if possible.
			All relevant informations are read from the URLs attached to this drop.
		"""
		mime = event.mimeData()
		if self.skelType is not None and mime.hasFormat("viur/treeDragData"):
			data = json.loads(mime.data("viur/treeDragData").data().decode("UTF-8"))
			self.extend(data[self.skelType + "s"])
		elif self.skelType is None and (
					mime.hasFormat("viur/listDragData") or mime.hasFormat("viur/hierarchyDragData")):
			if mime.hasFormat("viur/listDragData"):
				data = json.loads(mime.data("viur/listDragData").data().decode("UTF-8"))
			else:
				data = json.loads(mime.data("viur/hierarchyDragData").data().decode("UTF-8"))
			self.extend(data["entities"])

	def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
		event.accept()

	def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
		mime = event.mimeData()
		if self.skelType is not None and mime.hasFormat("viur/treeDragData"):
			event.accept()
		elif self.skelType is None and (
					mime.hasFormat("viur/listDragData") or mime.hasFormat("viur/hierarchyDragData")):
			event.accept()
		else:
			event.ignore()

	def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
		"""
			Catch and handle QKeySequence.Delete.
		"""
		if e.matches(QtGui.QKeySequence.Delete):
			for index in self.selectionModel().selection().indexes():
				self.model().removeItemAtIndex(index)
		else:
			super(SelectedEntitiesWidget, self).keyPressEvent(e)
