#!/usr/bin/env python3
"""
Viur Admin

Copyright 2012-2019 Mausbrand Informationssysteme GmbH
Licensed under GPL Version 3.
http://www.gnu.org/licenses/gpl-3.0

http://www.viur.is
http://docs.viur.is
"""

import os
import sys
import traceback
from collections import namedtuple
from typing import Any
from viur_admin.pyodidehelper import isPyodide

min_version = (3, 6)
if sys.version_info < min_version:
	# no logger objects present here
	sys.stderr.write("You need python3.6 or newer! - found: %r\n" % sys.version_info)
	sys.exit(1)

# got this from https://fman.io/blog/pyqt-excepthook/ - very helpful


def excepthook(exc_type: Any, exc_value: Any, exc_tb: Any) -> None:
	enriched_tb = _add_missing_frames(exc_tb) if exc_tb else exc_tb
	# Note: sys.__excepthook__(...) would not work here.
	# We need to use print_exception(...):
	traceback.print_exception(exc_type, exc_value, enriched_tb)


def _add_missing_frames(tb: Any) -> Any:
	result = fake_tb(tb.tb_frame, tb.tb_lasti, tb.tb_lineno, tb.tb_next)
	frame = tb.tb_frame.f_back
	while frame:
		result = fake_tb(frame, frame.f_lasti, frame.f_lineno, result)
		frame = frame.f_back
	return result


fake_tb = namedtuple(
	'fake_tb', ('tb_frame', 'tb_lasti', 'tb_lineno', 'tb_next')
)

sys.excepthook = excepthook

# end of extended error handling

from viur_admin.log import prepareLogger

from argparse import ArgumentParser

try:
	from PyQt5 import QtGui, QtCore, QtWidgets, QtSvg, QtWebEngineWidgets
except ImportError as err:
	# no logger objects present here
	if not isPyodide:
		sys.stderr.write(
			"QT Bindings are missing or incomplete! Ensure PyQT5 is build with QtCore, QtGui, QtWidgets, QtOpenGL, QtWebKit and QtWebKitWidgets" + "\n")
		sys.exit(1)

from PyQt5.QtWidgets import QStyleFactory

# enable highdpi scaling
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
# use highdpi icons
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

styleKeys = QStyleFactory.keys()
styleKeys.append("Viur")

if not isPyodide:
	from pkg_resources import resource_filename, resource_listdir

	parser = ArgumentParser()
	parser.add_argument(
		'-d', '--debug', dest='debug', default='info',
		help="Debug-Level ('debug', 'info', 'warning' or 'critical')", type=str,
		choices=["debug", "info", "warning", "critical"])
	parser.add_argument(
		'--remote-debugging-port', dest='remote_debugging_port', default='8080',
		help="WebView remote debugging port", type=int)
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
	parser.add_argument(
		"-t", "--theme", dest="theme", default="Viur",
		help="Choose your prefered widget style from the list",
		choices=styleKeys
	)
	args = parser.parse_args()
	args = args
	prepareLogger(args.debug)
	from viur_admin.config import conf
	conf.cmdLineOpts = args
	app = QtWidgets.QApplication(sys.argv)
else:
	prepareLogger(False)
	app = None
	#import js, traceback, io
	#def customExceptHook(etype, value, tb):  # Log Python exceptions to console
	#	ioStr = io.StringIO()
	#	traceback.print_exception(etype, value, tb, file=ioStr)
	#	ioStr.seek(0)
	#	js.console.log(str(ioStr.read()))
	#	sys.__excepthook__(etype, value, traceback)
	#sys.excepthook = customExceptHook



import viur_admin.protocolwrapper
import viur_admin.handler
import viur_admin.widgets
import viur_admin.bones
import viur_admin.actions
import viur_admin.ui.icons_rc


from viur_admin.login import Login, SimpleLogin
from viur_admin.mainwindow import MainWindow
from viur_admin import utils

if 0 and not isPyodide:
	if args.theme != "Viur":
		try:
			QtWidgets.QApplication.setStyle(QStyleFactory.create(args.theme))
			QtWidgets.QApplication.setPalette(QtWidgets.QApplication.style().standardPalette())
		except Exception as err:
			print(err)
	else:
		css = QtCore.QFile(":icons/app.css")
		css.open(QtCore.QFile.ReadOnly)
		data = str(css.readAll(), encoding='ascii')
		# data = str(open("app.css", "rb").read(), encoding="ascii")
		app.setStyleSheet(data)

cwd = os.getcwd()
prgc = sys.argv[0]

if not isPyodide:
	if prgc.startswith("/") or prgc[1] == ":":
		path = os.path.dirname(prgc)
	else:
		path = os.path.abspath(os.path.dirname(os.path.join(cwd, prgc)))
	os.chdir(path)
	print(path)


def reportError(type: Any, value: Any, tb: Any) -> Any:
	print("*" * 40)
	print(type)
	print(value)
	traceback.print_tb(tb)
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


#if 0 and (args.report == "auto" and not os.path.exists(".git")) or args.report == "yes":  # Report errors only if not being a local development instance
#	sys.excepthook = reportError

def dragOverEvent(event):
	event.stopPropagation()
	event.preventDefault()
	event.dataTransfer.dropEffect = 'copy'
	QtGui.QGuiApplication.processEvents()
	return False

def dropEvent(event):
	event.stopPropagation()
	event.preventDefault()
	QtGui.QGuiApplication.processEvents()
	screen = QtGui.QGuiApplication.screens()[0]
	sp = QtGui.QCursor.pos(screen)
	for widget in widgets_at(sp):
		if "htmlDropEvent" in dir(widget):
			widget.htmlDropEvent(event.dataTransfer.files)
			break


mainWindowRef = None

def widgets_at(pos):
	"""Return ALL widgets at `pos`
	Arguments:
	    pos (QPoint): Position at which to get widgets
	   """
	global mainWindowRef
	widgets = []
	widget_at = mainWindowRef.childAt(pos)
	while widget_at:
		widgets.append(widget_at)
		# Make widget invisible to further enquiries
		widget_at.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
		widget_at = mainWindowRef.childAt(pos)
	# Restore attribute
	for widget in widgets:
		widget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
	return widgets

def main() -> None:
	global mainWindowRef
	if not isPyodide:
		transFiles = resource_listdir("viur_admin", "locales")
		for file in transFiles:
			if file.endswith(".qm"):
				translator = QtCore.QTranslator()
				filename = resource_filename("viur_admin", os.path.join("locales", file))

				translator.load(filename)
				conf.availableLanguages[file[: -3]] = translator
				if "language" in conf.adminConfig and conf.adminConfig["language"] == file[: -3]:
					app.installTranslator(translator)

		if conf.migrateConfig:
			from viur_admin.config_migration_wizard import ConfigMigrationWizard
			wizard = ConfigMigrationWizard()
			wizard.exec()
	else:
		import js
		canvas = js.document.getElementById("qtcanvas")
		canvas.addEventListener("dragover", dragOverEvent, False)
		canvas.addEventListener("drop", dropEvent, False)

	moduleWhitelist = None
	groupWhitelist = None
	try:
		import viur_admin.module_overwrites
		moduleWhitelist = viur_admin.module_overwrites.moduleWhitelist
		groupWhitelist = viur_admin.module_overwrites.groupWhitelist
	except ImportError:
		pass

	mainWindow = MainWindow(
		moduleWhitelist=moduleWhitelist,
		groupWhitelist=groupWhitelist)
	if isPyodide:
		l = SimpleLogin()
	else:
		l = Login()
	l.show()
	if not isPyodide:
		app.exec_()
		print("after AppExec")
		conf.savePortalConfig()
		conf.saveConfig()
		print("after SaveConfig")
	mainWindowRef = mainWindow
	return mainWindow, l


if __name__ == '__main__':
	main()

