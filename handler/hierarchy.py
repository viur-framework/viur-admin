# -*- coding: utf-8 -*-
from time import sleep, time
import sys
import os
import os.path

from viur_admin.ui.hierarchyUI import Ui_Hierarchy
from PyQt5 import QtCore, QtGui, QtWidgets
from viur_admin.network import NetworkService
from viur_admin.event import event
from viur_admin.config import conf
from viur_admin.utils import RegisterQueue, Overlay, formatString, loadIcon
from viur_admin.utils import WidgetHandler
from viur_admin.widgets.hierarchy import HierarchyWidget
from viur_admin.widgets.edit import EditWidget


class HierarchyRepoHandler(WidgetHandler):  # FIXME
    """Class for holding one Repo-Entry within the modules-list"""

    def __init__(self, modul, repo, *args, **kwargs):
        super(HierarchyRepoHandler, self).__init__(lambda: HierarchyWidget(modul, repo["key"]), descr=repo["name"],
                                                   vanishOnClose=False, *args, **kwargs)


class HierarchyCoreHandler(WidgetHandler):  # FIXME
    """Class for holding the main (module) Entry within the modules-list"""

    def __init__(self, modul, *args, **kwargs):
        super(WidgetHandler, self).__init__(*args, **kwargs)
        self.modul = modul
        config = conf.serverConfig["modules"][modul]
        if config["icon"]:
            if config["icon"].lower().startswith("http://") or config["icon"].lower().startswith("https://"):
                icon = config["icon"]
            else:
                icon = loadIcon(config["icon"])
        else:
            icon = loadIcon("icons/modules/hierarchy.svg")
        super(HierarchyCoreHandler, self).__init__(lambda: HierarchyWidget(modul), icon=icon, vanishOnClose=False,
                                                   *args, **kwargs)
        self.setText(0, config["name"])
        self.repos = []
        self.tmp_obj = QtCore.QObject()
        self.fetchTask = NetworkService.request("/%s/listRootNodes" % modul, parent=self.tmp_obj)
        self.fetchTask.finished.connect(self.setRepos)

    def setRepos(self):
        data = NetworkService.decode(self.fetchTask)
        self.fetchTask.deleteLater()
        self.fetchTask = None
        self.tmp_obj.deleteLater()
        self.tmp_obj = None
        self.repos = data
        if len(self.repos) > 1:
            for repo in self.repos:
                d = HierarchyRepoHandler(self.modul, repo)
                self.addChild(d)


class HierarchyHandler(QtCore.QObject):
    def __init__(self, *args, **kwargs):
        QtCore.QObject.__init__(self, *args, **kwargs)
        # self.connect( event, QtCore.SIGNAL('requestModulHandler(PyQt_PyObject,PyQt_PyObject)'),
        # self.requestModulHandler )
        print("FileHandler event id", id(event))
        event.connectWithPriority('requestModulHandler', self.requestModulHandler, event.lowPriority)

    def requestModulHandler(self, queue, modul):
        config = conf.serverConfig["modules"][modul]
        if ( config["handler"] == "hierarchy" ):
            f = lambda: HierarchyCoreHandler(modul)
            queue.registerHandler(5, f)


_hierarchyHandler = HierarchyHandler()
