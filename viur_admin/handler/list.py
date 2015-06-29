import time
import os
import os.path

from PyQt5 import QtCore, QtGui
from viur_admin.network import NetworkService
from viur_admin.event import event
from viur_admin.ui.editpreviewUI import Ui_BasePreview
from viur_admin.utils import RegisterQueue, Overlay, formatString, loadIcon, WidgetHandler
from viur_admin.config import conf
# from mainwindow import WidgetHandler
from viur_admin.widgets.list import ListWidget
from viur_admin.priorityqueue import protocolWrapperInstanceSelector


class PredefinedViewHandler(WidgetHandler):  # EntryHandler
    """Holds one view for this modul (preconfigured from Server)"""

    def __init__(self, modul, viewName, *args, **kwargs):
        config = conf.serverConfig["modules"][modul]
        myview = [x for x in config["views"] if x["name"] == viewName][0]
        if all([(x in myview.keys()) for x in ["filter", "columns"]]):
            widgetFactory = lambda: ListWidget(modul, myview["columns"], myview["filter"])
        else:
            widgetFactory = lambda: ListWidget(modul)
        if "icon" in myview.keys():
            if myview["icon"].lower().startswith("http://") or myview["icon"].lower().startswith("https://"):
                icon = myview["icon"]
            else:
                icon = loadIcon(myview["icon"])
        else:
            icon = loadIcon(":icons/modules/list.svg")
        super(PredefinedViewHandler, self).__init__(widgetFactory, icon=icon, vanishOnClose=False, *args, **kwargs)
        self.viewName = viewName
        self.setText(0, myview["name"])


class ListCoreHandler(WidgetHandler):  # EntryHandler
    """Class for holding the main (module) Entry within the modules-list"""

    def __init__(self, modul, *args, **kwargs):
        # Config parsen
        config = conf.serverConfig["modules"][modul]
        if "columns" in config.keys():
            if "filter" in config.keys():
                widgetGen = lambda: ListWidget(modul, config["columns"], config["filter"])
            else:
                widgetGen = lambda: ListWidget(modul, config["columns"])
        else:
            widgetGen = lambda: ListWidget(modul)
        if "icon" in config.keys() and config["icon"]:
            if config["icon"].lower().startswith("http://") or config["icon"].lower().startswith("https://"):
                icon = config["icon"]
            else:
                icon = loadIcon(config["icon"])
        else:
            icon = loadIcon(":icons/modules/list.svg")
        super(ListCoreHandler, self).__init__(widgetGen, descr=config["name"], icon=icon, sortIndex=config.get("sortIndex", 0), vanishOnClose=False, *args,
                                              **kwargs)
        if "views" in config.keys():
            for view in config["views"]:
                self.addChild(PredefinedViewHandler(modul, view["name"]))


class ListHandler(QtCore.QObject):
    def __init__(self, *args, **kwargs):
        QtCore.QObject.__init__(self, *args, **kwargs)
        print("ListHandler event id", id(event))
        event.connectWithPriority('requestModulHandler', self.requestModulHandler, event.lowPriority)

        # self.connect( event, QtCore.SIGNAL('requestModulHandler(PyQt_PyObject,PyQt_PyObject)'), self.requestModulHandler )
        #self.connect( event, QtCore.SIGNAL('requestModulListActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)') ,  self.requestModulListActions )

    def requestModulHandler(self, queue, modulName):
        f = lambda: ListCoreHandler(modulName)
        queue.registerHandler(0, f)


_listHandler = ListHandler()
