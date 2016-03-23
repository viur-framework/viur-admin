# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
from viur_admin.bones.bone_interface import BoneEditInterface

from viur_admin.bones.base import BaseViewBoneDelegate
from viur_admin.event import event
from viur_admin.network import NetworkService
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector
from viur_admin.priorityqueue import protocolWrapperInstanceSelector
from viur_admin.ui.relationalselectionUI import Ui_relationalSelector
from viur_admin.utils import formatString, Overlay, WidgetHandler
from viur_admin.widgets.edit import EditWidget
from viur_admin.widgets.list import ListWidget
from viur_admin.widgets.selectedEntities import SelectedEntitiesWidget


class BaseBone:
	pass


class RelationalViewBoneDelegate(BaseViewBoneDelegate):
	cantSort = True

	def __init__(self, modul, boneName, structure):
		super(RelationalViewBoneDelegate, self).__init__(modul, boneName, structure)
		self.format = "$(name)"
		if "format" in structure[boneName].keys():
			self.format = structure[boneName]["format"]
		self.modul = modul
		self.structure = structure
		self.boneName = boneName

	def displayText(self, value, locale):
		print( value, locale)
		return formatString(self.format, self.structure, value)


class AutocompletionModel(QtCore.QAbstractListModel):
	def __init__(self, modul, format, structure, *args, **kwargs):
		super(AutocompletionModel, self).__init__(*args, **kwargs)
		self.modul = modul
		self.format = format
		self.structure = structure
		self.dataCache = []

	def rowCount(self, *args, **kwargs):
		return len(self.dataCache)

	def data(self, index, role):
		if not index.isValid():
			return
		elif role != QtCore.Qt.ToolTipRole and role != QtCore.Qt.EditRole and role != QtCore.Qt.DisplayRole:
			return
		if index.row() >= 0 and index.row() < self.rowCount():
			return formatString(self.format, self.structure, self.dataCache[index.row()])

	def setCompletionPrefix(self, prefix):
		NetworkService.request("/%s/list" % self.modul, {"name$lk": prefix, "orderby": "name"},
		                       successHandler=self.addCompletionData)

	def addCompletionData(self, req):
		try:
			data = NetworkService.decode(req)
		except ValueError:  # Query was canceled
			return
		self.layoutAboutToBeChanged.emit()
		self.dataCache = []
		for skel in data["skellist"]:
			self.dataCache.append(skel)
		self.layoutChanged.emit()

	def getItem(self, label):
		res = [x for x in self.dataCache if formatString(self.format, self.structure, x) == label]
		if len(res):
			return res[0]
		return


class RelationalEditBone(BoneEditInterface):
	GarbageTypeName = "RelationalEditBone"
	skelType = None

	def __init__(self, moduleName, boneName, readOnly, kind, destModul, multiple, format="$(name)", editWidget=None,
	             *args, **kwargs):
		super(RelationalEditBone, self).__init__(moduleName, boneName, readOnly, editWidget, *args, **kwargs)
		self.toModul = destModul
		self.multiple = multiple
		self.format = format
		self.overlay = Overlay(self)
		self.kind = kind
		if not self.multiple:
			self.layout = QtWidgets.QHBoxLayout(self)
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
			self.selection = None
		else:
			self.selection = []
			self.layout.addWidget(self.addBtn)

	@classmethod
	def fromSkelStructure(cls, moduleName, boneName, skelStructure, **kwargs):
		readOnly = "readonly" in skelStructure[boneName].keys() and skelStructure[boneName]["readonly"]
		multiple = skelStructure[boneName]["multiple"]
		kind = skelStructure[boneName]["type"].split(".")[1]
		if "modul" in skelStructure[boneName].keys():
			destModul = skelStructure[boneName]["modul"]
		else:
			destModul = kind
		format = "$(name)"
		if "format" in skelStructure[boneName].keys():
			format = skelStructure[boneName]["format"]
		return cls(moduleName, boneName, readOnly, kind, destModul, multiple, format, **kwargs)

	def installAutoCompletion(self):
		"""
			Installs our autoCompleter on self.entry if possible
		"""
		if not self.multiple:
			self.autoCompletionModel = AutocompletionModel(self.toModul, self.format, {})  # FIXME: {} was
			# self.skelStructure
			self.autoCompleter = QtWidgets.QCompleter(self.autoCompletionModel)
			self.autoCompleter.setModel(self.autoCompletionModel)
			self.autoCompleter.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
			self.entry.setCompleter(self.autoCompleter)
			self.entry.textChanged.connect(self.reloadAutocompletion)
			self.autoCompleter.activated.connect(self.setAutoCompletion)  # Broken...
			self.autoCompleter.highlighted.connect(self.setAutoCompletion)

	def updateVisiblePreview(self):
		realModule = self.toModul
		if realModule.endswith("_rootNode"):
			realModule = realModule.replace("_rootNode", "")
		protoWrap = protocolWrapperInstanceSelector.select(realModule)
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
		if self.multiple:
			widgetItem = self.previewLayout.takeAt(0)
			while widgetItem:
				widgetItem = self.previewLayout.takeAt(0)
			if self.selection and len(self.selection) > 0:
				for item in self.selection:
					lbl = QtWidgets.QLabel(self.previewWidget)
					lbl.setText(formatString(self.format, structure, item))
					self.previewLayout.addWidget(lbl)
				self.addBtn.setText("Auswahl ändern")
			else:
				self.addBtn.setText("Auswählen")
		else:
			if self.selection:
				self.entry.setText(formatString(self.format, structure, self.selection))
			else:
				self.entry.setText("")

	def reloadAutocompletion(self, text):
		if text and len(text) > 2:
			self.autoCompletionModel.setCompletionPrefix(text)

	def setAutoCompletion(self, label):
		res = self.autoCompletionModel.getItem(label)
		if res:
			self.setSelection([res])

	def setSelection(self, selection):
		if self.multiple:
			self.selection = selection
		elif len(selection) > 0:
			self.selection = selection[0]
		else:
			self.selection = None
		self.updateVisiblePreview()

	def onAddBtnReleased(self, *args, **kwargs):
		editWidget = RelationalBoneSelector(self.moduleName, self.boneName, self.multiple, self.toModul, self.selection)
		editWidget.selectionChanged.connect(self.setSelection)

	def onDelBtnReleased(self, *args, **kwargs):
		if self.multiple:
			self.selection = []
		else:
			self.selection = None
		self.updateVisiblePreview()

	def unserialize(self, data):
		self.selection = data[self.boneName]
		self.updateVisiblePreview()

	def serializeForPost(self):
		if not self.selection:
			return {self.boneName: None}
		if self.multiple:
			return {self.boneName: [str(x["id"]) for x in self.selection]}
		elif self.selection:
			return {self.boneName: str(self.selection["id"])}
		else:
			return {self.boneName: None}


class RelationalBoneSelector(QtWidgets.QWidget):
	selectionChanged = QtCore.pyqtSignal((object,))
	displaySourceWidget = ListWidget
	displaySelectionWidget = SelectedEntitiesWidget
	GarbageTypeName = "RelationalBoneSelector"

	def __init__(self, moduleName, boneName, multiple, toModul, selection, *args, **kwargs):
		super(RelationalBoneSelector, self).__init__(*args, **kwargs)
		self.moduleName = moduleName
		self.boneName = boneName
		self.multiple = multiple
		self.modul = toModul
		self.selection = selection
		self.ui = Ui_relationalSelector()
		self.ui.setupUi(self)
		layout = QtWidgets.QHBoxLayout(self.ui.tableWidget)
		self.ui.tableWidget.setLayout(layout)
		self.list = self.displaySourceWidget(self.modul, editOnDoubleClick=False, parent=self)
		layout.addWidget(self.list)
		self.list.show()
		layout = QtWidgets.QHBoxLayout(self.ui.listSelected)
		self.ui.listSelected.setLayout(layout)
		self.selection = self.displaySelectionWidget(self.modul, selection, parent=self)
		layout.addWidget(self.selection)
		self.selection.show()
		if not self.multiple:
			# self.list.setSelectionMode( self.list.SingleSelection )
			self.selection.hide()
			self.ui.lblSelected.hide()
		self.list.itemDoubleClicked.connect(self.onSourceItemDoubleClicked)
		self.list.itemClicked.connect(self.onItemClicked)
		self.ui.btnSelect.clicked.connect(self.onBtnSelectReleased)
		self.ui.btnCancel.clicked.connect(self.onBtnCancelReleased)
		event.emit('stackWidget', self)

	def getBreadCrumb(self):
		protoWrap = protocolWrapperInstanceSelector.select(self.moduleName)
		assert protoWrap is not None
		# FIXME: Bad hack to get the editWidget we belong to
		skel = None
		for widget in WidgetHandler.mainWindow.handlerForWidget(self).widgets:
			if isinstance(widget, EditWidget):
				if not widget.key or widget.clone:  # We're adding a new entry
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
		assert self.boneName in skel.keys()
		return QtCore.QCoreApplication.translate("RelationalBoneSelector", "Select %s") % skel[self.boneName][
			"descr"], QtGui.QIcon(":icons/actions/change_selection.svg")

	def onSourceItemDoubleClicked(self, item):
		"""
			An item has been doubleClicked in our listWidget.
			Read its properties and add them to our selection.
		"""
		data = item
		if self.multiple:
			self.selection.extend([data])
		else:
			self.selectionChanged.emit([data])
			event.emit("popWidget", self)

	def onBtnSelectReleased(self, *args, **kwargs):
		print("onBtnSelectReleased")
		selection = self.selection.get()
		print("selection", selection)
		self.selectionChanged.emit(self.selection.get())
		event.emit("popWidget", self)

	def onBtnCancelReleased(self, *args, **kwargs):
		print("onBtnCancelReleased")
		event.emit("popWidget", self)

	def getFilter(self):
		return self.list.getFilter()

	def setFilter(self, filter):
		return self.list.setFilter(filter)

	def getModul(self):
		return self.list.getModul()

	def onItemClicked(self, item):
		print("RelationalBoneSelector.onItemClicked")
		pass


def CheckForRelationalicBone(moduleName, boneName, skelStucture):
	return skelStucture[boneName]["type"].startswith("relational.")


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForRelationalicBone, RelationalEditBone)
viewDelegateSelector.insert(2, CheckForRelationalicBone, RelationalViewBoneDelegate)
