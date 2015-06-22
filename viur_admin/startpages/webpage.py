#!/usr/bin/python
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWebKitWidgets
from network import NetworkService
from config import conf

"""
	Displayes the specified webpage.
"""


class WebWidget(QtWebKitWidgets.QWebView):
    def __init__(self):
        super(WebWidget, self).__init__()
        NetworkService.request(
            "%s%s" % (NetworkService.url.replace("/admin", ""), conf.serverConfig["configuration"]["startPage"] ),
            secure=True, successHandler=self.setHTML)

    def setHTML(self, req):
        data = bytes(req.readAll()).decode("UTF-8")
        self.setHtml(data, QtCore.QUrl(NetworkService.url.replace("/admin", "")))

