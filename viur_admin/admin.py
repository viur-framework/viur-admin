#!/usr/bin/env python3
"""
Viur Admin

Copyright 2012-2013 Mausbrand Informationssysteme GmbH
Licensed under GPL Version 3.
http://www.gnu.org/licenses/gpl-3.0

http://www.viur.is
http://docs.viur.is
"""

import logging
import sys
import os
from argparse import ArgumentParser
try:
    from PyQt5 import QtGui, QtCore, QtWebKit, QtWidgets, QtSvg
except ImportError:
    print("QT Bindings are missing or incomplete! Ensure PyQT5 is build with QtCore, QtGui, QtWidgets, QtOpenGL, QtWebKit and QtWebKitWidgets")
    sys.exit(1)

from pkg_resources import resource_filename, resource_listdir
from viur_admin.config import conf


app = QtWidgets.QApplication(sys.argv)

import viur_admin.protocolwrapper
import viur_admin.handler
import viur_admin.widgets
import viur_admin.bones
import viur_admin.actions
from viur_admin.login import Login
from viur_admin.mainwindow import MainWindow
import viur_admin.ui.icons_rc

min_version = (3, 2)
if sys.version_info < min_version:
    print("You need python3.2 or newer!")
    sys.exit(1)


# app.setStyle("plastique")
css = QtCore.QFile(":icons/app.css")
css.open(QtCore.QFile.ReadOnly)
data = str(css.readAll(), encoding='ascii')
print()
print(data)
print()
app.setStyleSheet(data)
app.setStyleSheet(open("app.css", "r").read())

cwd = os.getcwd()
prgc = sys.argv[0]

if prgc.startswith("/") or prgc[1] == ":":
    path = os.path.dirname(prgc)
else:
    path = os.path.abspath(os.path.dirname(os.path.join(cwd, prgc)))
os.chdir(path)

parser = ArgumentParser()
# parser.add_argument('-d', '--debug', dest='debug', default='warning',
#                   help="Debug-Level ('debug', 'info', 'warning' or 'critical')", type="choice",
#                   choices=["debug", "info", "warning", "critical"])
# parser.add_argument('-r', '--report', dest='report', default='auto',
#                   help="Report exceptions to viur.is ('yes', 'no' or 'auto')", type="choice",
#                   choices=["yes", "no", "auto"])
parser.add_argument('-i', '--no-ignore', dest='noignore', default=False,
                      help="Disable automatic exclusion of temporary files on upload", action="store_true")

args = parser.parse_args()
conf.cmdLineOpts = args

logging.getLogger().setLevel(logging.DEBUG)

# from bugsnag import Notification

# def reportError(type, value, tb):
#     print("*" * 40)
#     print(type)
#     print(value)
#     traceback.print_tb(tb)
#
#     if os.path.exists(".git"):
#         releaseStage = "development"
#     else:
#         releaseStage = "production"
#     try:
#         import BUILD_CONSTANTS
#
#         appVersion = BUILD_CONSTANTS.BUILD_RELEASE_STRING
#     except:  #Local development or not a freezed Version
#         appVersion = "unknown"
#         try:  #Reading the head-revision from git
#             gitHead = open(".git/FETCH_HEAD", "r").read()
#             for line in gitHead.splitlines():
#                 line = line.replace("\t", " ")
#                 if "branch 'master'" in line:
#                     appVersion = line.split(" ")[0]
#         except:
#             pass
#     n = Notification(type, value, tb, {"appVersion": appVersion,
#                                        "apiKey": "9ceeab3886a9ff81c184a6d60d970421"  #Our API-Key for that project
#     }
#     )
#     n.deliver()
#
#
# if (options.report == "auto" and not os.path.exists(
#         ".git")) or options.report == "yes":  #Report errors only if not beeing a local development instance
#     sys.excepthook = reportError

# conf.cmdLineOpts = options  #Store the command-line options



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

    mw = MainWindow()
    l = Login()
    l.show()
    app.exec_()

    conf.savePortalConfig()
    conf.saveConfig()


if __name__ == '__main__':
    main()
