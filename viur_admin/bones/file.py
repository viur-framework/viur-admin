# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.widgets.file import FileWidget
from viur_admin.bones.treeitem import TreeItemBone, TreeBoneSelector
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector
from viur_admin.priorityqueue import protocolWrapperInstanceSelector
from viur_admin.network import RemoteFile
from viur_admin.utils import formatString
from viur_admin.bones.base import BaseViewBoneDelegate


class FileViewBoneDelegate(BaseViewBoneDelegate):
	cantSort = True

	def __init__(self, modul, boneName, structure):
		super(FileViewBoneDelegate, self).__init__(modul, boneName, structure)
		self.format = "$(name)"
		if "format" in structure[boneName].keys():
			self.format = structure[boneName]["format"]

	def setImage(self, remoteFile):
		fn = remoteFile.getFileName()
		try:
			self.cache[remoteFile.dlKey] = QtGui.QImage(fn)
		except:
			pass
		self.request_repaint[int, QtCore.QObject].emit()

	def paint(self, painter, option, index):
		if not "cache" in dir(self):
			self.cache = {}
		model = index.model()
		try:
			record = model.dataCache[index.row()][model.fields[index.column()]]
			if record and isinstance(record, list) and len(record) > 0:
				record = record[0]
		except:
			record = None
		if not record:
			return (super(FileViewBoneDelegate, self).paint(painter, option, index))
		if not record["dlkey"] in self.cache.keys():
			self.cache[record["dlkey"]] = None
			RemoteFile(record["dlkey"], successHandler=self.setImage)
			return (super(FileViewBoneDelegate, self).paint(painter, option, index))
		elif not self.cache[record["dlkey"]]:  # Image not loaded yet
			return (super(FileViewBoneDelegate, self).paint(painter, option, index))
		painter.save()
		painter.drawImage(option.rect, self.cache[record["dlkey"]])
		painter.restore()

	def displayText(self, value, locale):
		return (formatString(self.format, self.structure, value))


class FileItemBone(TreeItemBone):
	skelType = "leaf"

	def onAddBtnReleased(self, *args, **kwargs):
		editWidget = FileBoneSelector(self.modulName, self.boneName, self.multiple, self.toModul, self.selection,
		                              parent=self)
		editWidget.selectionChanged.connect(self.setSelection)

	def loadIconFromRequest(self, request):
		preview = QtGui.QIcon(request.getFileName())
		label = QtWidgets.QLabel(self)
		label.setPixmap(preview.pixmap(QtCore.QSize(16, 16)))
		self.layout.insertWidget(0, label)

	def updateVisiblePreview(self):
		protoWrap = protocolWrapperInstanceSelector.select(self.toModul)
		assert protoWrap is not None
		if self.skelType is None:
			structure = protoWrap.viewStructure
		elif self.skelType == "leaf":
			structure = protoWrap.viewLeafStructure
		elif self.skelType == "node":
			structure = protoWrap.viewNodeStructure
		if structure is None:
			return
		if self.multiple:
			widgetItem = self.previewLayout.takeAt(0)
			while widgetItem:
				widgetItem = self.previewLayout.takeAt(0)
			if self.selection and len(self.selection) > 0:
				for item in self.selection:
					print("format", self.format, structure, item)
					previewIcon = QtGui.QIcon(item)
					lbl = QtWidgets.QLabel(self.previewWidget)
					lbl.setText(formatString(self.format, structure, item))
					self.previewLayout.addWidget(lbl)
				self.addBtn.setText("blah Auswahl ändern")
			else:
				self.addBtn.setText("blub Auswählen")
		else:
			if self.selection:
				print("format", self.format, structure, self.selection)
				if self.selection["mimetype"].startswith("image/"):
					RemoteFile(self.selection["dlkey"], successHandler=self.loadIconFromRequest)
				self.entry.setText(formatString(self.format, structure, self.selection))
			else:
				self.entry.setText("")


class FileBoneSelector(TreeBoneSelector):
	displaySourceWidget = FileWidget


def CheckForFileBone(modulName, boneName, skelStucture):
	return (skelStucture[boneName]["type"].startswith("treeitem.file"))

# Register this Bone in the global queue
editBoneSelector.insert(4, CheckForFileBone, FileItemBone)
viewDelegateSelector.insert(4, CheckForFileBone, FileViewBoneDelegate)