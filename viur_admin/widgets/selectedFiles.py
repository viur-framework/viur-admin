# -*- coding: utf-8 -*-
from PyQt5 import QtGui, QtWidgets

from viur_admin.utils import itemFromUrl
from viur_admin.log import getLogger
from viur_admin.widgets.file import FileItem

logger = getLogger(__name__)


class SelectedFilesWidget(QtWidgets.QListWidget):
	"""
		Displays the currently selected files of one fileBone.
	"""

	def __init__(self, modul, selection=None, *args, **kwargs):
		"""
			@param parent: Parent-Widget
			@type parent: QWidget
			@param modul: Modul which entities we'll display. (usually "file" in this context)
			@type modul: String
			@param selection: Currently selected Items.
			@type selection: List-of-Dict, Dict or None
		"""
		super(SelectedFilesWidget, self).__init__(*args, **kwargs)
		self.selection = selection or []
		self.modul = modul
		if isinstance(self.selection, dict):  # This was a singleSelection before
			self.selection = [self.selection]
		for s in self.selection:
			self.addItem(FileItem(s, self))
		self.setAcceptDrops(True)
		self.itemDoubleClicked.connect(self.onItemDoubleClicked)

	def onItemDoubleClicked(self, item):
		"""
			One of our Items has been double-clicked.
			Remove it from the selection
		"""
		logger.debug("selectedFiles.onItemDoubleClicked: %r, %r", item, self.selection)
		try:
			self.selection.remove(item.entryData)
		except ValueError as err:
			logger.debug("selectedItem should be in the selection list")
			pass
		self.clear()
		for s in self.selection:
			self.addItem(FileItem(s, self))

	def dropEvent(self, event):
		"""
			We got a Drop! Add them to the selection if possible.
			Files contain their dlkey instead of an id.
			Well check the events.source widget for more informations about the files,
			and add them only if we succed.
		"""
		logger.debug("selectedFiles.dropEvent: %r", event)
		mime = event.mimeData()
		if not mime.hasUrls():
			return
		for url in mime.urls():
			res = itemFromUrl(url)
			if not res:
				continue
			modul, dlkey, name = res
			if not id or modul != self.modul:
				continue
			srcWidget = event.source()
			if not srcWidget:  # Not dragged from this application
				continue
			items = srcWidget.selectedItems()
			for item in items:
				if "dlkey" in item.data.keys() and dlkey == item.data["dlkey"]:
					self.extend([item.data])
					break

	def set(self, selection):
		"""
			Set our current selection to "selection".
			@param selection: The new selection
			@type selection: List-of-Dict, Dict or None
		"""
		self.clear()
		self.selection = selection
		if isinstance(self.selection, dict):
			self.selection = [self.selection]
		for s in self.selection:
			self.addItem(FileItem(s, self))

	def extend(self, selection):
		"""
			Append the given items to our selection.
			@param selection: New items
			@type selection: List
		"""
		self.selection += selection
		for s in selection:
			self.addItem(FileItem(s, self))

	def get(self):
		"""
			Returns the currently selected items.
			@returns: List or None
		"""
		return self.selection

	def dragMoveEvent(self, event):
		event.accept()

	def dragEnterEvent(self, event):
		mime = event.mimeData()
		if not mime.hasUrls():
			event.ignore()
		if not any([itemFromUrl(x) for x in mime.urls()]):
			event.ignore()
		event.accept()

	def keyPressEvent(self, e):
		"""
			Catch and handle QKeySequence.Delete.
		"""
		if e.matches(QtGui.QKeySequence.Delete):
			for item in self.selectedItems():
				self.selection.remove(item.data)
			self.clear()
			for s in self.selection:
				self.addItem(FileItem(s, self))
		else:
			super(SelectedFilesWidget, self).keyPressEvent(e)
