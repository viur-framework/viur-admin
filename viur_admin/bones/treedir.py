from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.bones.bone_interface import BoneEditInterface
from viur_admin.bones.relational import RelationalViewBoneDelegate, RelationalEditBone, RelationalBoneSelector
from viur_admin.event import event
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector
from viur_admin.utils import Overlay
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
			Prevent installing an autoCompletion for this modul (not implementet yet)
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
		# if not isinstance(item, self.list.getNodeItemClass()):
		# 	return
		#
		# data = item.entryData
		# if self.multiple:
		# 	self.selection.extend([data])
		# else:
		# 	self.selectionChanged.emit([data])
		# 	event.emit("popWidget", self)

	def onItemClicked(self, item):
		print("TreeDirBoneSelector.onItemClicked")
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
