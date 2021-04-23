# -*- coding: utf-8 -*-
from typing import List, Any, Dict, Tuple

from PyQt5 import QtCore, QtGui

from viur_admin.config import conf
from viur_admin.event import event
from viur_admin.mainwindow import WidgetHandler
from viur_admin.utils import loadIcon
from viur_admin.widgets.edit import EditWidget, ApplicationType


class SingletonEntryHandler(WidgetHandler):
	"""Class for holding the main (module) Entry within the modules-list"""

	def __init__(
			self,
			module: str,
			*args: Any,
			**kwargs: Any):
		widgetFactory = lambda: EditWidget(module, ApplicationType.SINGLETON, "singleton")
		name = ""
		sortIndex = 0
		icon = None
		if module in conf.serverConfig["modules"]:
			config = conf.serverConfig["modules"][module]
			if config["icon"]:
				if config["icon"].lower().startswith("http://") or config["icon"].lower().startswith("https://"):
					icon = config["icon"]
				else:
					icon = loadIcon(config["icon"])
			else:
				icon = loadIcon("singleton")
			name = config["name"]
			sortIndex = config.get("sortIndex", 0)
		super(SingletonEntryHandler, self).__init__(
			widgetFactory,
			descr=name,
			icon=icon,
			sortIndex=sortIndex,
			vanishOnClose=False,
			*args,
			**kwargs)

	def getBreadCrumb(self) -> Tuple[str, QtGui.QIcon]:
		"""
			Dont use the description of our edit widget here
		"""
		return self.text(0), self.icon(0)


class SingletonHandler(QtCore.QObject):
	def __init__(
			self,
			*args: Any,
			**kwargs: Any):
		QtCore.QObject.__init__(self, *args, **kwargs)
		event.connectWithPriority('requestModuleHandler', self.requestModuleHandler, event.lowPriority)

	# print("SingletonHandler event id", id(event))

	def requestModuleHandler(self, queue: Any, moduleName: str) -> None:
		config = conf.serverConfig["modules"][moduleName]
		if config["handler"] == "singleton":
			queue.registerHandler(5, lambda: SingletonEntryHandler(moduleName))


_singletonHandler = SingletonHandler()
