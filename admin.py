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

## Some basic checks to ensure that the current python interpreter meets our minimum requirements
min_version = (3,2)
if sys.version_info<min_version:
	print("You need python3.2 or newer!")
	sys.exit(1)
if 1:
	from PySide import QtGui, QtCore, QtOpenGL, QtWebKit
else: # ImportError:
	print( "QT Bindings are missing or incomplete! Ensure PyQT is build with Qt, QtGui, QtCore, QtOpenGL and QtWebKit" )
	sys.exit(1)
#try:
#	from PySide import Qsci
#except ImportError:
#	print( "Error importing QScintilla2 (Qsci)!")
#	sys.exit(1)

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
parser.add_option('-d', '--debug', dest='debug', default='warning', help="Debug-Level ('debug', 'info', 'warning' or 'critical')", type="choice", choices=["debug", "info", "warning", "critical"])
parser.add_option('-r', '--report', dest='report', default='auto', help="Report exceptions to viur.is ('yes', 'no' or 'auto')", type="choice", choices=["yes", "no", "auto"])
parser.add_option('-i', '--no-ignore', dest='noignore', default=False, help="Disable automatic exclusion of temporary files on upload", action="store_true")
(options, args) = parser.parse_args()

#Apply options
logging.getLogger().setLevel( getattr( logging, options.debug.upper()  ) )

from mainwindow import MainWindow
from handler import *
from bones import *
from login import Login
from config import conf
import urllib, urllib.request
from urllib.parse import quote_plus
from bugsnag import Notification

def reportError( type, value, tb ):
	print( "*"*40 )
	print( type )
	print( value )
	traceback.print_tb(tb)
	
	if os.path.exists( ".git" ):
		releaseStage = "development"
	else:
		releaseStage = "production"
	try:
		import BUILD_CONSTANTS
		appVersion = BUILD_CONSTANTS.BUILD_RELEASE_STRING
	except: #Local development or not a freezed Version
		appVersion = "unknown"
		try: #Reading the head-revision from git
			gitHead = open(".git/FETCH_HEAD", "r").read()
			for line in gitHead.splitlines():
				line = line.replace("\t", " ")
				if "branch 'master'" in line:
					appVersion = line.split(" ")[0]
		except:
			pass
	n = Notification( type, value, tb, { "appVersion": appVersion,
				"apiKey": "9ceeab3886a9ff81c184a6d60d970421" #Our API-Key for that project
				}
			)
	n.deliver()


if (options.report == "auto" and not os.path.exists( ".git" )) or options.report=="yes": #Report errors only if not beeing a local development instance
	sys.excepthook = reportError

conf.cmdLineOpts = options #Store the command-line options

import plugin

app = QtGui.QApplication(sys.argv)
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
print("don1e")
sys.stdout.flush()
conf.savePortalConfig()
conf.saveConfig()


