#!/usr/bin/env python3
"""
Viur Admin

Copyright 2012-2013 Mausbrand Informationssysteme GmbH
Licensed under GPL Version 3.
http://www.gnu.org/licenses/gpl-3.0

http://www.viur.is
http://docs.viur.is
"""

import sys, os, traceback
from io import StringIO
from optparse import OptionParser
import logging

#Fixing the path
cwd = os.getcwd()
prgc = sys.argv[0]

if prgc.startswith("/") or prgc[1]==":":
	path = os.path.dirname( prgc )
else:
	path = os.path.abspath( os.path.dirname( os.path.join( cwd, prgc ) ) )
os.chdir( path )

#Check CMD-Line options
parser = OptionParser(usage="usage: %prog [options]")
parser.add_option('-d', '--debug',    dest='debug', default='warning', help=u"Debug-Level ('debug', 'info', 'warning' or 'critical')", type="choice", choices=["debug", "info", "warning", "critical"])
parser.add_option('-r', '--report',    dest='report', default='auto', help=u"Report exceptions to viur.is ('yes', 'no' or 'auto')", type="choice", choices=["yes", "no", "auto"])
(options, args) = parser.parse_args()

#Apply options
logging.getLogger().setLevel( getattr( logging, options.debug.upper()  ) )

from PyQt4 import Qt, QtCore
from mainwindow import MainWindow
from handler import *
from bones import *
from login import Login
from config import conf
import urllib, urllib.request
from urllib.parse import quote_plus
from event import EventDispatcher


def reportError( type, value, tb ):
	print( "*"*40 )
	print( type )
	print( value )
	traceback.print_tb(tb)
	def dict2Data( data ):
		l = []
		for k, v in data.items():
			k = quote_plus(k)
			if isinstance(v,  str):
				v = [v]
			elif isinstance(v,  int) or isinstance(v,  int):
				v = [str(v)]
			for i in v:
				l.append("%s=%s" % (k, quote_plus(i)))
		return "&".join( l ).encode("UTF8" )
	try:
		report_url = "https://viur-is.appspot.com/bugtracker/logError"
		io = StringIO()
		traceback.print_tb(tb, file=io)
		io.seek(0)
		tbs = io.read()
		params = dict2Data( {"err_type":str(type), "err_tracebak":tbs} )
		assert urllib.request.urlopen( report_url, params ).read()=="OK"
	except:
		traceback.print_exc()

if (options.report == "auto" and not os.path.exists( ".git" )) or options.report=="yes": #Report errors only if not beeing a local development instance
	sys.excepthook = reportError

import plugin


app = Qt.QApplication(sys.argv)
#Load translations
transFiles = os.listdir("./locales/")
for file in transFiles:
	if file.endswith(".qm"):
		translator = QtCore.QTranslator()
		translator.load( os.path.join( path, "locales", file ) )
		conf.availableLanguages[ file[ : -3 ] ] = translator
		if "language" in conf.adminConfig.keys() and conf.adminConfig["language"]==file[ : -3 ]:
			app.installTranslator( translator )

app.setStyleSheet( open("app.css", "r").read() )
mw = MainWindow()
l = Login()
l.show()
app.exec_()
conf.savePortalConfig()
conf.saveConfig()
EventDispatcher.shutdown()
