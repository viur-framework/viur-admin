# -*- coding: utf-8 -*-

from typing import Any, List, Dict
import shutil

from PyQt5 import QtWidgets, QtCore

from viur_admin.config import conf
from viur_admin.log import getLogger
from viur_admin.ui.configuration_migration_wizardUI import Ui_configMigrationWizard

"""
	Allows editing the local accountlist.
"""

__author__ = 'Stefan Kögl'

logger = getLogger(__name__)


class ConfigMigrationWizard(QtWidgets.QWizard):
	def __init__(
			self,
			*args: Any,
			**kwargs: Any):
		super(ConfigMigrationWizard, self).__init__(*args, **kwargs)
		self.ui = Ui_configMigrationWizard()
		self.ui.setupUi(self)
		self.forcePageFlip = False
		self.ui.pathSelector.currentIndexChanged.connect(self._setData)
		self.currentConfigIndex = 0

	def validateCurrentPage(self) -> bool:
		return True

	def initializePage(self, pageId: int) -> None:
		super(ConfigMigrationWizard, self).initializePage(pageId)
		if pageId == 0:
			try:
				self.ui.pathSelector.addItems([item["displayedName"] for item in conf.payload])
				self._setData(0)
			except Exception as err:
				logger.exception(err)
		if pageId == 1:
			pass
		# logger.debug(self.validAuthMethods)
		# try:
		# 	self.ui.cbAuthSelector.setCurrentText(self.currentPortalConfig["authMethod"])
		# except Exception as err:
		# 	logger.exception(err)

	def validateCurrentPage(self) -> bool:
		currentId = self.currentId()
		if currentId == 0:
			logger.debug("migration config: %r, %r", conf.payload[self.currentConfigIndex]["path"], conf.storagePath)
			shutil.copytree(conf.payload[self.currentConfigIndex]["path"], conf.storagePath)
			conf.loadConfig()
		if currentId == 1:
			self.finished.emit(True)
			return True
		return True

	@QtCore.pyqtSlot(int)
	def _setData(self, index: int) -> None:
		self.currentConfigIndex = index
		self.ui.changedInput.setDateTime(conf.payload[index]["lastUsed"])
		self.ui.versionInput.setText(conf.payload[index]["version"])
