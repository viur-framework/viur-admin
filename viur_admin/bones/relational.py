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
from viur_admin.widgets.edit import EditWidget, collectBoneErrors
from viur_admin.widgets.selectedEntities import SelectedEntitiesWidget
from viur_admin.network import NetworkService, RequestWrapper
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector
from viur_admin.priorityqueue import protocolWrapperInstanceSelector
from viur_admin.bones.base import BaseViewBoneDelegate, LanguageContainer, MultiContainer
from viur_admin import config
from viur_admin.pyodidehelper import isPyodide


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
		self.commitData.connect(self.commitDataCb)

	def displayText(self, value: str, locale: QtCore.QLocale) -> str:
		relStructList = self.structure[self.boneName]["using"]
		relStructDict = {k: v for k, v in relStructList} if relStructList else {}
		if value == "-Lade-":
			return value
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
			#logger.exception(err)
			# We probably received some garbage
			value = ""
		return value

	def createEditor(self, parent, option, index):
		protoWrap = protocolWrapperInstanceSelector.select(self.moduleName)
		assert protoWrap is not None
		skelStructure = protoWrap.editStructure
		wdgGen = editBoneSelector.select(self.moduleName, self.boneName, skelStructure)
		widget = wdgGen.fromSkelStructure(self.moduleName, self.boneName, skelStructure, editWidget=self)
		widget.setParent(parent)
		parent.parent().verticalHeader().setSectionResizeMode(index.row(), parent.parent().verticalHeader().ResizeToContents)
		return widget

	def editorEvent(self, event: QtCore.QEvent, model: QtCore.QAbstractItemModel, option: 'QStyleOptionViewItem', index: QtCore.QModelIndex):
		self.editingModel = model
		self.editingIndex = index
		self.editingItem = model.dataCache[index.row()]
		return False

	def commitDataCb(self, editor):
		protoWrap = protocolWrapperInstanceSelector.select(self.moduleName)
		assert protoWrap is not None
		self.editTaskID = protoWrap.edit(self.editingItem["key"], **{self.boneName: editor.serializeForPost()})
		self.editingModel.dataCache[self.editingIndex.row()][self.boneName] = "-Lade-"
		self.editingModel = None
		self.editingIndex = None
		self.request_repaint.emit()


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

	def columnCount(self, *args: Any, **kwargs: Any) -> int:
		return 2

	def data(self, index: QtCore.QModelIndex, role: Union[int, None] = None) -> Any:
		if not index.isValid():
			return
		elif role != QtCore.Qt.ToolTipRole and role != QtCore.Qt.EditRole and role != QtCore.Qt.DisplayRole:
			return
		if 0 <= index.row() < self.rowCount():
			if index.column() == 0:
				#print(formatString("$(name)", self.structure, self.dataCache[index.row()]))
				#return formatString("$(name)", self.structure, self.dataCache[index.row()])
				return str(self.dataCache[index.row()].get("name"))
			else:
				return "foo"

	def setCompletionPrefixHint(self, prefix: str) -> None:
		NetworkService.request(
			"/%s/list" % self.module,
			{"search": prefix},
			successHandler=self.addCompletionData)

	def addCompletionData(self, req: RequestWrapper) -> None:
		try:
			data = NetworkService.decode(req)
		except ValueError:  # Query was canceled
			return
		self.beginResetModel()
		#self.dataCache = []
		changed = False
		for skel in data["skellist"]:
			if self.dataCache:
				for s in self.dataCache:
					if s["key"] == skel["key"]:
						break
				else:
					self.dataCache.append(skel)
					changed = True
			else:
				self.dataCache.append(skel)
				changed = True
		self.endResetModel()
		self.parent().complete()

	def getItem(self, label: str) -> Union[str, None]:
		#res = [x for x in self.dataCache if formatString(self.format, self.structure, x) == label]
		res = [x for x in self.dataCache if x.get("name") == label]
		if len(res):
			return res[0]
		return



class InternalEdit(QtWidgets.QWidget):
	def __init__(
			self,
			parent: QtWidgets.QWidget,
			using: Dict[str, Any],
			text: str,
			values: Dict[str, Any],
			errors: List[Dict]):
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
			if 0 and bone["error"] and not ignoreMissing:
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
		self.unserialize(values, errors)

	def unserialize(self, data: Dict[str, Any], errors: List[Dict]) -> None:
		try:
			for key, bone in self.bones.items():
				logger.debug("unserialize bone: %r", bone)
				bone.unserialize(data.get(key), collectBoneErrors(errors, key))
		except AssertionError as err:
			pass

	def serializeForPost(self) -> Dict[str, Any]:
		res: Dict[str, Any] = dict()
		for key, bone in self.bones.items():
			data = bone.serializeForPost()
			# print("InternalEdit.serializeForPost: key, value", key, data)
			res[key] = data
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
		self.internalEdits: InternalEdit = None
		self.blockAutoCompletion = False
		outerLayout = QtWidgets.QVBoxLayout(self.editWidget)  # Vbox with Relational entry and optional using edit
		hboxWidget = QtWidgets.QWidget(self.editWidget)
		hboxLayout = QtWidgets.QHBoxLayout(hboxWidget)
		outerLayout.addWidget(hboxWidget)
		self.previewIcon = None

		self.addBtn = QtWidgets.QPushButton(
			QtCore.QCoreApplication.translate("RelationalEditBone", "Change selection"),
			parent=hboxWidget)
		iconadd = QtGui.QIcon()
		iconadd.addPixmap(QtGui.QPixmap(":icons/actions/change_selection.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.addBtn.setIcon(iconadd)
		self.addBtn.released.connect(self.onAddBtnReleased)
		self.entry = QtWidgets.QLineEdit(hboxWidget)
		self.installAutoCompletion()
		hboxLayout.addWidget(self.entry)
		hboxLayout.addWidget(self.addBtn)
		if not self.multiple:  ## FIXME: AND SELF REQUIRED
			icon6 = QtGui.QIcon()
			icon6.addPixmap(QtGui.QPixmap(":icons/actions/cancel.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
			self.delBtn = QtWidgets.QPushButton("", parent=self.editWidget)
			self.delBtn.setIcon(icon6)
			self.delBtn.released.connect(self.onDelBtnReleased)
			hboxLayout.addWidget(self.delBtn)
		self.selection: Dict[str, Any] = None
		self.usingEdit = QtWidgets.QWidget(hboxWidget)
		self.previewLayout = QtWidgets.QVBoxLayout(self.usingEdit)
		outerLayout.addWidget(self.usingEdit)
		self.lastErrors = []  # List of errors we receveid in last unserialize call


	@classmethod
	def fromSkelStructure(
			cls,
			moduleName: str,
			boneName: str,
			skelStructure: dict,
			**kwargs: Any) -> Any:
		myStruct = skelStructure[boneName]
		readOnly = "readonly" in myStruct and myStruct["readonly"]
		if "module" in myStruct:
			destModul = myStruct["module"]
		else:
			destModul = myStruct["type"].split(".")[1]
		fmt = "$(name)"
		if "format" in myStruct:
			fmt = myStruct["format"]
		widgetGen = lambda: cls(
			moduleName,
			boneName,
			readOnly,
			multiple=myStruct.get("multiple"),
			destModule=destModul,
			using=myStruct["using"],
			format=fmt)
		if myStruct.get("multiple"):
			preMultiWidgetGen = widgetGen
			widgetGen = lambda: MultiContainer(preMultiWidgetGen)
		if myStruct.get("languages"):
			preLangWidgetGen = widgetGen
			widgetGen = lambda: LanguageContainer(myStruct["languages"], preLangWidgetGen)
		return widgetGen()

	def installAutoCompletion(self) -> None:
		"""
				Installs our autoCompleter on self.entry if possible
		"""
		self.autoCompleter = QtWidgets.QCompleter(self)
		self.autoCompletionModel = AutocompletionModel(self.toModule, self.format, {}, parent=self.autoCompleter)  # FIXME: {} was
		self.autoCompleter.setModel(self.autoCompletionModel)
		self.autoCompleter.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
		self.autoCompleter.setCompletionMode(self.autoCompleter.UnfilteredPopupCompletion)
		self.autoCompleter.setFilterMode(QtCore.Qt.MatchContains)
		self.entry.setCompleter(self.autoCompleter)
		self.entry.textChanged.connect(self.reloadAutocompletion)
		self.autoCompleter.activated[str].connect(self.setAutoCompletion)  # Broken...
		self.autoCompleter.highlighted.connect(self.setAutoCompletion)

	def updateVisiblePreview(self) -> None:
		self.blockAutoCompletion = True
		protoWrap = protocolWrapperInstanceSelector.select(self.realModule)
		assert protoWrap is not None, "Unknown module: %s" % self.realModule
		if self.skelType is None:
			structure = protoWrap.viewStructure
		elif self.skelType == "leaf":
			structure = protoWrap.viewLeafStructure
		elif self.skelType == "node":
			structure = protoWrap.viewNodeStructure
		else:
			return
		if self.using:
			while self.previewLayout.takeAt(0):
				pass
			item = InternalEdit(self.usingEdit, self.using, "FIXME", self.selection["rel"] if self.selection else {}, errors=self.lastErrors)
			item.show()
			self.previewLayout.addWidget(item)
			self.internalEdits = item
			self.addBtn.setText("Auswahl ändern")
		if self.selection:
			self.entry.setText(formatString(self.format, self.selection, structure))
		else:
			self.entry.setText("")
		self.blockAutoCompletion = False

	def reloadAutocompletion(self, text: str) -> None:
		if text and len(text) > 2 and not self.blockAutoCompletion:
			self.autoCompletionModel.setCompletionPrefixHint(text)
			QtGui.QGuiApplication.processEvents()

	def setAutoCompletion(self, label: str) -> None:
		res = self.autoCompletionModel.getItem(label)
		if res:
			self.setSelection([res])

	def setSelection(self, selection: Union[list, dict, None]) -> None:
		data = [{"dest": x, "rel": {}} if "dest" not in x else x for x in selection]
		if len(selection) > 0:
			self.selection = data[0]
		else:
			self.selection = None
		self.updateVisiblePreview()

	def onAddBtnReleased(self, *args: Any, **kwargs: Any) -> None:
		editWidget = RelationalBoneSelector(
			self.moduleName,
			self.boneName,
			False, #self.multiple,
			self.toModule,
			self.selection)
		editWidget.selectionChanged.connect(self.setSelection)

	def onDelBtnReleased(self, *args: Any, **kwargs: Any) -> None:
		self.selection = None
		self.updateVisiblePreview()

	def unserialize(self, data: Dict[str, Any], errors: List[Dict]) -> None:
		self.selection = data
		self.lastErrors = errors
		self.updateVisiblePreview()
		self.setErrors(errors)

	def serializeForPost(self) -> Dict[str, Any]:
		if not self.selection:
			return None
			#return {self.boneName: None}
		if self.using:
			resDict = self.internalEdits.serializeForPost()
			resDict["key"] = self.selection["dest"]["key"]
			return resDict
		else:
			return self.selection["dest"]["key"]


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
		# self.list.setSelectionMode( self.list.SingleSelection )
		if not self.multiple:
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
