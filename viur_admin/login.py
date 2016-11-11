import urllib.parse

from viur_admin.log import getLogger

logger = getLogger(__name__)

import json
import re

from PyQt5 import QtCore, QtWidgets, QtGui, QtWebKitWidgets, QtWebKit, QtNetwork

from viur_admin.ui.loginformUI import Ui_LoginWindow
from viur_admin.ui.addportalwizardUI import Ui_AddPortalWizard
from viur_admin.accountmanager import Accountmanager
from viur_admin.network import NetworkService, securityTokenProvider, nam
from viur_admin.event import event
from viur_admin import config
from viur_admin.utils import Overlay, showAbout
from viur_admin.locales import ISO639CODES


class GoogleLoginView(QtWidgets.QDialog):

	def __init__(self, res, parent=None):
		super(QtWidgets.QDialog, self).__init__(parent)
		# self.jar = QtNetwork.QNetworkCookieJar()
		self.webView = QtWebKitWidgets.QWebView()
		self.setLayout(QtWidgets.QVBoxLayout())
		self.layout().addWidget(self.webView)
		self.webView.settings().setAttribute(QtWebKit.QWebSettings.JavascriptEnabled, True)
		self.webView.settings().setAttribute(QtWebKit.QWebSettings.JavascriptCanOpenWindows, True)
		self.webView.page().setNetworkAccessManager(nam)
		self.webView.setUrl(QtCore.QUrl(res["url"]))
		self.setModal(True)
		self.webView.urlChanged.connect(self.onUrlChanged)
		self.webView.loadFinished.connect(self.onLoadFinished)
		self.resize(1024, 800)

	def onUrlChanged(self, url):
		logger.debug("urlChanged: %r", url)
		if self.webView.findText("OKAY"):
			# logger.debug("cookies: %r", self.webView.page().networkAccessManager().cookieJar().allCookies())
			self.close()
			self.deleteLater()

	def onLoadFinished(self, status):
		logger.debug("loadFinished: %r", status)
		if self.webView.findText("OKAY"):
			# logger.debug("cookies: %r", self.webView.page().networkAccessManager().cookieJar().allCookies())
			self.close()
			self.deleteLater()


class AddPortalWizard(QtWidgets.QWizard):
	def __init__(self, *args, **kwargs):
		super(AddPortalWizard, self).__init__(*args, **kwargs)
		self.ui = Ui_AddPortalWizard()
		self.ui.setupUi(self)
		self.forcePageFlip = False
		self.choosenAuthMethod = None

	def validateCurrentPage(self):
		if self.forcePageFlip:
			self.forcePageFlip = False
			return True
		if self.currentId()==0:
			if not self.ui.editTitle.text():
				print("Kein Title")
				return False
			server = self.ui.editServer.text()
			if not server or not (server.startswith("http://") or server.startswith("https://")):
				print("Invalid Server")
				return False
			if not server.endswith("/"):
				server += "/"
			NetworkService.url = server + "admin"
			NetworkService.request(
				"/user/getAuthMethods", successHandler=self.onAuthMethodsKnown, failureHandler=self.onError)
			self.setDisabled(True)
			return False
		return True

	def nextId(self):
		return self.currentId()+1

	def onAuthMethodsKnown(self, req):
		data = NetworkService.decode(req)
		print(data)
		self.ui.cbAuthSelector.clear()
		seenList = []
		for authMethod, verificationMethod in data:
			if not authMethod in seenList:
				seenList.append(authMethod)
				self.ui.cbAuthSelector.addItem(authMethod)
		self.setDisabled(False)
		self.forcePageFlip = True
		self.next()

	def onError(self, req):
		print("***ERROR***")
		print(req)
		self.setDisabled(False)

class LoginTask(QtCore.QObject):
	loginFailed = QtCore.pyqtSignal((str,))
	loginSucceeded = QtCore.pyqtSignal()
	captchaRequired = QtCore.pyqtSignal((str, str))

	def __init__(self, username, password, captchaToken=None, captcha=None, *args, **kwargs):
		super(LoginTask, self).__init__(*args, **kwargs)
		logger.debug("Starting LoginTask")
		self.username = username
		self.password = password
		self.captcha = captcha
		self.captchaToken = captchaToken
		config.conf.currentUsername = username
		config.conf.currentPassword = password
		self.req = None
		self.webview = None
		self.accountType = None
		self.isLocalServer = False
		self.hostName = urllib.parse.urlparse(NetworkService.url).hostname or NetworkService.url
		self.parentWidget = kwargs["parent"]
		if urllib.parse.urlparse(NetworkService.url).port:  # Assume local Development
			logger.debug("Assuming local development Server")
			self.isLocalServer = True
			NetworkService.request(
				"http://%s:%s/_ah/login" % (self.hostName, urllib.parse.urlparse(NetworkService.url).port),
				successHandler=self.onWarmup, failureHandler=self.onError)
		else:
			self.onWarmup()

	def onWarmup(self, request=None):  # Warmup request has finished
		logger.debug("Checkpoint: onWarmup")
		if self.isLocalServer:
			NetworkService.request("http://%s:%s/admin/user/getAuthMethods" % (
				self.hostName, urllib.parse.urlparse(NetworkService.url).port,),
			                       finishedHandler=self.onAuthMethodKnown)
		else:
			NetworkService.request("https://%s/admin/user/getAuthMethods" % (self.hostName,),
			                       finishedHandler=self.onAuthMethodKnown)

	def onAuthMethodKnown(self, request):
		logger.debug("Checkpoint: onAuthMethodKnown")
		method = request.readAll().data().decode("UTF-8").lower()
		print(method)
		if method == "x-viur-internal":
			logger.debug("LoginTask using method x-viur-internal")
			NetworkService.request("/user/auth_userpassword/login", {"name": self.username, "password": self.password}, secure=True,
			                       successHandler=self.onViurAuth, failureHandler=self.onError)
		else:  # Fallback to google account auth
			logger.debug("LoginTask using method x-google-account")
			if self.isLocalServer:
				NetworkService.request("http://%s:%s/_ah/login?email=%s&admin=True&action=login" % (
					self.hostName, urllib.parse.urlparse(NetworkService.url).port, self.username), None,
				                       finishedHandler=self.onLocalAuth)
			else:
				NetworkService.request("/user/login", secure=True,
				                       successHandler=self.onGoogleAuthLoginUrl, failureHandler=self.onError)

	def onViurAuth(self, request):  # We received an response to our auth request
		logger.debug("Checkpoint: onViurAuth")
		try:
			res = NetworkService.decode(request)
		except:  # Something went wrong
			self.onError(msg="Unable to decode response!")
			return
		if str(res).lower() == "okay":
			securityTokenProvider.reset()  # User-login flushes the session, invalidate all skeys
			self.onLoginSucceeded(request)
		else:
			self.onError(msg='Received response != "okay"!')

	def onLocalAuth(self, request):
		logger.debug("Checkpoint: onLocalAuth")
		NetworkService.request(
			"http://%s:%s/admin/user/auth_googleaccount/login" % (self.hostName, urllib.parse.urlparse(NetworkService.url).port), None,
			successHandler=self.onLoginSucceeded, failureHandler=self.onError)

	def onGoogleAuthLoginUrl(self, request):
		res = bytes(request.readAll().data()).decode("UTF-8")
		logger.debug("Checkpoint: onGoogleAuthSuccess: %r", res)
		res = json.loads(res)
		self.webview = GoogleLoginView(res, parent=self.parentWidget)
		self.webview.exec()
		self.webview = None
		self.onLoginSucceeded(request)
		# authToken = None
		# for line in res.splitlines():
		# 	if line.lower().startswith("auth="):
		# 		authToken = line[5:].strip()
		# logger.debug("LoginTask got AuthToken: %s...", authToken[:6] if authToken else authToken)
		# if not authToken:
		# 	if "CaptchaRequired".lower() in res.lower():
		# 		logger.info("Need captcha")
		# 		captchaToken = None
		# 		captchaURL = None
		# 		for line in res.splitlines():
		# 			if line.lower().startswith("captchatoken"):
		# 				captchaToken = line[13:]
		# 			elif line.lower().startswith("captchaurl"):
		# 				captchaURL = line[11:]
		# 		assert captchaToken and captchaURL
		# 		self.captchaRequired.emit(captchaToken, captchaURL)
		# 		self.deleteLater()
		# 		return
		# 	else:
		# 		self.onError(msg="Found no authToken in response!")
		# 		return
		# # Normalizing the URL we use
		# url = NetworkService.url.lower()
		# if url.endswith("/"):  # Remove tailing /
		# 	url = url[: -1]
		# if not url.endswith("/admin"):
		# 	url = url + "/admin"
		# if not url.startswith("https://"):  # Assert that a secure protocol is specified
		# 	if url.startswith("http://"):
		# 		if not urllib.parse.urlparse(url).port:  # Dosnt look like development Server
		# 			url = "https://" + url[7:]  # Dont use insecure protocol on live server
		# 	else:
		# 		url = "https://" + url
		# argsStr = urllib.parse.urlencode({"continue": "{0}/user/login".format(url), "auth": authToken})
		# NetworkService.request("https://{0}/_ah/login?{1}".format(self.hostName, argsStr),
		#                        successHandler=self.onGAEAuth,
		#                        failureHandler=self.onError)

	def onGAEAuth(self, request=None):
		logger.debug("Checkpoint: onGAEAuth")
		NetworkService.request("/user/login", successHandler=self.onLoginSucceeded, failureHandler=self.onError)

	def onError(self, request=None, error=None, msg=None):
		logger.debug("onerror: %r, %r, %r", request, error, msg)
		self.loginFailed.emit(QtCore.QCoreApplication.translate("Login", msg or str(error)))
		self.deleteLater()

	def onLoginSucceeded(self, req):
		"""
			Try to convince the server to send us its content in our language
		"""
		if "language" in config.conf.adminConfig.keys():
			lang = config.conf.adminConfig["language"]
		else:
			lang = "en"
		logger.debug("Logged in successfully")
		NetworkService.request("/setLanguage/%s" % lang, secure=True, successHandler=self.onLanguageSet,
		                       failureHandler=self.onError)

	def onLanguageSet(self, req):
		"""
			The language has been set, we are done with this task
		"""
		self.loginSucceeded.emit()
		self.deleteLater()


class Login(QtWidgets.QMainWindow):
	def __init__(self, *args, **kwargs):
		QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
		self.ui = Ui_LoginWindow()
		self.ui.setupUi(self)
		self.accman = None  # Reference to our Account-MGR
		self.helpBrowser = None
		self.activeAccount = None
		event.connectWithPriority('resetLoginWindow', self.enableForm, event.lowPriority)
		event.connectWithPriority('accountListChanged', self.loadAccounts, event.lowPriority)
		self.ui.cbPortal.currentRowChanged.connect(self.onCbPortalCurrentRowChanged)
		self.captchaToken = None
		self.loadAccounts()
		self.overlay = Overlay(self)
		shortCut = QtWidgets.QShortcut(self)
		shortCut.setKey("Return")
		shortCut.activated.connect(self.onBtnLoginReleased)
		# Populate the language-selector
		self.langKeys = list(config.conf.availableLanguages.keys())
		self.ui.cbLanguages.blockSignals(True)
		for k in self.langKeys:
			self.ui.cbLanguages.addItem(ISO639CODES[k])
		currentLang = "en"
		if "language" in config.conf.adminConfig.keys():
			currentLang = config.conf.adminConfig["language"]
		if currentLang in self.langKeys:
			self.ui.cbLanguages.setCurrentIndex(self.langKeys.index(currentLang))
		self.ui.actionAbout.triggered.connect(self.onActionAboutTriggered)
		self.ui.actionHelp.triggered.connect(self.onActionHelpTriggered)
		self.ui.actionAccountmanager.triggered.connect(self.onActionAccountmanagerTriggered)
		self.ui.cbLanguages.blockSignals(False)
		self.ui.btnLogin.clicked.connect(self.onBtnLoginReleased)
		self.ui.startAccManagerBTN.released.connect(self.onStartAccManagerBTNReleased)
		self.ui.cbLanguages.currentIndexChanged.connect(self.onCbLanguagesCurrentIndexChanged)

	def changeEvent(self, *args, **kwargs):
		super(Login, self).changeEvent(*args, **kwargs)
		self.ui.retranslateUi(self)

	def loadAccounts(self):
		cb = self.ui.cbPortal
		cb.clear()
		config.conf.loadConfig()
		currentPortalName = config.conf.adminConfig.get("currentPortalName")
		logger.debug("currentPortalName: %r", currentPortalName)
		currentIndex = 0
		for ix, account in enumerate(config.conf.accounts):
			cb.addItem(account["name"])
			if account["name"] == currentPortalName:
				currentIndex = ix
		if len(config.conf.accounts) > 0:
			cb.setCurrentRow(currentIndex)
			self.onCbPortalCurrentRowChanged(currentIndex)
		if self.accman:
			self.accman.deleteLater()
			self.accman = None
		cb.setFocus()

	def onCbPortalCurrentRowChanged(self, index):
		if isinstance(index, str):
			return
		if self.ui.cbPortal.currentIndex() == -1:
			activeaccount = {"name": "", "user": "", "password": "", "url": ""}
		else:
			activeaccount = config.conf.accounts[self.ui.cbPortal.currentIndex().row()]
			config.conf.adminConfig["currentPortalName"] = activeaccount["name"]
			config.conf.saveConfig()
		self.activeAccount = activeaccount

	def onLoginSucceeded(self):
		logger.debug("onLoginSucceeded")
		self.overlay.inform(self.overlay.SUCCESS, QtCore.QCoreApplication.translate("Login", "Login successful"))
		config.conf.loadPortalConfig(NetworkService.url)
		event.emit("loginSucceeded")
		self.hide()

	def statusMessageUpdate(self, type, message):
		self.ui.statusbar.showMessage(message, 5000)

	def onEditPasswordReturnPressed(self):
		self.onBtnLoginReleased()

	def onBtnLoginReleased(self):
		logger.debug("onBtnLoginReleased")
		url = self.ui.editUrl.displayText()
		username = self.ui.editUsername.text()
		password = self.ui.editPassword.text()
		cb = self.ui.cbPortal
		if (cb.currentIndex() == -1):
			reply = QtWidgets.QMessageBox.question(
				self,
				QtCore.QCoreApplication.translate("Login", "Save this account"),
				QtCore.QCoreApplication.translate("Login", "Save this account permanently?"),
				QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
			if reply == QtWidgets.QMessageBox.Yes:
				pw = password
				accname, okaypressed = QtWidgets.QInputDialog.getText(
					self,
					QtCore.QCoreApplication.translate("Login", "Save this account"),
					QtCore.QCoreApplication.translate("Login", "Enter a name for this account"))
				if okaypressed:
					reply = QtWidgets.QMessageBox.question(
						self,
						QtCore.QCoreApplication.translate("Login", "Save this account"),
						QtCore.QCoreApplication.translate("Login", "Save the password, too?"),
						QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
						QtWidgets.QMessageBox.No)
					if reply == QtWidgets.QMessageBox.No:
						pw = ""
					saveacc = {
						"name": accname,
						"user": username,
						"password": pw,
						"url": url
					}
					config.conf.accounts.append(saveacc)
		elif cb.currentIndex() != 0:  # Move this account to the beginning, so it will be selected on the next start
			# of admin
			account = config.conf.accounts[cb.currentIndex().row()]
			config.conf.accounts.remove(account)
			config.conf.accounts.insert(0, account)
		NetworkService.setup(url)
		if self.captchaToken:
			captcha = self.ui.editCaptcha.text()
		else:
			captcha = None
		self.overlay.inform(self.overlay.BUSY, QtCore.QCoreApplication.translate("Login", "Login in progress"))
		if self.accman:
			self.accman.deleteLater()
			self.accman = None
		if self.helpBrowser:
			self.helpBrowser.deleteLater()
			self.helpBrowser = None
		self.login(username, password, captcha)

	def onStartAccManagerBTNReleased(self):
		if self.accman:
			self.accman.deleteLater()
			self.accman = None
		self.accman = Accountmanager()
		self.accman.show()

	def onActionAccountmanagerTriggered(self):
		self.onStartAccManagerBTNReleased()

	def onActionAboutTriggered(self, checked=None):
		if checked is None:
			return
		showAbout(self)

	def onActionHelpTriggered(self):
		QtGui.QDesktopServices.openUrl(QtCore.QUrl("http://www.viur.is/site/Admin-Dokumentation"))

	def setCaptcha(self, token, url):
		self.captchaToken = token
		self.captchaReq = NetworkService.request(
			"https://www.google.com/accounts/{0}".format(url),
			finishedHandler=self.onCaptchaAvailable)

	def onCaptchaAvailable(self):
		pixmap = QtGui.QPixmap()
		data = bytes(self.captchaReq.readAll())
		pixmap.loadFromData(data)
		self.ui.lblCaptcha.setPixmap(pixmap)
		self.ui.editCaptcha.show()
		self.ui.editCaptcha.setText("")
		self.overlay.inform(self.overlay.ERROR, QtCore.QCoreApplication.translate("Login", "Captcha required"))
		self.captchaReq.deleteLater()
		self.captchaReq = None

	def login(self, username, password, captcha=None):
		"""
		Then:
		Download Modulconfiguration from Server and set things up.
		Calls L{resetLoginWindow} on failure, L{applyConfig} otherwise
		"""
		self.overlay.inform(self.overlay.BUSY)
		if captcha:
			loginTask = LoginTask(username, password, self.captchaToken, captcha, parent=self)
		else:
			loginTask = LoginTask(username, password, parent=self)
		loginTask.loginSucceeded.connect(self.onLoginSucceeded)
		loginTask.captchaRequired.connect(self.setCaptcha)
		loginTask.loginFailed.connect(self.onLoginFailed)

	# self.connect( self.loginTask, QtCore.SIGNAL("reqCaptcha(PyQt_PyObject,PyQt_PyObject)"), self.setCaptcha )

	# self.connect( self.loginTask, QtCore.SIGNAL("loginFailed(PyQt_PyObject)"), self.enableForm )

	def onLoginFailed(self, msg):
		self.overlay.inform(self.overlay.ERROR, msg)

	def enableForm(self, msg=None):
		if msg:
			self.overlay.inform(self.overlay.ERROR, msg)
		else:
			self.overlay.clear()
		self.show()

	def onCbLanguagesCurrentIndexChanged(self, index):
		if not isinstance(index, int):
			return
		for v in config.conf.availableLanguages.values():  # Fixme: Removes all (even unloaded) translations
			QtCore.QCoreApplication.removeTranslator(v)
		newLanguage = self.langKeys[index]
		QtCore.QCoreApplication.installTranslator(config.conf.availableLanguages[newLanguage])
		config.conf.adminConfig["language"] = newLanguage

	def onEditUsernameTextChanged(self, txt):
		"""
			Check if the Username given is a valid email-address, and warn
			the user if it isnt
		"""
		regex = re.compile("[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}")
		res = regex.findall(txt.lower())
		palette = self.ui.editUsername.palette()
		if len(res) == 1:
			palette.setColor(palette.Active, palette.Text, QtGui.QColor(0, 0, 0))
			self.ui.editUsername.setToolTip(
				QtCore.QCoreApplication.translate("Login", "This Email address looks valid"))
		else:
			palette.setColor(palette.Active, palette.Text, QtGui.QColor(255, 0, 0))
			self.ui.editUsername.setToolTip(QtCore.QCoreApplication.translate("Login", "This Email address is invalid"))
		self.ui.editUsername.setPalette(palette)
