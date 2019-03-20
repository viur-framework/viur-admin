# -*- coding: utf-8 -*-

from viur_admin.log import getLogger

logger = getLogger(__name__)


from PyQt5 import QtCore

from viur_admin.config import conf
from viur_admin.event import event
from viur_admin.utils import loadIcon, WidgetHandler
from viur_admin.widgets.list import ListWidget
import viur_admin.ui.icons_rc


class PredefinedViewHandler(WidgetHandler):  # EntryHandler
	"""Holds one view for this module (preconfigured from Server)"""

	def __init__(self, modul, viewName, *args, **kwargs):
		config = conf.serverConfig["modules"][modul]
		myview = [x for x in config["views"] if x["name"] == viewName][0]
		widgetFactory = lambda: ListWidget(modul, myview.get("columns", list()), myview.get("filter", list()))
		if "icon" in myview.keys():
			if myview["icon"].lower().startswith("http://") or myview["icon"].lower().startswith("https://"):
				icon = myview["icon"]
			else:
				icon = loadIcon(myview["icon"])
		else:

			icon = loadIcon(":icons/modules/list.svg")
		super(PredefinedViewHandler, self).__init__(widgetFactory, descr=myview["name"], icon=icon, vanishOnClose=False, *args, **kwargs)
		self.viewName = viewName


class ListCoreHandler(WidgetHandler):  # EntryHandler
	"""Class for holding the main (module) Entry within the modules-list"""

	def __init__(self, modul, *args, **kwargs):
		# Config parsen
		config = conf.serverConfig["modules"][modul]
		# logger.debug("ListCoreHandler.init: %r", config.get("name", "NoListCoreHandlerName"), config.get("columns"))
		actions = config.get("actions")
		widgetGen = lambda: ListWidget(
			modul,
			fields=config.get("columns", list()),
			filter=config.get("filter", list()),
			actions=actions
		)
		icon = None
		if "icon" in config.keys() and config["icon"]:
			icon = loadIcon(config["icon"])
		super(ListCoreHandler, self).__init__(
				widgetGen, descr=config["name"],
				icon=icon,
				sortIndex=config.get("sortIndex", 0),
				vanishOnClose=False, *args,
				**kwargs)
		if "views" in config.keys():
			for view in config["views"]:
				self.addChild(PredefinedViewHandler(modul, view["name"]))


class ListHandler(QtCore.QObject):
	def __init__(self, *args, **kwargs):
		QtCore.QObject.__init__(self, *args, **kwargs)
		event.connectWithPriority('requestModulHandler', self.requestModulHandler, event.lowPriority)

	def requestModulHandler(self, queue, moduleName):
		f = lambda: ListCoreHandler(moduleName)
		queue.registerHandler(0, f)


_listHandler = ListHandler()
