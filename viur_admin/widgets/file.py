# -*- coding: utf-8 -*-

import os
import shutil
import time
from collections import deque
from hashlib import sha1
from typing import Union, List, Any, Dict
from urllib.parse import quote

from PyQt5 import QtCore, QtGui, QtWidgets
from viur_admin.pyodidehelper import isPyodide
if not isPyodide:
	from requests import Session

from viur_admin.config import conf
from viur_admin.log import getLogger
from viur_admin.network import NetworkService, nam, RequestWrapper
from viur_admin.priorityqueue import protocolWrapperInstanceSelector
from viur_admin.ui.fileDownloadProgressUI import Ui_FileDownloadProgress
from viur_admin.ui.fileUploadProgressUI import Ui_FileUploadProgress
from viur_admin.widgets.tree import TreeWidget, LeafItem, TreeListView
from viur_admin.utils import loadIcon
from time import sleep

logger = getLogger(__name__)
iconByExtension: Dict[str, QtGui.QIcon] = dict()


class PreviewDownloadWorker(QtCore.QObject):
	previewImageAvailable = QtCore.pyqtSignal(str, str, QtGui.QIcon, QtCore.QSize)
	previewPixmapAvailable = QtCore.pyqtSignal(str, str, QtGui.QPixmap)

	def __init__(self, cookies: Any, parent: QtWidgets.QWidget = None, pixmapMode=False):
		super(PreviewDownloadWorker, self).__init__(parent)
		self.taskQueue: deque = deque()
		if not isPyodide:
			self.session = Session()
		self.running = True
		self.pixmapMode = pixmapMode

		if cookies:
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

	@QtCore.pyqtSlot(str)
	def onRequestPreviewImage(self, dlKey: str, dlUrl: str) -> None:
		logger.debug("PreviewDownloadWorker.onRequestPreviewImage: %r", dlKey)
		self.taskQueue.append((dlKey, dlUrl))

	@QtCore.pyqtSlot()
	def onRequestStopRunning(self) -> None:
		logger.debug("previewTask request finishing...")
		self.running = False

	@QtCore.pyqtSlot()
	def work(self) -> None:
		while self.running:
			try:
				dlKey, dlUrl = self.taskQueue.popleft()
				fileName = os.path.join(conf.currentPortalConfigDirectory, sha1(dlKey.encode("UTF-8")).hexdigest())
				if not os.path.isfile(fileName):
					response = self.session.get(NetworkService.url.replace("/admin", "") + dlUrl,
					                            stream=True)
					newfile = open(fileName, "wb+")
					shutil.copyfileobj(response.raw, newfile)
					newfile.seek(0)
					fileData = newfile.read()
				else:
					fileData = open(fileName, "rb").read()

				pixmap = QtGui.QPixmap()
				pixmap.loadFromData(fileData)
				if not pixmap.isNull():
					if self.pixmapMode:
						self.previewPixmapAvailable.emit(dlKey, fileName, pixmap)
					else:
						icon = QtGui.QIcon()
						icon.addPixmap(pixmap.scaled(104, 104), QtGui.QIcon.Normal, QtGui.QIcon.On)
						self.previewImageAvailable.emit(dlKey, fileName, icon, pixmap.size())
			except IndexError:
				self.running = False

	def requestPreview(self, dlKey, dlUrl):
		self.requestPreviewImage.emit(dlKey, dlUrl)



class FileItem(LeafItem):
	"""Displays a file (including its preview if possible) inside a QListWidget.
	"""

	def __init__(self, data: Dict[str, Any], parent: QtWidgets.QWidget):
		super(FileItem, self).__init__(data, parent)
		extension = self.entryData["name"].split(".")[-1].lower()
		icon = iconByExtension.get(extension)
		if not icon:
			extensionToIconMap = {
				"png": "image-file",
				"jpg": "image-file",
				"jpeg": "image-file",
				"tiff": "image-file",
				"bmp": "image-file",
				"avi": "video-file",
				"mpg": "video-file",
				"mpeg": "video-file",
				"flv": "video-file",
				"ts": "video-file",
				"mp3": "audio-file",
				"wav": "audio-file",
				"pdf": "pdf-file",
			}
			if extension in extensionToIconMap:
				icon = loadIcon(extensionToIconMap[extension])
			else:
				icon = loadIcon("file")
			iconByExtension[extension] = icon
		self.setIcon(icon)
		#if ("mimetype" in data and str(data["mimetype"]).lower().startswith("image")):
		#	previewer.previewImageAvailable.connect(self.onPreviewImageAvailable)
		#	previewer.requestPreview(data["dlkey"], data["downloadUrl"])

		self.setToolTip('<strong>{0}</strong>'.format(data["name"]))
		if ("metamime" in data and str(data["metamime"]).lower().startswith("image")):
			self._parent.previewDownloadWorker.onRequestPreviewImage(data["dlkey"], data["downloadUrl"])
		self.setText(self.entryData["name"])


class UploadStatusWidget(QtWidgets.QWidget):
	"""Upload files and/or directories from the the local filesystem to the server.

	This one is recursive, it supports uploading of files in subdirectories as well.
	Subdirectories on the server are created as needed.
	The functionality is bound to a widget displaying the current progress.

	If downloading has finished, finished(PyQt_PyObject=self) is emited.
	"""

	def __init__(
			self,
			*args: Any,
			**kwargs: Any):
		"""This ctor creates an instance of our upload widget instance
		"""

		super(UploadStatusWidget, self).__init__(*args, **kwargs)
		self.ui = Ui_FileUploadProgress()
		self.ui.setupUi(self)
		self.uploader = None
		logger.debug("UploadStatusWidget.init: %r, %r", args, kwargs)
		self.ui.btnCancel.clicked.connect(self.onBtnCancelReleased)

	def setUploader(self, uploader: Any) -> None:
		self.uploader = uploader
		self.uploader.uploadProgress.connect(self.onUploadProgress)
		self.uploader.finished.connect(self.onFinished)
		self.uploader.failed.connect(self.onFinished)
		self.ui.pbarTotal.setRange(0, uploader.stats["filesTotal"])

	def onBtnCancelReleased(self) -> None:
		self.setDisabled(True)
		self.uploader.onCanceled()

	def onUploadProgress(
			self,
			currentFileDone: int,
			currentFileTotal: int) -> None:
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

	def askOverwriteFile(self, title: str, text: str) -> Union[bool, None]:
		res = QtWidgets.QMessageBox.question(
			self,
			title,
			text,
			buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
			        QtWidgets.QMessageBox.Cancel)
		if res == QtWidgets.QMessageBox.Yes:
			return True
		elif res == QtWidgets.QMessageBox.Cancel:
			return False
		return None

	def onFinished(self, req: RequestWrapper) -> None:
		self.deleteLater()


class DownloadStatusWidget(QtWidgets.QWidget):
	"""
		Download files and/or directories from the server into the local filesystem.
		The functionality is bound to a widget displaying the current progress.
		If downloading has finished, finished(PyQt_PyObject=self) is emited.
	"""

	directorySize = 15  # Let's count an directory as 15 Bytes

	def __init__(
			self,
			downloader: Any,
			*args: Any,
			**kwargs: Any):
		logger.debug("DownloadStatusWidget.init: %r, %r, %r", downloader, args, kwargs)
		super(DownloadStatusWidget, self).__init__(*args, **kwargs)
		self.ui = Ui_FileDownloadProgress()
		self.ui.setupUi(self)
		self.downloader = downloader
		self.downloader.downloadProgress.connect(self.onDownloadProgress)
		self.downloader.finished.connect(self.onFinished)
		self.ui.btnCancel.released.connect(downloader.cancel)

	def onDownloadProgress(self, bytesDone: int, bytesTotal: int) -> None:
		"""Updates the process widget

		:param bytesDone:
		:param bytesTotal:
		"""
		stats = self.downloader.getStats()
		self.ui.lblProgress.setText(
			QtCore.QCoreApplication.translate("FileHandler", "Files: %s/%s, Directories: %s/%s, Bytes: %s/%s") % (
				stats["filesDone"], stats["filesTotal"], stats["dirsDone"], stats["dirsTotal"], stats["bytesDone"],
				stats["bytesTotal"]))
		self.ui.pbarTotal.setRange(0, stats["filesTotal"])
		self.ui.pbarTotal.setValue(stats["filesDone"])

	def onFinished(self, req: RequestWrapper) -> None:
		self.deleteLater()


class FileListView(TreeListView):
	leafItem = FileItem

	requestPreview = QtCore.pyqtSignal(str)

	def __init__(
			self,
			module: str,
			rootNode: str = None,
			node: str = None,
			*args: Any,
			**kwargs: Any):
		super(FileListView, self).__init__(module, rootNode, node, *args, **kwargs)
		# raise Exception("here we are")
		if isPyodide:
			self.previewDownloadWorker = None
		else:
			self.thread = QtCore.QThread(self)
			self.thread.setObjectName('FileListView.previewDownloadThread')
			self.previewDownloadWorker = PreviewDownloadWorker(nam.cookieJar().allCookies())
			self.previewDownloadWorker.previewImageAvailable.connect(self.onPreviewImageAvailable)
			self.previewDownloadWorker.moveToThread(self.thread)
			self.requestPreview.connect(self.previewDownloadWorker.onRequestPreviewImage)
			self.thread.started.connect(self.previewDownloadWorker.work)
			self.thread.start(QtCore.QThread.IdlePriority)
			self.destroyed.connect(self.previewDownloadWorker.onRequestStopRunning)
			self.thread.finished.connect(self.thread.deleteLater)
		logger.debug("FileListView.__init__: thread started")

	def prepareDeletion(self) -> None:
		if not isPyodide:
			self.previewDownloadWorker.onRequestStopRunning()
			self.thread.quit()
			self.thread.wait()

	def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
		if not isPyodide:
			self.previewDownloadWorker.onRequestStopRunning()
			self.thread.quit()
			super(FileListView, self).closeEvent(a0)

	def addItem(self, item: Dict[str, Any]) -> None:
		try:
			self.itemCache[item.entryData["dlkey"]] = item
		except:
			pass
		super(FileListView, self).addItem(item)

	@QtCore.pyqtSlot(str)
	def onRequestPreview(self, dlKey: str) -> None:
		logger.debug("FileListView.onRequestPreview: %r", dlKey)
		if not isPyodide:
			self.requestPreview.emit(dlKey)

	def onPreviewImageAvailable(
			self,
			dlkey: str,
			fileName: str,
			icon: QtGui.QIcon,
			iconDims: Any) -> None:
		logger.debug("FileListView.onPreviewImageAvailable: %r, %r, %r", dlkey, fileName, icon)
		fileItem = self.itemCache.get(dlkey)
		# FIXME: why the fileitem was not found???
		if fileItem:
			fileItem.setIcon(icon)
			landScapeOrPortrait = iconDims.height() < iconDims.width()
			if landScapeOrPortrait:
				fileItem.setToolTip('<img src="{0}" height="{1}"><br><strong>{2}</strong>'.format(
					fileName, 400, str(fileItem.entryData["name"])))
			else:
				fileItem.setToolTip('<img src="{0}" width="{1}"><br><strong>{2}</strong>'.format(
					fileName, 400, str(fileItem.entryData["name"])))
		else:
			logger.warning("fileItem could not be found: dlkey=%r, filename=%r, icon=%r", dlkey, fileName, icon)

	def doUpload(
			self,
			files: List[str],
			node: str) -> None:
		"""Uploads a list of files to the Server and adds them to the given path on the server.

		:param files: List of local filenames including their full, absolute path
		:param node: the rootNode which will receive the uploads
		"""
		logger.debug("doUpload: %r, %r", files, node)
		if not files:
			return
		protoWrap = protocolWrapperInstanceSelector.select(self.getModul())
		protoWrap.upload(files, node)


	def doDownload(
			self,
			targetDir: str,
			files: List[str],
			dirs: List[str]) -> None:
		"""Download a list of files and/or directories from the server to the local file-system.

		:param targetDir: Local, existing and absolute path
		:param files: List of files in this directory which should be downloaded
		:param dirs: List of directories (in the directory specified by rootNode+path) which should be downloaded
		"""

		protoWrap = protocolWrapperInstanceSelector.select(self.getModul())
		downloader = protoWrap.download(targetDir, files, dirs)
		self.parent().layout().addWidget(DownloadStatusWidget(downloader))

	def htmlDropEvent(self, fileList):
		fileList = [fileList.item(x) for x in range(0, fileList.length)]
		if fileList:
			self.doUpload(fileList, self.getNode())

	def dropEvent(self, event: QtGui.QDropEvent) -> None:
		"""Allow Drag&Drop'ing from the local filesystem into our fileview
		"""
		if (all([str(file.toLocalFile()).startswith("file://") or str(file.toLocalFile()).startswith("/") or (
				len(str(file.toLocalFile())) > 0 and str(file.toLocalFile())[1] == ":") for file in
		         event.mimeData().urls()])) and len(event.mimeData().urls()) > 0:
			# Its an upload (files/dirs dragged from the local filesystem into our fileview)
			self.doUpload([file.toLocalFile() for file in event.mimeData().urls()], self.getNode())
		else:
			super(FileListView, self).dropEvent(event)

	def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
		logger.debug("TreeListWidget.dragMoveEvent")
		if (all([str(file.toLocalFile()).startswith("file://") or str(file.toLocalFile()).startswith("/") or (
				len(str(file.toLocalFile())) > 0 and str(file.toLocalFile())[1] == ":") for file in
				 event.mimeData().urls()])) and len(event.mimeData().urls()) > 0:
			event.accept()  # We have to accept external drops separately
		else:
			return super().dragMoveEvent(event)

	def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
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

	def __init__(
			self,
			*args: Any,
			**kwargs: Any):
		super(FileWidget, self).__init__(
			actions=["dirup", "mkdir", "upload", "download", "edit", "rename", "delete", "switchview"], *args, **kwargs)

	def prepareDeletion(self) -> None:
		self.tree.prepareDeletion()

	def doUpload(self, files: List[str], node: str) -> None:
		return self.tree.doUpload(files, node)

	def doDownload(self, targetDir: str, files: List[str], dirs: List[str]) -> None:
		return self.tree.doDownload(targetDir, files, dirs)
