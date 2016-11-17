#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from viur_admin.log import getLogger

logger = getLogger(__name__)
import os
from hashlib import sha512
from pprint import pprint
from operator  import attrgetter
from time import time, sleep


class Config(object):
	def __init__(self):
		object.__init__(self)
		self.storagePath = os.path.join(os.path.expanduser("~"), ".viuradmin")
		if not os.path.isdir(self.storagePath):
			os.mkdir(self.storagePath)
		self.accounts = []
		self.portal = {}
		self.adminConfig = {}
		self.serverConfig = {"modules": {}}
		self.currentPortalConfigDirectory = None
		self.currentUsername = None  # Store the current Username/Password sothat
		self.currentPassword = None  # plugins are able to authenticate against other services
		self.currentUserEntry = None
		self.availableLanguages = {}
		self.cmdLineOpts = None
		self.loadConfig()

	def xor(self, data, key=None):
		"""This applys at least some *VERY BASIC* obscurfaction to saved passwords
		DO NOT RELY ON THIS TO GUARD ANYTHING"""
		key = bytes([x for x in range(0, 254)])
		klen = len(key)
		res = []
		for i in range(0, len(data)):
			res.append(data[i] ^ key[i % klen])
		return bytes(res)

	def loadConfig(self):
		# Load stored accounts
		configFileName = os.path.join(self.storagePath, "accounts.dat")
		try:
			configFileObject = open(configFileName, "rb")
			configData = self.xor(configFileObject.read()).decode("UTF-8")
			cfg = json.loads(configData)
			self.accounts = cfg
		except:
			logger.error("Could not load accounts")
			self.accounts = []

		self.accounts.sort(key=lambda x: x["name"].lower())
		for account in self.accounts:
			if not "key" in account.keys():
				account["key"] = int(time())
				sleep(1)  # Bad hack to ensure key is unique; runs only once at first start
		# Load rest of the config
		configFileName = os.path.join(self.storagePath, "config.dat")
		try:
			configFileObject = open(configFileName, "rb")
			configData = self.xor(configFileObject.read()).decode("UTF-8")
			cfg = json.loads(configData)
			self.adminConfig = cfg
		except Exception as err:
			logger.exception(err)
			self.adminConfig = {}

	def saveConfig(self):
		# Save accounts
		configFileName = os.path.join(self.storagePath, "accounts.dat")
		configFileObject = open(configFileName, "w+b")
		configData = self.xor(json.dumps(self.accounts).encode("UTF-8"))
		configFileObject.write(configData)
		configFileObject.flush()
		configFileObject.close()
		# Save rest of the config
		configFileName = os.path.join(self.storagePath, "config.dat")
		configFileObject = open(configFileName, "w+b")
		configData = self.xor(json.dumps(self.adminConfig).encode("UTF-8"))
		configFileObject.write(configData)
		configFileObject.flush()
		configFileObject.close()

	def loadPortalConfig(self, url):
		logger.debug("LOADING PORTAL CONFIG")
		self.currentPortalConfigDirectory = os.path.join(self.storagePath, sha512(url.encode("UTF-8")).hexdigest())
		try:
			if not os.path.isdir(self.currentPortalConfigDirectory):
				os.mkdir(self.currentPortalConfigDirectory)
			configFileObject = open(os.path.join(self.currentPortalConfigDirectory, "config.dat"), "rb")
			configData = configFileObject.read().decode("UTF-8")
			cfg = json.loads(configData)
			self.portal = cfg
		except Exception as err:
			logger.error("Could not load Portal Config")
			logger.exception(err)
			self.portal = {"modules": {}}

	def savePortalConfig(self):
		if not self.currentPortalConfigDirectory:
			return
		configFileObject = open(os.path.join(self.currentPortalConfigDirectory, "config.dat"), "w+b")
		configData = json.dumps(self.portal).encode("UTF-8")
		configFileObject.write(configData)
		configFileObject.flush()
		configFileObject.close()


conf = Config()
