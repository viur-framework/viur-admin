# -*- coding: utf-8 -*-

import os

import shutil
from collections import deque

from requests import Session, utils
from hashlib import sha1
from urllib.parse import quote

from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.config import conf
from viur_admin.log import getLogger
from viur_admin.network import NetworkService, nam
from viur_admin.priorityqueue import protocolWrapperInstanceSelector
from viur_admin.ui.fileDownloadProgressUI import Ui_FileDownloadProgress
from viur_admin.ui.fileUploadProgressUI import Ui_FileUploadProgress
from viur_admin.widgets.tree import TreeWidget, LeafItem, TreeListView

logger = getLogger(__name__)


class PreviewThread(QtCore.QThread):
	requestPreviewImage = QtCore.pyqtSignal((str))
	previewImageAvailable = QtCore.pyqtSignal((str, str, QtGui.QIcon))

	def __init__(self):
		super(PreviewThread, self).__init__()
		self.shouldTerminate = False
		self.taskQueue = deque()
		self.requestPreviewImage.connect(self.onRequestPreviewImage)
		self.threadThread = None
		self.start(QtCore.QThread.IdlePriority)
		while self.threadThread is None:
			self.usleep(5)

		self.baseUrl = None
		self.session = Session()

	def onLoginSuccess(self):
		cookies = nam.cookieJar().allCookies()

		cookieJar = self.session.cookies
		for cookie in cookies:
			logger.debug("raw cookie: %r, sessionCookie: %r", cookie.toRawForm(), cookie.isSessionCookie())
			dictCookie = {
				"name": bytes(cookie.name()).decode(),
				"value": bytes(cookie.value()).decode(),
				"secure": cookie.isSecure(),
				"path": cookie.path(),
				"domain": cookie.domain()
			}
			if not cookie.isSessionCookie():
				dictCookie["expires"] = cookie.expirationDate().toPyDateTime().timestamp()
			cookieJar.set(**dictCookie)

		self.baseUrl = NetworkService.url.replace("/admin", "")

	def downloadFile(self, url, absFilename):
		response = self.session.get(url, stream=True)
		newfile = open(absFilename, "wb+")
		shutil.copyfileobj(response.raw, newfile)
		newfile.seek(0)
		return newfile.read()

	def run(self):
		self.threadThread = self.currentThread()
		while not self.shouldTerminate:
			try:
				dlKey = self.taskQueue.popleft()
				fileName = os.path.join(conf.currentPortalConfigDirectory, sha1(dlKey.encode("UTF-8")).hexdigest())
				logger.debug("fileName: %r", fileName)
				if not os.path.isfile(fileName):
					fileData = self.downloadFile(
						"{0}{1}{2}".format(self.baseUrl, "/file/download/", quote(dlKey)),
						fileName
					)
				else:
					fileData = open(fileName, "rb").read()
				pixmap = QtGui.QPixmap()
				pixmap.loadFromData(fileData)

				if not pixmap.isNull():
					icon = QtGui.QIcon(pixmap.scaled(104, 104))
					self.previewImageAvailable.emit(dlKey, fileName, icon)
				self.msleep(25)
			except IndexError:
				self.sleep(1)

	def onRequestPreviewImage(self, dlkey):
		logger.debug("PreviewThread.onRequestPreviewImage: %r", dlkey)
		if dlkey not in self.taskQueue:
			self.taskQueue.append(dlkey)

	def requestPreview(self, dlkey):
		logger.debug("PreviewThread.requestPreview: %r", dlkey)
		self.requestPreviewImage.emit(dlkey)


previewer = PreviewThread()
iconByExtension = dict()


class FileItem(LeafItem):
	"""
		Displayes a file (including its preview if possible) inside a QListWidget.
	"""

	def __init__(self, data, parent):
		super(FileItem, self).__init__(data, parent)
		self.entryData = data

		extension = self.entryData["name"].split(".")[-1].lower()
		icon = iconByExtension.get(extension)
		if not icon:
			fileInfo = QtCore.QFileInfo(":icons/filetypes/%s.png" % extension)
			fileInfo2 = QtCore.QFileInfo(":icons/filetypes/%s.svg" % extension)
			if fileInfo2.exists():
				icon = QtGui.QIcon(":icons/filetypes/%s.svg" % extension)
			elif fileInfo.exists():
				icon = QtGui.QIcon(":icons/filetypes/%s.png" % extension)
			else:
				icon = QtGui.QIcon(":icons/filetypes/document.png")
			iconByExtension[extension] = icon
		self.setIcon(icon)
		if ("metamime" in data and str(data["metamime"]).lower().startswith("image")) or (
				extension in ["jpg", "jpeg", "png"] and "servingurl" in data and data["servingurl"]):
			previewer.requestPreview(data["dlkey"])
		self.setText(self.entryData["name"])


class UploadStatusWidget(QtWidgets.QWidget):
	"""
		Upload files and/or directories from the the local filesystem to the server.
		This one is recursive, it supports uploading of files in subdirectories as well.
		Subdirectories on the server are created as needed.
		The functionality is bound to a widget displaying the current progress.
		If downloading has finished, finished(PyQt_PyObject=self) is emited.
	"""

	def __init__(self, *args, **kwargs):
		"""Copy paste error

		TODO: fix the docs

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
		logger.debug("UploadStatusWidget.init: %r, %r", args, kwargs)

	def setUploader(self, uploader):
		self.uploader = uploader
		self.uploader.uploadProgress.connect(self.onUploadProgress)
		self.uploader.finished.connect(self.onFinished)
		self.ui.pbarTotal.setRange(0, uploader.stats["filesTotal"])

	def onBtnCancelReleased(self, *args, **kwargs):
		self.uploader.cancelUpload()

	def onUploadProgress(self, currentFileDone, currentFileTotal):
		stats = self.uploader.getStats()
		logger.debug("UploadStatusWidget.onUploadProgress: %r", stats)
		self.ui.lblProgress.setText(
			QtCore.QCoreApplication.translate(
				"FileHandler",
				"Files: %s/%s, Directories: %s/%s, Bytes: %s/%s") % (
				stats["filesDone"],
				stats["filesTotal"],
				stats["dirsDone"],
				stats["dirsTotal"],
				stats["bytesDone"],
				stats["bytesTotal"])
		)

		self.ui.pbarFile.setRange(0, currentFileTotal)
		self.ui.pbarFile.setValue(currentFileDone)
		self.ui.pbarTotal.setValue(stats["filesDone"])

	def askOverwriteFile(self, title, text):
		res = QtWidgets.QMessageBox.question(self, title, text,
		                                     buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
		                                             QtWidgets.QMessageBox.Cancel)
		if res == QtWidgets.QMessageBox.Yes:
			return True
		elif res == QtWidgets.QMessageBox.Cancel:
			return False
		return None

	def onFinished(self, req):
		self.deleteLater()


class DownloadStatusWidget(QtWidgets.QWidget):
	"""
		Download files and/or directories from the server into the local filesystem.
		The functionality is bound to a widget displaying the current progress.
		If downloading has finished, finished(PyQt_PyObject=self) is emited.
	"""

	directorySize = 15  # Let's count an directory as 15 Bytes

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
		logger.debug("DownloadStatusWidget.init: %r, %r, %r", downloader, args, kwargs)
		super(DownloadStatusWidget, self).__init__(*args, **kwargs)
		self.ui = Ui_FileDownloadProgress()
		self.ui.setupUi(self)
		self.downloader = downloader
		self.downloader.downloadProgress.connect(self.onDownloadProgress)
		self.downloader.finished.connect(self.onFinished)
		self.ui.btnCancel.released.connect(downloader.cancel)

	def onDownloadProgress(self, bytesDone, bytesTotal):
		"""Updates the process widget

		:param bytesDone:
		:type bytesDone: int
		:param bytesTotal:
		:type bytesTotal: int
		:return:
		"""
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

	def __init__(self, module, rootNode=None, node=None, *args, **kwargs):
		super(FileListView, self).__init__(module, rootNode, node, *args, **kwargs)
		previewer.previewImageAvailable.connect(self.onPreviewImageAvailable)

	def addItem(self, aitem):
		try:
			self.itemCache[aitem.entryData["dlkey"]] = aitem
		except:
			pass
		super(FileListView, self).addItem(aitem)

	def onPreviewImageAvailable(self, dlkey, fileName, icon):
		logger.debug("FileListView.onPreviewImageAvailable: %r, %r, %r", dlkey, fileName, icon)
		fileItem = self.itemCache[dlkey]
		fileItem.setIcon(icon)
		width = 400
		fileItem.setToolTip('<img src="{0}" width="{1}"><br>{2}'.format(
			fileName, width, str(fileItem.entryData["name"])))

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
		uploadStatusWidget = UploadStatusWidget()
		self.parent().layout().addWidget(uploadStatusWidget)
		protoWrap = protocolWrapperInstanceSelector.select(self.getModul())
		uploader = protoWrap.upload(files, node)
		uploadStatusWidget.setUploader(uploader)

	def doDownload(self, targetDir, files, dirs):
		"""
			Download a list of files and/or directories from the server to the local file-system.
			@param targetDir: Local, existing and absolute path
			@type targetDir: String
			@param files: List of files in this directory which should be downloaded
			@type files: list
			@param dirs: List of directories (in the directory specified by rootNode+path) which should be downloaded
			@type dirs: list
		"""
		protoWrap = protocolWrapperInstanceSelector.select(self.getModul())
		downloader = protoWrap.download(targetDir, files, dirs)
		self.parent().layout().addWidget(DownloadStatusWidget(downloader))

	def dropEvent(self, event):
		"""Allow Drag&Drop'ing from the local filesystem into our fileview
		"""
		if (all([str(file.toLocalFile()).startswith("file://") or str(file.toLocalFile()).startswith("/") or (
				len(str(file.toLocalFile())) > 0 and str(file.toLocalFile())[1] == ":") for file in
		         event.mimeData().urls()])) and len(event.mimeData().urls()) > 0:
			# Its an upload (files/dirs dragged from the local filesystem into our fileview)
			self.doUpload([file.toLocalFile() for file in event.mimeData().urls()], self.getNode())
		else:
			super(FileListView, self).dropEvent(event)

	def dragEnterEvent(self, event):
		"""Allow Drag&Drop'ing from the local filesystem into our fileview and dragging files out again
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
	"""Extension for TreeWidget to handle the specialities of files like Up&Downloading.
	"""

	treeWidget = FileListView

	def __init__(self, *args, **kwargs):
		previewer.onLoginSuccess()
		super(FileWidget, self).__init__(
			actions=["dirup", "mkdir", "upload", "download", "edit", "rename", "delete", "switchview"], *args, **kwargs)

	def doUpload(self, files, node):
		return self.tree.doUpload(files, node)

	def doDownload(self, targetDir, files, dirs):
		return self.tree.doDownload(targetDir, files, dirs)
