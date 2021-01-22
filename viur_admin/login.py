from typing import Any, Dict, Callable

from viur_admin.log import getLogger

logger = getLogger(__name__)
from viur_admin.pyodidehelper import isPyodide
if isPyodide:
	from PyQt5 import QtCore, QtWidgets, QtGui
	QtWebEngineWidgets = None
else:
	from PyQt5 import QtCore, QtWidgets, QtGui, QtWebEngineWidgets

from viur_admin.ui.loginformUI import Ui_LoginWindow
from viur_admin.ui.simpleloginUI import Ui_simpleLogin
from viur_admin.ui.authuserpasswordUI import Ui_AuthUserPassword
from viur_admin.accountmanager import AccountManager
from viur_admin.network import NetworkService, securityTokenProvider, nam, MyCookieJar, RequestWrapper
from viur_admin.event import event
from viur_admin import config
from viur_admin.utils import Overlay, showAbout
from viur_admin.locales import ISO639CODES
from datetime import datetime


class AuthProviderBase(QtWidgets.QWidget):
	def __init__(
			self,
			currentPortalConfig: Dict[str, Any],
			*,
			isWizard: bool = False,
			parent: QtCore.QObject = None):
		super(AuthProviderBase, self).__init__(parent=parent)
		self.currentPortalConfig = currentPortalConfig
		self.isWizard = isWizard

	def startAuthenticating(self) -> None:
		raise NotImplementedError()

	def getUpdatedPortalConfig(self) -> Dict[str, Any]:
		raise NotImplementedError()


class AuthGoogle(AuthProviderBase):
	loginFailed = QtCore.pyqtSignal((str,))
	loginSucceeded = QtCore.pyqtSignal()
	secondFactorRequired = QtCore.pyqtSignal((str,))
	advancesAutomatically = True  # No need to click the next-button; we'll detect changes inside the browser ourself

	def __init__(
			self,
			currentPortalConfig: Dict[str, Any],
			*,
			isWizard: bool = False,
			parent: QtCore.QObject = None):
		super(AuthGoogle, self).__init__(
			currentPortalConfig=currentPortalConfig,
			isWizard=isWizard,
			parent=parent)
		self.didSucceed = False
		self.webView = QtWebEngineWidgets.QWebEngineView()
		self.setLayout(QtWidgets.QVBoxLayout())
		self.layout().addWidget(self.webView)
		self.chromeCookieJar = self.webView.page().profile().cookieStore()
		self.chromeCookieJar.cookieAdded.connect(self.onCookieAdded)
		self.chromeCookieJar.loadAllCookies()
		for cookie in nam.cookieJar().allCookies():
			self.chromeCookieJar.setCookie(cookie)
		self.webView.setUrl(QtCore.QUrl(currentPortalConfig["server"] + "admin/user/auth_googleaccount/login"))
		self.webView.urlChanged.connect(self.onUrlChanged)
		self.webView.loadFinished.connect(self.onLoadFinished)

	def onCookieAdded(self, cookie: Any) -> None:
		# logger.debug("onCookieAdded: %r", cookie)
		nam.cookieJar().insertCookie(cookie)

	def startAuthenticating(self) -> None:
		logger.debug("LoginTask using method x-google")
		if not self.isWizard:
			self.show()

	# username = self.currentPortalConfig["username"]
	# password = self.currentPortalConfig["password"] or self.ui.editPassword.text()

	def onUrlChanged(self, url: str) -> None:
		logger.debug("urlChanged: %r", url)
		self.checkAuthenticationStatus()

	def onLoadFinished(self, status: Any) -> None:
		logger.debug("loadFinished: %r", status)
		self.checkAuthenticationStatus()

	def authStatusCallback(self, data: str) -> None:
		logger.debug("authStatusCallback: %r", data)
		okayFound = data.find("OKAY")
		logger.debug("checkAuthenticationStatus: %r", okayFound)
		if okayFound != -1:
			if not self.isWizard:
				self.close()
			self.loginSucceeded.emit()
		elif data.find("X-VIUR-2FACTOR-") != -1:
			html = self.webView.page().mainFrame().toHtml()
			startPos = html.find("X-VIUR-2FACTOR-")
			secondFactorType = html[startPos, html.find("\"", startPos + 1)]
			secondFactorType = secondFactorType.replace("X-VIUR-2FACTOR-", "")
			if not self.isWizard:
				self.close()
			self.secondFactorRequired.emit(secondFactorType)

	def checkAuthenticationStatus(self) -> None:
		page = self.webView.page()
		page.toPlainText(self.authStatusCallback)

	def onError(
			self,
			request: RequestWrapper = None,
			error: Callable = None,
			msg: str = None) -> None:
		logger.debug("onerror: %r, %r, %r", request, error, msg)
		self.loginFailed.emit(QtCore.QCoreApplication.translate("Login", msg or str(error)))

	def getUpdatedPortalConfig(self) -> Dict[str, Any]:
		# We cant store anything for now
		return dict()

	def closeEvent(self, event: Any) -> None:
		if not self.didSucceed:
			self.loginFailed.emit(QtCore.QCoreApplication.translate("Login", "Aborted"))


class AuthUserPassword(AuthProviderBase):
	loginFailed = QtCore.pyqtSignal((str,))
	loginSucceeded = QtCore.pyqtSignal()
	secondFactorRequired = QtCore.pyqtSignal((str,))
	advancesAutomatically = False

	def __init__(
			self,
			currentPortalConfig: Dict[str, Any],
			*,
			isWizard: bool = False,
			parent: QtCore.QObject = None):
		super(AuthUserPassword, self).__init__(
			currentPortalConfig=currentPortalConfig,
			isWizard=isWizard,
			parent=parent)
		self.ui = Ui_AuthUserPassword()
		self.ui.setupUi(self)
		self.ui.editUsername.setText(currentPortalConfig.get("username", ""))
		password = currentPortalConfig.get("password", "")
		self.ui.editPassword.setText(password)
		self.ui.cbSavePassword.setChecked(bool(password))

	def getUpdatedPortalConfig(self) -> Dict[str, Any]:
		self.currentPortalConfig["username"] = self.ui.editUsername.text().strip("\n").strip()
		if self.ui.cbSavePassword.checkState():
			self.currentPortalConfig["password"] = self.ui.editPassword.text().strip("\n").strip()
		else:
			self.currentPortalConfig["password"] = ""
		return self.currentPortalConfig

	def startAuthenticating(self) -> None:
		logger.debug("LoginTask using method x-viur-internal")
		username = self.currentPortalConfig["username"]
		password = self.currentPortalConfig["password"] or self.ui.editPassword.text()
		if not password:
			if isPyodide:  # No not issue getText (Its a blocking operation)
				self.loginFailed.emit("Aborted")
				return
			password, isOkay = QtWidgets.QInputDialog.getText(self, "Password", "Password")
			if not isOkay:
				self.loginFailed.emit("Aborted")
				return
		NetworkService.request("/user/auth_userpassword/login", {"name": username, "password": password}, secure=True,
		                       successHandler=self.onViurAuth, failureHandler=self.onError)

	def onViurAuth(self, request: RequestWrapper) -> None:  # We received an response to our auth request
		logger.debug("Checkpoint: onViurAuth")
		staticSkey = None
		for headerNameByteArray, headerValueByteArray in request.request.rawHeaderPairs():
			headerName = headerNameByteArray.data().decode("LATIN-1").lower()
			if headerName == "sec-x-viur-staticskey":
				staticSkey = headerValueByteArray.data().decode("LATIN-1")
				break
		try:
			res = NetworkService.decode(request)
		except Exception as err:  # Something went wrong
			logger.error("onViurAuth: Except")
			self.onError(msg="Unable to decode response!")
			return
		logger.debug("onViurAuth: %r", res)
		if str(res).lower() == "okay":
			print("onViurAuth: okay")
			if staticSkey:  # Pass the static skey to the securityTokenProvider so it can skip fetching new skeys
				securityTokenProvider.staticSecurityKey = staticSkey
			self.loginSucceeded.emit()
		elif str(res).startswith("X-VIUR-2FACTOR-"):
			secondFactor = str(res).replace("X-VIUR-2FACTOR-", "")
			self.secondFactorRequired.emit(secondFactor)
		else:
			logger.debug("onViurAuth: else: %r", res)
			self.onError(msg='Received response != "okay"!')

	def onError(self, request: RequestWrapper = None, error: Any = None, msg: Any = None) -> None:
		logger.debug("onerror: %r, %r, %r", request, error, msg)
		self.loginFailed.emit(QtCore.QCoreApplication.translate("Login", msg or str(error)))


class VerifyTimeBasedOTP(QtWidgets.QWidget):
	loginFailed = QtCore.pyqtSignal((str,))
	loginSucceeded = QtCore.pyqtSignal()

	def __init__(
			self,
			currentPortalConfig: Dict[str, Any],
			isWizard: bool = False,
			*args: Any,
			**kwargs: Any):
		super(VerifyTimeBasedOTP, self).__init__(*args, **kwargs)
		self.currentPortalConfig = currentPortalConfig

	def startAuthenticating(self) -> None:
		logger.debug("VerifyOtp start")  #
		self.startRun()

	def startRun(self) -> None:
		token, isOkay = QtWidgets.QInputDialog.getText(self, "Insert Token", "Token")
		if not isOkay:
			self.loginFailed.emit("Aborted")
			return
		NetworkService.request("/user/f2_timebasedotp/otp", {"otptoken": token}, secure=True,
		                       successHandler=self.onViurAuth, failureHandler=self.onError)

	def onViurAuth(self, req: RequestWrapper) -> None:
		res = NetworkService.decode(req)
		if isinstance(res, dict) and "action" in res and res["action"] == "edit":
			msg = QtWidgets.QMessageBox.warning(self, "Invalid token", "Your token did not verify. Please try again")
			self.startRun()
		elif isinstance(res, str) and res.lower() == "okay":
			self.loginSucceeded.emit()
		logger.debug("VerifyOtp.onViurAuth: %r", res)

	def onError(self, req: RequestWrapper) -> None:
		res = NetworkService.decode(req)
		logger.debug("VerifyOtp.onError: %r", res)


class LoginTask(QtCore.QObject):
	loginFailed = QtCore.pyqtSignal((str,))
	loginSucceeded = QtCore.pyqtSignal()
	captchaRequired = QtCore.pyqtSignal((str, str))

	authenticationProvider = {
		"X-VIUR-AUTH-User-Password": AuthUserPassword,
		"X-VIUR-AUTH-Google-Account": AuthGoogle
	}

	verificationProvider = {
		"TimeBasedOTP": VerifyTimeBasedOTP
	}

	def __init__(
			self,
			currentPortalConfig: Dict[str, Any],
			isWizard: bool = False,
			*args: Any,
			**kwargs: Any):
		super(LoginTask, self).__init__(*args, **kwargs)
		logger.debug("Starting LoginTask")
		self.currentPortalConfig = currentPortalConfig
		self.isWizard = isWizard
		assert currentPortalConfig["authMethod"] in self.authenticationProvider, "Unknown authentication method"
		self.authProvider = self.authenticationProvider[currentPortalConfig["authMethod"]](
			currentPortalConfig,
			isWizard=isWizard,
			parent=self.parent()
		)
		self.authProvider.loginSucceeded.connect(self.onLoginSucceeded)
		self.authProvider.loginFailed.connect(self.onLoginFailed)
		self.authProvider.secondFactorRequired.connect(self.onSecondFactorRequired)
		self.verificationProviderInstance = None

	def startAuthenticationFlow(self) -> None:
		self.authProvider.startAuthenticating()

	def startSetup(self) -> Any:
		return self.authProvider

	def getUpdatedPortalConfig(self) -> Any:
		self.currentPortalConfig.update(self.authProvider.getUpdatedPortalConfig())
		return self.currentPortalConfig

	def onLoginSucceeded(
			self,
			*args: Any,
			**kwargs: Any) -> None:
		logger.debug("LoginTask: Login OKAY")
		self.loginSucceeded.emit()

	def onSecondFactorRequired(self, factor: str) -> None:
		self.verificationProviderInstance = self.verificationProvider[factor](self.currentPortalConfig)
		self.verificationProviderInstance.loginSucceeded.connect(self.onLoginSucceeded)
		self.verificationProviderInstance.loginFailed.connect(self.onLoginFailed)
		self.verificationProviderInstance.startAuthenticating()

	def onLoginFailed(
			self,
			msg: str,
			*args: Any,
			**kwargs: Any) -> None:
		logger.debug("LoginTask.onLoginFailed: %r", msg)
		self.loginFailed.emit(msg)


class Login(QtWidgets.QMainWindow):
	def __init__(
			self,
			*args: Any,
			**kwargs: Any):
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
		self.langKeys = list(config.conf.availableLanguages)
		self.ui.cbLanguages.blockSignals(True)
		for k in self.langKeys:
			self.ui.cbLanguages.addItem(ISO639CODES[k])
		currentLang = "en"
		if "language" in config.conf.adminConfig:
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

	def changeEvent(
			self,
			*args: Any,
			**kwargs: Any) -> None:
		super(Login, self).changeEvent(*args, **kwargs)
		self.ui.retranslateUi(self)

	def loadAccounts(self) -> None:
		cb = self.ui.cbPortal
		cb.clear()
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

	def onCbPortalCurrentRowChanged(self, index: Any) -> None:
		if isinstance(index, str):
			return
		if self.ui.cbPortal.currentIndex() == -1:
			activeaccount = {"name": "", "user": "", "password": "", "server": ""}
		else:
			activeaccount = config.conf.accounts[self.ui.cbPortal.currentIndex().row()]
			config.conf.adminConfig["currentPortalName"] = activeaccount["name"]
			config.conf.saveConfig()
		self.activeAccount = activeaccount

	def onLoginSucceeded(self) -> None:
		logger.debug("onLoginSucceeded")
		self.overlay.inform(self.overlay.SUCCESS, QtCore.QCoreApplication.translate("Login", "Login successful"))
		# config.conf.loadPortalConfig(NetworkService.url, withCookies=False)
		event.emit("loginSucceeded")
		self.hide()

	def statusMessageUpdate(self, type: str, message: str) -> None:
		self.ui.statusbar.showMessage(message, 5000)

	def onEditPasswordReturnPressed(self) -> None:
		self.onBtnLoginReleased()

	def onBtnLoginReleased(self) -> None:
		if self.loginTask:
			self.loginTask.deleteLater()
		cb = self.ui.cbPortal
		currentPortalCfg = config.conf.accounts[cb.currentIndex().row()]
		NetworkService.setup(currentPortalCfg["server"] + "admin")

		if cb.currentIndex().row() != 0:
			# Move this account to the beginning, so it will be selected on the next start
			# of admin
			account = config.conf.accounts[cb.currentIndex().row()]
			config.conf.accounts.remove(account)
			config.conf.accounts.insert(0, account)
		self.loginTask = LoginTask(currentPortalCfg, parent=self)
		self.loginTask.loginSucceeded.connect(self.onLoginSucceeded)
		self.loginTask.loginFailed.connect(self.onLoginFailed)
		self.overlay.inform(self.overlay.BUSY, QtCore.QCoreApplication.translate("Login", "Login in progress"))
		if self.accman:
			self.accman.deleteLater()
			self.accman = None
		if self.helpBrowser:
			self.helpBrowser.deleteLater()
			self.helpBrowser = None
		config.conf.loadPortalConfig(NetworkService.url)
		# now we're going to test if we're still logged in via restored and valid cookies
		# or have to start the login task
		NetworkService.request(
			"/user/view/self",
			secure=True,
			failSilent=True,
			successHandler=self.onNotLoggedInYet,  #self.onSkipAuth, FIXME!
			failureHandler=self.onNotLoggedInYet
		)

	def onCheckSuccessAuth(self, request: RequestWrapper) -> None:
		"""Login credentials aka cookies are still valid, so we can progress with admin startup

		:param req:
		:return:
		"""
		try:
			currentUserEntry = NetworkService.decode(request)["values"]
			logger.debug("MainWindow.onLoadUser: %r", currentUserEntry)
		except Exception as err:
			return self.onNotLoggedInYet(request)
		else:
			logger.debug("onCheckSuccessAuth success: %r", request)
			self.loginTask.loginSucceeded.emit()

	def onNotLoggedInYet(self, req: RequestWrapper) -> None:
		"""Login credentials aka cookies are neither present nor valid anymore, so cleanup the cookiejar of our networking subsystem
		and proceed with login

		:param req:
		:return:
		"""
		logger.debug("onNotLoggedInYet: %r", req)
		nam.setCookieJar(MyCookieJar())
		self.loginTask.startAuthenticationFlow()

	def onStartAccManagerBTNReleased(self) -> None:
		if self.accman:
			self.accman.deleteLater()
			self.accman = None
		self.accman = AccountManager()
		self.accman.show()

	def onActionAccountmanagerTriggered(self) -> None:
		self.onStartAccManagerBTNReleased()

	def onActionAboutTriggered(self, checked: bool = None) -> None:
		if checked is None:
			return
		showAbout(self)

	def onActionHelpTriggered(self) -> None:
		QtGui.QDesktopServices.openUrl(QtCore.QUrl("http://www.viur.is/site/Admin-Dokumentation"))

	def login(
			self,
			username: str,
			password: str,
			captcha: Any = None) -> None:
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

	def onLoginFailed(self, msg: str) -> None:
		self.overlay.inform(self.overlay.ERROR, msg)
		self.loadAccounts()

	def enableForm(self, msg: str = None) -> None:
		if msg:
			self.overlay.inform(self.overlay.ERROR, msg)
		else:
			self.overlay.clear()
		self.show()

	def onCbLanguagesCurrentIndexChanged(self, index: Any) -> None:
		if not isinstance(index, int):
			return
		for v in config.conf.availableLanguages.values():  # Fixme: Removes all (even unloaded) translations
			QtCore.QCoreApplication.removeTranslator(v)
		newLanguage = self.langKeys[index]
		QtCore.QCoreApplication.installTranslator(config.conf.availableLanguages[newLanguage])
		config.conf.adminConfig["language"] = newLanguage

class SimpleLogin(QtWidgets.QMainWindow):
	def __init__(
			self,
			*args: Any,
			**kwargs: Any):
		QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
		self.ui = Ui_simpleLogin()
		self.ui.setupUi(self)
		self.ui.loginBtn.clicked.connect(self.onBtnLoginReleased)
		self.setDisabled(True)
		self.ui.statusLbl.setText("Please login")
		self.loginTask = None
		NetworkService.request("/user/view/self", successHandler=self.onHasSession, failureHandler=self.onNoSession, failSilent=True)

	def onHasSession(self, req):
		data = NetworkService.decode(req)
		if data["values"] and data["values"]["access"] and "root" in data["values"]["access"]:
			event.emit("loginSucceeded")
			self.hide()
		else:
			try:
				userName = data["values"]["name"]
			except:
				userName = "unkown user"
			self.requestLogoutBox = QtWidgets.QMessageBox(
				QtWidgets.QMessageBox.Question,
				QtCore.QCoreApplication.translate("SimpleLogin", "Logout?"),
				QtCore.QCoreApplication.translate("SimpleLogin", "This user (%s) cannot be used with ViUR Admin. Do you want to log out?") % userName,
				(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No),
				self
			)
			self.requestLogoutBox.buttonClicked.connect(self.reqLogoutCallback)
			self.requestLogoutBox.open()
			QtGui.QGuiApplication.processEvents()
			self.requestLogoutBox.adjustSize()


	def reqLogoutCallback(self, clickedBtn):
		if clickedBtn == self.requestLogoutBox.button(self.requestLogoutBox.Yes):
			NetworkService.request("/user/logout", secure=True, successHandler=self.onNoSession)
		else:
			self.ui.statusLbl.setText("The current user has no access to ViUR Admin - please reload page")
		self.requestLogoutBox = None

	def onNoSession(self, *args, **kwargs):
		self.setDisabled(False)

	def onBtnLoginReleased(self):
		self.setDisabled(True)
		self.loginTask = LoginTask({
			"authMethod": "X-VIUR-AUTH-User-Password",
			"username": self.ui.usernameEdit.text(),
			"password": self.ui.passwordEdit.text(),
		})
		self.loginTask.loginFailed.connect(self.onLoginFailed)
		self.loginTask.loginSucceeded.connect(self.onLoginSucceeded)
		self.loginTask.startAuthenticationFlow()

	def onLoginFailed(self, reason):
		self.ui.statusLbl.setText("%s Login failed: %s" % (datetime.now().strftime("%H:%M:%S") ,reason))
		self.setDisabled(False)

	def onLoginSucceeded(self, *args, **kwargs):
		logger.debug("onLoginSucceeded")
		NetworkService.request("/user/view/self", successHandler=self.onHasSession, failureHandler=self.onNoSession,
						   failSilent=True)

