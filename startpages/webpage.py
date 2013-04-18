#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from PySide import QtGui, QtCore, QtWebKit
from network import NetworkService
from config import conf

"""
	Displayes the specified webpage.
"""

class WebWidget( QtWebKit.QWebView ):

	def __init__(self):
		super( WebWidget, self ).__init__()
		NetworkService.request( "%s%s" % (NetworkService.url.replace("/admin",""), conf.serverConfig["configuration"]["startPage"] ), secure=True, successHandler=self.setHTML )
	
	def setHTML( self, req ):
		data = bytes( req.readAll() ).decode("UTF-8")
		self.setHtml( data, QtCore.QUrl( NetworkService.url.replace("/admin","") ) )

