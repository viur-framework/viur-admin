# -*- coding: utf-8 -*-
from typing import Callable, Any, Dict, List, Tuple, Union
from viur_admin.pyodidehelper import isPyodide
from viur_admin.log import getLogger

logger = getLogger(__name__)

from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.config import conf
from viur_admin.network import NetworkService, RemoteFile, RequestWrapper
from viur_admin.pyodidehelper import isPyodide


if isPyodide:
	import js
	_singleFileCallback = None
	_summernoteAcceptCallback = None
	_fileSelectElem = js.document.getElementById("singlefileupload")
	def _singeFileSelectChange(event):
		global _singleFileCallback, _fileSelectElem
		if _singleFileCallback:
			_singleFileCallback(_fileSelectElem.files[0])
		_singleFileCallback = None
	_fileSelectElem.addEventListener("change", _singeFileSelectChange, False)

	def showSingleFileSelect(callback):
		global _singleFileCallback, _fileSelectElem
		_singleFileCallback = callback
		_fileSelectElem.value = ""
		_fileSelectElem.click()

	def switchToSummernote(currentText, acceptCallback):
		global _summernoteAcceptCallback
		_summernoteAcceptCallback = acceptCallback
		js.switchToEditor(currentText)

	def _summernoteCallback(event):
		global _summernoteAcceptCallback
		res = js.getEditorContents()
		if _summernoteAcceptCallback:
			_summernoteAcceptCallback(res)
		_summernoteAcceptCallback = None

	js.document.getElementById("textBoneAcceptBtn").addEventListener("click", _summernoteCallback, False)
else:
	def showSingleFileSelect(callback):
		raise NotImplementedError()

	def switchToSummernote(currentText, acceptCallback):
		raise NotImplementedError()

class RegisterQueue:
	"""
	Propagates through the QT-Eventqueue and collects all Handlers able to scope with the current request
	"""

	def __init__(self, *args: Any, **kwargs: Any):
		super(RegisterQueue, self).__init__()
		self.queue: Dict[int, List[Callable]] = dict()

	def registerHandler(self, priority: int, handler: Callable) -> None:
		"""
		Registers an Object with given priority

		@type priority: int
		@param priority: Priority of the handler. The higest one wins.
		@type handler: Object
		"""
		if priority not in self.queue:
			self.queue[priority] = []
		self.queue[priority].append(handler)

	def getBest(self) -> Callable:
		"""
		Returns the handler with the higest priority.
		If 2 or more handlers claim the same higest priority, the first one is returned

		@return: Object
		"""
		prios = [x for x in self.queue]
		prios.sort()
		return self.queue[prios[-1]][0]

	def getAll(self) -> List[Callable]:
		"""
		Returns all handlers in ascending order

		@return: [Object]
		"""
		prios = [x for x in self.queue]
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

	def __init__(self, parent: QtWidgets.QWidget=None):
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

	def paintEvent(self, event: QtGui.QPaintEvent) -> None:
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

	def start(self) -> None:
		"""
		Starts displaying.
		Dont call this directly
		"""
		if 1 or isPyodide:
			return
		if self.timer:
			self.show()
			return
		self.resize(self.parent().size())
		self.parent().setEnabled(False)
		self.counter = 0
		self.first = True
		self.timer = self.startTimer(100)
		self.show()

	def clear(self, force: bool = False) -> None:
		"""
		Clears the overlay.
		Its parent becomes accessible again
		@param force: If True, it clears the overlay istantly. Otherwise, only overlays in state busy will be
		cleared; if there currently displaying an error/success message, the will persist (for the rest of thair
		display-time)
		@type force: Bool
		"""
		if 1 or isPyodide:
			return
		if not (force or self.status == self.BUSY):
			return
		if self.timer:
			self.killTimer(self.timer)
			self.timer = None
		self.status = None
		self.resize(QtCore.QSize(1, 1))
		self.parent().setEnabled(True)
		self.hide()

	def inform(self, status: str, message: str = "") -> None:
		"""
		Draws a informal message over its parent-widget's area.
		If type is not Overlay.BUSY, it clears automaticaly after a few seconds.

		@type status: One of [Overlay.BUSY, Overlay.MISSING, Overlay.ERROR, Overlay.SUCCESS]
		@param status: Type of the message displayed. Sets the icon and the display duration.
		@type message: string
		@param message: Text to display
		TODO: change status into real enum
		"""
		if 1 or isPyodide:
			return
		assert (status in [self.BUSY, self.MISSING, self.ERROR, self.SUCCESS])
		self.status = status
		self.message = message
		if status != self.BUSY:
			self.counter = 0
		self.start()

	def timerEvent(self, event: QtCore.QTimerEvent) -> None:
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
	Each of these provides access to one module and holds the references
	to the widgets shown inside L{MainWindow.ui.stackedWidget}
	"""
	mainWindow = None

	def __init__(
			self,
			widgetGenerator: Callable,
			descr: str = "",
			icon: QtGui.QIcon = None,
			vanishOnClose: bool = True,
			mainWindow: QtWidgets.QWidget = None,
			sortIndex: int = 0,
			*args: Any,
			**kwargs: Any):
		super(WidgetHandler, self).__init__(*args, **kwargs)
		if mainWindow:
			self.mainWindow = mainWindow
		if self.mainWindow is None:
			raise UnboundLocalError(
				"You either have to create the mainwindow before using this class or specifiy an replacement.")
		self.widgets: List[QtWidgets.QWidget] = list()
		self.widgetGenerator = widgetGenerator
		try:
			prefix, descr = descr.split(": ", 1)
		except ValueError as err:
			pass
		self.setText(0, descr)
		if conf.cmdLineOpts and conf.cmdLineOpts.show_sortindex:
			self.setText(1, str(sortIndex))
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
				self.setIcon(0, QtGui.QIcon.fromTheme("list"))
		else:
			self.setIcon(0, QtGui.QIcon.fromTheme("list"))
		self.vanishOnClose = vanishOnClose

	def loadIconFromRequest(self, request: RequestWrapper) -> None:
		filename = request.getFileName()
		icon = QtGui.QIcon(filename)
		logger.debug("WidgetHandler.loadIconFromRequest: %r, %r", filename, icon)
		self.setIcon(0, icon)

	def focus(self) -> None:
		"""
		If this handler holds at least one widget, the last widget
		on the stack gains focus
		"""
		if not self.widgets:
			self.widgets.append(self.widgetGenerator())
			self.mainWindow.addWidget(self.widgets[-1])
			# event.emit( QtCore.SIGNAL("addWidget(PyQt_PyObject)"), self.widgets[ -1 ] )
			self.setIcon(1, QtGui.QIcon.fromTheme("cancel-cross"))
		self.mainWindow.focusHandler(self)

	# event.emit( QtCore.SIGNAL("focusHandler(PyQt_PyObject)"), self )

	def close(self) -> None:
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

	def getBreadCrumb(self) -> Tuple[str, QtGui.QIcon]:
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

	def clicked(self) -> None:
		"""
		Called whenever the user selects the handler from the treeWidget.
		"""
		self.setExpanded(not self.isExpanded())
		self.focus()

	def contextMenu(self) -> None:
		"""
		Currently unused
		"""
		pass

	def stackHandler(self) -> None:
		"""
			Stacks this handler onto the currently active one.
		"""
		self.mainWindow.stackHandler(self)

	def register(self) -> None:
		"""
			Adds this handler as a top-level one
		"""
		self.mainWindow.addHandler(self)

	def __lt__(self, other: Any) -> None:
		key1 = self.sortIndex
		key2 = other.sortIndex
		try:
			return float(key1) > float(key2)
		except ValueError:
			return key1 > key2


class GroupHandler(WidgetHandler):
	"""
		Toplevel widget for one module-group
	"""

	def clicked(self) -> None:
		"""
		Called whenever the user selects the handler from the treeWidget.
		"""
		self.setExpanded(not self.isExpanded())

	def contextMenu(self) -> None:
		"""
		Currently unused
		"""
		pass


class WheelEventFilter(QtCore.QObject):
	"""
		Prevent MouseWheelActions if the widget has no focus.
		This fixes accidential changing values in editWidget while scrolling.
	"""

	def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:
		if event.type() == QtCore.QEvent.Wheel:
			event.ignore()
			return True
		return False


wheelEventFilter = WheelEventFilter()


class ViurTabBar(QtWidgets.QTabBar):
	"""Used in conjunction with WheelEventFilter especially for QTabWidget

	"""

	def __init__(self, parent: QtWidgets.QWidget = None):
		super(ViurTabBar, self).__init__(parent)
		self.installEventFilter(wheelEventFilter)


def urlForItem(module: str, item: Dict[str, Any]) -> QtCore.QUrl:
	"""
		Returns a QUrl for the given item.
		Usefull for creating a QDrag which can be dropped outside the application.
		@param module: Name of the module, this item belongs to.
		@type module: String
		@param item: Data-Dictionary of the item. Must contain at least an "id" key.
		@type item: Dict
		@returns: QUrl
	"""
	if "dlkey" in item:  # Its a file, fill in its dlkey, sothat drag&drop to the outside works
		if "name" in item:
			return (QtCore.QUrl("%s/%s/download/%s/%s" % (
				NetworkService.url.replace("/admin", ""), module, item["dlkey"], item["name"])))
		else:  # Return a URL without a name appended
			return QtCore.QUrl("%s/%s/download/%s" % (NetworkService.url.replace("/admin", ""), module, item["dlkey"]))
	else:
		if "name" in item:
			return QtCore.QUrl(
				"%s/%s/view/%s/%s" % (NetworkService.url.replace("/admin", ""), module, item["key"], item["name"]))
		else:  # Return a URL without a name appended
			return QtCore.QUrl("%s/%s/view/%s" % (NetworkService.url.replace("/admin", ""), module, item["key"]))


def itemFromUrl(url: QtCore.QUrl) -> Union[Tuple[str, str, str], None]:
	"""
		Parses a URL constructed by urlForItem.
		Returns a tuple (module, id, name ) if parsing is successfull, None otherwise.
		@param url: Url which should be parsed.
		@type url: QUrl or String
		@returns: Tuple (module, id, name ) or None
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
	if modul not in conf.serverConfig["modules"]:  # Unknown module
		return None
	if len(parts) > 3:
		return modul, parts[2], parts[3]
	else:
		return modul, parts[2], ""


def formatString(format: str, data: Dict[str, Any], structure: Dict[str, Any] = None, prefix: List[str] = None, language: str = "de", _rec: int = 0) -> str:
	"""
	Parses a string given by format and substitutes placeholders using values specified by data.

	The syntax for the placeholders is $(%s).
	Its possible to traverse to sub-dictionarys by using a dot as seperator.
	If data is a list, the result each element from this list applied to the given string; joined by ", ".

	Example:

		data = {"name": "Test","subdict": {"a":"1","b":"2"}}
		formatString = "Name: $(name), subdict.a: $(subdict.a)"

	Result: "Name: Test, subdict.a: 1"

	:param format: String containing the format.
	:type format: str

	:param data: Data applied to the format String
	:type data: list | dict

	:param structure: Parses along the structure of the given skeleton.
	:type structure: dict

	:param prefix: a key which will be used to lookup information in a dict under data
	:type prefix: list

	:param language: the 2 char name of a language which should be used for translated data, e.g 'de'
	:type language: str

	:param _rec: a counter for internal debugging purposes, whichs holds the number of recursive calls
	:type _rec: int

	:return: The traversed string with the replaced values.
	:rtype: str
	"""

	if structure and isinstance(structure, list):
		structure = {k: v for k, v in structure}

	prefix = prefix or []
	res = format

	try:
		if isinstance(data, list):
			return ", ".join([formatString(format, x, structure, prefix, language, _rec=_rec + 1) for x in data])

		elif isinstance(data, str):
			return data

		elif not data:
			return res

		for key in data:
			val = data[key]
			struct = structure.get(key) if structure else None

			# logger.debug("key: %r, val: %r", key, val)
			# print("%s%s: %s" % (_rec * " ", key, struct))

			if isinstance(val, dict):
				if struct and ("$(%s)" % ".".join(prefix + [key])) in res:
					langs = struct.get("languages")
					if langs:
						if language and language in langs and language in val:
							val = val[language]
						else:
							val = ", ".join(val.values())

					else:
						continue

				else:
					res = formatString(res, val, structure, prefix + [key], language, _rec=_rec + 1)

			elif isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
				res = formatString(res, val[0], structure, prefix + [key], language, _rec=_rec + 1)
			elif isinstance(val, list):
				val = ", ".join(val)

			res = res.replace("$(%s)" % (".".join(prefix + [key])), str(val))
	except Exception as err:
		pass
	# logger.debug("in formatString: %r, %r, %r", format, data, err)
	return res

def colorizeIcon(inData: bytes) -> QtGui.QIcon:
	"""
		Rewrites the fill-color in the given SVG-Data with the text-color from the current palette and returns
		it as an QIcon
	"""
	palette = QtWidgets.QApplication.instance().palette()
	print(palette.text().color().name())
	targetColor = b"#FF0000"
	inData = inData.replace(b"#FFFFFF", targetColor) \
		.replace(b"#fff", targetColor) \
		.replace(b"\"#FFFFFF\"", b"\"%s\"" % targetColor)
	return QtGui.QIcon(QtGui.QPixmap.fromImage(QtGui.QImage.fromData(inData)))

def loadIcon(icon: Union[QtGui.QIcon, str]) -> Union[QtGui.QIcon, str]:
	"""
		Tries to create an icon from the given filename.
		If that image exists in different sizes, all of them are loaded.
	"""
	if isinstance(icon, QtGui.QIcon):
		return icon
	elif isinstance(icon, str):
		if icon.startswith(":"):
			svgData = QtCore.QFile(icon)
			if not svgData.open(QtCore.QFile.ReadOnly):
				svgData = QtCore.QFile(":icons/question.svg")
				assert svgData.open(QtCore.QFile.ReadOnly)
				#return QtGui.QIcon.fromTheme("question")
			return colorizeIcon(svgData.readAll())
		elif "/" not in icon and not "." in icon:
			if icon.startswith("icon-"):
				icon = icon[5:]
			svgData = QtCore.QFile(":icons/%s.svg" % icon)
			if not svgData.open(QtCore.QFile.ReadOnly):
				svgData = QtCore.QFile(":icons/question.svg")
				assert svgData.open(QtCore.QFile.ReadOnly)
				#return QtGui.QIcon.fromTheme("question")
			return colorizeIcon(svgData.readAll())
		elif icon.startswith("/"):
			return icon
	return QtGui.QIcon.fromTheme("question")


def showAbout(parent: QtWidgets.QWidget = None) -> None:
	"""Shows the about-dialog

	:param parent:
	:type parent: QtWidgets.QWidget
	:return:
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

def getIconTheme() -> Tuple[bool, str]:
	"""
		Tries to guess if the user uses a dark theme and switch to the white icons if needed.
		:return: (True, "viur-dark") if the user uses a dark theme else (False, "viur-light")
	"""
	return False, "viur-light"
