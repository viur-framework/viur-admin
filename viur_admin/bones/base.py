# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Union

from PyQt5 import QtCore, QtWidgets, QtGui

from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector
from viur_admin.utils import wheelEventFilter, ViurTabBar
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


class MultiContainer(QtWidgets.QWidget):
	def __init__(self, widgetGen):
		super().__init__()
		self.widgetGen = widgetGen
		self.setLayout(QtWidgets.QVBoxLayout(self))
		self.btnAdd = QtWidgets.QPushButton("Hinzufügen", self)
		self.btnAdd.setIcon(QtGui.QIcon.fromTheme("add"))
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
		removeBtn.setIcon(QtGui.QIcon.fromTheme("cancel-cross"))
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

	def serializeForPost(self):
		return [wdg.children()[1].serializeForPost() for wdg in self.children() if wdg not in [self.btnAdd, self.layout()]]


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
		self.editingItem = model.dataCache[index.row()]
		return False

	def displayText(self, value: str, locale: QtCore.QLocale) -> str:
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
		return super(BaseViewBoneDelegate, self).displayText(str(value), locale)

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
