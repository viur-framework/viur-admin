# -*- coding: utf-8 -*-
from typing import Any, Dict, List

from PyQt5 import QtCore

from viur_admin.config import conf
from viur_admin.event import event
from viur_admin.log import getLogger
from viur_admin.priorityqueue import protocolWrapperInstanceSelector
from viur_admin.utils import WidgetHandler
from viur_admin.widgets.file import FileWidget

logger = getLogger(__name__)


class FileRepoHandler(WidgetHandler):
	def __init__(
			self,
			module: str,
			repo: Dict[str, Any],
			*args: Any,
			**kwargs: Any):
		super(FileRepoHandler, self).__init__(
			lambda: FileWidget(module, repo["key"]),
			vanishOnClose=False,
			*args,
			**kwargs)
		self.repo = repo
		self.setText(0, repo["name"])


class FileBaseHandler(WidgetHandler):
	def __init__(
			self,
			module: str,
			*args: Any,
			**kwargs: Any):
		logger.debug("module: %r, %r, %r", module, args, kwargs)
		self.module = module
		config = conf.serverConfig["modules"][module]
		descr = config.get("name", "")
		if config["icon"]:
			kwargs["icon"] = config["icon"]
		super(FileBaseHandler, self).__init__(
			lambda: FileWidget(module), sortIndex=config.get("sortIndex", 0), descr=descr, vanishOnClose=False,
			*args, **kwargs)

		event.connectWithPriority("preloadingFinished", self.setRepos, event.lowPriority)

	# self.tmpObj = QtCore.QObject()
	# fetchTask = NetworkService.request("/%s/listRootNodes" % module, parent=self.tmpObj )
	# self.tmpObj.connect( fetchTask, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.setRepos)

	def setRepos(self) -> None:
		"""
			Called if preloading has finished.
			Check if there is more than one repository avaiable
			for us.
		"""
		protoWrap = protocolWrapperInstanceSelector.select(self.module)
		assert protoWrap is not None
		if len(protoWrap.rootNodes) > 1:
			for repo in protoWrap.rootNodes:
				d = FileRepoHandler(self.module, repo)
				self.addChild(d)


class FileHandler(QtCore.QObject):
	def __init__(
			self,
			*args: Any,
			**kwargs: Any):
		QtCore.QObject.__init__(self, *args, **kwargs)
		event.connectWithPriority('requestModuleHandler', self.requestModuleHandler, event.lowPriority)

	def requestModuleHandler(self, queue: Any, module: str) -> None:
		config = conf.serverConfig["modules"][module]
		if config["handler"] == "tree.simple.file":
			queue.registerHandler(5, lambda: FileBaseHandler(module))


_fileHandler = FileHandler()
