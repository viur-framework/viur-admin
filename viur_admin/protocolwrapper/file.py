#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

from collections import deque
from typing import Sequence, List, Any, Dict

from PyQt5 import QtCore

from viur_admin.config import conf
from viur_admin.log import getLogger
from viur_admin.network import NetworkService, RequestWrapper
from viur_admin.priorityqueue import protocolWrapperClassSelector
from viur_admin.protocolwrapper.tree import TreeWrapper

logger = getLogger(__name__)


def x_startswith_dot(x: str) -> bool:
	# print(repr(x))
	return x.startswith("."),


def x_lower(x: str) -> bool:
	# print(repr(x))
	return x.lower == "thumbs.db"


def x_startswith_tilde(x: str) -> bool:
	# print(repr(x))
	return x.startswith("~") or x.endswith("~")


# List of patterns of filenames/directories, which wont get uploaded
ignorePatterns = [
	# x_startswith_dot,
	# x_lower,
	# x_startswith_tilde,
	lambda x: x.startswith("."),  # All files/dirs starting with a dot (".")
	lambda x: x.lower() == "thumbs.db",  # Thumbs.DB,
	lambda x: x.startswith("~") or x.endswith("~")  # Temp files (usually starts/ends with ~)
]


class FileUploader(QtCore.QObject):
	uploadProgress = QtCore.pyqtSignal((int, int))
	succeeded = QtCore.pyqtSignal(dict)
	failed = QtCore.pyqtSignal()
	cancel = QtCore.pyqtSignal()

	def __init__(
			self,
			fileName: str,
			node: str = None,
			*args: Any,
			**kwargs: Any):
		"""
		Uploads a file to the Server

		@param fileName: Full Filename (and Path)
		@type fileName: str
		@param node: ID of the target rootNode
		@type node: str
		"""
		super(FileUploader, self).__init__(*args, **kwargs)
		self.fileName = fileName
		self.node = node
		self.isCanceled = False
		self.hasFinished = False
		self.cancel.connect(self.onCanceled)
		self.bytesTotal = os.path.getsize(self.fileName.encode(sys.getfilesystemencoding()))
		logger.debug("FileUploader sizeof: %r, %r", fileName, self.bytesTotal)
		self.bytesDone = 0
		NetworkService.request("/file/getUploadURL", successHandler=self.startUpload, secure=True)

	def startUpload(self, req: RequestWrapper) -> None:
		self.uploadProgress.emit(0, 1)
		url = req.readAll().data().decode("UTF-8")
		myFile = QtCore.QFile(self.fileName)
		myFile.open(QtCore.QIODevice.ReadOnly)
		params = {"Filedata": myFile}
		if self.node:
			params["node"] = self.node
		req = NetworkService.request(url, params, finishedHandler=self.onFinished)
		req.uploadProgress.connect(self.onProgress)

	def onFinished(self, req: RequestWrapper) -> None:
		try:
			data = NetworkService.decode(req)
		except:
			self.hasFinished = True
			self.failed.emit()
			return
		self.bytesDone = self.bytesTotal
		self.hasFinished = True
		self.succeeded.emit(data)

	def onProgress(self, req: RequestWrapper, bytesSend: int, bytesTotal: int) -> None:
		logger.debug("FileUploader.onProgress: %r, %r, %r", req, bytesSend, bytesTotal)
		self.bytesTotal = bytesTotal
		self.bytesDone = bytesSend
		self.uploadProgress.emit(bytesSend, bytesTotal)
		if self.isCanceled:
			req.abort()

	def getStats(self) -> None:
		stats = {
			"dirsTotal": 0,
			"dirsDone": 0,
			"filesTotal": 1,
			"filesDone": 1 if self.bytesDone == self.bytesTotal else 0,
			"bytesTotal": self.bytesTotal,
			"bytesDone": self.bytesDone
		}
		logger.debug("FileUploader.getStats: %r", stats)
		return stats

	def onCanceled(self) -> None:
		self.isCanceled = True


class RecursiveUploader(QtCore.QObject):
	"""Upload files and/or directories from the the local filesystem to the server.

	This one is recursive, it supports uploading of files in subdirectories as well.
	Subdirectories on the server are created as needed.
	The functionality is bound to a widget displaying the current progress.
	If downloading has finished, finished(PyQt_PyObject=self) is emited.
	"""

	directorySize = 15  # Let's count an directory as 15 Bytes
	finished = QtCore.pyqtSignal(QtCore.QObject)
	failed = QtCore.pyqtSignal(QtCore.QObject)
	uploadProgress = QtCore.pyqtSignal((int, int))
	cancel = QtCore.pyqtSignal()

	def getDirName(self, name: str) -> str:
		name, head = os.path.split(name)
		if head:
			return head
		name, head = os.path.split(name)
		if head:
			return head
		else:
			return name

	def __init__(
			self,
			files: List[Any],
			node: str,
			module: str,
			stats: Any,
			*args: Any,
			**kwargs: Any):
		"""
			@param files: List of local files or directories (including their absolute path) which will be uploaded.
			@type files: list
			@param node: Destination rootNode
			@type node: str
			@param path: Remote destination path, relative to rootNode.
			@type path: str
			@param module: Modulname to upload to (usually "file")
			@type module: str
		"""
		super(RecursiveUploader, self).__init__(*args, **kwargs)
		logger.debug("RecursiveUploader.init: %r, %r, %r, %r, %r, %r", files, node, module, stats, args, kwargs)
		self.node = node
		self.module = module
		self.hasFinished = False
		self.taskQueue: deque = deque()
		self.runningTasks = 0
		filteredFiles = [
			x for x in files if
			conf.cmdLineOpts.noignore or not any([pattern(x) for pattern in ignorePatterns])]
		# self.recursionInfo = [ (  ) ] , [node], {}) ]
		self.cancel.connect(self.onCanceled)
		self.isCanceled = False
		if stats:
			self.stats = stats
			logger.debug("initialsStats: %r, %r", stats["filesTotal"], stats["bytesTotal"])
		else:
			self.stats = {
				"dirsTotal": 0,
				"dirsDone": 0,
				"filesTotal": 0,
				"filesDone": 0,
				"bytesTotal": 0,
				"bytesDone": 0
			}

		for fileName in filteredFiles:
			name, fname = os.path.split(fileName)
			if not fname:
				name, fname = os.path.split(name)
			if not conf.cmdLineOpts.noignore and any([pattern(fname) for pattern in ignorePatterns]):
				# We can ignore that file
				continue
			if os.path.isdir(fileName.encode(sys.getfilesystemencoding())):
				task = {
					"type": "netreq",
					"args": ["/{0}/list/node/{1}".format(self.module, self.node)],
					"kwargs": {"successHandler": self.onDirListAvailable},
					"uploadDirName": fileName}
				self.taskQueue.append(task)
			else:
				task = {
					"type": "upload",
					"args": [fileName, self.node],
					"kwargs": {"parent": self}}
				self.taskQueue.append(task)
		logger.debug("RecursiveUploader.init: %r", self.stats)
		# self.uploadProgress.emit(0, 0)
		self.launchNextRequest()
		self.tid = self.startTimer(150)

	def launchNextRequest(self) -> None:
		if not len(self.taskQueue):
			return
		if self.runningTasks > 1:
			return
		self.runningTasks += 1
		task = self.taskQueue.popleft()
		if task["type"] == "netreq":
			r = NetworkService.request(*task["args"], **task["kwargs"])
			r.uploadDirName = task["uploadDirName"]
		elif task["type"] == "upload":
			r = FileUploader(*task["args"], **task["kwargs"])
			r.uploadProgress.connect(self.onUploadProgress)
			r.succeeded.connect(self.onRequestFinished)
			self.cancel.connect(r.cancel)
		elif task["type"] == "rekul":
			r = RecursiveUploader(*task["args"], **task["kwargs"])
			r.uploadProgress.connect(self.uploadProgress)
			r.finished.connect(self.onRequestFinished)
			self.cancel.connect(r.cancel)
		else:
			raise NotImplementedError()

	def onRequestFinished(self, *args: Any, **kwargs: Any) -> None:
		self.runningTasks -= 1
		self.launchNextRequest()

	def timerEvent(self, e: QtCore.QTimerEvent) -> None:
		"""Check if we have busy tasks left
		"""

		super(RecursiveUploader, self).timerEvent(e)
		busy = self.runningTasks > 0

		if not busy:
			self.hasFinished = True
			self.finished.emit(self)
			self.killTimer(self.tid)

	def getStats(self) -> dict:
		stats = {
			"dirsTotal": 0,
			"dirsDone": 0,
			"filesTotal": 0,
			"filesDone": 0,
			"bytesTotal": 0,
			"bytesDone": 0
		}

		# Merge my stats in
		for k in stats:
			try:
				stats[k] += self.stats[k]
			except KeyError:
				pass
		for child in self.children():
			try:
				tmp = child.getStats()
				for k in stats:
					if isinstance(child, FileUploader) and k == "filesTotal":
						# We count files in advance; don't include FileUpload-Class while counting
						continue
					try:
						stats[k] += tmp[k]
					except KeyError as err:
						pass
					except TypeError as err:
						logger.error(
							"RecursiveUploader.getStats - error occurred while collecting stats from child: %r, %r, %r, %r",
							stats, tmp, child, k)
			# logger.exception(err)
			except AttributeError as err:
				# logger.exception(err)
				pass
		logger.debug("RecursiveUploader.getStats: %r", stats)
		return stats

	def onDirListAvailable(self, req: RequestWrapper) -> None:
		logger.debug("onDirListAvailable")
		self.runningTasks -= 1
		if self.isCanceled:
			return
		data = NetworkService.decode(req)
		for skel in data["skellist"]:
			if skel["name"].lower() == self.getDirName(req.uploadDirName).lower():
				logger.debug("onDirListAvailable: directory %r already exists", skel["name"])
				self.stats["dirsDone"] += 1

				task = {
					"type": "rekul",
					"args": [
						[os.path.join(req.uploadDirName, x) for x in os.listdir(req.uploadDirName)],
						skel["key"],
						self.module,
						None
					],
					"kwargs": {"parent": self}}
				self.taskQueue.append(task)
		else:
			task = {
				"type": "netreq",
				"args": [
					"/%s/add/" % self.module,
					{"node": self.node, "name": self.getDirName(req.uploadDirName), "skelType": "node"}],
				"kwargs": {"secure": True, "finishedHandler": self.onMkDir},
				"uploadDirName": req.uploadDirName}
			self.taskQueue.append(task)
		self.launchNextRequest()

	def onMkDir(self, req: RequestWrapper) -> None:
		if self.isCanceled:
			return
		data = NetworkService.decode(req)
		assert data["action"] == "addSuccess"
		self.stats["dirsDone"] += 1
		self.stats["bytesDone"] += self.directorySize
		self.runningTasks -= 1

		task = {
			"type": "rekul",
			"args": [
				[os.path.join(req.uploadDirName, x) for x in os.listdir(req.uploadDirName)],
				data["values"]["key"], self.module,
				None
			],
			"kwargs": {"parent": self}}
		self.taskQueue.append(task)
		self.launchNextRequest()

	def onCanceled(self, *args: Any, **kwargs: Any) -> None:
		self.isCanceled = True

	def onFailed(self, *args: Any, **kwargs: Any) -> None:
		self.failed.emit(self)

	def onUploadProgress(self, bytesSend: int, bytesTotal: int) -> None:
		logger.debug("RecursiveUploader.onUploadProgress: %r, %r", bytesSend, bytesTotal)
		self.uploadProgress.emit(bytesSend, bytesTotal)


class RecursiveDownloader(QtCore.QObject):
	"""
		Download files and/or directories from the server into the local filesystem.
		The functionality is bound to a widget displaying the current progress.
		If downloading has finished, finished(PyQt_PyObject=self) is emited.
	"""

	directorySize = 15  # Let's count an directory as 15 Bytes
	finished = QtCore.pyqtSignal(QtCore.QObject)
	failed = QtCore.pyqtSignal(QtCore.QObject)
	canceled = QtCore.pyqtSignal(QtCore.QObject)
	downloadProgress = QtCore.pyqtSignal((int, int))

	def __init__(
			self,
			localTargetDir: str,
			files: Sequence[str],
			dirs: Sequence[str],
			module: str,
			*args: Any,
			**kwargs: Any):
		"""
			@param localTargetDir: Local, existing and absolute destination-path
			@type localTargetDir: str
			@param rootNode: RootNode to download from
			@type rootNode: str
			@param path: Remote path, relative to rootNode.
			@type path: str
			@param files: List of files in the given remote path
			@type files: List
			@param dirs: List of directories in the given remote path
			@type dirs: List
			@param module: Modulname to download from (usually "file")
			@type module: str
		"""
		super(RecursiveDownloader, self).__init__(*args, **kwargs)
		self.localTargetDir = localTargetDir
		self.module = module
		self._cancel = False
		self.stats = {
			"dirsTotal": 0,
			"dirsDone": 0,
			"filesTotal": 0,
			"filesDone": 0,
			"bytesTotal": 0,
			"bytesDone": 0
		}
		self.remainingRequests = 0
		for file in files:
			self.remainingRequests += 1
			dlkey = "/%s/download/%s/file.dat" % (self.module, file["dlkey"])
			request = NetworkService.request(
				dlkey, successHandler=self.saveFile,
				finishedHandler=self.onRequestFinished)
			request.fname = file["name"]
			request.fsize = file["size"]
			request.downloadProgress.connect(self.onDownloadProgress)
			self.canceled.connect(request.abort)
			self.stats["filesTotal"] += 1
			self.stats["bytesTotal"] += file["size"]
		for directory in dirs:
			assert "~" not in directory["name"] and ".." not in directory["name"]
			for nodeType in ["node", "leaf"]:
				self.remainingRequests += 1
				if not os.path.exists(os.path.join(self.localTargetDir, directory["name"])):
					os.mkdir(os.path.join(self.localTargetDir, directory["name"]))

				request = NetworkService.request(
					"/{0}/list/{1}/{2}".format(self.module, nodeType, directory["key"]),
					successHandler=self.onListDir,
					finishedHandler=self.onRequestFinished)

				request.dname = directory["name"]
				request.ntype = nodeType
			self.stats["dirsTotal"] += 1
			self.stats["bytesTotal"] += self.directorySize

	def onRequestFinished(self, req: RequestWrapper) -> None:
		if self._cancel:
			return
		self.remainingRequests -= 1  # Decrease our request counter
		if self.remainingRequests == 0:
			QtCore.QTimer.singleShot(100, self.onFinished)

	def onFinished(self) -> None:
		# Delay emiting the finished signal
		self.finished.emit(self)

	def saveFile(self, req: RequestWrapper) -> None:
		if self._cancel:
			return
		fh = open(os.path.join(self.localTargetDir, req.fname), "wb+")
		fh.write(req.readAll().data())
		self.stats["filesDone"] += 1
		self.stats["bytesDone"] += req.fsize
		self.downloadProgress.emit(0, 0)

	def onDownloadProgress(self, bytesDone: int, bytesTotal: int) -> None:
		self.downloadProgress.emit(bytesDone, bytesTotal)

	# self.ui.pbarTotal.setRange( 0, bytesTotal )
	# self.ui.pbarTotal.setValue( bytesDone )

	def onListDir(self, req: RequestWrapper) -> None:
		if self._cancel:
			return
		data = NetworkService.decode(req)
		if len(data["skellist"]) == 0:  # Nothing to do here
			return
		if req.ntype == "node":
			self.remainingRequests += 1
			r = RecursiveDownloader(
				os.path.join(self.localTargetDir, req.dname),
				[],
				data["skellist"],
				self.module,
				parent=self)
			r.downloadProgress.connect(self.downloadProgress)
			r.finished.connect(self.onRequestFinished)
			self.canceled.connect(r.cancel)
		else:
			self.remainingRequests += 1
			self.stats["dirsDone"] += 1
			self.stats["bytesDone"] += self.directorySize
			r = RecursiveDownloader(
				os.path.join(self.localTargetDir, req.dname),
				data["skellist"],
				[],
				self.module,
				parent=self)
			r.downloadProgress.connect(self.downloadProgress)
			r.finished.connect(self.onRequestFinished)

	def getStats(self) -> dict:
		stats = {
			"dirsTotal": 0,
			"dirsDone": 0,
			"filesTotal": 0,
			"filesDone": 0,
			"bytesTotal": 0,
			"bytesDone": 0}
		# Merge my stats in
		for k in stats:
			stats[k] += self.stats[k]
		for child in self.children():
			if "getStats" in dir(child):
				tmp = child.getStats()
				for k in stats:
					stats[k] += tmp[k]
		return stats

	def cancel(self) -> None:
		self._cancel = True
		self.canceled.emit(self)


class FileWrapper(TreeWrapper):
	protocolWrapperInstancePriority = 3

	def __init__(self, *args: Any, **kwargs: Any):
		super(FileWrapper, self).__init__(*args, **kwargs)
		self.transferQueues: list = list()  # Keep a reference to uploader/downloader

	def buildStats(self, filteredFiles: Sequence[str]) -> dict:
		stats = {
			"dirsTotal": 0,
			"dirsDone": 0,
			"filesTotal": 0,
			"filesDone": 0,
			"bytesTotal": 0,
			"bytesDone": 0
		}

		for myPath in filteredFiles:
			if os.path.isdir(myPath.encode(sys.getfilesystemencoding())):
				stats["dirsTotal"] += 1  # for the root

				for root, directories, files in os.walk(myPath):
					encodedRoot = root.encode(sys.getfilesystemencoding())
					for item in files:
						encodedItem = item.encode(sys.getfilesystemencoding())
						print(repr(encodedRoot), repr(encodedItem))
						stats["bytesTotal"] += os.path.getsize(os.path.join(encodedRoot, encodedItem))
					stats["filesTotal"] += len(files)
					lenDirectories = len(directories)
					stats["dirsTotal"] += lenDirectories
					stats["bytesTotal"] += 15 * lenDirectories
			else:
				stats["filesTotal"] += 1
				stats["bytesTotal"] += os.path.getsize(myPath.encode(sys.getfilesystemencoding()))

		logger.debug("buildStats finished: %r, %r", stats["filesTotal"], stats["bytesTotal"])
		return stats

	def upload(self, files: Sequence[str], node: Sequence[str]) -> RecursiveUploader:
		"""
			Uploads a list of files to the Server and adds them to the given path on the server.
			@param files: List of local file names including their full, absolute path
			@type files: list
			@param node: RootNode which will receive the uploads
			@type node: str
		"""
		if not files:
			return

		filteredFiles = [
			x for x in files if
			conf.cmdLineOpts.noignore or not any([pattern(x) for pattern in ignorePatterns])]
		stats = self.buildStats(filteredFiles)
		uploader = RecursiveUploader(filteredFiles, node, self.module, stats, parent=self)
		uploader.finished.connect(self.delayEmitEntriesChanged)
		logger.debug("Filewrapper.upload: %r, %r, %r", files, node, uploader)
		return uploader

	def download(self, targetDir: str, files: Sequence[str], dirs: Sequence[str]) -> RecursiveDownloader:
		"""
			Download a list of files and/or directories from the server to the local file-system.
			@param targetDir: Local, existing and absolute path
			@type targetDir: str
			@param files: List of files in this directory which should be downloaded
			@type files: list
			@param dirs: List of directories (in the directory specified by rootNode+path) which should be downloaded
			@type dirs: list
		"""
		downloader = RecursiveDownloader(targetDir, files, dirs, self.module)
		downloader.finished.connect(self.delayEmitEntriesChanged)
		return downloader


def CheckForFileModul(moduleName: str, moduleList: str) -> bool:
	modulData = moduleList[moduleName]
	if "handler" in modulData and modulData["handler"].startswith("tree.simple.file"):
		return True
	return False


protocolWrapperClassSelector.insert(3, CheckForFileModul, FileWrapper)
