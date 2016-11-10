#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

from PyQt5 import QtCore

from viur_admin.config import conf
from viur_admin.log import getLogger
from viur_admin.network import NetworkService, RequestGroup, RequestWrapper
from viur_admin.priorityqueue import protocolWrapperClassSelector
from viur_admin.protocolwrapper.tree import TreeWrapper

logger = getLogger(__name__)


def x_startswith_dot(x):
	# print(repr(x))
	return x.startswith("."),


def x_lower(x):
	# print(repr(x))
	return x.lower == "thumbs.db"


def x_startswith_tilde(x):
	# print(repr(x))
	return x.startswith("~") or x.endswith("~")


# List of patterns of filenames/directories, which wont get uploaded
ignorePatterns = [
	# x_startswith_dot,
	# x_lower,
	# x_startswith_tilde,
	lambda x: x.startswith("."),  # All files/dirs starting with a dot (".")
	lambda x: x.lower() == "thumbs.db",  # Thumbs.DB,
	lambda x: x.startswith("~") or x.endswith("~")  # Temp files (ususally starts/ends with ~)
]


class FileUploader(QtCore.QObject):
	uploadProgress = QtCore.pyqtSignal((int, int))
	succeeded = QtCore.pyqtSignal(dict)
	failed = QtCore.pyqtSignal()
	cancel = QtCore.pyqtSignal()

	def __init__(self, fileName, node=None, *args, **kwargs):
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

	def startUpload(self, req):
		self.uploadProgress.emit(0, 1)
		url = req.readAll().data().decode("UTF-8")
		params = {"Filedata": open(self.fileName.encode(sys.getfilesystemencoding()), "rb")}
		if self.node:
			params["node"] = self.node
		req = NetworkService.request(url, params, finishedHandler=self.onFinished)
		req.uploadProgress.connect(self.onProgress)

	def onFinished(self, req):
		try:
			data = NetworkService.decode(req)
		except:
			self.hasFinished = True
			self.failed.emit()
			return
		self.bytesDone = self.bytesTotal
		self.hasFinished = True
		self.succeeded.emit(data)

	def onProgress(self, req, bytesSend, bytesTotal):
		logger.debug("FileUploader.onProgress: %r, %r, %r", req, bytesSend, bytesTotal)
		self.bytesTotal = bytesTotal
		self.bytesDone = bytesSend
		self.uploadProgress.emit(bytesSend, bytesTotal)
		if self.isCanceled:
			req.abort()

	def getStats(self):
		stats = {
			"dirsTotal": 0,
			"dirsDone": 0,
			"filesTotal": 1,
			"filesDone": 1 if self.bytesDone == self.bytesTotal else 0,
			"bytesTotal": self.bytesTotal,
			"bytesDone": self.bytesDone}
		logger.debug("FileUploader.getStats: %r", stats)
		return stats

	def onCanceled(self):
		self.isCanceled = True


class RecursiveUploader(QtCore.QObject):
	"""
		Upload files and/or directories from the the local filesystem to the server.
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

	def getDirName(self, name):
		name, head = os.path.split(name)
		if head:
			return head
		name, head = os.path.split(name)
		if head:
			return head
		else:
			return name

	def __init__(self, files, node, module, *args, **kwargs):
		"""
			@param files: List of local files or directories (including thier absolute path) which will be uploaded.
			@type files: list
			@param node: Destination rootNode
			@type node: str
			@param path: Remote destination path, relative to rootNode.
			@type path: str
			@param module: Modulname to upload to (usually "file")
			@type module: str
		"""
		super(RecursiveUploader, self).__init__(*args, **kwargs)
		self.node = node
		self.module = module
		self.hasFinished = False
		filteredFiles = [
			x for x in files if
			conf.cmdLineOpts.noignore or not any([pattern(x) for pattern in ignorePatterns])]
		# self.recursionInfo = [ (  ) ] , [node], {}) ]
		self.cancel.connect(self.onCanceled)
		self.isCanceled = False
		self.stats = {
			"dirsTotal": 0,
			"dirsDone": 0,
			"filesTotal": 0,
			"filesDone": 0,
			"bytesTotal": 0,
			"bytesDone": 0}
		for fileName in filteredFiles:
			name, fname = os.path.split(fileName)
			if not fname:
				name, fname = os.path.split(name)
			if not conf.cmdLineOpts.noignore and any([pattern(fname) for pattern in ignorePatterns]):
				# We can ignore that file
				continue
			if os.path.isdir(fileName.encode(sys.getfilesystemencoding())):
				r = NetworkService.request("/%s/list/node/%s" % (self.module, self.node),
				                           successHandler=self.onDirListAvailable)
				r.uploadDirName = fileName
				self.stats["dirsTotal"] += 1
			else:
				r = FileUploader(fileName, self.node, parent=self)
				r.uploadProgress.connect(self.onUploadProgress)
				self.cancel.connect(r.cancel)
		logger.debug("RecursiveUploader.init: %r", self.stats)
		# self.uploadProgress.emit(0, 0)
		self.tid = self.startTimer(150)

	def timerEvent(self, e):
		"""
			Check if we have busy tasks left
		"""
		super(RecursiveUploader, self).timerEvent(e)
		busy = False
		for child in self.children():
			if isinstance(child, RequestWrapper) or isinstance(child, RequestGroup) or isinstance(child,
			                                                                                      FileUploader) or isinstance(
					child, RecursiveUploader):
				if not child.hasFinished:
					busy = True
					break
		if not busy:
			self.hasFinished = True
			self.finished.emit(self)
			self.killTimer(self.tid)

	def getStats(self):
		stats = {
			"dirsTotal": 0,
			"dirsDone": 0,
			"filesTotal": 0,
			"filesDone": 0,
			"bytesTotal": 0,
			"bytesDone": 0}
		# Merge my stats in
		for k in stats.keys():
			stats[k] += self.stats[k]
		for child in self.children():
			try:
				tmp = child.getStats()
				for k in stats.keys():
					try:
						stats[k] += tmp[k]
					except TypeError as err:
						logger.error(
							"RecursiveUploader.getStats - error occurred while collecting stats from child: %r, %r, %r, %r",
							stats, tmp, child, k)
						logger.exception(err)
			except AttributeError as err:
				logger.exception(err)
				pass
		logger.debug("RecursiveUploader.getStats: %r", stats)
		return stats

	def onDirListAvailable(self, req):
		logger.debug("onDirListAvailable")
		if self.isCanceled:
			return
		data = NetworkService.decode(req)
		for skel in data["skellist"]:
			if skel["name"].lower() == self.getDirName(req.uploadDirName).lower():
				logger.debug("onDirListAvailable dir: %r", skel["name"])
				# This directory allready exists
				self.stats["dirsDone"] += 1
				r = RecursiveUploader([os.path.join(req.uploadDirName, x) for x in os.listdir(req.uploadDirName)],
				                      skel["key"], self.module, parent=self)
				r.uploadProgress.connect(self.uploadProgress)
				self.cancel.connect(r.cancel)
				self.uploadProgress.emit(0, 1)
				return
		r = NetworkService.request("/%s/add/" % self.module,
		                           {"node": self.node, "name": self.getDirName(req.uploadDirName), "skelType": "node"},
		                           secure=True, finishedHandler=self.onMkDir)
		r.uploadDirName = req.uploadDirName
		self.uploadProgress.emit(0, 1)

	def onMkDir(self, req):
		if self.isCanceled:
			return
		data = NetworkService.decode(req)
		assert data["action"] == "addSuccess"
		self.stats["dirsDone"] += 1
		r = RecursiveUploader([os.path.join(req.uploadDirName, x) for x in os.listdir(req.uploadDirName)],
		                      data["values"]["key"], self.module, parent=self)
		r.uploadProgress.connect(self.uploadProgress)
		self.cancel.connect(r.cancel)
		self.uploadProgress.emit(0, 1)

	def onCanceled(self, *args, **kwargs):
		self.isCanceled = True

	def onFailed(self, *args, **kwargs):
		self.failed.emit(self)

	def onUploadProgress(self, bytesSend, bytesTotal):
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
	downloadProgress = QtCore.pyqtSignal((int, int))

	def __init__(self, localTargetDir, files, dirs, modul, *args, **kwargs):
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
			@param modul: Modulname to download from (usually "file")
			@type modul: str
		"""
		super(RecursiveDownloader, self).__init__(*args, **kwargs)
		self.localTargetDir = localTargetDir
		self.modul = modul
		self.cancel = False
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
			dlkey = "/%s/download/%s/file.dat" % (self.modul, file["dlkey"])
			request = NetworkService.request(
					dlkey, successHandler=self.saveFile,
					finishedHandler=self.onRequestFinished)
			request.fname = file["name"]
			request.fsize = file["size"]
			request.downloadProgress.connect(self.onDownloadProgress)
			self.stats["filesTotal"] += 1
			self.stats["bytesTotal"] += file["size"]
		for directory in dirs:
			assert "~" not in directory["name"] and ".." not in directory["name"]
			for t in ["node", "leaf"]:
				self.remainingRequests += 1
				if not os.path.exists(os.path.join(self.localTargetDir, directory["name"])):
					os.mkdir(os.path.join(self.localTargetDir, directory["name"]))
				request = NetworkService.request("/%s/list/%s/%s" % (self.modul, t, directory["key"]),
				                                 successHandler=self.onListDir, finishedHandler=self.onRequestFinished)
				request.dname = directory["name"]
				request.ntype = t
			self.stats["dirsTotal"] += 1
			self.stats["bytesTotal"] += self.directorySize

	def onRequestFinished(self, req):
		self.remainingRequests -= 1  # Decrease our request counter
		if self.remainingRequests == 0:
			QtCore.QTimer.singleShot(100, self.onFinished)

	def onFinished(self):
		# Delay emiting the finished signal
		self.finished.emit(self)

	def saveFile(self, req):
		fh = open(os.path.join(self.localTargetDir, req.fname), "wb+")
		fh.write(req.readAll().data())
		self.stats["filesDone"] += 1
		self.stats["bytesDone"] += req.fsize
		self.downloadProgress.emit(0, 0)

	def onDownloadProgress(self, bytesDone, bytesTotal):
		self.downloadProgress.emit(bytesDone, bytesTotal)

	# self.ui.pbarTotal.setRange( 0, bytesTotal )
	# self.ui.pbarTotal.setValue( bytesDone )

	def onListDir(self, req):
		data = NetworkService.decode(req)
		if len(data["skellist"]) == 0:  # Nothing to do here
			return
		if req.ntype == "node":
			self.remainingRequests += 1
			r = RecursiveDownloader(
					os.path.join(self.localTargetDir, req.dname),
					[],
					data["skellist"],
					self.modul,
					parent=self)
			r.downloadProgress.connect(self.downloadProgress)
			r.finished.connect(self.onRequestFinished)
		else:
			self.remainingRequests += 1
			self.stats["dirsDone"] += 1
			self.stats["bytesDone"] += self.directorySize
			r = RecursiveDownloader(
					os.path.join(self.localTargetDir, req.dname),
					data["skellist"],
					[],
					self.modul,
					parent=self)
			r.downloadProgress.connect(self.downloadProgress)
			r.finished.connect(self.onRequestFinished)

	def getStats(self):
		stats = {
			"dirsTotal": 0,
			"dirsDone": 0,
			"filesTotal": 0,
			"filesDone": 0,
			"bytesTotal": 0,
			"bytesDone": 0}
		# Merge my stats in
		for k in stats.keys():
			stats[k] += self.stats[k]
		for child in self.children():
			if "getStats" in dir(child):
				tmp = child.getStats()
				for k in stats.keys():
					stats[k] += tmp[k]
		return stats


class FileWrapper(TreeWrapper):
	protocolWrapperInstancePriority = 3

	def __init__(self, *args, **kwargs):
		super(FileWrapper, self).__init__(*args, **kwargs)
		self.transferQueues = []  # Keep a reference to uploader/downloader

	def upload(self, files, node):
		"""
			Uploads a list of files to the Server and adds them to the given path on the server.
			@param files: List of local file names including their full, absolute path
			@type files: list
			@param node: RootNode which will receive the uploads
			@type node: str
		"""
		if not files:
			return
		uploader = RecursiveUploader(files, node, self.module, parent=self)
		uploader.finished.connect(self.delayEmitEntriesChanged)
		return uploader

	def download(self, targetDir, files, dirs):
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
		self.downloader.finished.connect(self.delayEmitEntriesChanged)
		return downloader


def CheckForFileModul(moduleName, modulList):
	modulData = modulList[moduleName]
	if "handler" in modulData.keys() and modulData["handler"].startswith("tree.simple.file"):
		return True
	return False


protocolWrapperClassSelector.insert(3, CheckForFileModul, FileWrapper)
