# -*- coding: utf-8 -*-
from typing import Dict, Any, List

from PyQt5 import QtCore

from viur_admin.config import conf
from viur_admin.event import event
from viur_admin.network import NetworkService, RequestWrapper
from viur_admin.utils import WidgetHandler, RegisterQueue
from viur_admin.utils import loadIcon
from viur_admin.widgets.hierarchy import HierarchyWidget


class HierarchyRepoHandler(WidgetHandler):  # FIXME
	"""Class for holding one Repo-Entry within the modules-list"""

	def __init__(
			self,
			module: str,
			repo: Dict[str, Any],
			*args: Any,
			**kwargs: Any):
		super(HierarchyRepoHandler, self).__init__(
			lambda: HierarchyWidget(module, repo["key"]),
			descr=repo["name"],
			vanishOnClose=False,
			*args,
			**kwargs)


class HierarchyCoreHandler(WidgetHandler):  # FIXME
	"""Class for holding the main (module) Entry within the modules-list"""

	def __init__(
			self,
			module: str,
			*args: Any,
			**kwargs: Any):
		super(WidgetHandler, self).__init__(*args, **kwargs)
		self.module = module
		config = conf.serverConfig["modules"][module]
		if config["icon"]:
			if config["icon"].lower().startswith("http://") or config["icon"].lower().startswith("https://"):
				icon = config["icon"]
			else:
				icon = loadIcon(config["icon"])
		else:
			icon = loadIcon(":icons/modules/hierarchy.svg")
		super(HierarchyCoreHandler, self).__init__(
			lambda: HierarchyWidget(module),
			sortIndex=config.get("sortIndex", 0),
			descr=config["name"],
			icon=icon,
			vanishOnClose=False,
			*args,
			**kwargs)

		self.repos: List[Dict[str, Any]] = list()
		self.tmp_obj = QtCore.QObject()
		fetchTask = NetworkService.request("/%s/listRootNodes" % module, parent=self.tmp_obj)
		fetchTask.requestSucceeded.connect(self.setRepos)

	def setRepos(self, req: RequestWrapper) -> None:
		data = NetworkService.decode(req)
		self.tmp_obj.deleteLater()
		self.tmp_obj = None
		self.repos = data
		if len(self.repos) > 1:
			for repo in self.repos:
				d = HierarchyRepoHandler(self.module, repo)
				self.addChild(d)


class HierarchyHandler(QtCore.QObject):
	def __init__(
			self,
			*args: Any,
			**kwargs: Any):
		QtCore.QObject.__init__(self, *args, **kwargs)
		event.connectWithPriority('requestModuleHandler', self.requestModuleHandler, event.lowPriority)

	def requestModuleHandler(self, queue: RegisterQueue, module: str) -> None:
		config = conf.serverConfig["modules"][module]
		if config["handler"] == "hierarchy" or config["handler"].startswith("hierarchy."):
			f = lambda: HierarchyCoreHandler(module)
			queue.registerHandler(5, f)


_hierarchyHandler = HierarchyHandler()
