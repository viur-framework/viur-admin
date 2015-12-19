# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.ui.fileUploadProgressUI import Ui_FileUploadProgress
from viur_admin.ui.fileDownloadProgressUI import Ui_FileDownloadProgress
from viur_admin.network import RemoteFile
from viur_admin.widgets.tree import TreeWidget, LeafItem, TreeListView
from viur_admin.priorityqueue import protocolWrapperInstanceSelector


class FileItem(LeafItem):
	"""
		Displayes a file (including its preview if possible) inside a QListWidget.
	"""

	def __init__(self, data, parent):
		super(FileItem, self).__init__(data, parent)
		self.entryData = data
		extension = self.entryData["name"].split(".")[-1].lower()
		print("extension", extension)
		fileInfo = QtCore.QFileInfo(":icons/filetypes/%s.png" % extension)
		fileInfo2 = QtCore.QFileInfo(":icons/filetypes/%s.svg" % extension)
		if fileInfo2.exists():
			icon = QtGui.QIcon(":icons/filetypes/%s.svg" % (extension))
		elif fileInfo.exists():
			icon = QtGui.QIcon(":icons/filetypes/%s.png" % (extension))
		else:
			icon = QtGui.QIcon(":icons/filetypes/unknown.png")
		self.setIcon(icon)
		if ("metamime" in data.keys() and str(data["metamime"]).lower().startswith("image")) or (
							extension in ["jpg", "jpeg", "png"] and "servingurl" in data.keys() and data["servingurl"]):
			RemoteFile(data["dlkey"], successHandler=self.updateIcon)
		self.setText(self.entryData["name"][:20])

	def updateIcon(self, remoteFile):
		pixmap = QtGui.QPixmap()
		pixmap.loadFromData(remoteFile.getFileContents())
		if not pixmap.isNull():
			icon = QtGui.QIcon(pixmap.scaled(104, 104))
			self.setIcon(icon)
			self.setToolTip("<img src=\"%s\" width=\"200\" height=\"200\"><br>%s" % (
				remoteFile.getFileName(), str(self.entryData["name"])))
			self.listWidget().setViewMode(0)
			self.listWidget().setViewMode(1)


class UploadStatusWidget(QtWidgets.QWidget):
	"""
		Upload files and/or directories from the the local filesystem to the server.
		This one is recursive, it supports uploading of files in subdirectories as well.
		Subdirectories on the server are created as needed.
		The functionality is bound to a widget displaying the current progress.
		If downloading has finished, finished(PyQt_PyObject=self) is emited.
	"""

	directorySize = 15  # Let's count an directory as 15 Bytes

	def __init__(self, uploader, *args, **kwargs):
		"""
			@param files: List of local files or directories (including thier absolute path) which will be uploaded.
			@type files: List
			@param rootNode: Destination rootNode
			@type rootNode: String
			@param path: Remote destination path, relative to rootNode.
			@type path: String
			@param modul: Modulname to upload to (usually "file")
			@type modul: String
		"""
		super(UploadStatusWidget, self).__init__(*args, **kwargs)
		self.ui = Ui_FileUploadProgress()
		self.ui.setupUi(self)
		self.uploader = uploader
		self.uploader.uploadProgress.connect(self.onUploadProgress)
		self.uploader.finished.connect(self.onFinished)
		self.ui.btnCancel.released.connect(uploader.cancel)

	def onBtnCancelReleased(self, *args, **kwargs):
		self.uploader.cancelUpload()

	def onUploadProgress(self, bytesSend, bytesTotal):
		stats = self.uploader.getStats()
		self.ui.lblProgress.setText(
			QtCore.QCoreApplication.translate("FileHandler", "Files: %s/%s, Directories: %s/%s, Bytes: %s/%s") % (
				stats["filesDone"], stats["filesTotal"], stats["dirsDone"], stats["dirsTotal"], stats["bytesDone"],
				stats["bytesTotal"]))
		self.ui.pbarTotal.setRange(0, stats["filesTotal"])
		self.ui.pbarTotal.setValue(stats["filesDone"])
		self.ui.pbarFile.setRange(0, stats["bytesTotal"])
		self.ui.pbarFile.setValue(stats["bytesDone"])

	def askOverwriteFile(self, title, text):
		res = QtWidgets.QMessageBox.question(self, title, text,
		                                     buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
		                                             QtWidgets.QMessageBox.Cancel)
		if res == QtWidgets.QMessageBox.Yes:
			return (True)
		elif res == QtWidgets.QMessageBox.Cancel:
			return (False)
		return (None)

	def onFinished(self, req):
		self.deleteLater()


class DownloadStatusWidget(QtWidgets.QWidget):
	"""
		Download files and/or directories from the server into the local filesystem.
		The functionality is bound to a widget displaying the current progress.
		If downloading has finished, finished(PyQt_PyObject=self) is emited.
	"""

	directorySize = 15  # Letz count an directory as 15 Bytes

	def __init__(self, downloader, *args, **kwargs):
		"""
			@param localTargetDir: Local, existing and absolute destination-path
			@type localTargetDir: String
			@param rootNode: RootNode to download from
			@type rootNode: String
			@param path: Remote path, relative to rootNode.
			@type path: String
			@param files: List of files in the given remote path
			@type files: List
			@param dirs: List of directories in the given remote path
			@type dirs: List
			@param modul: Modulname to download from (usually "file")
			@type modul: String
		"""
		super(DownloadStatusWidget, self).__init__(*args, **kwargs)
		self.ui = Ui_FileDownloadProgress()
		self.ui.setupUi(self)
		self.downloader = downloader
		self.downloader.downloadProgress.connect(self.onDownloadProgress)
		self.downloader.finished.connect(self.onFinished)

	# self.ui.btnCancel.released.connect( downloader.cancel )

	def onDownloadProgress(self, bytesDone, bytesTotal):
		stats = self.downloader.getStats()
		self.ui.lblProgress.setText(
			QtCore.QCoreApplication.translate("FileHandler", "Files: %s/%s, Directories: %s/%s, Bytes: %s/%s") % (
				stats["filesDone"], stats["filesTotal"], stats["dirsDone"], stats["dirsTotal"], stats["bytesDone"],
				stats["bytesTotal"]))
		self.ui.pbarTotal.setRange(0, stats["filesTotal"])
		self.ui.pbarTotal.setValue(stats["filesDone"])

	def onFinished(self, req):
		self.deleteLater()


class FileListView(TreeListView):
	leafItem = FileItem

	def doUpload(self, files, node):
		"""
			Uploads a list of files to the Server and adds them to the given path on the server.
			@param files: List of local filenames including their full, absolute path
			@type files: List
			@param rootNode: RootNode which will recive the uploads
			@type rootNode: String
			@param path: Path (server-side) relative to the given RootNode
			@type path: String
		"""
		if not files:
			return
		protoWrap = protocolWrapperInstanceSelector.select(self.getModul())
		uploader = protoWrap.upload(files, node)
		self.parent().layout().addWidget(UploadStatusWidget(uploader))

	# uploader = RecursiveUploader( files, rootNode, path, self.getModul() )
	# self.ui.boxUpload.addWidget( uploader )
	# self.connect( uploader, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.onTransferFinished )
	# self.connect( uploader, QtCore.SIGNAL("failed(PyQt_PyObject)"), self.onTransferFailed )

	def doDownload(self, targetDir, files, dirs):
		"""
			Download a list of files and/or directories from the server to the local file-system.
			@param targetDir: Local, existing and absolute path
			@type targetDir: String
			@param rootNode: RootNode to download from
			@type rootNode: String
			@param path: Path relative to the RootNode containing the files and directories which should be downloaded
			@type path: String
			@param files: List of files in this directory which should be downloaded
			@type files: List
			@param dirs: List of directories (in the directory specified by rootNode+path) which should be downloaded
			@type dirs: List
		"""
		protoWrap = protocolWrapperInstanceSelector.select(self.getModul())
		downloader = protoWrap.download(targetDir, files, dirs)
		self.parent().layout().addWidget(DownloadStatusWidget(downloader))

	def dropEvent(self, event):
		"""
			Allow Drag&Drop'ing from the local filesystem into our fileview
		"""
		if (all([str(file.toLocalFile()).startswith("file://") or str(file.toLocalFile()).startswith("/") or (
						len(str(file.toLocalFile())) > 0 and str(file.toLocalFile())[1] == ":") for file in
		         event.mimeData().urls()])) and len(event.mimeData().urls()) > 0:
			# Its an upload (files/dirs draged from the local filesystem into our fileview)
			self.doUpload([file.toLocalFile() for file in event.mimeData().urls()], self.getNode())
		else:
			super(FileListView, self).dropEvent(event)

	def dragEnterEvent(self, event):
		"""
			Allow Drag&Drop'ing from the local filesystem into our fileview and dragging files out again
			(drag directorys out isnt currently supported)
		"""
		if (all([file.toLocalFile() and (
						str(file.toLocalFile()).startswith("file://") or str(file.toLocalFile()).startswith("/") or
						str(file.toLocalFile())[1] == ":") for file in event.mimeData().urls()])) and len(
			event.mimeData().urls()) > 0:
			event.accept()
		else:
			super(FileListView, self).dragEnterEvent(event)


class FileWidget(TreeWidget):
	"""
		Extension for TreeWidget to handle the specialities of files like Up&Downloading.
	"""

	treeWidget = FileListView

	def __init__(self, *args, **kwargs):
		super(FileWidget, self).__init__(
			actions=["dirup", "mkdir", "upload", "download", "edit", "rename", "delete", "switchview"], *args, **kwargs)

	def doUpload(self, files, node):
		return (self.tree.doUpload(files, node))

	def doDownload(self, targetDir, files, dirs):
		return (self.tree.doDownload(targetDir, files, dirs))
