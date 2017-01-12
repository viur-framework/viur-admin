# -*- coding: utf-8 -*-

from viur_admin.widgets.file import FileListView
from viur_admin.widgets.tree import TreeWidget


class FileWidget(TreeWidget):
	"""
		Extension for TreeWidget to handle the specialities of files like Up&Downloading.
	"""

	treeWidget = FileListView

	def __init__(self, *args, **kwargs):
		super(FileWidget, self).__init__(
				actions=["dirup", "mkdir", "upload", "download", "edit", "rename", "delete", "switchview"], *args,
				**kwargs)
