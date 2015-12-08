#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.config import conf
from viur_admin.network import NetworkService, RemoteFile


class RegisterQueue:
	"""
	Propagates through the QT-Eventqueue and collects all Handlers able to scope with the current request
	"""

	def __init__(self):
		super().__init__()
		self.queue = {}

	def registerHandler(self, priority, handler):
		"""
		Registers an Object with given priority

		@type priority: int
		@param priority: Priority of the handler. The higest one wins.
		@type handler: Object
		"""
		if priority not in self.queue.keys():
			self.queue[priority] = []
		self.queue[priority].append(handler)

	def getBest(self):
		"""
		Returns the handler with the higest priority.
		If 2 or more handlers claim the same higest priority, the first one is returned

		@return: Object
		"""
		prios = [x for x in self.queue.keys()]
		prios.sort()
		return self.queue[prios[-1]][0]

	def getAll(self):
		"""
		Returns all handlers in ascending order

		@return: [Object]
		"""
		prios = [x for x in self.queue.keys()]
		prios.sort()
		res = []
		for p in prios:
			for item in self.queue[p]:
				res.append(item)
		return res


class Overlay(QtWidgets.QWidget):
	"""
	Blocks its parent widget by displaying a busy or a short message over
	the parent.
	"""

	BUSY = "busy"
	MISSING = "missing"
	ERROR = "error"
	SUCCESS = "okay"

	INFO_DURATION = 30  # 2 seconds
	WARNING_DURATION = 30
	ERROR_DURATION = 30

	def __init__(self, parent=None):
		"""
		@type parent: QWidget
		"""
		QtWidgets.QWidget.__init__(self, parent)
		palette = QtGui.QPalette(self.palette())
		palette.setColor(palette.Background, QtCore.Qt.transparent)
		self.setPalette(palette)
		self.status = None
		animIdx = 0
		self.okayImage = QtGui.QImage(":icons/status/success_white.svg")
		self.missingImage = QtGui.QImage(":icons/status/missing_white.svg")
		self.errorImage = QtGui.QImage(":icons/status/error_transparent.svg")
		self.timer = None
		self.counter = 0
		self.first = False
		self.message = None
		self.resize(QtCore.QSize(1, 1))
		self.hide()

	def paintEvent(self, event):
		"""
		Draws the message/busy overlay

		See http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/html/qwidget.html#paintEvent
		"""
		"""
		Draws the message/busy overlay

		See http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/html/qwidget.html#paintEvent
		"""
		painter = QtGui.QPainter()
		painter.begin(self)
		painter.setRenderHint(QtGui.QPainter.Antialiasing)
		if self.status == self.BUSY:
			painter.fillRect(event.rect(), QtGui.QBrush(QtGui.QColor(255, 255, 255, 128)))
			animIdx = int((self.counter) % 7)
			painter.pen().setWidth(4)
			coords = [(self.width() / 2 - 30, self.height() / 2 - 30),  # Top left
			          (self.width() / 2, (self.height() / 2) - 30),  # Top center
			          (self.width() / 2 + 30, (self.height() / 2) - 30),  # Top right
			          (self.width() / 2 + 30, (self.height() / 2)),  # Center right
			          (self.width() / 2 + 30, (self.height() / 2) + 30),  # Bottom right
			          (self.width() / 2, (self.height() / 2) + 30),  # Bottom center
			          (self.width() / 2 - 30, (self.height() / 2) + 30),  # Bottom left
			          (self.width() / 2 - 30, (self.height() / 2))]  # Center left
			for i in range(0, 8):
				if (animIdx - i) % 8 == 0:
					color = QtGui.QColor(84, 1, 11, min(255, self.counter * 10))
				elif (animIdx - i) % 8 == 1:
					color = QtGui.QColor(147, 2, 20, min(255, self.counter * 10))
				else:
					color = QtGui.QColor(211, 3, 28, min(255, self.counter * 10))
				x, y = coords[i]
				painter.fillRect(int(x - 15), int(y - 15), 20, 20, color)
			painter.pen().setWidth(1)
			painter.setPen(QtGui.QColor(0, 0, 0, min(255, self.counter * 10)))
			fm = QtGui.QFontMetrics(painter.font())
			fontWidth = fm.width(self.message)
			painter.drawText(self.width() / 2 - fontWidth / 2, (self.height() / 2) + 55, self.message)
		elif self.status == self.SUCCESS:
			if self.counter > self.INFO_DURATION - 10:
				painter.setOpacity((20 - self.counter) / 10.0)
			painter.fillRect(event.rect(), QtGui.QBrush(QtGui.QColor(52, 131, 63, 192)))
			painter.drawImage((self.width() / 2 - self.okayImage.width() / 2),
			                  (self.height() / 2 - self.okayImage.height() / 2), self.okayImage)
			fm = QtGui.QFontMetrics(painter.font())
			fontWidth = fm.width(self.message)
			painter.setPen(QtGui.QColor(255, 255, 255))
			painter.drawText(self.width() / 2 - fontWidth / 2, (self.height() / 2 + self.okayImage.height() / 2) + 50,
			                 self.message)
			if self.counter > self.INFO_DURATION:
				self.clear(True)
		elif self.status == self.MISSING:
			if self.counter > self.WARNING_DURATION - 10:
				painter.setOpacity((20 - self.counter) / 10.0)
			painter.fillRect(event.rect(), QtGui.QBrush(QtGui.QColor(0, 65, 110, 192)))
			painter.drawImage((self.width() / 2 - self.missingImage.width() / 2),
			                  (self.height() / 2 - self.missingImage.height() / 2), self.missingImage)
			fm = QtGui.QFontMetrics(painter.font())
			fontWidth = fm.width(self.message)
			painter.setPen(QtGui.QColor(255, 255, 255))
			painter.drawText(self.width() / 2 - fontWidth / 2,
			                 (self.height() / 2 + self.missingImage.height() / 2) + 50, self.message)
			if self.counter > self.WARNING_DURATION:
				self.clear(True)
		elif self.status == self.ERROR:
			if self.counter > self.ERROR_DURATION - 10:
				painter.setOpacity((20 - self.counter) / 10.0)
			painter.fillRect(event.rect(), QtGui.QBrush(QtGui.QColor(0, 0, 0, 128)))
			painter.drawImage((self.width() / 2 - self.errorImage.width() / 2),
			                  (self.height() / 2 - self.errorImage.height() / 2), self.errorImage)
			fm = QtGui.QFontMetrics(painter.font())
			fontWidth = fm.width(self.message)
			painter.setPen(QtGui.QColor(248, 197, 51))
			painter.drawText(self.width() / 2 - fontWidth / 2, (self.height() / 2 + self.errorImage.height() / 2) + 50,
			                 self.message)
			if self.counter > self.ERROR_DURATION:
				self.clear(True)
		painter.end()

	def start(self):
		"""
		Starts displaying.
		Dont call this directly
		"""
		if self.timer:
			self.show()
			return
		self.resize(self.parent().size())
		self.parent().setEnabled(False)
		self.counter = 0
		self.first = True
		self.timer = self.startTimer(100)
		self.show()

	def clear(self, force=False):
		"""
		Clears the overlay.
		Its parent becomes accessible again
		@param force: If True, it clears the overlay istantly. Otherwise, only overlays in state busy will be
		cleared; if there currently displaying an error/success message, the will persist (for the rest of thair
		display-time)
		@type force: Bool
		"""
		if not (force or self.status == self.BUSY):
			return
		if self.timer:
			self.killTimer(self.timer)
			self.timer = None
		self.status = None
		self.resize(QtCore.QSize(1, 1))
		self.parent().setEnabled(True)
		self.hide()

	def inform(self, status, message=""):
		"""
		Draws a informal message over its parent-widget's area.
		If type is not Overlay.BUSY, it clears automaticaly after a few seconds.

		@type status: One of [Overlay.BUSY, Overlay.MISSING, Overlay.ERROR, Overlay.SUCCESS]
		@param status: Type of the message displayed. Sets the icon and the display duration.
		@type message: string
		@param message: Text to display
		"""
		assert (status in [self.BUSY, self.MISSING, self.ERROR, self.SUCCESS])
		self.status = status
		self.message = message
		if status != self.BUSY:
			self.counter = 0
		self.start()

	def timerEvent(self, event):
		"""
		Draws the next frame in the animation.

		See http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/html/qobject.html#timerEvent
		"""
		self.resize(self.parent().size())
		if self.first:  # Give the parent a chance to find its final size
			self.first = False
			return
		self.counter += 1
		if (self.counter > max(
				[self.ERROR_DURATION, self.INFO_DURATION, self.WARNING_DURATION]) and self.status != self.BUSY):
			self.clear(True)
			return
		self.update()


class WidgetHandler(QtWidgets.QTreeWidgetItem):
	"""
	Holds the items displayed top-left within the admin.
	Each of these provides access to one modul and holds the references
	to the widgets shown inside L{MainWindow.ui.stackedWidget}
	"""
	mainWindow = None

	def __init__(self, widgetGenerator, descr="", icon=None, vanishOnClose=True, mainWindow=None, sortIndex=0, *args,
	             **kwargs):
		"""
		@type modul: string
		@param modul: Name of the modul handled
		"""
		super(WidgetHandler, self).__init__(*args, **kwargs)
		if mainWindow:
			self.mainWindow = mainWindow
		if self.mainWindow is None:
			raise UnboundLocalError(
				"You either have to create the mainwindow before using this class or specifiy an replacement.")
		self.widgets = []
		self.widgetGenerator = widgetGenerator
		try:
			prefix, descr = descr.split(": ", 1)
		except ValueError:
			pass
		self.setText(0, descr)
		# self.setText(1, str(sortIndex))
		self.sortIndex = sortIndex
		if icon:
			if isinstance(icon, QtGui.QIcon):
				self.setIcon(0, icon)
			elif isinstance(icon, str) and not icon.startswith("/") and not ("..") in icon and not icon.startswith(
					"https://") and not icon.startswith("http://"):
				self.setIcon(0, QtGui.QIcon(":{0}".format(icon)))
			elif isinstance(icon, str):
				RemoteFile(icon, successHandler=self.loadIconFromRequest)
			else:
				self.setIcon(0, QtGui.QIcon(":icons/modules/list.svg"))
		else:
			self.setIcon(0, QtGui.QIcon(":icons/modules/list.svg"))
		self.vanishOnClose = vanishOnClose

	def loadIconFromRequest(self, request):
		icon = QtGui.QIcon(request.getFileName())
		# logging.debug("loadIconFromRequest %r", icon)
		self.setIcon(0, icon)

	def focus(self):
		"""
		If this handler holds at least one widget, the last widget
		on the stack gains focus
		"""
		if not self.widgets:
			self.widgets.append(self.widgetGenerator())
			self.mainWindow.addWidget(self.widgets[-1])
			# event.emit( QtCore.SIGNAL("addWidget(PyQt_PyObject)"), self.widgets[ -1 ] )
			self.setIcon(1, QtGui.QIcon(":icons/actions/cancel.svg"))
		self.mainWindow.focusHandler(self)

	# event.emit( QtCore.SIGNAL("focusHandler(PyQt_PyObject)"), self )

	def close(self):
		"""
		Closes *one* widgets of this handler
		"""
		if self.widgets:
			self.mainWindow.removeWidget(self.widgets.pop())
		if len(self.widgets) > 0:
			self.focus()
		else:
			if self.vanishOnClose:
				self.mainWindow.removeHandler(self)
			else:
				self.mainWindow.unfocusHandler(self)
				self.setIcon(1, QtGui.QIcon())

	def getBreadCrumb(self):
		for widget in self.widgets[:: -1]:
			try:
				txt, icon = widget.getBreadCrumb()
				if not icon:
					icon = QtGui.QIcon()
				elif not isinstance(icon, QtGui.QIcon):
					icon = QtGui.QIcon(icon)
				self.setIcon(0, icon)
				self.setText(0, txt)
				return txt, icon
			except:
				continue
		return self.text(0), self.icon(0)

	def clicked(self):
		"""
		Called whenever the user selects the handler from the treeWidget.
		"""
		self.setExpanded(not self.isExpanded())
		self.focus()

	def contextMenu(self):
		"""
		Currently unused
		"""
		pass

	def stackHandler(self):
		"""
			Stacks this handler onto the currently active one.
		"""
		self.mainWindow.stackHandler(self)

	def register(self):
		"""
			Adds this handler as a top-level one
		"""
		self.mainWindow.addHandler(self)

	def __lt__(self, other):
		# column = self.treeWidget().sortColumn()
		key1 = self.sortIndex
		key2 = other.sortIndex
		try:
			return float(key1) < float(key2)
		except ValueError:
			return key1 < key2


class GroupHandler(WidgetHandler):
	"""
		Toplevel widget for one modul-group
	"""

	def clicked(self):
		"""
		Called whenever the user selects the handler from the treeWidget.
		"""
		self.setExpanded(not self.isExpanded())

	def contextMenu(self):
		"""
		Currently unused
		"""
		pass


class WheelEventFilter(QtCore.QObject):
	"""
		Prevent MouseWheelActions if the widget has no focus.
		This fixes accidential changing values in editWidget while scrolling.
	"""

	def eventFilter(self, obj, event):
		if event.type() == QtCore.QEvent.Wheel and obj.focusPolicy() == QtCore.Qt.StrongFocus:
			event.ignore()
			return True
		return False


wheelEventFilter = WheelEventFilter()


def urlForItem(modul, item):
	"""
		Returns a QUrl for the given item.
		Usefull for creating a QDrag which can be dropped outside the application.
		@param modul: Name of the modul, this item belongs to.
		@type modul: String
		@param item: Data-Dictionary of the item. Must contain at least an "id" key.
		@type item: Dict
		@returns: QUrl
	"""
	if "dlkey" in item.keys():  # Its a file, fill in its dlkey, sothat drag&drop to the outside works
		if "name" in item.keys():
			return (QtCore.QUrl("%s/%s/download/%s/%s" % (
				NetworkService.url.replace("/admin", ""), modul, item["dlkey"], item["name"])))
		else:  # Return a URL without a name appended
			return QtCore.QUrl("%s/%s/download/%s" % (NetworkService.url.replace("/admin", ""), modul, item["dlkey"]))
	else:
		if "name" in item.keys():
			return QtCore.QUrl(
				"%s/%s/view/%s/%s" % (NetworkService.url.replace("/admin", ""), modul, item["id"], item["name"]))
		else:  # Return a URL without a name appended
			return QtCore.QUrl("%s/%s/view/%s" % (NetworkService.url.replace("/admin", ""), modul, item["id"]))


def itemFromUrl(url):
	"""
		Parses a URL constructed by urlForItem.
		Returns a tuple (modul, id, name ) if parsing is successfull, None otherwise.
		@param url: Url which should be parsed.
		@type url: QUrl or String
		@returns: Tuple (modul, id, name ) or None
	"""
	if isinstance(url, QtCore.QUrl):
		url = url.toString()
	# Strip host and query-string
	url = url[url.find("/", 7):]
	if "?" in url:
		url = url[: url.find("?")]
	parts = [x for x in url.split("/") if x]
	if len(parts) < 3:
		return None
	if parts[1].lower() != "view":
		return None
	modul = parts[0]
	if modul not in conf.serverConfig["modules"].keys():  # Unknown modul
		return None
	if len(parts) > 3:
		return modul, parts[2], parts[3]
	else:
		return modul, parts[2], ""


def formatString(format, skelStructure, data, prefix=None):
	""" Parses a String given by format and substitutes Placeholders using values specified by data.
	Syntax for Placeholders is $(%s). Its possible to traverse to subdictionarys by using a dot as seperator.
	If data is a list, the result each element from this list applied to the given string; joined by ", ".
	Example:
	data = {"name": "Test","subdict": {"a":"1","b":"2"}}
	formatString = "Name: $(name), subdict.a: $(subdict.a)"
	Result: "Name: Test, subdict.a: 1"

	@type format: String
	@param format: String contining the format
	@type skelStructure: Dict
	@param skelStructure: Parses along the structure of the given skeleton
	@type data: List or Dict
	@param data: Data applied to the format String
	@return: String
	"""

	def chooseLang(value, prefs, key):  # FIXME: Copy&Paste from bones/string
		"""
			Tries to select the best language for the current user.
			Value is the dictionary of lang -> text recived from the server,
			prefs the list of languages (in order of preference) for that bone.
		"""
		if not isinstance(value, dict):
			return str(value)
		# Datastore format. (ie the langdict has been serialized to name.lang pairs
		try:
			lang = "%s.%s" % (key, conf.adminConfig["language"])
		except:
			lang = ""
		if lang in value.keys() and value[lang]:
			return value[lang]
		for lang in prefs:
			if "%s.%s" % (key, lang) in value.keys():
				if value["%s.%s" % (key, lang)]:
					return value["%s.%s" % (key, lang)]
		# Normal edit format ( name : { lang: xx } ) format
		if key in value.keys() and isinstance(value[key], dict):
			langDict = value[key]
			try:
				lang = conf.adminConfig["language"]
			except:
				lang = ""
			if lang in langDict.keys():
				return langDict[lang]
			for lang in prefs:
				if lang in langDict.keys():
					if langDict[lang]:
						return langDict[lang]
		return ""

	if isinstance(skelStructure, list):
		# The server sends the information as list; but the first thing
		# editWidget etc does, is building up an dictionary again.
		# It this hasn't happen yet, we do it here
		tmpDict = {}
		for key, bone in skelStructure:
			tmpDict[key] = bone
		skelStructure = tmpDict
	prefix = prefix or []
	if isinstance(data, list):
		return ", ".join([formatString(format, skelStructure, x, prefix) for x in data])
	res = format
	if isinstance(data, str):
		return data
	if not data:
		return "" # FIXME: testing if this is better than return the format string as provided
	for key in data.keys():
		if isinstance(data[key], dict):
			res = formatString(res, skelStructure, data[key], prefix + [key])
		elif isinstance(data[key], list) and len(data[key]) > 0 and isinstance(data[key][0], dict):
			res = formatString(res, skelStructure, data[key][0], prefix + [key])
		else:
			res = res.replace("$(%s)" % (".".join(prefix + [key])), str(data[key]))
	# Check for translated top-level bones
	if not prefix:
		for key, bone in skelStructure.items():
			if "languages" in bone.keys() and bone["languages"]:
				res = res.replace("$(%s)" % key, str(chooseLang(data, bone["languages"], key)))
	return res


def loadIcon(icon):
	"""
		Tries to create an icon from the given filename.
		If that image exists in different sizes, all of them are loaded.
	"""
	if isinstance(icon, QtGui.QIcon):
		return icon
	elif isinstance(icon, str) and not icon.startswith("/") and not ("..") in icon and not icon.startswith(
			"https://") and not icon.startswith("http://"):
		return QtGui.QIcon(":{0}".format(icon))
	elif isinstance(icon, str):
		return icon
	else:
		return QtGui.QIcon(":icons/modules/list.svg")


def showAbout(parent=None):
	"""
	Shows the about-dialog
	"""
	try:
		import BUILD_CONSTANTS

		version = BUILD_CONSTANTS.BUILD_RELEASE_STRING
		vdate = BUILD_CONSTANTS.BUILD_TIMESTAMP
	except ImportError:  # Local development or not a freezed Version
		vdate = "development version"
		version = "unknown"
		try:
			gitHead = open(".git/FETCH_HEAD", "r").read()
			for line in gitHead.splitlines():
				line = line.replace("\t", " ")
				if "branch 'master'" in line:
					version = line.split(" ")[0]
		except:
			pass
	appName = "Viur Informationssystem - Administration"
	appDescr = "© Mausbrand Informationssysteme GmbH\n"
	appDescr += "Version: %s\n" % vdate
	appDescr += "Revision: %s" % version
	QtWidgets.QMessageBox.about(parent, appName, appDescr)
