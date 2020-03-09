# -*- coding: utf-8 -*-
from typing import Any, Dict, List

from viur_admin.widgets.file import FileListView
from viur_admin.widgets.tree import TreeWidget


class FileWidget(TreeWidget):
	"""
		Extension for TreeWidget to handle the specialities of files like Up&Downloading.
	"""

	treeWidget = FileListView

	def __init__(self, *args: Any, **kwargs: Any):
		super(FileWidget, self).__init__(
				actions=["dirup", "mkdir", "upload", "download", "edit", "rename", "delete", "switchview"], *args,
				**kwargs)
