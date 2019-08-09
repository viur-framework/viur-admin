# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.config import conf
from viur_admin.event import event
from viur_admin.handler.list import PredefinedViewHandler
from viur_admin.utils import WidgetHandler, loadIcon
from viur_admin.widgets.list import ListWidget


class CalenderWidget(ListWidget):
	def __init__(self, *args, **kwargs):
		super(CalenderWidget, self).__init__(*args, **kwargs)
		self.filterTypes = [("none", QtCore.QCoreApplication.translate("CalenderList", "unfiltered")),
		                    ("year", QtCore.QCoreApplication.translate("CalenderList", "Year")),
		                    ("month", QtCore.QCoreApplication.translate("CalenderList", "Month")),
		                    ("day", QtCore.QCoreApplication.translate("CalenderList", "Day"))]
		layout = QtWidgets.QHBoxLayout()
		self.layout().insertLayout(1, layout)
		self.cbFilterType = QtGui.QComboBox()
		layout.addWidget(self.cbFilterType)
		self.deFilter = QtGui.QDateTimeEdit()
		layout.addWidget(self.deFilter)
		self.currentFilterMode = None
		for k, v in self.filterTypes:
			self.cbFilterType.addItem(v, k)
		self.deFilter.setEnabled(False)
		self.cbFilterType.currentIndexChanged.connect(self.onCurrentIndexChanged)
		self.deFilter.dateTimeChanged.connect(self.onDateChanged)

	def onCurrentIndexChanged(self, idx):
		if not isinstance(idx, int):
			return
		self.currentFilterMode = self.filterTypes[idx][0]
		if self.currentFilterMode == "none":
			self.deFilter.setDisplayFormat("---")
			self.deFilter.setEnabled(False)
		elif self.currentFilterMode == "year":
			self.deFilter.setDisplayFormat(QtCore.QCoreApplication.translate("CalenderList", "yyyy"))
			self.deFilter.setEnabled(True)
		elif self.currentFilterMode == "month":
			self.deFilter.setDisplayFormat(QtCore.QCoreApplication.translate("CalenderList", "MM.yyyy"))
			self.deFilter.setEnabled(True)
		elif self.currentFilterMode == "day":
			self.deFilter.setDisplayFormat(QtCore.QCoreApplication.translate("CalenderList", "dd.MM.yyyy"))
			self.deFilter.setEnabled(True)
		self.updateDateFilter()

	def onDateChanged(self, date):
		self.updateDateFilter()

	def updateDateFilter(self):
		filter = self.getFilter()
		if self.currentFilterMode == "none":
			if filter and "startdate$gt" in filter:
				del filter["startdate$gt"]
			if filter and "startdate$lt" in filter:
				del filter["startdate$lt"]
		elif self.currentFilterMode == "year":
			filter["startdate$gt"] = self.deFilter.date().toString("01.01.yyyy")
			filter["startdate$lt"] = "01.01.%0.4i" % (self.deFilter.date().year() + 1)
		elif self.currentFilterMode == "month":
			filter["startdate$gt"] = self.deFilter.date().toString("01.MM.yyyy")
			# Calculate enddate: set Day of Month to 01; add 33 Days, read Year+Month
			filter["startdate$lt"] = QtCore.QDate(self.deFilter.date().year(), self.deFilter.date().month(), 1).addDays(
					33).toString("01.MM.yyyy")
		elif self.currentFilterMode == "day":
			filter["startdate$gt"] = self.deFilter.date().toString("dd.MM.yyyy")
			filter["startdate$lt"] = self.deFilter.date().addDays(1).toString("dd.MM.yyyy")
		self.setFilter(filter)


class CalenderCoreHandler(WidgetHandler):  # EntryHandler
	"""Class for holding the main (module) Entry within the modules-list"""

	def __init__(self, modul, *args, **kwargs):
		# Config parsen
		config = conf.serverConfig["modules"][modul]
		if "columns" in config:
			if "filter" in config:
				widgetGen = lambda: CalenderWidget(modul, config["columns"], config["filter"])
			else:
				widgetGen = lambda: CalenderWidget(modul, config["columns"])
		else:
			widgetGen = lambda: CalenderWidget(modul)
		if config["icon"]:
			if config["icon"].lower().startswith("http://") or config["icon"].lower().startswith("https://"):
				icon = config["icon"]
			else:
				icon = loadIcon(config["icon"])
		else:
			icon = loadIcon(None)
		super(CalenderCoreHandler, self).__init__(widgetGen, descr=config["name"], icon=icon, vanishOnClose=False,
		                                          *args, **kwargs)
		if "views" in config:
			for view in config["views"]:
				self.addChild(PredefinedViewHandler(modul, view["name"]))


class CalenderHandler(QtCore.QObject):
	def __init__(self, *args, **kwargs):
		super(CalenderHandler, self).__init__(*args, **kwargs)
		event.connectWithPriority('requestModuleHandler', self.requestModuleHandler, event.lowPriority)

	def requestModuleHandler(self, queue, modul):
		config = conf.serverConfig["modules"][modul]
		if config["handler"].startswith("list.calender"):
			f = lambda: CalenderCoreHandler(modul)
			queue.registerHandler(4, f)


_calenderHandler = CalenderHandler()
