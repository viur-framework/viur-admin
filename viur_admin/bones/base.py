# -*- coding: utf-8 -*-
import copy
from typing import Any, Dict, List, Union

from PyQt5 import QtCore, QtWidgets, QtGui

from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector
from viur_admin.utils import wheelEventFilter, ViurTabBar, loadIcon, boneErrorCodeToIcon
from viur_admin.widgets.edit import collectBoneErrors
from viur_admin.config import conf


class LanguageContainer(QtWidgets.QTabWidget):
	def __init__(self, languages, widgetGen):
		super().__init__()
		self.languages = languages
		self.setTabBar(ViurTabBar(self))
		self.blockSignals(True)
		self.currentChanged.connect(self.onTabCurrentChanged)
		for lang in languages:
			edit = widgetGen()
			# edit.setReadOnly(self.readOnly)
			# self.langEdits[lang] = edit
			self.addTab(edit, lang)

	def onTabCurrentChanged(self, idx: int) -> None:
		wdg = self.tabWidget.widget(idx)
		for k, v in self.langEdits.items():
			if v == wdg:
				# event.emit("tabLanguageChanged", k)
				wdg.setFocus()
				return

	def unserialize(self, data, errors: List[Dict]):
		if not isinstance(data, dict):
			return  # Fixme
		for idx, lng in enumerate(self.languages):
			wdg = self.widget(idx)
			langData = data.get(lng)
			wdg.unserialize(langData, collectBoneErrors(errors, str(lng)))

	def serializeForPost(self):
		r = {lng: self.widget(idx).serializeForPost() for idx, lng in enumerate(self.languages)}
		return r

	def setErrors(self, boneErrors):
		# FIXME: We should handle errors directly assigned to this bone
		for idx, lng in enumerate(self.languages):
			widget = self.widget(idx)
			tmpErrs = []
			for error in boneErrors:
				if error["fieldPath"] and error["fieldPath"][0] == lng:
					error["fieldPath"] = error["fieldPath"][1:]
					tmpErrs.append(error)
			widget.setErrors(tmpErrs)

	def getEffectiveMaximumBoneError(self, inOptionalContainer: bool = False) -> int:
		return max([self.widget(idx).getEffectiveMaximumBoneError() for idx, lng in enumerate(self.languages)])

class TabMultiContainer(QtWidgets.QTabWidget):
	# For extended relations / recordBones. They will be rendered as a tabbar
	def __init__(self, widgetGen, textFormatFunc=None):
		super().__init__()
		self.widgetGen = widgetGen
		self.textFormatFunc = textFormatFunc
		self.setMovable(True)
		self.setTabsClosable(True)
		self.btn = QtWidgets.QPushButton("Hinzufügen", self)
		self.btn.setIcon(loadIcon("add"))
		self.btn.pressed.connect(self.onAddButtonClicked)
		self.setCornerWidget(self.btn)
		self.btn.setMinimumSize(self.btn.width(), self.btn.height())
		self.tabCloseRequested.connect(self.onTabCloseRequested)
		self.newIndex = 0

	def onTabCloseRequested(self, index: int):
		self.removeTab(index)
		if not self.count():  # Ensure the "add" button stayes visible
			self.btn.setMinimumSize(self.btn.width(), self.btn.height())

	def _mkEntry(self):
		self.newIndex += 1
		wdg = self.widgetGen()
		self.addTab(wdg, loadIcon("bookmark-add"), "Neuer Eintrag %s" % self.newIndex)
		self.btn.setMinimumSize(0,0)
		return wdg

	def onAddButtonClicked(self, *args, **kwargs):
		self._mkEntry()

	def unserialize(self, data, errors: List[Dict]):
		self.clear()
		if not data:
			return
		elif isinstance(data, list):
			for idx, d in enumerate(data):
				wdg = self._mkEntry()
				wdg.unserialize(d, collectBoneErrors(errors, str(idx)))
				if self.textFormatFunc:
					self.setTabText(idx, self.textFormatFunc(d))
		else:
			wdg = self._mkEntry()
			wdg.unserialize(data, collectBoneErrors(errors, "0"))
			if self.textFormatFunc:
				self.setTabText(0, self.textFormatFunc(d))

	def getChildBones(self):
		for x in range(0, self.count()):
			yield self.widget(x)

	def serializeForPost(self):
		return [x.serializeForPost() for x in self.getChildBones()]

	def setErrors(self, boneErrors):
		for idx, childBone in enumerate(self.getChildBones()):
			tmpErrs = []
			for error in boneErrors:
				if error["fieldPath"] and error["fieldPath"][0] == str(idx):
					error["fieldPath"] = error["fieldPath"][1:]
					tmpErrs.append(error)
			childBone.setErrors(tmpErrs)
			icon = boneErrorCodeToIcon(childBone.getEffectiveMaximumBoneError(False))  # FIXME
			self.setTabIcon(idx, icon)

	def getEffectiveMaximumBoneError(self, inOptionalContainer: bool = False) -> int:
		return max([x.getEffectiveMaximumBoneError(inOptionalContainer) for x in self.getChildBones()])

class ListMultiContainer(QtWidgets.QWidget):
	# For simple relations, multi stringBones etc. They will be rendered in a list, top to bottom
	def __init__(self, widgetGen):
		super().__init__()
		self.widgetGen = widgetGen
		self.setLayout(QtWidgets.QVBoxLayout(self))
		self.btnAdd = QtWidgets.QPushButton("Hinzufügen", self)
		self.btnAdd.setIcon(loadIcon("add"))
		self.layout().addWidget(self.btnAdd)
		self.btnAdd.released.connect(self.onAddButtonClicked)  # TODO: check if this is working
		# self.btnAdd.released.connect(lambda *args, **kwargs: self.genTag("", True))  # FIXME: Lambda
		self.btnAdd.show()

	def clearContents(self):
		for widget in self.children():
			if widget is self.btnAdd or widget is self.layout():
				continue
			self.layout().removeWidget(widget)

	def _mkEntry(self):
		containterWdg = QtWidgets.QWidget()
		containterWdg.setLayout(QtWidgets.QHBoxLayout())
		wdg = self.widgetGen()
		containterWdg.layout().addWidget(wdg)
		removeBtn = QtWidgets.QPushButton()
		removeBtn.setIcon(loadIcon("cancel"))
		containterWdg.layout().addWidget(removeBtn)
		self.layout().addWidget(containterWdg)
		idx = self.children().index(containterWdg)
		removeBtn.released.connect(lambda: self.removeLine(idx))
		return wdg

	def removeLine(self, idx):
		c = self.children()[idx]
		self.layout().removeWidget(c)
		c.deleteLater()

	def onAddButtonClicked(self, *args, **kwargs):
		self._mkEntry()

	def unserialize(self, data, errors: List[Dict]):
		self.clearContents()
		if not data:
			return
		elif isinstance(data, list):
			for idx, d in enumerate(data):
				wdg = self._mkEntry()
				wdg.unserialize(d, collectBoneErrors(errors, str(idx)))
		else:
			wdg = self._mkEntry()
			wdg.unserialize(data, collectBoneErrors(errors, "0"))

	def getChildBones(self):
		yield from (wdg.children()[1] for wdg in self.children() if wdg not in [self.btnAdd, self.layout()])

	def serializeForPost(self):
		return [wdg.serializeForPost() for wdg in self.getChildBones()]

	def setErrors(self, boneErrors):
		# FIXME: We should handle errors directly assigned to this bone
		for idx, childBone in enumerate(self.getChildBones()):
			tmpErrs = []
			for error in boneErrors:
				if error["fieldPath"] and error["fieldPath"][0] == str(idx):
					error["fieldPath"] = error["fieldPath"][1:]
					tmpErrs.append(error)
			childBone.setErrors(tmpErrs)

	def getEffectiveMaximumBoneError(self, inOptionalContainer: bool = False) -> int:
		return max([-1]+[x.getEffectiveMaximumBoneError(inOptionalContainer) for x in self.getChildBones()])

def chooseLang(value: Dict[str, Any], prefs: List[str], currentLanguageSelection: str = None) -> Union[str, dict, None]:
	"""
		Tries to select the best language for the current user.
		Value is the dictionary of lang -> text received from the server,
		prefs the list of languages (in order of preference) for that bone.
	"""
	if not isinstance(value, dict):
		return value
	if currentLanguageSelection:
		lang = currentLanguageSelection
		return value.get(lang)
	try:
		lang = conf.adminConfig["language"]
	except KeyError:
		lang = ""
	if lang in value and value[lang]:
		return value[lang]
	for lang in prefs:
		if lang in value:
			if value[lang]:
				return value[lang]
	return None

class BaseViewBoneDelegate(QtWidgets.QStyledItemDelegate):
	request_repaint = QtCore.pyqtSignal()

	def __init__(
			self,
			moduleName: str,
			boneName: str,
			skelStructure: dict,
			*args: Any,
			**kwargs: Any):
		super().__init__(**kwargs)
		self.skelStructure = skelStructure
		self.boneName = boneName
		self.moduleName = moduleName
		self.language = None
		self.editingModel = None
		self.editingIndex = None
		self.editingItem = None
		self.commitData.connect(self.commitDataCb)

	def isEditable(self):
		return False

	def openContextMenu(self, point: QtCore.QPoint, parentWidget) -> None:
		if self.boneName not in self.skelStructure:
			return
		if "languages" in self.skelStructure[self.boneName]:
			languages = self.skelStructure[self.boneName]["languages"]
		else:
			languages = None
		menu = QtWidgets.QMenu(parentWidget)
		languagesMenu = menu.addMenu("Languages")
		if languages:
			lngGroup = QtWidgets.QActionGroup(menu)
			defaultAction = lngGroup.addAction("Preferred Language")
			defaultAction.setCheckable(True)
			defaultAction.setChecked(not bool(self.language))
			defaultAction.language = None
			for lng in languages:
				lngAction = lngGroup.addAction(lng)
				lngAction.setCheckable(True)
				lngAction.setChecked(self.language == lng)
				lngAction.language = lng
			lngGroup.setExclusive(True)
			languagesMenu.addActions(lngGroup.actions())
		else:
			languagesMenu.setDisabled(True)
		editAction = menu.addAction("Edit")
		editAction.setCheckable(True)
		if not self.isEditable():
			editAction.setEnabled(False)
		else:
			editAction.setChecked(parentWidget.getColumEditMode(self.boneName))
		editAction.action = "editable"
		selection = menu.exec_(parentWidget.mapToGlobal(point))
		if selection:
			if "language" in dir(selection):
				self.language = selection.language
			elif "action" in dir(selection):
				if selection.action == "editable":
					parentWidget.setColumEditMode(self.boneName, editAction.isChecked())
			#parentWidget.list.model().setDisplayedFields([x.key for x in actions if x.isChecked()])

	def editorEvent(self, event: QtCore.QEvent, model: QtCore.QAbstractItemModel, option: 'QStyleOptionViewItem', index: QtCore.QModelIndex):
		self.editingModel = model
		self.editingIndex = index
		self.editingItem = model.data(index, QtCore.Qt.UserRole)
		return False

	def displayText(self, value: dict, locale: QtCore.QLocale) -> str:
		value = value.get(self.boneName)
		# print("StringViewBoneDelegate.displayText:", value, locale)
		if self.boneName in self.skelStructure:
			if "multiple" in self.skelStructure[self.boneName]:
				multiple = self.skelStructure[self.boneName]["multiple"]
			else:
				multiple = False
			if "languages" in self.skelStructure[self.boneName]:
				languages = self.skelStructure[self.boneName]["languages"]
			else:
				languages = None
			if multiple and languages:
				try:
					value = ", ".join(chooseLang(value, languages))
				except:
					value = ""
			elif multiple and not languages:
				value = ", ".join(value)
			elif not multiple and languages:
				value = chooseLang(value, languages)
			else:  # Not multiple nor languages
				pass
		return str(value)

	def commitDataCb(self, editor):
		raise NotImplementedError

class BaseEditBone(BoneEditInterface):
	def __init__(
			self,
			moduleName: str,
			boneName: str,
			readOnly: bool,
			required: bool,
			editWidget: QtWidgets.QWidget = None,
			*args: Any,
			**kwargs: Any):
		super(BaseEditBone, self).__init__(moduleName, boneName, readOnly, required, editWidget, *args, **kwargs)
		self.layout = QtWidgets.QHBoxLayout(self.editWidget)
		self.lineEdit = QtWidgets.QLineEdit(self.editWidget)
		self.layout.addWidget(self.lineEdit)
		self.setParams()
		self.lineEdit.show()

	def setParams(self) -> None:
		self.setEnabled(not self.readOnly)

	@staticmethod
	def fromSkelStructure(
			moduleName: str,
			boneName: str,
			skelStructure: dict,
			**kwargs: Any) -> Any:
		readOnly = "readonly" in skelStructure[boneName] and skelStructure[boneName]["readonly"]
		required = "required" in skelStructure[boneName] and skelStructure[boneName]["required"]
		return BaseEditBone(moduleName, boneName, readOnly, required, **kwargs)

	def unserialize(self, data: dict, errors: List[Dict]) -> None:
		self.setErrors(errors)
		self.lineEdit.setText(str(data) if data else "")

	def serializeForPost(self) -> dict:
		return self.lineEdit.displayText()

	def serializeForDocument(self) -> dict:
		return self.serialize()


# Register this Bone in the global queue
editBoneSelector.insert(0, lambda *args, **kwargs: True, BaseEditBone)
viewDelegateSelector.insert(0, lambda *args, **kwargs: True, BaseViewBoneDelegate)

class CombinedViewDelegate(BaseViewBoneDelegate):
	"""
		This is the combined view delegate for tree modules, in which one key (boneName) can have
		different types as there two skeletons (nodes and leafs) that get combined into one view.
		In this case, this delegate is selected and will forward the displayText() call to the
		appropriate delegate based on the current skeleton type.
	"""
	cantSort = True

	def __init__(
			self,
			modulName: str,
			boneName: str,
			skelStructure: dict,
			*args: Any,
			**kwargs: Any):
		super(CombinedViewDelegate, self).__init__(modulName, boneName, skelStructure, *args, **kwargs)
		self.skelStructure = skelStructure
		self.boneName = boneName
		self.modulName = modulName
		# Create the delegate for nodes
		structureClone = copy.deepcopy(skelStructure)
		structureClone[self.boneName] = structureClone[self.boneName][0]
		delegateFactory = viewDelegateSelector.select(self.modulName, self.boneName, structureClone)
		self.nodeDelegate = delegateFactory(self.modulName, self.boneName, structureClone)
		# Create the delegate for leafs
		structureClone = copy.deepcopy(skelStructure)
		structureClone[self.boneName] = structureClone[self.boneName][1]
		delegateFactory = viewDelegateSelector.select(self.modulName, self.boneName, structureClone)
		self.leafDelegate = delegateFactory(self.modulName, self.boneName, structureClone)


	def displayText(self, value: dict, locale: QtCore.QLocale):
		#print("COMBI", value)
		if value.get("_type") == "node":
			return self.nodeDelegate.displayText(value, locale)
		elif value.get("_type") == "leaf":
			return self.leafDelegate.displayText(value, locale)
		else:
			return "?"


## Combined viewdelegate for treeViews
def CheckForCombinedViewDelegate(
		moduleName: str,
		boneName: str,
		skelStucture: Dict[str, Any]) -> bool:
	return isinstance(skelStucture[boneName], list)

viewDelegateSelector.insert(999999, CheckForCombinedViewDelegate, CombinedViewDelegate)