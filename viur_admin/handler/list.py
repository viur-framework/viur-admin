# -*- coding: utf-8 -*-

from viur_admin.log import getLogger
from PyQt5 import QtCore

from viur_admin.config import conf
from viur_admin.event import event
from viur_admin.utils import loadIcon, WidgetHandler
from viur_admin.widgets.list import ListWidget


logger = getLogger(__name__)


class PredefinedViewHandler(WidgetHandler):  # EntryHandler
	"""Holds one view for this module (preconfigured from Server)"""

	def __init__(self, modul, viewName, *args, **kwargs):
		config = conf.serverConfig["modules"][modul]
		myview = [x for x in config["views"] if x["name"] == viewName][0]
		icon = loadIcon(myview["icon"])
		super(PredefinedViewHandler, self).__init__(
			lambda: ListWidget(modul, myview.get("columns", list()), myview.get("filter", dict())),
			descr=myview["name"],
			icon=icon,
			vanishOnClose=False,
			*args,
			**kwargs)
		self.viewName = viewName


class ListCoreHandler(WidgetHandler):  # EntryHandler
	"""Class for holding the main (module) Entry within the modules-list"""

	def __init__(self, modul, *args, **kwargs):
		# Config parsen
		ListCoreHandlerConfig = conf.serverConfig["modules"][modul]
		logger.debug("ListCoreHandler configuration: %r", ListCoreHandlerConfig)
		actions = ListCoreHandlerConfig.get("actions")
		widgetGen = lambda: ListWidget(
			modul,
			fields=ListCoreHandlerConfig.get("columns", list()),
			filter=ListCoreHandlerConfig.get("filter", dict()),
			actions=actions
		)

		icon = None
		if "icon" in ListCoreHandlerConfig and ListCoreHandlerConfig["icon"]:
			icon = loadIcon(ListCoreHandlerConfig["icon"])

		super(ListCoreHandler, self).__init__(
			widgetGen,
			descr=ListCoreHandlerConfig["name"],
			icon=icon,
			sortIndex=ListCoreHandlerConfig.get("sortIndex", 0),
			vanishOnClose=False,
			*args,
			**kwargs)

		if "views" in ListCoreHandlerConfig.keys():
			for view in ListCoreHandlerConfig["views"]:
				self.addChild(PredefinedViewHandler(modul, view["name"]))


class ListHandler(QtCore.QObject):
	def __init__(self, *args, **kwargs):
		QtCore.QObject.__init__(self, *args, **kwargs)
		event.connectWithPriority('requestModulHandler', self.requestModulHandler, event.lowPriority)

	def requestModulHandler(self, queue, moduleName):
		f = lambda: ListCoreHandler(moduleName)
		queue.registerHandler(0, f)


_listHandler = ListHandler()
