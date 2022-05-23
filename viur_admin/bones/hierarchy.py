# -*- coding: utf-8 -*-
from typing import Any, List, Dict

from PyQt5 import QtWidgets

from viur_admin.log import getLogger

logger = getLogger(__name__)

from viur_admin.event import event
from viur_admin.bones.relational import RelationalViewBoneDelegate, RelationalEditBone, RelationalBoneSelector
from viur_admin.widgets.hierarchy import HierarchyWidget
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector


class HierarchyItemViewBoneDelegate(RelationalViewBoneDelegate):
	pass


class HierarchyItemBone(RelationalEditBone):
	def onAddBtnReleased(self, *args: Any, **kwargs: Any) -> None:
		editWidget = HierarchyBoneSelector(self.moduleName, self.boneName, self.multiple, self.toModule, self.selection)
		editWidget.selectionChanged.connect(self.setSelection)

	def installAutoCompletion(self) -> None:
		"""
			Prevent installing an autoCompletion for this module (not implementet yet)
		"""
		if not self.multiple:
			self.entry.setReadOnly(True)


class HierarchyBoneSelector(RelationalBoneSelector):
	displaySourceWidget = HierarchyWidget

	def onSourceItemDoubleClicked(self, item: QtWidgets.QListWidgetItem) -> None:
		"""
			An item has been doubleClicked in our listWidget.
			Read its properties and add them to our selection.
		"""
		data = item.entryData
		if self.multiple:
			self.selection.extend([data])
		else:
			self.selectionChanged.emit([data])
			event.emit("popWidget", self)


def CheckForHierarchyItemBone(
		moduleName: str,
		boneName: str,
		boneStructure: Dict[str, Any]) -> bool:
	return boneStructure["type"].startswith("hierarchy.")


viewDelegateSelector.insert(1, CheckForHierarchyItemBone, HierarchyItemViewBoneDelegate)
editBoneSelector.insert(1, CheckForHierarchyItemBone, HierarchyItemBone)
