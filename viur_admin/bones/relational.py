# -*- coding: utf-8 -*-
from typing import Union, Any, List, Dict, Tuple

from viur_admin.log import getLogger

logger = getLogger(__name__)

from collections import OrderedDict

from PyQt5 import QtCore, QtGui, QtWidgets
from viur_admin.bones.bone_interface import BoneEditInterface

from viur_admin.event import event
from viur_admin.utils import formatString, Overlay, WidgetHandler
from viur_admin.ui.relationalselectionUI import Ui_relationalSelector
from viur_admin.widgets.list import ListWidget
from viur_admin.widgets.edit import EditWidget
from viur_admin.widgets.selectedEntities import SelectedEntitiesWidget
from viur_admin.network import NetworkService, RequestWrapper
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector
from viur_admin.priorityqueue import protocolWrapperInstanceSelector
from viur_admin.bones.base import BaseViewBoneDelegate
from viur_admin import config


class BaseBone:
	pass


class RelationalViewBoneDelegate(BaseViewBoneDelegate):
	cantSort = True

	def __init__(self, module: str, boneName: str, structure: Dict[str, Any]):
		super(RelationalViewBoneDelegate, self).__init__(module, boneName, structure)
		# logger.debug("RelationalViewBoneDelegate.init: %r", boneName)
		self.format = "$(name)"
		if "format" in structure[boneName]:
			self.format = structure[boneName]["format"]
		self.module = module
		self.structure = structure
		self.boneName = boneName

	def displayText(self, value: str, locale: QtCore.QLocale) -> str:
		relStructList = self.structure[self.boneName]["using"]
		relStructDict = {k: v for k, v in relStructList} if relStructList else {}
		# logger.debug("RelationalViewBoneDelegate.displayText: %r, %r", self.boneName, value)
		try:
			if isinstance(value, list):
				if relStructList:
					# logger.debug("RelationalViewBoneDelegate.displayText: %r, %r, %r", self.boneName, self.format, self.structure)
					value = ", ".join([(formatString(
						formatString(self.format, x["dest"], self.structure[self.boneName]["relskel"], prefix=["dest"],
						             language=config.conf.adminConfig["language"]),
						relStructDict, x["rel"], prefix=["rel"], language=config.conf.adminConfig["language"]) or x[
						                    "key"]) for x in value])
				else:
					value = ", ".join([formatString(self.format, x["dest"], self.structure, prefix=["dest"],
					                                language=config.conf.adminConfig["language"]) for x in value])
			elif isinstance(value, dict):
				value = formatString(
					formatString(self.format, value["dest"], self.structure[self.boneName]["relskel"], prefix=["dest"],
					             language=config.conf.adminConfig["language"]),
					relStructDict, value["rel"], prefix=["rel"], language=config.conf.adminConfig["language"]) or value[
					        "key"]
		except Exception as err:
			logger.exception(err)
			# We probably received some garbage
			value = ""
		return value


class AutocompletionModel(QtCore.QAbstractTableModel):
	def __init__(
			self,
			module: str,
			format: str,
			structure: Dict[str, Any],
			*args: Any,
			**kwargs: Any):
		super(AutocompletionModel, self).__init__(*args, **kwargs)
		self.module = module
		self.format = format
		self.structure = structure
		self.dataCache: List[Dict[str, Any]] = list()

	def rowCount(self, *args: Any, **kwargs: Any) -> int:
		return len(self.dataCache)

	def colCount(self, *args: Any, **kwargs: Any) -> int:
		return 2

	def data(self, index: QtCore.QModelIndex, role: Union[int, None] = None) -> Any:
		if not index.isValid():
			return
		elif role != QtCore.Qt.ToolTipRole and role != QtCore.Qt.EditRole and role != QtCore.Qt.DisplayRole:
			return
		if 0 <= index.row() < self.rowCount():
			if index.col() == 0:
				return formatString(self.format, self.structure, self.dataCache[index.row()])
			else:
				return "foo"

	def setCompletionPrefix(self, prefix: str) -> None:
		NetworkService.request(
			"/%s/list" % self.module,
			{"name$lk": prefix, "orderby": "name"},
			successHandler=self.addCompletionData)

	def addCompletionData(self, req: RequestWrapper) -> None:
		try:
			data = NetworkService.decode(req)
		except ValueError:  # Query was canceled
			return
		self.layoutAboutToBeChanged.emit()
		self.dataCache = []
		for skel in data["skellist"]:
			self.dataCache.append(skel)
		self.layoutChanged.emit()

	def getItem(self, label: str) -> Union[str, None]:
		res = [x for x in self.dataCache if formatString(self.format, self.structure, x) == label]
		if len(res):
			return res[0]
		return


class InternalEdit(QtWidgets.QWidget):
	def __init__(
			self,
			parent: QtWidgets.QWidget,
			using: Dict[str, Any],
			text: str,
			values: Dict[str, Any]):
		super(InternalEdit, self).__init__(parent)
		self.layout = QtWidgets.QVBoxLayout(self)
		self.dest = QtWidgets.QLabel(text)
		self.layout.addWidget(self.dest)
		self.bones: Dict[str, Any] = OrderedDict()
		self.module = ""
		self.values = values
		ignoreMissing = True
		tmpDict = dict()
		for key, bone in using:
			tmpDict[key] = bone

		for key, bone in using:
			if not bone["visible"]:
				continue
			wdgGen = editBoneSelector.select(self.module, key, tmpDict)
			widget = wdgGen.fromSkelStructure(self.module, key, tmpDict)
			if bone["error"] and not ignoreMissing:
				dataWidget = QtWidgets.QWidget()
				layout = QtWidgets.QHBoxLayout(dataWidget)
				dataWidget.setLayout(layout)
				layout.addWidget(widget, stretch=1)
				iconLbl = QtWidgets.QLabel(dataWidget)
				if bone["required"]:
					iconLbl.setPixmap(QtGui.QPixmap(":icons/status/error.png"))
				else:
					iconLbl.setPixmap(QtGui.QPixmap(":icons/status/incomplete.png"))
				layout.addWidget(iconLbl, stretch=0)
				iconLbl.setToolTip(str(bone["error"]))
			else:
				dataWidget = widget
			lblWidget = QtWidgets.QWidget(self)
			layout = QtWidgets.QHBoxLayout(lblWidget)
			if "params" in bone and isinstance(bone["params"], dict) and "tooltip" in bone["params"]:
				lblWidget.setToolTip(self.parseHelpText(bone["params"]["tooltip"]))
			descrLbl = QtWidgets.QLabel(bone["descr"], lblWidget)
			descrLbl.setWordWrap(True)
			if bone["required"]:
				font = descrLbl.font()
				font.setBold(True)
				font.setUnderline(True)
				descrLbl.setFont(font)
			layout.addWidget(descrLbl)
			layout.addWidget(dataWidget)
			self.layout.addWidget(lblWidget)
			self.bones[key] = widget
		self.unserialize(values["rel"])

	def unserialize(self, data: Dict[str, Any]) -> None:
		try:
			for bone in self.bones.values():
				logger.debug("unserialize bone: %r", bone)
				bone.unserialize(data)
		except AssertionError as err:
			pass

	def serializeForPost(self) -> Dict[str, Any]:
		res: Dict[str, Any] = dict()
		for key, bone in self.bones.items():
			data = bone.serializeForPost()
			# print("InternalEdit.serializeForPost: key, value", key, data)
			res.update(data)
		res["key"] = self.values["dest"]["key"]
		return res


class RelationalEditBone(BoneEditInterface):
	GarbageTypeName = "ExtendedRelationalEditBone"
	skelType = None

	def __init__(
			self,
			moduleName: str,
			boneName: str,
			readOnly: bool,
			destModule: str,
			multiple: bool,
			using: Union[str, None] = None,
			format: str = "$(name)",
			*args: Any,
			**kwargs: Any):
		super(RelationalEditBone, self).__init__(moduleName, boneName, readOnly, *args, **kwargs)
		logger.debug("RelationalEditBone: %r, %r, %r, %r", moduleName, boneName, readOnly, destModule)
		self.toModule = self.realModule = destModule
		if self.toModule.endswith("_rootNode"):
			self.realModule = destModule[:-9]
		self.multiple = multiple
		self.using = using
		self.format = format
		self.overlay = Overlay(self)
		self.internalEdits: List[InternalEdit] = list()
		if not self.multiple:
			self.layout = QtWidgets.QHBoxLayout(self)
			self.previewIcon = None
		else:
			self.layout = QtWidgets.QVBoxLayout(self)
			self.previewWidget = QtWidgets.QWidget(self)
			self.previewLayout = QtWidgets.QVBoxLayout(self.previewWidget)
			self.layout.addWidget(self.previewWidget)
		self.addBtn = QtWidgets.QPushButton(
			QtCore.QCoreApplication.translate("RelationalEditBone", "Change selection"),
			parent=self)
		iconadd = QtGui.QIcon()
		iconadd.addPixmap(QtGui.QPixmap(":icons/actions/change_selection.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.addBtn.setIcon(iconadd)
		self.addBtn.released.connect(self.onAddBtnReleased)
		if not self.multiple:
			self.entry = QtWidgets.QLineEdit(self)
			self.installAutoCompletion()
			self.layout.addWidget(self.entry)
			icon6 = QtGui.QIcon()
			icon6.addPixmap(QtGui.QPixmap(":icons/actions/cancel.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
			self.delBtn = QtWidgets.QPushButton("", parent=self)
			self.delBtn.setIcon(icon6)
			self.delBtn.released.connect(self.onDelBtnReleased)
			self.layout.addWidget(self.addBtn)
			self.layout.addWidget(self.delBtn)
			self.selection: Dict[str, Any] = None
		else:
			self.selection: List[Dict[str, Any]] = list()
			self.layout.addWidget(self.addBtn)

	@classmethod
	def fromSkelStructure(
			cls,
			moduleName: str,
			boneName: str,
			skelStructure: dict,
			**kwargs: Any) -> Any:
		readOnly = "readonly" in skelStructure[boneName] and skelStructure[boneName]["readonly"]
		multiple = skelStructure[boneName]["multiple"]
		if "module" in skelStructure[boneName]:
			destModul = skelStructure[boneName]["module"]
		else:
			destModul = skelStructure[boneName]["type"].split(".")[1]
		fmt = "$(name)"
		if "format" in skelStructure[boneName]:
			fmt = skelStructure[boneName]["format"]
		return cls(
			moduleName,
			boneName,
			readOnly,
			multiple=multiple,
			destModule=destModul,
			using=skelStructure[boneName]["using"],
			format=fmt)

	def installAutoCompletion(self) -> None:
		"""
				Installs our autoCompleter on self.entry if possible
		"""
		if not self.multiple:
			self.autoCompletionModel = AutocompletionModel(self.toModule, self.format, {})  # FIXME: {} was
			self.autoCompleter = QtWidgets.QCompleter(self.autoCompletionModel)
			self.autoCompleter.setModel(self.autoCompletionModel)
			self.autoCompleter.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
			self.entry.setCompleter(self.autoCompleter)
			self.entry.textChanged.connect(self.reloadAutocompletion)
			self.autoCompleter.activated.connect(self.setAutoCompletion)  # Broken...
			self.autoCompleter.highlighted.connect(self.setAutoCompletion)

	def updateVisiblePreview(self) -> None:
		protoWrap = protocolWrapperInstanceSelector.select(self.realModule)
		assert protoWrap is not None, "Unknown module: %s" % self.realModule
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
					self.addBtn.setText("Auswählen")
		else:
			if self.multiple:
				widgetItem = self.previewLayout.takeAt(0)
				while widgetItem:
					widgetItem = self.previewLayout.takeAt(0)
				if self.selection and len(self.selection) > 0:
					for item in self.selection:
						lbl = QtWidgets.QLabel(self.previewWidget)
						lbl.setText(formatString(self.format, item, structure))
						self.previewLayout.addWidget(lbl)
			else:
				if self.selection:
					self.entry.setText(formatString(self.format, self.selection, structure))
				else:
					self.entry.setText("")

	def reloadAutocompletion(self, text: str) -> None:
		if text and len(text) > 2:
			self.autoCompletionModel.setCompletionPrefix(text)

	def setAutoCompletion(self, label: str) -> None:
		res = self.autoCompletionModel.getItem(label)
		if res:
			self.setSelection([res])

	def setSelection(self, selection: Union[list, dict, None]) -> None:
		data = [{"dest": x, "rel": {}} if "dest" not in x else x for x in selection]
		if self.multiple:
			self.selection = data
		elif len(selection) > 0:
			self.selection = data[0]
		else:
			self.selection = None
		self.updateVisiblePreview()

	def onAddBtnReleased(self, *args: Any, **kwargs: Any) -> None:
		editWidget = RelationalBoneSelector(
			self.moduleName,
			self.boneName,
			self.multiple,
			self.toModule,
			self.selection)
		editWidget.selectionChanged.connect(self.setSelection)

	def onDelBtnReleased(self, *args: Any, **kwargs: Any) -> None:
		if self.multiple:
			self.selection = []
		else:
			self.selection = None
		self.updateVisiblePreview()

	def unserialize(self, data: Dict[str, Any]) -> None:
		self.selection = data[self.boneName]
		self.updateVisiblePreview()

	def serializeForPost(self) -> Dict[str, Any]:
		if not self.selection:
			return {self.boneName: None}

		res = {}
		if self.using:
			if self.multiple:
				for ix, item in enumerate(self.internalEdits):
					entry = item.serializeForPost()
					if isinstance(entry, dict):
						for k, v in entry.items():
							res["{0}.{1}.{2}".format(self.boneName, ix, k)] = v
					else:
						res["{0}.{1}.key".format(self.boneName, ix)] = entry
		else:
			if isinstance(self.selection, dict):
				res["{0}.0.key".format(self.boneName)] = self.selection["dest"]["key"]
			elif isinstance(self.selection, list):
				for idx, item in enumerate(self.selection):
					res["{0}.{1}.key".format(self.boneName, idx)] = item["dest"]["key"]
			else:
				raise ValueError("Unknown selection type %s" % str(type(self.selection)))

		return res


class RelationalBoneSelector(QtWidgets.QWidget):
	selectionChanged = QtCore.pyqtSignal((object,))
	displaySourceWidget = ListWidget
	displaySelectionWidget = SelectedEntitiesWidget
	GarbageTypeName = "ExtendedRelationalBoneSelector"

	def __init__(
			self,
			moduleName: str,
			boneName: str,
			multiple: bool,
			toModul: str,
			selection: list,
			*args: Any,
			**kwargs: Any):
		super(RelationalBoneSelector, self).__init__(*args, **kwargs)
		logger.debug("RelationalBoneSelector.init: %r, %r, %r, %r, %r", moduleName, boneName, multiple, toModul,
		             selection)
		self.moduleName = moduleName
		self.boneName = boneName
		self.multiple = multiple
		self.module = toModul
		self.selection = selection
		self.ui = Ui_relationalSelector()
		self.ui.setupUi(self)
		layout = QtWidgets.QHBoxLayout(self.ui.tableWidget)
		self.ui.tableWidget.setLayout(layout)
		self.list = self.displaySourceWidget(self.module, editOnDoubleClick=False, parent=self)
		layout.addWidget(self.list)
		self.list.show()
		layout = QtWidgets.QHBoxLayout(self.ui.listSelected)
		self.ui.listSelected.setLayout(layout)
		self.selection = self.displaySelectionWidget(self.module, selection, parent=self)
		layout.addWidget(self.selection)
		self.selection.show()
		if not self.multiple:
			# self.list.setSelectionMode( self.list.SingleSelection )
			self.selection.hide()
			self.ui.lblSelected.hide()
		self.list.itemDoubleClicked.connect(self.onSourceItemDoubleClicked)
		self.list.itemClicked.connect(self.onSourceItemClicked)
		self.ui.btnSelect.clicked.connect(self.onBtnSelectReleased)
		self.ui.btnCancel.clicked.connect(self.onBtnCancelReleased)
		event.emit('stackWidget', self)

	def getBreadCrumb(self) -> Tuple[Union[str, None], QtGui.QIcon]:
		protoWrap = protocolWrapperInstanceSelector.select(self.moduleName)
		assert protoWrap is not None
		# FIXME: Bad hack to get the editWidget we belong to
		skel: Union[Dict[str, Any], None] = None
		for widget in WidgetHandler.mainWindow.handlerForWidget(self).widgets:
			if isinstance(widget, EditWidget):
				if (not widget.key) or widget.clone:  # We're adding a new entry
					if widget.skelType == "leaf":
						skel = protoWrap.addLeafStructure
					elif widget.skelType == "node":
						skel = protoWrap.addNodeStructure
					else:
						skel = protoWrap.addStructure
				else:
					if widget.skelType == "leaf":
						skel = protoWrap.editLeafStructure
					elif widget.skelType == "node":
						skel = protoWrap.editNodeStructure
					else:
						skel = protoWrap.editStructure
		assert skel is not None
		assert self.boneName in skel
		return QtCore.QCoreApplication.translate("ExtendedRelationalBoneSelector", "Select %s") % skel[self.boneName][
			"descr"], QtGui.QIcon(":icons/actions/change_selection.svg")

	def onSourceItemClicked(self, item: QtWidgets.QListWidgetItem) -> None:
		pass

	def onSourceItemDoubleClicked(self, item: QtWidgets.QListWidgetItem) -> None:
		"""
				An item has been doubleClicked in our listWidget.
				Read its properties and add them to our selection.
		"""
		logger.debug("RelationalEditBone.onSourceItemDoubleClicked: %r", item)
		data = item
		if self.multiple:
			self.selection.extend([data])
		else:
			self.selectionChanged.emit([data])
			event.emit("popWidget", self)

	def onBtnSelectReleased(self, *args: Any, **kwargs: Any) -> None:
		logger.debug("onBtnSelectReleased")
		try:
			self.selection.prepareDeletion()
		except AttributeError:
			pass
		self.selectionChanged.emit(self.selection.get())
		event.emit("popWidget", self)

	def onBtnCancelReleased(self, *args: Any, **kwargs: Any) -> None:
		logger.debug("onBtnCancelReleased")
		try:
			self.selection.prepareDeletion()
		except AttributeError:
			pass
		event.emit("popWidget", self)

	def getFilter(self) -> Dict[str, Any]:
		return self.list.getFilter()

	def setFilter(self, queryFilter: Dict[str, Any]) -> None:
		return self.list.setFilter(queryFilter)

	def getModul(self) -> str:
		return self.list.getModul()


def CheckForRelationalicBone(moduleName: str, boneName: str, skelStucture: Dict[str, Any]) -> bool:
	return skelStucture[boneName]["type"].startswith("relational.")


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForRelationalicBone, RelationalEditBone)
viewDelegateSelector.insert(2, CheckForRelationalicBone, RelationalViewBoneDelegate)
