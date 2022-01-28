# -*- coding: utf-8 -*-
from typing import Any, Dict, List

from PyQt5 import QtCore, QtGui, QtWidgets
from viur_admin.pyodidehelper import isPyodide
from viur_admin.bones.base import BaseViewBoneDelegate
from viur_admin.bones.relational import InternalEdit
from viur_admin.bones.treeitem import TreeItemBone, TreeBoneSelector
from viur_admin.log import getLogger
from viur_admin.network import RemoteFile, RequestWrapper
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector
from viur_admin.priorityqueue import protocolWrapperInstanceSelector
from viur_admin.widgets.file import FileWidget
from viur_admin.widgets.selectedFiles import SelectedFilesWidget
from viur_admin import config
import safeeval

logger = getLogger(__name__)


# This class has been disabled (it's currently rendered by the normal relational view delegate)
class FileViewBoneDelegate(BaseViewBoneDelegate):
	cantSort = True

	def __init__(self, module: str, boneName: str, structure: dict):
		super(FileViewBoneDelegate, self).__init__(module, boneName, structure)
		if not hasattr(self, "cache"):
			self.cache: Dict[str, str] = dict()
		self.format = "value['name']"
		self.structure = structure
		if "format" in structure[boneName]:
			self.format = structure[boneName]["format"]
		self.safeEval = safeeval.SafeEval()
		try:
			self.ast = self.safeEval.compile(self.format)
		except:
			self.ast = self.safeEval.compile("value['name']")

	def setImage(self, remoteFile: RequestWrapper) -> None:
		fn = remoteFile.getFileName()
		try:
			self.cache[remoteFile.dlKey] = QtGui.QImage(fn)
		except:
			pass
		self.request_repaint.emit()

	def paint(self, painter: Any, option: Any, index: Any) -> Any:
		if not index.isValid():
			return super(FileViewBoneDelegate, self).paint(painter, option, index)
		model = index.model()
		try:
			index_column = index.column()
			#logger.debug("model and fields: %r, %r, %r", index_column, model.fields, model)
			model_fields = model.fields[index_column]
			index_row = index.row()
			cache_row = model.dataCache[index_row]
			record = cache_row[model_fields]
			#logger.info("record cache row: %r", record)
			if record and isinstance(record, list) and len(record) > 0:
				record = record[0]
		except (IndexError, KeyError) as err:
			#logger.exception(err)
			record = None
		if not record:
			return super(FileViewBoneDelegate, self).paint(painter, option, index)

		if record["dest"]["dlkey"] not in self.cache:
			self.cache[record["dest"]["dlkey"]] = None
			RemoteFile(record["dest"]["dlkey"], successHandler=self.setImage)
			return super(FileViewBoneDelegate, self).paint(painter, option, index)
		elif not self.cache[record["dest"]["dlkey"]]:  # Image not loaded yet
			return super(FileViewBoneDelegate, self).paint(painter, option, index)
		painter.save()
		painter.drawImage(option.rect, self.cache[record["dest"]["dlkey"]])
		painter.restore()
		return super(FileViewBoneDelegate, self).paint(painter, option, index)

	def displayText(self, value: str, locale: QtCore.QLocale) -> None:
		try:
			value = self.safeEval.execute(self.ast, {
				"value": value,
				"structure": self.structure,
				"language": config.conf.adminConfig.get("language", "en")
			})
		except Exception as e:
			logger.exception(e)
			value = "(invalid format string)"
		return super(FileViewBoneDelegate, self).displayText(value, locale)


class MultiItemWidget(QtWidgets.QWidget):
	def __init__(self, text: str, parent: QtWidgets.QWidget = None):
		super(MultiItemWidget, self).__init__(parent)
		self.previewImage = QtWidgets.QLabel(self)
		self.previewImage.hide()
		self.label = QtWidgets.QLabel(self)
		self.label.setText(text)
		self.rowLayout = QtWidgets.QHBoxLayout(self)
		self.rowLayout.addWidget(self.previewImage)
		self.rowLayout.addWidget(self.label)

	def loadIconFromRequest(self, request: RequestWrapper) -> None:
		preview = QtGui.QIcon(request.getFileName())
		self.previewImage.setPixmap(preview.pixmap(QtCore.QSize(32, 32)))
		self.previewImage.show()


class FileItemBone(TreeItemBone):
	skelType = "leaf"

	def htmlDropEvent(self, fileList):
		if fileList:
			self.setDisabled(True)
			fileList = [fileList[0]]  # Crop to first file
			protoWrap = protocolWrapperInstanceSelector.select(self.toModule)
			uploader = protoWrap.upload(fileList, None)
			uploader.finished.connect(self.htmlUploadFinished)

	def htmlUploadFinished(self, uploader):
		self.setDisabled(False)
		self.unserialize({"dest": uploader.uploadResults[0], "rel": None}, {})

	def onAddBtnReleased(self, *args: Any, **kwargs: Any) -> None:
		editWidget = FileBoneSelector(
			self.moduleName,
			self.boneName,
			self.multiple,
			self.toModule,
			self.selection,
			parent=self)
		editWidget.selectionChanged.connect(self.setSelection)

	def loadIconFromRequest(self, request: RequestWrapper) -> None:
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

	def updateVisiblePreview(self) -> None:
		protoWrap = protocolWrapperInstanceSelector.select(self.toModule)
		assert protoWrap is not None, "Module %s has no protoWrap" % self.toModule
		structure = None
		if self.skelType is None:
			structure = protoWrap.viewStructure
		elif self.skelType == "leaf":
			structure = protoWrap.viewLeafStructure
		elif self.skelType == "node":
			structure = protoWrap.viewNodeStructure
		if structure is None:
			return
		if self.selection:
			logger.debug("selection: %r", self.selection)
			if not self.selection["dest"].get("_pending") and self.selection["dest"]["mimetype"].startswith("image/") and not isPyodide:
				RemoteFile(self.selection["dest"]["dlkey"], successHandler=self.loadIconFromRequest)
			try:
				value = self.safeEval.execute(self.ast, {
					"value": self.selection,
					"structure": structure,
					"language": config.conf.adminConfig.get("language", "en")
				})
			except Exception as e:
				logger.exception(e)
				value = "(invalid format string)"
			self.entry.setText(value)
		else:
			self.entry.setText("")


class FileBoneSelector(TreeBoneSelector):
	displaySourceWidget = FileWidget
	displaySelectionWidget = SelectedFilesWidget

	def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
		"""Handle multiple selection via return or enter key press"""

		if self.multiple and e.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
			self.selection.extend([item.entryData for item in self.list.selectedItems()])
		else:
			super(FileBoneSelector, self).keyPressEvent(e)

	def prepareDeletion(self) -> None:
		self.selection.prepareDeletion()
		self.list.prepareDeletion()


def CheckForFileBone(
		moduleName: str,
		boneName: str,
		skelStucture: Dict[str, Any]) -> bool:
	return skelStucture[boneName]["type"].startswith("relational.tree.leaf.file")


# Register this Bone in the global queue
editBoneSelector.insert(4, CheckForFileBone, FileItemBone)
# viewDelegateSelector.insert(4, CheckForFileBone, FileViewBoneDelegate)  # Disable the fileViewDelegate
