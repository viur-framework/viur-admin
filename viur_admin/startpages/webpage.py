# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWebKitWidgets, QtWebKit

from viur_admin.config import conf
from viur_admin.network import NetworkService, nam


class WebWidget(QtWebKitWidgets.QWebView):
	"""Displays a pre rendered page received from viur server instance
	"""

	def __init__(self):
		super(WebWidget, self).__init__()
		self.settings().setAttribute(QtWebKit.QWebSettings.JavascriptEnabled, True)
		self.settings().setAttribute(QtWebKit.QWebSettings.JavascriptCanOpenWindows, True)
		self.page().setNetworkAccessManager(nam)
		self.setUrl(QtCore.QUrl(
				"%s%s" % (NetworkService.url.replace("/admin", ""), conf.serverConfig["configuration"]["startPage"])))
