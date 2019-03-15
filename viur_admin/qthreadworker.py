# -*- coding: utf-8 -*-
from PyQt5.QtCore import QObject, QThread, QEventLoop, pyqtSignal, pyqtSlot

from viur_admin.log import getLogger

logger = getLogger(__name__)

__author__ = "Stefan Kögl <sk@mausbrand.de>"


class QThreadWorker(QObject):
	IDLE = 0
	RUNNING = 1
	PAUSED = 2

	started = pyqtSignal()
	finished = pyqtSignal()

	def __init__(self, parent=None):
		self.state = self.IDLE
		super(QThreadWorker, self).__init__(parent)

	@pyqtSlot()
	def pause(self):
		dispatcher = QThread.currentThread().eventDispatcher()
		if not dispatcher:
			logger.error("thread with no dispatcher")
			return

		if self.state != self.RUNNING:
			return

		self.state = self.PAUSED
		logger.debug("paused")
		while self.state == self.PAUSED:
			dispatcher.processEvents(QEventLoop.WaitForMoreEvents)

	@pyqtSlot()
	def resume(self):
		if self.state == self.PAUSED:
			self.state = self.RUNNING
			logger.debug("resumed")

	@pyqtSlot()
	def cancel(self):
		if self.state != self.IDLE:
			self.state = self.IDLE
			logger.debug("cancelled")

	def _is_cancelled(self):
		dispatcher = QThread.currentThread().eventDispatcher()
		if not dispatcher:
			logger.error("thread with no dispatcher")
			return False

		dispatcher.processEvents(QEventLoop.AllEvents)
		return self.state == self.IDLE
