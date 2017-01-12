#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib.request
import urllib.error
import urllib.parse
from urllib.parse import quote_plus
import os
from datetime import datetime, timedelta
from xml.dom.minidom import parseString
import random
import urllib

from PyQt5 import QtGui, QtCore, QtWidgets

import sys
import sys
import time
from math import ceil, pow
from network import NetworkService
from config import conf

"""
	Displayes the amount of visitors for the last 7 days.
	Requirements: - The application provides an anaylitcs-table-ID (conf["admin.analyticsKey"])
				- The current user has the right to see this table
	Otherwise, an ViUR splashscreen is displayed.
"""


class GraphPlotter(QtWidgets.QWidget):
	bgColor = "#FFFFFF"
	graphColor = "#000000"
	txtColor = "#000000"
	highlightColor = "#ff0000"
	grapDataColor = {"total": "#FF0000",
	                 "facebook": "#00FF00",
	                 "twitter": "#0000FF",
	                 "google": "#00FFFF"
	                 }

	def __init__(self):
		super(GraphPlotter, self).__init__()
		self.data = {}
		self.mousePos = 0, 0
		self.setMouseTracking(True)
		self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding))
		self.setMinimumSize(QtCore.QSize(256, 256))
		for x in range(0, 8):
			self.data[x] = {"total": 0}

	def mouseMoveEvent(self, event):
		super(GraphPlotter, self).mouseMoveEvent(event)
		self.mousePos = event.pos().x(), event.pos().y()
		self.update()

	def setData(self, data):
		self.data = data
		self.update()

	def paintEvent(self, event):
		highlightStats = None  # Highlight this point on mouseover: (x,y), day, source, visits
		qp = QtGui.QPainter()
		qp.begin(self)
		rect = event.rect()
		qp.fillRect(rect, QtGui.QColor(self.bgColor))
		qp.setPen(QtGui.QColor(self.graphColor))
		dataMax = max([x["total"] for x in self.data.values()] + [1.0])
		qp.drawLine(100, 10, 100, event.rect().height() - 50)
		qp.drawLine(100, event.rect().height() - 50, event.rect().width() - 50, event.rect().height() - 50)
		l = pow(10, (len(str(dataMax))))
		graphMax = ceil(dataMax / l) * l
		if graphMax * 0.25 > dataMax:
			graphMax *= 0.25
		elif graphMax * 0.5 > dataMax:
			graphMax *= 0.5
		elif graphMax * 0.75 > dataMax:
			graphMax *= 0.75
		xStep = (event.rect().width() - 150) / 7.0
		graphHeigt = event.rect().height() - 60
		qp.setFont(QtGui.QFont('Decorative', 10))
		for x in range(0, 5):  # Y-Axis description
			g = x / 4.0
			yPos = int(15 + (graphHeigt * g))
			qp.setPen(QtGui.QColor(self.graphColor))
			qp.drawLine(95, yPos - 5, 105, yPos - 5)
			qp.setPen(QtGui.QColor(self.txtColor))
			qp.drawText(10, yPos, str(int(graphMax - (graphMax * g))))
		xPos = 100
		for y in range(len(self.data.keys()) - 1, -1, -1):  # X-Axis description
			dtNow = datetime.now()
			qp.setPen(QtGui.QColor(self.graphColor))
			qp.drawLine(xPos, event.rect().height() - 45, xPos, event.rect().height() - 55)
			qp.setPen(QtGui.QColor(self.txtColor))
			qp.drawText(QtCore.QRect(xPos - 40, event.rect().height() - 45, 80, 20), QtCore.Qt.AlignCenter,
			            (dtNow - timedelta(days=y)).strftime("%d.%m.%Y"))
			xPos += xStep
		visitSources = []
		for x in range(0, 8):
			for key in self.data[x].keys():
				if not key in visitSources:
					visitSources.append(key)
		for type in visitSources:
			xPos = 100
			lastPos = None
			if type in self.grapDataColor.keys():
				qp.setPen(QtGui.QColor(self.grapDataColor[type]))
			else:
				qp.setPen(QtGui.QColor("#000000"))
			for x in range(7, -1, -1):
				try:
					val = self.data[x][type]
				except KeyError:  # No visists from this source this day
					val = 0
				pointHeight = (event.rect().height() - 50) - float(val) / float(graphMax) * graphHeigt
				if lastPos:
					qp.drawLine(lastPos[0], lastPos[1], xPos, pointHeight)
				lastPos = (xPos, pointHeight)
				qp.drawLine(xPos - 5, pointHeight + 5, xPos + 5, pointHeight - 5)
				qp.drawLine(xPos + 5, pointHeight + 5, xPos - 5, pointHeight - 5)
				# Highlight the element if mouse-over
				if (self.mousePos[0] - xPos) * (self.mousePos[0] - xPos) + (self.mousePos[1] - pointHeight) * (
							self.mousePos[1] - pointHeight) < 20:
					highlightStats = (xPos, pointHeight), x, type, val
				xPos += xStep
		if highlightStats:
			(x, y), day, type, visists = highlightStats
			qp.setPen(QtGui.QColor(self.bgColor))
			qp.fillRect(QtCore.QRect(x - 120, y + 10, 240, 30), QtGui.QColor(self.bgColor))
			qp.setPen(QtGui.QColor(self.highlightColor))
			qp.drawArc(QtCore.QRect(x - 8, y - 8, 16, 16), 0, 16 * 360)
			qp.drawRect(x - 120, y + 10, 240, 30)
			qp.setPen(QtGui.QColor(self.graphColor))
			if type == "total":
				txt = QtCore.QCoreApplication.translate("Analytics", "%s (total): %s") % (
					(dtNow - timedelta(days=day)).strftime("%d.%m.%Y"), visists)
			else:
				txt = QtCore.QCoreApplication.translate("Analytics", "%s via %s: %s") % (
					(dtNow - timedelta(days=day)).strftime("%d.%m.%Y"), type, visists)
			qp.drawText(QtCore.QRect(x - 115, y + 12, 230, 26), QtCore.Qt.AlignCenter, txt)
		qp.end()


class AnalyticsTableModel(QtCore.QAbstractTableModel):
	"""Model for displaying data within a listView"""
	_chunkSize = 25

	def __init__(self, parent, *args):
		QtCore.QAbstractTableModel.__init__(self, parent, *args)
		self.data = {}
		self.fields = []

	def setData(self, data):
		self.emit(QtCore.SIGNAL("modelAboutToBeReset()"))
		self.data = data
		self.fields = ["total"]
		for stat in self.data.values():
			for key in stat.keys():
				if not key in self.fields:
					self.fields.append(key)
		self.emit(QtCore.SIGNAL("modelReset()"))

	def rowCount(self, parent):
		return (len(self.data.keys()))

	def columnCount(self, parent):
		return (len(self.fields))

	def data(self, index, role):
		if not index.isValid():
			return None
		elif role != QtCore.Qt.DisplayRole:
			return None
		if index.row() >= 0 and (index.row() < len(self.data.keys())):
			try:
				return (self.data[len(self.data.keys()) - index.row()][self.fields[index.column()]])
			except KeyError:  # No visists from this source this day
				return (0)
		else:
			return (" ? ")

	def headerData(self, col, orientation, role):
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			return (self.fields[col])
		elif orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
			return ((datetime.now() - timedelta(days=col)).strftime(
				QtCore.QCoreApplication.translate("Analytics", "%d.%m.%Y")))
		return None

	def sort(self, colum, order):
		return


class AnalytisWidget(QtWidgets.QWidget):
	def __init__(self):
		super(AnalytisWidget, self).__init__()
		self.queue = []
		self.sessionID = None
		self.isDisplayingStats = False  # Wherever weve successfully retrived the first stats
		self.data = {}
		for x in range(0, 8):
			tot = random.randrange(0, 10000)
			self.data[x] = {"total": 0}
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)
		self.imgLbl = QtWidgets.QLabel(self)
		self.imgLbl.setPixmap(QtGui.QPixmap(":icons/viur_splash.png"))
		self.layout.addWidget(self.imgLbl)
		self.plot = GraphPlotter()
		self.plot.hide()
		self.model = AnalyticsTableModel(self)
		self.tableView = QtGui.QTableView(self)
		self.tableView.hide()
		self.tableView.setModel(self.model)
		if "configuration" in conf.serverConfig.keys() and "analyticsKey" in conf.serverConfig["configuration"].keys():
			self.uaKey = conf.serverConfig["configuration"]["analyticsKey"]
			# Start fetching the data
			credDict = {"Email": conf.currentUsername,
			            "Passwd": conf.currentPassword,
			            "source": "Viur-Admin",
			            "accountType": "HOSTED_OR_GOOGLE",
			            "service": "analytics"}
			credStr = urllib.parse.urlencode(credDict)
			self.request = NetworkService.request("https://www.google.com/accounts/ClientLogin",
			                                      credStr.encode("UTF-8"))
			self.request.finished.connect(self.onGoogleAuthSuccess)
			dtNow = datetime.now()
			for x in range(1, 8):
				tdStart = timedelta(days=x + 1)
				tdEnd = timedelta(days=x)
				url = "https://www.google.com/analytics/feeds/data?sort=-ga:visits&max-results=50&start-date=%s&ids" \
				      "=%s&metrics=ga:visits&end-date=%s&dimensions=ga:source" % (
					      (dtNow - tdStart).strftime("%Y-%m-%d"), self.uaKey, (dtNow - tdEnd).strftime("%Y-%m-%d"))
				self.queue.append((x, url))

	def onGoogleAuthSuccess(self):
		sid = bytes(self.request.readAll()).decode("UTF-8")
		self.request.deleteLater()
		self.request = None
		for l in sid.splitlines():
			if l.lower().startswith("auth"):
				self.sessionID = l[5:].strip()
		self.fetchNext()

	def fetchNext(self):
		if not self.sessionID:
			return
		if not self.request:
			if len(self.queue) > 0:
				self.request = NetworkService.request(self.queue[-1][1], extraHeaders={
					"Authorization": "GoogleLogin auth=" + self.sessionID})
				self.request.finished.connect(self.fetchNext)
				return
			return
		data = bytes(self.request.readAll()).decode("UTF-8")
		self.request.deleteLater()
		self.request = None
		currentRequestData = self.queue.pop()
		dom = parseString(data)
		try:
			self.data[currentRequestData[0]]["total"] = int(
				dom.getElementsByTagName('dxp:aggregates')[0].getElementsByTagName("dxp:metric")[0].getAttribute(
					"value"))
		except:  # We somehow got invalid data
			return
		items = dom.getElementsByTagName('entry')
		for item in items:
			src = item.getElementsByTagName("dxp:dimension")[0].getAttribute("value")
			visits = int(item.getElementsByTagName("dxp:metric")[0].getAttribute("value"))
			self.data[currentRequestData[0]][src] = visits
		if len(self.queue) > 0:
			self.request = NetworkService.request(self.queue[-1][1],
			                                      extraHeaders={"Authorization": "GoogleLogin auth=" + self.sessionID})
			self.request.finished.connect(self.fetchNext)
		if not self.isDisplayingStats:
			self.isDisplayingStats = True
			self.imgLbl.deleteLater()
			self.layout.addWidget(self.plot)
			self.layout.addWidget(self.tableView)
		self.model.setData(self.data)
		self.plot.setData(self.data)

	def resizeEvent(self, resizeEvent):
		"""Ensure Items in listWidget get realigned if the available space changes"""
		super(AnalytisWidget, self).resizeEvent(resizeEvent)
		if self.isDisplayingStats:
			self.tableView.reset()
