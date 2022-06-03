from abc import ABC
from PyQt5 import QtCore, QtWidgets
from viur_admin.log import getLogger, getStatusBar, logToUser
from typing import Optional

class TaskQueue(QtCore.QObject):
	def __init__(self, parent):
		super().__init__(parent)
		self.pendingTasks = []
		self.hasTaskRunning = False
		self.progressBar: QtWidgets.QProgressBar = None
		self.finishedTasks = 0

	def addTask(self, task):
		task.setParent(self)
		self.pendingTasks.append(task)
		self.tryRunNext()

	def updateDisplay(self):
		if not self.progressBar and self.pendingTasks:
			# Create a progress bar and add it to the status-bar
			self.progressBar = QtWidgets.QProgressBar()
			self.progressBar.setMaximum(len(self.pendingTasks)+self.finishedTasks)
			self.progressBar.setValue(self.finishedTasks)
			self.progressBar.setFormat("Syncing changes in module %s: %%v/%%m" % self.parent().module)
			getStatusBar().addWidget(self.progressBar)
			self.progressBar.show()
		elif self.progressBar and not self.pendingTasks:
			# We've finished, remove our progressbar from the status-bar
			getStatusBar().removeWidget(self.progressBar)
			self.progressBar.deleteLater()
			self.progressBar = None
			self.finishedTasks = 0
		elif self.progressBar:
			# Just update the progress
			self.progressBar.setMaximum(len(self.pendingTasks)+self.finishedTasks)
			self.progressBar.setValue(self.finishedTasks)


	def tryRunNext(self):
		self.updateDisplay()
		if not self.pendingTasks:
			return
		if self.hasTaskRunning:
			return
		self.hasTaskRunning = True
		task = self.pendingTasks.pop(0)
		task.start(self)

	def taskFinished(self, success:bool):
		self.hasTaskRunning = False
		if not success:  # A Task failed. Abort all pending tasks and reset the protowrap
			self.pendingTasks = []
			self.parent().reset()
		self.finishedTasks += 1
		self.tryRunNext()

class Task(QtCore.QObject):
	def start(self, queue):
		self.queue = queue
		self.run()

	def run(self):
		raise NotImplementedError()

	def finish(self, success:bool):
		self.queue.taskFinished(success)
		self.deleteLater()


class ProtocolWrapper(QtCore.QObject):
	protocolWrapperInstancePriority = -9999

	def __init__(self):
		super().__init__()
		self.temporaryKeyIndex: int = 0  # We'll assign temp. keys using this index
		self.temporaryKeyMap: dict[str, str] = {}  # Map of temp key -> finally assignend key from the server
		self.taskqueue = TaskQueue(self)

	def mkTempKey(self, kind):
		"""
			Create a new temporary key. That key is guranteed to be unique for this module.
			:param kind: usually self.module, may be also self.module+"_rootNode"
			:return: A unique identifier usable as temporary key
		"""
		idx = self.temporaryKeyIndex
		self.temporaryKeyIndex += 1
		return "temp:%s_%s" % (kind, idx)

	def isTemporaryKey(self, key: str) -> bool:
		"""
			Checks if the given key is temporary. If so, it may be resolved using meth:lookupTemporaryKey.
			:param key: The key to check
			:return: True, if the given key is temporary
		"""
		return key.startswith("temp:")

	def lookupTemporaryKey(self, tempKey: str) -> Optional[str]:
		"""
			Resolves a temporary key to the final one assigned by the server. May return None if the changes
			have not been synced to the server yet.
			:param tempKey: The temporary key to resolve
			:return: The final, server-assigned key or None
		"""
		return self.temporaryKeyMap.get(tempKey)

	def resolveTemporaryKey(self, tempKey, finalKey):
		"""
			Sets the final, server-assgined key for the given tempoary key. Must be called if the entry has been
			successfully created on the server and we got it's final key in addSuccess or the like.
		"""
		self.temporaryKeyMap[tempKey] = finalKey

	def reset(self):
		"""
			Usually called, if tasks failed to sync to the server.
			Reset all internal states and reload a fresh state.
		"""
		pass