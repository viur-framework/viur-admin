# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWebEngineWidgets

from viur_admin.log import getLogger
logger = getLogger(__name__)

from viur_admin.config import conf
from viur_admin.network import NetworkService, nam


class WebWidget(QtWebEngineWidgets.QWebEngineView):
	"""Displays a pre rendered page received from viur server instance
	"""

	def __init__(self):
		super(WebWidget, self).__init__()
		self.chromeCookieJar = self.page().profile().cookieStore()
		self.chromeCookieJar.cookieAdded.connect(self.onCookieAdded)
		self.chromeCookieJar.loadAllCookies()
		for cookie in nam.cookieJar().allCookies():
			self.chromeCookieJar.setCookie(cookie)
		self.setUrl(QtCore.QUrl(
				"%s%s" % (NetworkService.url.replace("/admin", ""), conf.serverConfig["configuration"]["startPage"])))

	def onCookieAdded(self, cookie):
		logger.error("WebWidget.onCookieAdded not yet handled properly: %r", cookie)
