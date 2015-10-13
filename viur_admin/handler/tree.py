# -*- coding: utf-8 -*-

from PyQt5 import QtCore

from viur_admin.event import event
from viur_admin.config import conf
from viur_admin.utils import RegisterQueue, loadIcon
from viur_admin.widgets.tree import TreeWidget
from viur_admin.mainwindow import WidgetHandler


class TreeBaseHandler(WidgetHandler):
	def __init__(self, modul, *args, **kwargs):
		config = conf.serverConfig["modules"][modul]
		if config["icon"]:
			if config["icon"].lower().startswith("http://") or config["icon"].lower().startswith("https://"):
				icon = config["icon"]
			else:
				icon = loadIcon(config["icon"])
		else:
			icon = loadIcon(":icons/modules/tree.svg")
		super(TreeBaseHandler, self).__init__(lambda: TreeWidget(modul), icon=icon, vanishOnClose=False, *args,
		                                      **kwargs)
		self.setText(0, config["name"])


class TreeHandler(QtCore.QObject):
	"""
	Created automatically to route Events to its handler in this file.png
	Do not create another instance of this!
	"""

	def __init__(self, *args, **kwargs):
		"""
		Do not instantiate this!
		All parameters are passed to QObject.__init__
		"""
		QtCore.QObject.__init__(self, *args, **kwargs)
		event.connectWithPriority('requestModulHandler', self.requestModulHandler, event.lowPriority)
		# print("TreeHandler event id", id(event))

	def requestModulHandler(self, queue, modul):
		"""Pushes a L{TreeBaseHandler} onto the queue if handled by "tree"

		@type queue: RegisterQueue
		@type modul: string
		@param modul: Name of the modul which should be handled
		"""
		config = conf.serverConfig["modules"][modul]
		if (config["handler"] == "tree" or config["handler"].startswith("tree.")):
			f = lambda: TreeBaseHandler(modul)
			queue.registerHandler(3, f)

	def openList(self, modulName, config):
		if "name" in config.keys():
			name = config["name"]
		else:
			name = "Liste"
		if "icon" in config.keys():
			icon = config["icon"]
		else:
			icon = None
		# event.emit(QtCore.SIGNAL('addHandlerWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),
		#            TreeList(modulName, config), name, icon)


_fileHandler = TreeHandler()
