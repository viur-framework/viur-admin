import urllib.parse

from viur_admin.log import getLogger

logger = getLogger(__name__)

import json
import re

from PyQt5 import QtCore, QtWidgets, QtGui, QtWebKitWidgets, QtWebKit, QtNetwork

from viur_admin.ui.loginformUI import Ui_LoginWindow
from viur_admin.ui.authuserpasswordUI import Ui_AuthUserPassword
from viur_admin.accountmanager import Accountmanager
from viur_admin.network import NetworkService, securityTokenProvider, nam
from viur_admin.event import event
from viur_admin import config
from viur_admin.utils import Overlay, showAbout
from viur_admin.locales import ISO639CODES


class AuthGoogle(QtWidgets.QWidget):
	loginFailed = QtCore.pyqtSignal((str,))
	loginSucceeded = QtCore.pyqtSignal()
	secondFactorRequired = QtCore.pyqtSignal((str,))
	advancesAutomatically = True  # No need to click the next-button; we'll detect changes inside the browser ourself

	def __init__(self, currentPortalConfig, parent=None):
		super(AuthGoogle, self).__init__(parent)
		self.currentPortalConfig = currentPortalConfig
		# self.jar = QtNetwork.QNetworkCookieJar()
		self.webView = QtWebKitWidgets.QWebView()
		self.setLayout(QtWidgets.QVBoxLayout())
		self.layout().addWidget(self.webView)
		self.webView.settings().setAttribute(QtWebKit.QWebSettings.JavascriptEnabled, True)
		self.webView.settings().setAttribute(QtWebKit.QWebSettings.JavascriptCanOpenWindows, True)
		self.webView.page().setNetworkAccessManager(nam)
		self.webView.setUrl(QtCore.QUrl(currentPortalConfig["server"]+"/admin/user/auth_googleaccount/login"))
		self.webView.urlChanged.connect(self.onUrlChanged)
		self.webView.loadFinished.connect(self.onLoadFinished)


	def startAuthenticating(self):
		logger.debug("LoginTask using method x-google")
		self.show()
		#username = self.currentPortalConfig["username"]
		#password = self.currentPortalConfig["password"] or self.ui.editPassword.text()

	def onUrlChanged(self, url):
		logger.debug("urlChanged: %r", url)
		if self.webView.findText("OKAY"):
			# logger.debug("cookies: %r", self.webView.page().networkAccessManager().cookieJar().allCookies())
			#self.close()
			#self.deleteLater()
			self.loginSucceeded.emit()
		elif self.webView.findText("ONE-TIME-PASSWORD"):
			print(self.webView.page().mainFrame().toHtml())
			self.secondFactorRequired.emit(self.webView.page().mainFrame().toHtml())

	def onLoadFinished(self, status):
		logger.debug("loadFinished: %r", status)
		if self.webView.findText("OKAY"):
			# logger.debug("cookies: %r", self.webView.page().networkAccessManager().cookieJar().allCookies())
			#self.close()
			#self.deleteLater()
			self.loginSucceeded.emit()
		elif self.webView.findText("ONE-TIME-PASSWORD"):
			print(self.webView.page().mainFrame().toHtml())
			self.secondFactorRequired.emit(self.webView.page().mainFrame().toHtml())

	def onError(self, request=None, error=None, msg=None):
		logger.debug("onerror: %r, %r, %r", request, error, msg)
		self.loginFailed.emit(QtCore.QCoreApplication.translate("Login", msg or str(error)))

	def getUpdatedPortalConfig(self):
		# We cant store anything for now
		return {}

class AuthUserPassword(QtWidgets.QWidget):
	loginFailed = QtCore.pyqtSignal((str,))
	loginSucceeded = QtCore.pyqtSignal()
	secondFactorRequired = QtCore.pyqtSignal((str,))
	advancesAutomatically = False

	def __init__(self, currentPortalConfig, *args, **kwargs):
		super(AuthUserPassword, self).__init__(*args, **kwargs)
		self.ui = Ui_AuthUserPassword()
		self.ui.setupUi(self)
		self.currentPortalConfig = currentPortalConfig

		#config.conf.currentUsername = username
		#config.conf.currentPassword = password

	def getUpdatedPortalConfig(self):
		self.currentPortalConfig["username"] = self.ui.editUsername.text()
		if self.ui.cbSavePassword.checkState():
			self.currentPortalConfig["password"] = self.ui.editPassword.text()
		else:
			self.currentPortalConfig["password"] = ""
		return self.currentPortalConfig

	def startAuthenticating(self):
		logger.debug("LoginTask using method x-viur-internal")
		username = self.currentPortalConfig["username"]
		password = self.currentPortalConfig["password"] or self.ui.editPassword.text()
		NetworkService.request("/user/auth_userpassword/login", {"name": username, "password": password}, secure=True,
		                       successHandler=self.onViurAuth, failureHandler=self.onError)

	def onViurAuth(self, request):  # We received an response to our auth request
		logger.debug("Checkpoint: onViurAuth")
		try:
			res = NetworkService.decode(request)
		except:  # Something went wrong
			print("onViurAuth: Except")
			self.onError(msg="Unable to decode response!")
			return
		if str(res).lower() == "okay":
			print("onViurAuth: okay")
			securityTokenProvider.reset()  # User-login flushes the session, invalidate all skeys
			self.loginSucceeded.emit()
		elif str(res).lower() == "one-time-password":
			self.secondFactorRequired.emit(res)
		else:
			print("onViurAuth: else")
			print(res)
			self.onError(msg='Received response != "okay"!')

	def onError(self, request=None, error=None, msg=None):
		logger.debug("onerror: %r, %r, %r", request, error, msg)
		self.loginFailed.emit(QtCore.QCoreApplication.translate("Login", msg or str(error)))


class VerifyOtp(QtWidgets.QWidget):
	loginFailed = QtCore.pyqtSignal((str,))
	loginSucceeded = QtCore.pyqtSignal()


	def __init__(self, currentPortalConfig, *args, **kwargs):
		super(VerifyOtp, self).__init__(*args, **kwargs)
		self.currentPortalConfig = currentPortalConfig

	def startAuthenticating(self):
		logger.debug("VerifyOtp start")#
		self.startRun()


	def startRun(self):
		token, isOkay = QtWidgets.QInputDialog.getText(self, "Insert Token", "Token")
		if not isOkay:
			self.loginFailed.emit("Aborted")
			return
		NetworkService.request("/user/f2_otp2factor/otp", {"otptoken": token}, secure=True,
		                       successHandler=self.onViurAuth, failureHandler=self.onError)

	def onViurAuth(self, req):
		res = NetworkService.decode(req)
		if isinstance(res, dict) and "action" in res.keys() and res["action"]=="edit":
			msg = QtWidgets.QMessageBox.warning(self, "Invalid token", "Your token did not verify. Please try again")
			self.startRun()
		elif isinstance(res, str) and res.lower()=="okay":
			self.loginSucceeded.emit()
		print("VerifyOtp.onViurAuth", res)

	def onError(self, req):
		res = NetworkService.decode(req)
		print("VerifyOtp.onError", res)




class LoginTask(QtCore.QObject):
	loginFailed = QtCore.pyqtSignal((str,))
	loginSucceeded = QtCore.pyqtSignal()
	captchaRequired = QtCore.pyqtSignal((str, str))

	authenticationProvider = {
		"X-VIUR-AUTH-User-Password": AuthUserPassword,
		"X-VIUR-AUTH-Google-Account": AuthGoogle
	}

	verificationProvider = {
		"X-VIUR-2Factor-Otp": VerifyOtp
	}

	def __init__(self, currentPortalConfig, *args, **kwargs):
		super(LoginTask, self).__init__(*args, **kwargs)
		logger.debug("Starting LoginTask")
		self.currentPortalConfig = currentPortalConfig
		assert currentPortalConfig["authMethod"] in self.authenticationProvider.keys(), "Unknown authentication method"
		self.authProvider = self.authenticationProvider[currentPortalConfig["authMethod"]](currentPortalConfig)
		self.authProvider.loginSucceeded.connect(self.onLoginSucceeded)
		self.authProvider.loginFailed.connect(self.onLoginFailed)
		self.authProvider.secondFactorRequired.connect(self.onSecondFactorRequired)
		self.verificationProviderInstance = None

	def startAuthenticationFlow(self):
		self.authProvider.startAuthenticating()


	def startSetup(self):
		return self.authProvider

	def getUpdatedPortalConfig(self):
		self.currentPortalConfig.update(self.authProvider.getUpdatedPortalConfig())
		return self.currentPortalConfig

	def onLoginSucceeded(self, *args, **kwargs):
		print("LoginTask: Login OKAY")
		self.loginSucceeded.emit()

	def onSecondFactorRequired(self, factor):
		if factor.lower()=="one-time-password":
			factor = "otp"
		self.verificationProviderInstance = self.verificationProvider["X-VIUR-2Factor-Otp"](self.currentPortalConfig)
		self.verificationProviderInstance.loginSucceeded.connect(self.onLoginSucceeded)
		self.verificationProviderInstance.loginFailed.connect(self.onLoginFailed)
		self.verificationProviderInstance.startAuthenticating()

	def onLoginFailed(self, msg, *args, **kwargs):
		print("LoginTask.onLoginFailed", msg)
		self.loginFailed.emit(msg)




class Login(QtWidgets.QMainWindow):
	def __init__(self, *args, **kwargs):
		QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
		self.ui = Ui_LoginWindow()
		self.ui.setupUi(self)
		self.accman = None  # Reference to our Account-MGR
		self.helpBrowser = None
		self.activeAccount = None
		self.loginTask = None
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
		if self.loginTask:
			self.loginTask.deleteLater()
		cb = self.ui.cbPortal
		currentPortalCfg = config.conf.accounts[cb.currentIndex().row()]
		print(currentPortalCfg)
		NetworkService.setup(currentPortalCfg["server"]+"admin")
		if cb.currentIndex().row() != 0:
			# Move this account to the beginning, so it will be selected on the next start
			# of admin
			account = config.conf.accounts[cb.currentIndex().row()]
			config.conf.accounts.remove(account)
			config.conf.accounts.insert(0, account)
		self.loginTask = LoginTask(currentPortalCfg)
		self.loginTask.loginSucceeded.connect(self.onLoginSucceeded)
		self.loginTask.loginFailed.connect(self.onLoginFailed)
		self.overlay.inform(self.overlay.BUSY, QtCore.QCoreApplication.translate("Login", "Login in progress"))
		if self.accman:
			self.accman.deleteLater()
			self.accman = None
		if self.helpBrowser:
			self.helpBrowser.deleteLater()
			self.helpBrowser = None
		self.loginTask.startAuthenticationFlow()


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
