# -*- coding: utf-8 -*-
from typing import Any, List, Dict, Union, Callable
from copy import deepcopy

from viur_admin.log import getLogger
from PyQt5 import QtCore

from viur_admin.config import conf
from viur_admin.event import event
from viur_admin.utils import loadIcon, WidgetHandler, RegisterQueue
from viur_admin.widgets.list import ListWidget


logger = getLogger(__name__)


class PredefinedViewHandler(WidgetHandler):  # EntryHandler
	"""Holds one view for this module (preconfigured from Server)"""

	def __init__(
			self,
			module: str,
			config: dict,
			viewName: str,
			*args: Any,
			**kwargs: Any):
		logger.debug("icon?: %r", config)
		icon = loadIcon(config.get("icon", None))
		super(PredefinedViewHandler, self).__init__(
			lambda: ListWidget(module, config, config.get("columns", list()), config.get("filter", dict())),
			descr=config["name"],
			icon=icon,
			vanishOnClose=False,
			*args,
			**kwargs)
		self.viewName = viewName



class ListCoreHandler(WidgetHandler):  # EntryHandler
	"""Class for holding the main (module) Entry within the modules-list"""

	def __init__(
			self,
			module: str,
			*args: Any,
			**kwargs: Any):
		# Config parsen
		ListCoreHandlerConfig = conf.serverConfig["modules"][module]
		logger.debug("ListCoreHandler configuration: %r", ListCoreHandlerConfig)
		actions = ListCoreHandlerConfig.get("actions")
		widgetGen = lambda: ListWidget(
			module,
			config=conf.serverConfig["modules"][module],
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

		if "views" in ListCoreHandlerConfig:
			for view in ListCoreHandlerConfig["views"]:
				viewConfig = deepcopy(view)
				viewConfig["handler"] = ListCoreHandlerConfig["handler"]
				self.addChild(PredefinedViewHandler(module, viewConfig, view["name"]))


class ListHandler(QtCore.QObject):
	def __init__(
			self,
			*args: Any,
			**kwargs: Any):
		# TODO: why not super here?
		QtCore.QObject.__init__(self, *args, **kwargs)
		event.connectWithPriority('requestModuleHandler', self.requestModuleHandler, event.lowPriority)

	def requestModuleHandler(self, queue: RegisterQueue, moduleName: str) -> bool:
		queue.registerHandler(0, lambda: ListCoreHandler(moduleName))


_listHandler = ListHandler()
