# -*- coding: utf-8 -*-

import glob
import json
import os
from datetime import datetime
from hashlib import sha512
from time import sleep, time
from typing import Any, Dict, List

from PyQt5 import QtNetwork

import viur_admin
from viur_admin.log import getLogger

logger = getLogger(__name__)


class Config(object):
	def __init__(self, *args: Any):
		super(Config, self).__init__()
		self.storagePath = os.path.abspath(
			os.path.join(
				os.path.expanduser("~"),
				".viuradmin-{0}.{1}".format(*viur_admin.__version__[:2])))
		self.payload: List[Any] = list()
		if not os.path.isdir(self.storagePath):
			try:
				os.makedirs(self.storagePath)
			except Exception as err:
				logger.exception(err)
			self._checkConfigurationMigration()
		self.accounts: List[Any] = list()
		self.portal: Dict[str, Any] = dict()
		self.adminConfig: Dict[str, Any] = {"language": "en"}
		self.serverConfig: Dict[str, Any] = {"modules": dict()}
		self.currentPortalConfigDirectory = None
		self.currentUsername = None  # Store the current Username/Password sothat
		self.currentPassword = None  # plugins are able to authenticate against other services
		self.currentUserEntry = None
		self.availableLanguages: Dict[str, Any] = dict()
		self.cmdLineOpts = None
		self.loadConfig()

	def _checkConfigurationMigration(self) -> None:
		oldDirectoriesRaw = glob.glob("{0}/.viuradmin*".format(os.path.expanduser("~")))
		for path in oldDirectoriesRaw:
			itemData = {
				"lastUsed": 0, #datetime.fromtimestamp(os.stat(os.path.join(self.storagePath, "accounts.dat")).st_mtime),
				"version": "1.0",
				"path": path,
				"displayedName": ""
			}
			try:
				pathParts = path.rsplit("-", 1)
				list(map(int, pathParts[1].split(".")))
				itemData["version"] = pathParts[1]
			except:
				pass
			itemData["displayedName"] = "{0}".format(path)
			self.payload.append(itemData)
		logger.debug("old configs: %r", self.payload)

	def xor(self, data: Dict[str, Any], key: str = None) -> bytes:
		"""This applies at least some *VERY BASIC* obscuring to saved passwords

		DO NOT RELY ON THIS TO GUARD ANYTHING
		"""
		key = bytes([x for x in range(0, 254)])
		klen = len(key)
		res = []
		for i in range(0, len(data)):
			res.append(data[i] ^ key[i % klen])
		return bytes(res)

	def loadConfig(self) -> None:
		# Load stored accounts
		logger.debug("Config.loadConfig")
		configFileName = os.path.join(self.storagePath, "accounts.dat")
		try:
			configFileObject = open(configFileName, "rb")
			configData = self.xor(configFileObject.read()).decode("UTF-8")
			self.accounts = json.loads(configData)
			for account in self.accounts:
				logger.debug("account: %r", account)
		except Exception as err:
			logger.exception(err)
			self.accounts = []

		self.accounts.sort(key=lambda x: x["name"].lower())
		changed = False
		# ensure account data conforms to our latest data scheme
		# TODO:  later also validated via json-schema
		for account in self.accounts:
			if "key" not in account:
				account["key"] = int(time())
				sleep(1)  # Bad hack to ensure key is unique; runs only once at first start
				changed = True
			if "url" in account and "server" not in account:
				account["server"] = account["url"]
				del account["url"]
				changed = True
			if "authMethod" not in account:
				account["authMethod"] = 'X-VIUR-AUTH-User-Password'
				changed = True

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

		if changed:
			self.saveConfig()

	def saveConfig(self) -> None:
		# Save accounts
		try:
			os.makedirs(self.storagePath)
		except Exception as err:
			pass
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

	def loadPortalConfig(
			self,
			url: str,
			withCookies: bool = True,
			forceReload: bool = True) -> None:
		from viur_admin import network
		logger.debug("Config.loadPortalConfig for url:%r, withCookies:%r, forcingReload:%r", url, withCookies,
		             forceReload)
		if self.portal and not forceReload:
			return
		self.currentPortalConfigDirectory = os.path.join(self.storagePath, sha512(url.encode("UTF-8")).hexdigest())
		try:
			if not os.path.isdir(self.currentPortalConfigDirectory):
				os.mkdir(self.currentPortalConfigDirectory)
			configFileObject = open(os.path.join(self.currentPortalConfigDirectory, "config.dat"), "rb")
			configData = configFileObject.read().decode("UTF-8")
			cfg = json.loads(configData)
			self.portal = cfg
			if withCookies:
				cookies = list()
				now = datetime.now()
				rawCookies = self.portal.get("cookies", list())
				logger.debug("rawCookies: %r for now: %r", len(rawCookies), now)
				for plainCookie in rawCookies:
					logger.debug("cookieRaw: %r", plainCookie)
					restoredCookie = QtNetwork.QNetworkCookie.parseCookies(bytearray(plainCookie, "ascii"))[0]
					# TODO: for now we restore all saved cookies
					# if restoredCookie.expirationDate() > now and plainCookie.startswith("viur"):
					logger.debug("restored cookie accepted: %r", restoredCookie)
					cookies.append(restoredCookie)
				network.nam.cookieJar().setAllCookies(cookies)
		except Exception as err:
			logger.error("Could not load Portal Config")
			logger.exception(err)
			self.portal = {"modules": {}}

	def savePortalConfig(self) -> None:
		from viur_admin import network
		if not self.currentPortalConfigDirectory:
			return
		configFileObject = open(os.path.join(self.currentPortalConfigDirectory, "config.dat"), "w+b")
		# now saving cookies needed
		self.portal["cookies"] = [str(cookie.toRawForm(), "ascii") for cookie in network.nam.cookieJar().allCookies()]
		configData = json.dumps(self.portal).encode("UTF-8")
		configFileObject.write(configData)
		configFileObject.flush()
		configFileObject.close()


conf = Config()
