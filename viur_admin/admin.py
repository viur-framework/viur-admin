#!/usr/bin/env python3
"""
Viur Admin

Copyright 2012-2018 Mausbrand Informationssysteme GmbH
Licensed under GPL Version 3.
http://www.gnu.org/licenses/gpl-3.0

http://www.viur.is
http://docs.viur.is
"""

import sys
import os
import traceback
min_version = (3, 2)
if sys.version_info < min_version:
	# no logger objects present here
	sys.stderr.write("You need python3.2 or newer! - found: %r\n" % sys.version_info)
	sys.exit(1)

from viur_admin.log import prepareLogger


from argparse import ArgumentParser
from viur_admin.bugsnag import Notification

try:
	from PyQt5 import QtGui, QtCore, QtWidgets, QtSvg, QtWebEngineWidgets
except ImportError as err:
	# no logger objects present here
	sys.stderr.write("QT Bindings are missing or incomplete! Ensure PyQT5 is build with QtCore, QtGui, QtWidgets, QtOpenGL, QtWebEngineWidgets" + "\n")
	sys.exit(1)

from pkg_resources import resource_filename, resource_listdir

parser = ArgumentParser()
parser.add_argument(
		'-d', '--debug', dest='debug', default='info',
		help="Debug-Level ('debug', 'info', 'warning' or 'critical')", type=str,
		choices=["debug", "info", "warning", "critical"])
parser.add_argument(
		'-r', '--report', dest='report', default='auto',
		help="Report exceptions to viur.is ('yes', 'no' or 'auto')", type=str,
		choices=["yes", "no", "auto"])
parser.add_argument(
		'-i', '--no-ignore', dest='noignore', default=False,
		help="Disable automatic exclusion of temporary files on upload", action="store_true")
parser.add_argument(
		'-s', '--show_sortindex', action="store_true",
		help="Shows Handler sortIndex (helpful for reordering modules)")



args = parser.parse_args()
args = args
prepareLogger(args.debug)
from viur_admin.config import conf

conf.cmdLineOpts = args

app = QtWidgets.QApplication(sys.argv)


import viur_admin.protocolwrapper
import viur_admin.handler
import viur_admin.widgets
import viur_admin.bones
import viur_admin.actions


from viur_admin.login import Login
from viur_admin.mainwindow import MainWindow
import viur_admin.ui.icons_rc

import viur_admin.plugins

app.setStyle("cleanlooks")
css = QtCore.QFile(":icons/app.css")
css.open(QtCore.QFile.ReadOnly)
data = str(css.readAll(), encoding='ascii')
# data = str(open("app.css", "rb").read(), encoding="ascii")
app.setStyleSheet(data)

cwd = os.getcwd()
prgc = sys.argv[0]

if prgc.startswith("/") or prgc[1] == ":":
	path = os.path.dirname(prgc)
else:
	path = os.path.abspath(os.path.dirname(os.path.join(cwd, prgc)))
os.chdir(path)


def reportError(type, value, tb):
	print("*" * 40)
	print(type)
	print(value)
	traceback.print_tb(tb)
	return
	if os.path.exists(".git"):
		releaseStage = "development"
	else:
		releaseStage = "production"
	try:
		import BUILD_CONSTANTS

		appVersion = BUILD_CONSTANTS.BUILD_RELEASE_STRING
	except:  # Local development or not a freezed Version
		appVersion = "unknown"
		try:  # Reading the head-revision from git
			gitHead = open(".git/FETCH_HEAD", "r").read()
			for line in gitHead.splitlines():
				line = line.replace("\t", " ")
				if "branch 'master'" in line:
					appVersion = line.split(" ")[0]
		except:
			pass

		n = Notification(
			type,
			value,
			tb,
			{
				"appVersion": appVersion,
				"apiKey": "9ceeab3886a9ff81c184a6d60d970421"  # Our API-Key for that project
			}
		)
	n.deliver()


if 0 and (args.report == "auto" and not os.path.exists(
		".git")) or args.report == "yes":  # Report errors only if not being a local development instance
	sys.excepthook = reportError


def main():
	transFiles = resource_listdir("viur_admin", "locales")
	for file in transFiles:
		if file.endswith(".qm"):
			translator = QtCore.QTranslator()
			filename = resource_filename("viur_admin", os.path.join("locales", file))

			translator.load(filename)
			conf.availableLanguages[file[: -3]] = translator
			if "language" in conf.adminConfig.keys() and conf.adminConfig["language"] == file[: -3]:
				app.installTranslator(translator)

	mainWindow = MainWindow()
	l = Login()
	l.show()
	app.exec_()
	print("after AppExec")
	conf.savePortalConfig()
	conf.saveConfig()
	print("after SaveConfig")


if __name__ == '__main__':
	main()
