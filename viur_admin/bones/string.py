# -*- coding: utf-8 -*-

from html import unescape as unescapeHtml
from typing import Union, List, Dict, Any, Callable

from PyQt5 import QtWidgets, QtGui, QtCore

from viur_admin.bones.base import BaseViewBoneDelegate, LanguageContainer, MultiContainer
from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.config import conf
from viur_admin.event import event
from viur_admin.log import getLogger
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector, extendedSearchWidgetSelector
from viur_admin.ui.extendedStringSearchPluginUI import Ui_Form
from viur_admin.utils import wheelEventFilter, ViurTabBar

logger = getLogger(__name__)


def chooseLang(value: Dict[str, Any], prefs: List[str]) -> Union[str, dict, None]:
	"""
		Tries to select the best language for the current user.
		Value is the dictionary of lang -> text received from the server,
		prefs the list of languages (in order of preference) for that bone.
	"""
	if not isinstance(value, dict):
		return value
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


class StringViewBoneDelegate(BaseViewBoneDelegate):
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
		return super(StringViewBoneDelegate, self).displayText(str(value), locale)


class Tag(QtWidgets.QWidget):
	def __init__(
			self,
			tag: str,
			editMode: int,
			*args: Any,
			**kwargs: Any):
		# print("Tag.init", tag, editMode)
		super(Tag, self).__init__(*args, **kwargs)
		self.setLayout(QtWidgets.QHBoxLayout(self))
		self.tag = tag
		self.lblDisplay = QtWidgets.QLabel(tag, self)
		self.editField = QtWidgets.QLineEdit(tag, self)
		icon6 = QtGui.QIcon()
		icon6.addPixmap(QtGui.QPixmap(":icons/actions/cancel.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.btnDelete = QtWidgets.QPushButton("Löschen", self)
		self.btnDelete.setIcon(icon6)
		self.layout().addWidget(self.lblDisplay)
		self.layout().addWidget(self.editField)
		self.layout().addWidget(self.btnDelete)
		if editMode:
			self.lblDisplay.hide()
			self.editField.show()
		else:
			self.lblDisplay.show()
			self.editField.hide()
		self.editField.editingFinished.connect(self.onEditingFinished)
		self.btnDelete.released.connect(self.deleteLater)
		self.lblDisplay.mousePressEvent = self.onEdit

	def onEdit(
			self,
			*args: Any,
			**kwargs: Any) -> None:
		self.lblDisplay.hide()
		self.editField.show()
		self.editField.setFocus()

	def onEditingFinished(
			self,
			*args: Any,
			**kwargs: Any) -> None:
		self.tag = self.editField.text()
		self.lblDisplay.setText(str(self.tag))
		self.lblDisplay.show()
		self.editField.hide()


class ExtendedStringFilterPlugin(QtWidgets.QGroupBox):
	def __init__(self, extension: Dict[str, Any], parent: Union[QtWidgets.QWidget, None] = None):
		super(ExtendedStringFilterPlugin, self).__init__(parent)
		self.extension = extension
		# self.view = view
		# self.module = module
		self.ui = Ui_Form()
		self.ui.setupUi(self)
		self.setTitle(extension["name"])

	@staticmethod
	def canHandleExtension(extension: Dict[str, Any]) -> bool:
		return (isinstance(extension, dict) and "type" in extension and (
				extension["type"] == "string" or extension["type"].startswith("string.")))


class StringEditBone(BoneEditInterface):
	def __init__(
			self,
			moduleName: str,
			boneName: str,
			readOnly: bool,
			multiple: bool = False,
			languages: List[str] = None,
			editWidget: Union[QtWidgets.QWidget, None] = None,
			*args: Any,
			**kwargs: Any):
		super(StringEditBone, self).__init__(moduleName, boneName, readOnly, editWidget=editWidget, *args, **kwargs)
		self.multiple = multiple
		self.languages = languages
		if 0 and self.languages and self.multiple:  # FIXME: Multiple and readOnly...
			self.setLayout(QtWidgets.QVBoxLayout(self))
			self.tabWidget = QtWidgets.QTabWidget(self)
			self.tabWidget.setTabBar(ViurTabBar(self))
			self.tabWidget.blockSignals(True)
			self.tabWidget.currentChanged.connect(self.onTabCurrentChanged)
			event.connectWithPriority("tabLanguageChanged", self.onTabLanguageChanged, event.lowPriority)
			self.layout().addWidget(self.tabWidget)
			self.langEdits: Dict[str, QtWidgets.QWidget] = dict()
			for lang in self.languages:
				container = QtWidgets.QWidget()
				self.langEdits[lang] = container
				container.setLayout(QtWidgets.QVBoxLayout(container))
				self.tabWidget.addTab(container, lang)
				btnAdd = QtWidgets.QPushButton("Hinzufügen", self)
				container.layout().addWidget(btnAdd)

				def genLambda(lang: str) -> Callable:
					return lambda *largs, **lkwargs: self.genTag("", True, lang)

				# btnAdd.released.connect(self.onAddButtonClickedLanguage)  # TODO: works here?
				btnAdd.released.connect(genLambda(lang))  # FIXME: Lambda..
			self.tabWidget.blockSignals(False)
			self.tabWidget.show()
		elif 0 and self.languages and not self.multiple:
			self.setLayout(QtWidgets.QVBoxLayout(self))
			self.tabWidget = QtWidgets.QTabWidget(self)
			self.tabWidget.setTabBar(ViurTabBar(self))
			self.tabWidget.blockSignals(True)
			self.tabWidget.currentChanged.connect(self.onTabCurrentChanged)
			event.connectWithPriority("tabLanguageChanged", self.onTabLanguageChanged, event.lowPriority)
			self.layout().addWidget(self.tabWidget)
			self.langEdits = {}
			for lang in self.languages:
				edit = QtWidgets.QLineEdit()
				edit.setReadOnly(self.readOnly)
				self.langEdits[lang] = edit
				self.tabWidget.addTab(edit, lang)
			self.tabWidget.blockSignals(False)
		elif 0 and  not self.languages and self.multiple:
			self.setLayout(QtWidgets.QVBoxLayout(self))
			self.btnAdd = QtWidgets.QPushButton("Hinzufügen", self)
			self.layout().addWidget(self.btnAdd)
			self.btnAdd.released.connect(self.onAddButtonClicked)  # TODO: check if this is working
			# self.btnAdd.released.connect(lambda *args, **kwargs: self.genTag("", True))  # FIXME: Lambda
			self.btnAdd.show()
		else:  # not languages and not multiple:
			self.setLayout(QtWidgets.QVBoxLayout(self))
			self.lineEdit = QtWidgets.QLineEdit(self)
			self.layout().addWidget(self.lineEdit)
			self.lineEdit.show()
			self.lineEdit.setReadOnly(self.readOnly)
		self.setFocusPolicy(QtCore.Qt.StrongFocus)
		self.installEventFilter(wheelEventFilter)

	@QtCore.pyqtSlot()
	def onAddButtonClicked(self) -> None:
		self.genTag("", True)

	@QtCore.pyqtSlot(str)
	def onAddButtonClickedLanguage(self, lang: str) -> None:
		self.genTag("", True, lang)

	@staticmethod
	def fromSkelStructure(
			moduleName: str,
			boneName: str,
			skelStructure: Dict[str, Any],
			**kwargs: Any) -> Any:
		myStruct = skelStructure[boneName]
		readOnly = bool(myStruct.get("readonly"))
		widgetGen = lambda: StringEditBone(
			moduleName,
			boneName,
			readOnly,
			multiple=False,
			languages=None,
			**kwargs)
		if myStruct.get("multiple"):
			preMultiWidgetGen = widgetGen
			widgetGen = lambda: MultiContainer(preMultiWidgetGen)
		if myStruct.get("languages"):
			preLangWidgetGen = widgetGen
			widgetGen = lambda: LanguageContainer(myStruct["languages"], preLangWidgetGen)
		return widgetGen()

		multiple = False
		languages = None
		if boneName in skelStructure:
			if "multiple" in skelStructure[boneName]:
				multiple = skelStructure[boneName]["multiple"]

			if "languages" in skelStructure[boneName]:
				languages = skelStructure[boneName]["languages"]
		return StringEditBone(
			moduleName,
			boneName,
			readOnly,
			multiple=multiple,
			languages=languages,
			**kwargs)

	def onTabLanguageChanged(self, lang: str) -> None:
		if lang in self.langEdits:
			try:
				self.tabWidget.blockSignals(True)
				self.tabWidget.setCurrentWidget(self.langEdits[lang])
				self.tabWidget.blockSignals(False)
			except RuntimeError as err:
				logger.exception(err)

	def onTabCurrentChanged(self, idx: int) -> None:
		wdg = self.tabWidget.widget(idx)
		for k, v in self.langEdits.items():
			if v == wdg:
				event.emit("tabLanguageChanged", k)
				wdg.setFocus()
				return

	def unserialize(self, data: Dict[str, Any]) -> None:
		# print("StringEditBone", data)
		#if self.boneName not in data:
		#	return
		#data = data[self.boneName]
		if not data:
			return
		if self.languages and self.multiple:
			assert isinstance(data, dict)
			for lang in self.languages:
				if lang in data:
					val = data[lang]
					if isinstance(val, str):
						self.genTag(unescapeHtml(val), lang=lang)
					elif isinstance(val, list):
						for v in val:
							self.genTag(unescapeHtml(v), lang=lang)
		elif self.languages and not self.multiple:
			assert isinstance(data, dict)
			for lang in self.languages:
				if lang in data:
					self.langEdits[lang].setText(unescapeHtml(str(data[lang])))
		elif not self.languages and self.multiple:
			if isinstance(data, list):
				for tagStr in data:
					self.genTag(unescapeHtml(tagStr))
			else:
				self.genTag(unescapeHtml(data))
		elif not self.languages and not self.multiple:
			self.lineEdit.setText(unescapeHtml(str(data)))
		else:
			pass

	def serializeForPost(self) -> Dict[str, Any]:
		res: Dict[str, Any] = dict()
		if self.languages and self.multiple:
			for lang in self.languages:
				res["%s.%s" % (self.boneName, lang)] = []
				for child in self.langEdits[lang].children():
					if isinstance(child, Tag):
						res["%s.%s" % (self.boneName, lang)].append(child.tag)
		elif not self.languages and self.multiple:
			res[self.boneName] = []
			for child in self.children():
				if isinstance(child, Tag):
					res[self.boneName].append(child.tag)
		elif self.languages and not self.multiple:
			for lang in self.languages:
				txt = self.langEdits[lang].text()
				if txt:
					res["%s.%s" % (self.boneName, lang)] = txt
		elif not self.languages and not self.multiple:
			return self.lineEdit.text()
		return res

	def genTag(self, tag: Tag, editMode : bool = False, lang: Union[str, None] = None) -> None:
		if lang is not None:
			self.langEdits[lang].layout().addWidget(Tag(tag, editMode))
		else:
			self.layout().addWidget(Tag(tag, editMode))


def CheckForStringBone(moduleName: str, boneName: str, skelStucture: Dict[str, Any]) -> bool:
	return (skelStucture[boneName]["type"] == "str")


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForStringBone, StringEditBone)
viewDelegateSelector.insert(2, CheckForStringBone, StringViewBoneDelegate)
extendedSearchWidgetSelector.insert(1, ExtendedStringFilterPlugin.canHandleExtension, ExtendedStringFilterPlugin)
