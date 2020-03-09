# -*- coding: utf-8 -*-
from typing import List, Any, Dict

from viur_admin.log import getLogger

logger = getLogger(__name__)

from PyQt5 import QtCore

from viur_admin.event import event
from viur_admin.config import conf
from viur_admin.utils import RegisterQueue, loadIcon
from viur_admin.widgets.tree import TreeWidget
from viur_admin.mainwindow import WidgetHandler


class TreeBaseHandler(WidgetHandler):
	def __init__(
			self,
			module: str,
			*args: Any,
			**kwargs: Any):
		config = conf.serverConfig["modules"][module]
		if config["icon"]:
			if config["icon"].lower().startswith("http://") or config["icon"].lower().startswith("https://"):
				icon = config["icon"]
			else:
				icon = loadIcon(config["icon"])
		else:
			icon = loadIcon(":icons/modules/tree.svg")
		super(TreeBaseHandler, self).__init__(lambda: TreeWidget(module), sortIndex=config.get("sortIndex", 0), descr=config["name"], icon=icon, vanishOnClose=False, *args,
		                                      **kwargs)
		logger.debug("TreeBaseHandler name: %r", config["name"])
		# self.setText(0, config["name"])


class TreeHandler(QtCore.QObject):
	"""
	Created automatically to route Events to its handler in this file.png
	Do not create another instance of this!
	"""

	def __init__(
			self,
			*args: Any,
			**kwargs: Any):
		"""
		Do not instantiate this!
		All parameters are passed to QObject.__init__
		"""
		QtCore.QObject.__init__(self, *args, **kwargs)
		event.connectWithPriority('requestModuleHandler', self.requestModuleHandler, event.lowPriority)

	# print("TreeHandler event id", id(event))

	def requestModuleHandler(self, queue: RegisterQueue, module: str) -> None:
		"""Pushes a L{TreeBaseHandler} onto the queue if handled by "tree"

		@type queue: RegisterQueue
		@type module: string
		@param module: Name of the module which should be handled
		"""
		config = conf.serverConfig["modules"][module]
		if config["handler"] == "tree" or config["handler"].startswith("tree."):
			queue.registerHandler(3, lambda: TreeBaseHandler(module))

	def openList(self, moduleName: str, config: Dict[str, Any]) -> None:
		if "name" in config:
			name = config["name"]
		else:
			name = "Liste"
		if "icon" in config:
			icon = config["icon"]
		else:
			icon = None
		# event.emit(QtCore.SIGNAL('addHandlerWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),
		#            TreeList(moduleName, config), name, icon)


_fileHandler = TreeHandler()
