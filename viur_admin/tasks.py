from typing import Callable, Tuple, Any, Dict, List

from PyQt5 import QtCore, QtWidgets, QtGui

from viur_admin.event import event
from viur_admin.network import NetworkService, RequestWrapper
from viur_admin.ui.taskUI import Ui_Task
from viur_admin.utils import Overlay, WidgetHandler, loadIcon
from viur_admin.widgets.edit import EditWidget, ApplicationType


class TaskEntryHandler(WidgetHandler):
	def __init__(self, widgetFactory: Callable, *args: Any, **kwargs: Any):
		super(TaskEntryHandler, self).__init__(
			widgetFactory,
			icon=loadIcon(":icons/menu/tasks.png"),
			vanishOnClose=True, *args, **kwargs)
		self.setText(0, QtCore.QCoreApplication.translate("tasks", "Tasks"))

	def getBreadCrumb(self) -> Tuple[str, QtGui.QIcon]:
		"""
			Dont use the description of our edit widget here
		"""
		if len(self.widgets) == 2:  # We adding exactly one task
			try:
				tasks = self.widgets[0].tasks
			except:
				tasks = None
			if tasks:
				taskDict = {}
				for t in tasks["skellist"]:
					taskDict[t["key"]] = t
				try:
					taskID = self.widgets[1].key
				except:
					taskID = None
				if taskID and taskID in taskDict:
					return taskDict[taskID]["name"], self.icon(0)
		return self.text(0), self.icon(0)


class TaskItem(QtWidgets.QListWidgetItem):
	def __init__(self, task: Any, *args: Any, **kwargs: Any):
		super(TaskItem, self).__init__(task["name"], *args, **kwargs)
		self.task = task


class TaskViewer(QtWidgets.QWidget):
	def __init__(self, *args: Any, **kwargs: Any):
		super(TaskViewer, self).__init__(*args, **kwargs)
		self.ui = Ui_Task()
		self.ui.setupUi(self)
		self.overlay = Overlay(self)
		self.overlay.inform(self.overlay.BUSY)
		self.tasks = None
		NetworkService.request("/_tasks/list", secure=True, successHandler=self.onTaskList)
		self.show()

	def onTaskList(self, req: RequestWrapper) -> None:
		self.tasks = NetworkService.decode(req)
		for task in self.tasks["skellist"]:
			item = TaskItem(task)
			self.ui.listWidget.addItem(item)
		self.overlay.clear()

	def on_listWidget_itemClicked(self, item: TaskItem) -> None:
		self.ui.lblName.setText(item.task["name"])
		self.ui.lblDescr.setText(item.task["descr"])

	def on_btnExecute_released(self, *args: Any, **kwargs: Any) -> None:
		item = self.ui.listWidget.currentItem()
		if not item:
			return
		taskID = item.task["key"]

		for i in range(self.ui.horizontalLayout.count()):
			if self.ui.horizontalLayout.itemAt(i).widget():
				self.ui.horizontalLayout.itemAt(i).widget().close()
		for i in range(self.ui.verticalLayout.count()):
			if self.ui.verticalLayout.itemAt(i).widget():
				self.ui.verticalLayout.itemAt(i).widget().close()
		task = None
		for t in self.tasks["skellist"]:
			if t["key"] == taskID:
				task = t
				break
		if not task:
			return
		nameLbl = QtWidgets.QLabel(task["name"], self)
		self.ui.verticalLayout.addWidget(nameLbl)
		descrLbl = QtWidgets.QLabel(task["descr"], self)
		self.ui.verticalLayout.addWidget(descrLbl)

		event.emit("stackWidget", EditWidget("_tasks", ApplicationType.SINGLETON, taskID))
