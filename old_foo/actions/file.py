# -*- coding: utf-8 -*-
import urllib.request
import urllib.parse
import urllib.error
import urllib.request
import urllib.error
import urllib.parse
from time import sleep, time
import sys
import os

from viur_admin.ui.treeUI import Ui_Tree
from PyQt5 import QtCore, QtGui, QtWidgets
from viur_admin.network import NetworkService, RemoteFile
from viur_admin.event import event
from viur_admin.config import conf
from viur_admin.widgets.file import FileWidget
from viur_admin.handler.list import ListCoreHandler
from viur_admin.utils import RegisterQueue, loadIcon
from viur_admin.priorityqueue import protocolWrapperInstanceSelector, actionDelegateSelector


class FileUploadAction(QtWidgets.QAction):
    def __init__(self, parent, *args, **kwargs):
        super(FileUploadAction, self).__init__(QtGui.QIcon(":icons/actions/upload_small.png"),
                                               QtCore.QCoreApplication.translate("FileHandler", "Upload files"), parent)
        self.triggered.connect(self.onTriggered)
        self.setShortcut(QtGui.QKeySequence.New)
        self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

    def onTriggered(self, e):
        files = QtGui.QFileDialog.getOpenFileNames()
        self.parent().doUpload(files, self.parent().getNode())

    @staticmethod
    def isSuitableFor(modul, actionName):
        return (modul == "tree.simple.file" or modul.startswith("tree.simple.file.")) and actionName == "upload"


actionDelegateSelector.insert(3, FileUploadAction.isSuitableFor, FileUploadAction)


class FileDownloadAction(QtWidgets.QAction):
    def __init__(self, parent, *args, **kwargs):
        super(FileDownloadAction, self).__init__(QtGui.QIcon(":icons/actions/download_small.png"),
                                                 QtCore.QCoreApplication.translate("FileHandler", "Download files"),
                                                 parent)
        self.triggered.connect(self.onTriggered)
        self.setShortcut(QtGui.QKeySequence.Save)
        self.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)

    def onTriggered(self, e):
        dirs = []
        files = []
        for item in self.parent().selectedItems():
            if isinstance(item, self.parent().getNodeItemClass()):
                print(self.parent().getNodeItemClass())
                dirs.append(item.entryData)
            else:
                files.append(item.entryData)
        if not files and not dirs:
            return
        targetDir = QtGui.QFileDialog.getExistingDirectory(self.parentWidget())
        if not targetDir:
            return
        self.parent().doDownload(targetDir, files, dirs)

    @staticmethod
    def isSuitableFor(modul, actionName):
        return (modul == "tree.simple.file" or modul.startswith("tree.simple.file.")) and actionName == "download"


actionDelegateSelector.insert(3, FileDownloadAction.isSuitableFor, FileDownloadAction)
