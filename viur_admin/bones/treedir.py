# -*- coding: utf-8 -*-


from viur_admin.log import getLogger

logger = getLogger(__name__)

from viur_admin.bones.relational import RelationalViewBoneDelegate, RelationalEditBone, RelationalBoneSelector
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector
from viur_admin.widgets.selectedEntities import SelectedEntitiesWidget
from viur_admin.widgets.tree import TreeWidget


class TreeDirViewBoneDelegate(RelationalViewBoneDelegate):
	pass


class TreeDirBone(RelationalEditBone):
	skelType = "node"

	def onAddBtnReleased(self, *args, **kwargs):
		editWidget = TreeDirBoneSelector(self.moduleName, self.boneName, self.multiple, self.toModul,
		                                 self.selection)
		editWidget.selectionChanged.connect(self.setSelection)

	def installAutoCompletion(self):
		"""
			Prevent installing an autoCompletion for this module (not implementet yet)
		"""
		if not self.multiple:
			self.entry.setReadOnly(True)


class TreeSelectedEntities(SelectedEntitiesWidget):
	skelType = "node"


class TreeDirBoneSelector(RelationalBoneSelector):
	displaySourceWidget = TreeWidget
	displaySelectionWidget = TreeSelectedEntities

	def onSourceItemDoubleClicked(self, item):
		"""
			An item has been doubleClicked in our listWidget.
			Read its properties and add them to our selection.
		"""
		return

	def onSourceItemClicked(self, item):
		if not isinstance(item, self.list.getNodeItemClass()):
			return

		data = item.entryData
		selection = self.selection.get()
		if data in selection:
			self.selection.set([])
		else:
			self.selection.set([data])


def CheckForTreeDirBone(moduleName, boneName, skelStucture):
	return skelStucture[boneName]["type"].startswith("treedir.")


# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForTreeDirBone, TreeDirBone)
viewDelegateSelector.insert(2, CheckForTreeDirBone, TreeDirViewBoneDelegate)
