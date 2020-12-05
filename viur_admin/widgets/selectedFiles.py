# -*- coding: utf-8 -*-
from typing import Any, List, Union, Dict

from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.pyodidehelper import isPyodide
from viur_admin.network import nam
from viur_admin.log import getLogger
from viur_admin.utils import itemFromUrl
from viur_admin.widgets.file import FileItem, PreviewDownloadWorker

logger = getLogger(__name__)


class SelectedFilesWidget(QtWidgets.QListWidget):
	"""
		Displays the currently selected files of one fileBone.
	"""

	requestPreview = QtCore.pyqtSignal(str)

	def __init__(
			self,
			module: str,
			selection: Union[List[Dict[str, Any]], Dict[str, Any], None] = None,
			*args: Any,
			**kwargs: Any):
		"""

		:param module: Modul which entities we'll display. (usually "file" in this context)
		:param selection: Currently selected Items.
		"""
		logger.debug("SelectedFilesWidget: %r, %r, %r, %r", module, selection, args, kwargs)
		super(SelectedFilesWidget, self).__init__(*args, **kwargs)
		if isinstance(selection, list):
			self.selection = selection and [s["dest"] for s in selection]
		elif isinstance(selection, dict):  # This was a singleSelection before
			self.selection = [selection["dest"]]
		else:
			self.selection = list()
		self.module = module
		self.itemCache: Dict[str, Any] = dict()
		self.setAcceptDrops(True)
		self.itemDoubleClicked.connect(self.onItemDoubleClicked)
		if not isPyodide:
			self.thread = QtCore.QThread(self)
			self.thread.setObjectName('SelectedFilesWidget.previewDownloadThread')
			self.previewDownloadWorker = PreviewDownloadWorker(nam.cookieJar().allCookies())
			self.previewDownloadWorker.previewImageAvailable.connect(self.onPreviewImageAvailable)
			self.previewDownloadWorker.moveToThread(self.thread)
			self.requestPreview.connect(self.previewDownloadWorker.onRequestPreviewImage)
			self.thread.started.connect(self.previewDownloadWorker.work)
			self.thread.start(QtCore.QThread.IdlePriority)
			self.destroyed.connect(self.previewDownloadWorker.onRequestStopRunning)
			self.thread.finished.connect(self.thread.deleteLater)
		for s in self.selection:
			self.addItem(FileItem(s, self))
		# raise Exception("here!!!")

	def prepareDeletion(self) -> None:
		self.previewDownloadWorker.onRequestStopRunning()
		self.thread.quit()
		self.thread.wait()

	@QtCore.pyqtSlot(str)
	def onRequestPreview(self, dlKey: str) -> None:
		logger.debug("SelectedFilesWidget.onRequestPreview: %r", dlKey)
		self.requestPreview.emit(dlKey)

	def onPreviewImageAvailable(self, dlkey: str, fileName: str, icon: QtGui.QIcon) -> None:
		logger.debug("SelectedFilesWidget.onPreviewImageAvailable: %r, %r, %r", dlkey, fileName, icon)
		fileItem = self.itemCache[dlkey]
		fileItem.setIcon(icon)
		width = 400
		fileItem.setToolTip('<img src="{0}" width="{1}"><br><strong>{2}</strong>'.format(
			fileName, width, str(fileItem.entryData["name"])))

	def addItem(self, aitem: Any) -> None:
		try:
			self.itemCache[aitem.entryData["dlkey"]] = aitem
		except:
			pass
		super(SelectedFilesWidget, self).addItem(aitem)

	def onItemDoubleClicked(self, item: Any) -> None:
		"""One of our Items has been double-clicked.

		Remove it from the selection
		"""
		try:
			itemKey = item.entryData["key"]
			for obj in self.selection[:]:
				logger.debug("obj: %r", obj)
				if obj["key"] == itemKey:
					self.selection.remove(obj)
					break
		except ValueError as err:
			pass
		self.clear()
		for s in self.selection:
			self.addItem(FileItem(s, self))

	def dropEvent(self, event: QtGui.QDropEvent) -> None:
		"""We got a Drop! Add them to the selection if possible.

		Files contain their dlkey instead of an id.
		Well check the events.source widget for more informations about the files,
		and add them only if we succed.
		"""
		mime = event.mimeData()
		if not mime.hasUrls():
			return
		for url in mime.urls():
			res = itemFromUrl(url)
			if not res:
				continue
			modul, dlkey, name = res
			if dlkey and modul != self.modul:
				continue
			srcWidget = event.source()
			if not srcWidget:  # Not dragged from this application
				continue
			items = srcWidget.selectedItems()
			for item in items:
				if "dlkey" in item.entryData and dlkey == item.entryData["dlkey"]:
					self.extend([item.entryData])
					break

	def set(self, selection: List[Any]) -> None:
		"""Set our current selection to "selection".

		:param selection: The new selection
		:type selection: list of dict, dict or None
		"""
		self.clear()
		self.selection = selection
		if isinstance(self.selection, dict):
			self.selection = [self.selection]
		for s in self.selection:
			self.addItem(FileItem(s, self))

	def extend(self, selection: List[Any]) -> None:
		"""Append the given items to our selection.

		:param selection: new items
		:type selection: list
		"""
		self.selection.extend(selection)
		for s in selection:
			self.addItem(FileItem(s, self))

	def get(self) -> List[Any]:
		"""Returns the currently selected items.

		:returns: list or None
		"""
		return self.selection

	def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
		event.accept()

	def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
		mime = event.mimeData()
		if not mime.hasUrls():
			event.ignore()
		if not any([itemFromUrl(x) for x in mime.urls()]):
			event.ignore()
		event.accept()

	def keyPressEvent(self, e: QtGui.QKeySequence) -> None:
		"""Catch and handle QKeySequence.Delete.
		"""

		if e.matches(QtGui.QKeySequence.Delete):
			for item in self.selectedItems():
				itemKey = item.entryData["key"]
				for obj in self.selection[:]:
					logger.debug("obj: %r", obj)
					if obj["key"] == itemKey:
						self.selection.remove(obj)
			self.clear()
			for s in self.selection:
				self.addItem(FileItem(s, self))
		else:
			super(SelectedFilesWidget, self).keyPressEvent(e)
