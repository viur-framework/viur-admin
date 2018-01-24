# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
from viur_admin.log import getLogger

from viur_admin.priorityqueue import actionDelegateSelector

logger = getLogger(__name__)


class FileUploadAction(QtWidgets.QAction):
	def __init__(self, parent, *args, **kwargs):
		super(FileUploadAction, self).__init__(QtGui.QIcon(":icons/actions/upload.svg"),
		                                       QtCore.QCoreApplication.translate("FileHandler", "Upload files"), parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.New)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self, e):
		homeDirs = QtCore.QStandardPaths.standardLocations(QtCore.QStandardPaths.HomeLocation)
		logger.debug("homeDirs: %r", homeDirs)
		files, other = QtWidgets.QFileDialog.getOpenFileNames(directory=homeDirs[0])
		print("file on triggered", files, repr(other))
		self.parent().doUpload(files, self.parent().getNode())

		# TODO: all this shit would be needed for being able to select both dirs and files, but it's also buggy.
		# TODO: if you go down into a directory hierarchy, all directories on the path and the files get selected. SO SAD!
		# dlg = QtWidgets.QFileDialog()
		# dlg.setFileMode(QtWidgets.QFileDialog.Directory)
		# dlg.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
		# listView = dlg.findChild(QtWidgets.QListView, "listView")
		# if listView:
		# 	listView.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
		# treeView = dlg.findChild(QtWidgets.QTreeView)
		# if treeView:
		# 	treeView.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
		# status = dlg.exec()
		# if status:
		# 	files = dlg.selectedFiles()
		# 	logger.debug("FileUploadAction upload instance: %r", self.parent())
		# 	self.parent().doUpload(files, self.parent().getNode())

	@staticmethod
	def isSuitableFor(modul, actionName):
		return (modul == "tree.simple.file" or modul.startswith("tree.simple.file.")) and actionName == "upload"


actionDelegateSelector.insert(3, FileUploadAction.isSuitableFor, FileUploadAction)


class FileDownloadAction(QtWidgets.QAction):
	def __init__(self, parent, *args, **kwargs):
		super(FileDownloadAction, self).__init__(QtGui.QIcon(":icons/actions/download.svg"),
		                                         QtCore.QCoreApplication.translate("FileHandler", "Download files"),
		                                         parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.Save)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self, e):
		dirs = []
		files = []
		for item in self.parent().selectedItems():
			if isinstance(item, self.parent().getNodeItemClass()):
				dirs.append(item.entryData)
			else:
				files.append(item.entryData)
		if not files and not dirs:
			return
		targetDir = QtWidgets.QFileDialog.getExistingDirectory(self.parentWidget())
		if not targetDir:
			return
		self.parent().doDownload(targetDir, files, dirs)

	@staticmethod
	def isSuitableFor(modul, actionName):
		return (modul == "tree.simple.file" or modul.startswith("tree.simple.file.")) and actionName == "download"


actionDelegateSelector.insert(3, FileDownloadAction.isSuitableFor, FileDownloadAction)
