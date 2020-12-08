# -*- coding: utf-8 -*-
from typing import Any, Dict, List

from PyQt5 import QtCore, QtWidgets, QtGui

from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector
from viur_admin.utils import wheelEventFilter, ViurTabBar
from viur_admin.widgets.edit import collectBoneErrors


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

iconCancel = QtGui.QIcon()
iconCancel.addPixmap(QtGui.QPixmap(":icons/actions/cancel.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

class MultiContainer(QtWidgets.QWidget):
	def __init__(self, widgetGen):
		super().__init__()
		self.widgetGen = widgetGen
		self.setLayout(QtWidgets.QVBoxLayout(self))
		self.btnAdd = QtWidgets.QPushButton("Hinzufügen", self)
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
		removeBtn.setIcon(iconCancel)
		containterWdg.layout().addWidget(removeBtn)
		self.layout().addWidget(containterWdg)
		idx = self.children().index(containterWdg)
		removeBtn.released.connect(lambda: self.removeLine(idx))
		return wdg

	def removeLine(self, idx):
		self.layout().removeWidget(self.children()[idx])

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


class BaseEditBone(BoneEditInterface):
	def __init__(
			self,
			moduleName: str,
			boneName: str,
			readOnly: bool,
			editWidget: QtWidgets.QWidget = None,
			*args: Any,
			**kwargs: Any):
		super(BaseEditBone, self).__init__(moduleName, boneName, readOnly, editWidget, *args, **kwargs)
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
		return BaseEditBone(moduleName, boneName, readOnly, **kwargs)

	def unserialize(self, data: dict, errors: List[Dict]) -> None:
		self.lineEdit.setText(str(data) if data else "")

	def serializeForPost(self) -> dict:
		return self.lineEdit.displayText()

	def serializeForDocument(self) -> dict:
		return self.serialize()


# Register this Bone in the global queue
editBoneSelector.insert(0, lambda *args, **kwargs: True, BaseEditBone)
viewDelegateSelector.insert(0, lambda *args, **kwargs: True, BaseViewBoneDelegate)
