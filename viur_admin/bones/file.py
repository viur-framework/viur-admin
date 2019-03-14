# -*- coding: utf-8 -*-

from viur_admin.log import getLogger

logger = getLogger(__name__)

from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.bones.base import BaseViewBoneDelegate
from viur_admin.bones.treeitem import TreeItemBone, TreeBoneSelector
from viur_admin.bones.relational import InternalEdit
from viur_admin.network import RemoteFile
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector
from viur_admin.priorityqueue import protocolWrapperInstanceSelector
from viur_admin.utils import formatString
from viur_admin.widgets.file import FileWidget
from viur_admin.widgets.selectedFiles import SelectedFilesWidget


class FileViewBoneDelegate(BaseViewBoneDelegate):
	cantSort = True

	def __init__(self, modul, boneName, structure):
		super(FileViewBoneDelegate, self).__init__(modul, boneName, structure)
		if not hasattr(self, "cache"):
			self.cache = dict()
		self.format = "$(name)"
		self.structure = structure
		if "format" in structure[boneName].keys():
			self.format = structure[boneName]["format"]

	def setImage(self, remoteFile):
		fn = remoteFile.getFileName()
		try:
			self.cache[remoteFile.dlKey] = QtGui.QImage(fn)
		except:
			pass
		self.request_repaint.emit()

	def paint(self, painter, option, index):
		model = index.model()
		try:
			index_column = index.column()
			model_fields = model.fields[index_column]
			index_row = index.row()
			cache_row = model.dataCache[index_row]
			record = cache_row[model_fields]
			if record and isinstance(record, list) and len(record) > 0:
				record = record[0]
		except (IndexError, KeyError) as err:
			record = None
		if not record:
			return super(FileViewBoneDelegate, self).paint(painter, option, index)

		if record["dest"]["dlkey"] not in self.cache.keys():
			self.cache[record["dest"]["dlkey"]] = None
			RemoteFile(record["dest"]["dlkey"], successHandler=self.setImage)
			return super(FileViewBoneDelegate, self).paint(painter, option, index)
		elif not self.cache[record["dest"]["dlkey"]]:  # Image not loaded yet
			return super(FileViewBoneDelegate, self).paint(painter, option, index)
		painter.save()
		painter.drawImage(option.rect, self.cache[record["dest"]["dlkey"]])
		painter.restore()

	def displayText(self, value, locale):
		return formatString(self.format, value, self.structure)


class MultiItemWidget(QtWidgets.QWidget):
	def __init__(self, text, parent=None):
		super(MultiItemWidget, self).__init__(parent)
		self.previewImage = QtWidgets.QLabel(self)
		self.previewImage.hide()
		self.label = QtWidgets.QLabel(self)
		self.label.setText(text)
		self.rowLayout = QtWidgets.QHBoxLayout(self)
		self.rowLayout.addWidget(self.previewImage)
		self.rowLayout.addWidget(self.label)

	def loadIconFromRequest(self, request):
		preview = QtGui.QIcon(request.getFileName())
		self.previewImage.setPixmap(preview.pixmap(QtCore.QSize(32, 32)))
		self.previewImage.show()


class FileItemBone(TreeItemBone):
	skelType = "leaf"

	def onAddBtnReleased(self, *args, **kwargs):
		editWidget = FileBoneSelector(
			self.moduleName,
			self.boneName,
			self.multiple,
			self.toModul,
			self.selection,
			parent=self)
		editWidget.selectionChanged.connect(self.setSelection)

	def loadIconFromRequest(self, request):
		# this former code should be inspected where and why we attached a icon to self
		# TODO: where self.previewIcon was defined before?
		# icon = QtGui.QIcon(request.getFileName())
		# if not self.previewIcon:
		# 	self.previewIcon = QtWidgets.QLabel(self)
		# 	self.previewIcon.setPixmap(icon.pixmap(QtCore.QSize(32, 32)))
		# 	self.layout.insertWidget(0, self.previewIcon)
		# else:
		# 	self.previewIcon.setPixmap(icon.pixmap(QtCore.QSize(32, 32)))

		preview = QtGui.QIcon(request.getFileName())
		label = self.layout.itemAt(0).widget()
		if not isinstance(label, QtWidgets.QLabel):
			label = QtWidgets.QLabel(self)
			label.setPixmap(preview.pixmap(QtCore.QSize(32, 32)))
			self.layout.insertWidget(0, label)
		else:
			label.setPixmap(preview.pixmap(QtCore.QSize(32, 32)))

	def updateVisiblePreview(self):
		protoWrap = protocolWrapperInstanceSelector.select(self.toModul)
		assert protoWrap is not None
		structure = None
		if self.skelType is None:
			structure = protoWrap.viewStructure
		elif self.skelType == "leaf":
			structure = protoWrap.viewLeafStructure
		elif self.skelType == "node":
			structure = protoWrap.viewNodeStructure
		if structure is None:
			return
		if self.using:
			if self.multiple:
				widgetItem = self.previewLayout.takeAt(0)
				while widgetItem:
					widgetItem = self.previewLayout.takeAt(0)
				if self.selection and len(self.selection) > 0:
					for item in self.selection:
						item = InternalEdit(self, self.using, formatString(self.format, item, structure), item, {})
						item.show()
						self.previewLayout.addWidget(item)
						self.internalEdits.append(item)
					self.addBtn.setText("Auswahl ändern")
				else:
					self.addBtn.setText("Dateien auswählen")
			else:
				if self.selection:
					logger.debug("selection: %r", self.selection)
					if self.selection["dest"]["mimetype"].startswith("image/"):
						RemoteFile(self.selection["dest"]["dlkey"], successHandler=self.loadIconFromRequest)
					self.entry.setText(formatString(self.format, self.selection, structure))
				else:
					self.entry.setText("")
		else:
			if self.multiple:
				widgetItem = self.previewLayout.takeAt(0)
				while widgetItem:
					widgetItem = self.previewLayout.takeAt(0)
				if self.selection and len(self.selection) > 0:
					for item in self.selection:
						lbl = MultiItemWidget(formatString(self.format, item, structure), parent=self.previewWidget)
						if item["dest"]["mimetype"].startswith("image/"):
							RemoteFile(item["dest"]["dlkey"], successHandler=lbl.loadIconFromRequest)
						self.previewLayout.addWidget(lbl)
					self.addBtn.setText("Auswahl ändern")
				else:
					self.addBtn.setText("Dateien auswählen")
			else:
				if self.selection:
					logger.debug("selection: %r", self.selection)
					if self.selection["dest"]["mimetype"].startswith("image/"):
						RemoteFile(self.selection["dest"]["dlkey"], successHandler=self.loadIconFromRequest)
					self.entry.setText(formatString(self.format, self.selection, structure))
				else:
					self.entry.setText("")


class FileBoneSelector(TreeBoneSelector):
	displaySourceWidget = FileWidget
	displaySelectionWidget = SelectedFilesWidget

	def keyPressEvent(self, e):
		"""Handle multiple selection via return or enter key press"""

		if self.multiple and e.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
			self.selection.extend([item.entryData for item in self.list.selectedItems()])
		else:
			super(FileBoneSelector, self).keyPressEvent(e)


def CheckForFileBone(moduleName, boneName, skelStucture):
	return skelStucture[boneName]["type"].startswith("treeitem.file")


# Register this Bone in the global queue
editBoneSelector.insert(4, CheckForFileBone, FileItemBone)
viewDelegateSelector.insert(4, CheckForFileBone, FileViewBoneDelegate)
