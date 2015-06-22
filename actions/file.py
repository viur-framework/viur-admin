# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.priorityqueue import actionDelegateSelector


class FileUploadAction(QtWidgets.QAction):
	def __init__(self, parent, *args, **kwargs):
		super(FileUploadAction, self).__init__(QtGui.QIcon(":icons/actions/upload.svg"),
		                                       QtCore.QCoreApplication.translate("FileHandler", "Upload files"), parent)
		self.triggered.connect(self.onTriggered)
		self.setShortcut(QtGui.QKeySequence.New)
		self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

	def onTriggered(self, e):
		files, other = QtWidgets.QFileDialog.getOpenFileNames()
		print("file on triggered", files, repr(other))
		self.parent().doUpload(files, self.parent().getNode())

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
				print(self.parent().getNodeItemClass())
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
