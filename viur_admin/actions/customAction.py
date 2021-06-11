# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
from viur_admin.config import conf
from viur_admin.network import NetworkService, RequestGroup, RemoteFile, RequestWrapper
from viur_admin.utils import WidgetHandler, loadIcon, colorizeIcon
from viur_admin.widgets.edit import EditWidget, ApplicationType
from viur_admin.log import getLogger
from viur_admin.pyodidehelper import isPyodide
from safeeval import SafeEval

logger = getLogger(__name__)

class CustomAction(QtWidgets.QAction):
	"""
		This class implements the server-side defined functions.
		See "customActions" on the module-level admininfo for more details.
	"""
	def __init__(self, config: dict, appType:ApplicationType, parent: QtWidgets.QWidget = None):
		super(CustomAction, self).__init__(
			config.get("name") or "Custom Action",
			parent)
		self.triggered.connect(self.onTriggered)
		self.appType = appType
		self.config = config
		self.saveEval = SafeEval()
		if appType == ApplicationType.LIST:
			self.parent().list.selectionModel().selectionChanged.connect(self.onItemSelectionChanged)
		self.setEnabled(False)
		self.checkEnabledAst = self.saveEval.compile(self.config["enabled"]) if self.config.get("enabled") else None
		icon = loadIcon(config.get("icon"))
		if isinstance(icon, QtGui.QIcon):
			self.setIcon(icon)
		elif isinstance(icon, str):
			RemoteFile(icon, successHandler=self.loadIconFromRequest)

	def loadIconFromRequest(self, request: RequestWrapper) -> None:
		icon = colorizeIcon(request.getFileContents())
		self.setIcon(icon)

	def onItemSelectionChanged(self, selected, deselected) -> None:
		if self.appType == ApplicationType.LIST:
			selection = self.parent().getSelection()
		else:
			selection = []
		if not self.config.get("allowMultiSelection") and len(selection) != 1:
			self.setEnabled(False)
			return
		if self.checkEnabledAst:
			for skel in selection:
				try:
					if not self.saveEval.execute(self.checkEnabledAst, {"skel": skel}):
						self.setEnabled(False)
						break
				except Exception as e:
					logger.exception(e)
					self.setEnabled(False)
					break
			else:
				self.setEnabled(True)
		else:
			self.setEnabled(True)

	def onTriggered(self) -> None:
		if self.appType == ApplicationType.LIST:
			selection = self.parent().getSelection()
		else:
			selection = []
		if self.config.get("action") == "fetch":
			req = RequestGroup(parent=self.parent(), finishedHandler=self.reloadParent)  # failureHandler=self.delayEmitEntriesChanged
			req.addToStatusBar("%s: {{finished}}/{{total}}" % self.config.get("name"), "Done")
			for item in selection:
				url = str(self.config.get("url")).replace("{{key}}", item["key"])
				r = NetworkService.request(url, secure=True, parent=req)
				req.addQuery(r)
		elif self.config.get("action") == "open":
			if not isPyodide:
				import webbrowser
				for item in selection:
					url = str(self.config.get("url")).replace("{{key}}", item["key"])
					webbrowser.open(url)
			else:
				import js
				for item in selection:
					url = str(self.config.get("url")).replace("{{key}}", item["key"])
					js.window.open(url)

	def reloadParent(self, *args, **kwargs):
		if self.appType == ApplicationType.LIST:
			self.parentWidget().list.model().reload()
