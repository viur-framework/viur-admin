# -*- coding: utf-8 -*-

from PyQt5 import QtCore

from viur_admin.event import event
from viur_admin.config import conf
from viur_admin.widgets.file import FileWidget
from viur_admin.utils import WidgetHandler
from viur_admin.utils import loadIcon
from viur_admin.priorityqueue import protocolWrapperInstanceSelector

print("protowrapper file", id(protocolWrapperInstanceSelector))


class FileRepoHandler(WidgetHandler):
    def __init__(self, modul, repo, *args, **kwargs):
        super(FileRepoHandler, self).__init__(lambda: FileWidget(modul, repo["key"]), vanishOnClose=False, *args,
                                              **kwargs)
        self.repo = repo
        self.setText(0, repo["name"])


class FileBaseHandler(WidgetHandler):
    def __init__(self, modul, *args, **kwargs):
        super(FileBaseHandler, self).__init__(lambda: FileWidget(modul), vanishOnClose=False, *args, **kwargs)
        self.modul = modul
        config = conf.serverConfig["modules"][modul]
        if config["icon"]:
            self.setIcon(0, loadIcon(config["icon"]))
        self.setText(0, config["name"])
        event.connectWithPriority("preloadingFinished", self.setRepos, event.lowPriority)

        # self.tmpObj = QtCore.QObject()
        # fetchTask = NetworkService.request("/%s/listRootNodes" % modul, parent=self.tmpObj )
        # self.tmpObj.connect( fetchTask, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.setRepos)

    def setRepos(self):
        """
            Called if preloading has finished.
            Check if there is more than one repository avaiable
            for us.
        """
        print(protocolWrapperInstanceSelector)
        protoWrap = protocolWrapperInstanceSelector.select(self.modul)
        assert protoWrap is not None
        if len(protoWrap.rootNodes) > 1:
            for repo in protoWrap.rootNodes:
                d = FileRepoHandler(self.modul, repo)
                self.addChild(d)


class FileHandler(QtCore.QObject):
    def __init__(self, *args, **kwargs):
        QtCore.QObject.__init__(self, *args, **kwargs)
        print("FileHandler event id", id(event))
        event.connectWithPriority('requestModulHandler', self.requestModulHandler, event.lowPriority)

    def requestModulHandler(self, queue, modul):
        config = conf.serverConfig["modules"][modul]
        if ( config["handler"] == "tree.simple.file" ):
            f = lambda: FileBaseHandler(modul)
            queue.registerHandler(5, f)


_fileHandler = FileHandler()


