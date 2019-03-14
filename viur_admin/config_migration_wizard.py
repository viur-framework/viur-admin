# -*- coding: utf-8 -*-
import os

from PyQt5 import QtWidgets
from viur_admin.config import conf

from viur_admin.log import getLogger
import glob
from viur_admin.ui.configuration_migration_wizardUI import Ui_configMigrationWizard

"""
	Allows editing the local accountlist.
"""

__author__ = 'Stefan Kögl'

logger = getLogger(__name__)


class ConfigMigrationWizard(QtWidgets.QWizard):
	def __init__(self, *args, **kwargs):
		super(ConfigMigrationWizard, self).__init__(*args, **kwargs)
		self.ui = Ui_configMigrationWizard()
		self.ui.setupUi(self)
		self.forcePageFlip = False

	def validateCurrentPage(self):
		return True

	def initializePage(self, pageId):
		super(ConfigMigrationWizard, self).initializePage(pageId)
		if pageId == 0:
			try:
				self.ui.pathSelector.addItems([item["displayedName"] for item in conf.payload])
				self.ui.changedInput.setDateTime(conf.payload[0]["lastUsed"])
				self.ui.versionInput.setText(conf.payload[0]["version"])
			except Exception as err:
				logger.exception(err)
		if pageId == 1:
			pass
			# logger.debug(self.validAuthMethods)
			# try:
			# 	self.ui.cbAuthSelector.setCurrentText(self.currentPortalConfig["authMethod"])
			# except Exception as err:
			# 	logger.exception(err)

	def accept(self):
		pass
