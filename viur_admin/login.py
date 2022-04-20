from typing import Any, Dict, Callable

from viur_admin.log import getLogger

logger = getLogger(__name__)
from viur_admin.pyodidehelper import isPyodide
if isPyodide:
	from PyQt5 import QtCore, QtWidgets, QtGui
	QtWebEngineWidgets = None
else:
	from PyQt5 import QtCore, QtWidgets, QtGui, QtWebEngineWidgets, QtNetwork
	import webbrowser
	import http.server
	import socketserver
from viur_admin.ui.loginformUI import Ui_LoginWindow
from viur_admin.ui.simpleloginUI import Ui_simpleLogin
from viur_admin.ui.authuserpasswordUI import Ui_AuthUserPassword
from viur_admin.accountmanager import AccountItem, AddPortalWizard
from viur_admin.network import NetworkService, securityTokenProvider, nam, MyCookieJar, RequestWrapper
from viur_admin.event import event
from viur_admin import config
from viur_admin.utils import Overlay, showAbout, loadIcon
from viur_admin.locales import ISO639CODES
from datetime import datetime
import random
import string
from time import sleep


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

if isPyodide:
	class GoogleAuthenticationHandler():
		pass
	class LocalAuthGoogleThread():
		pass
else:
	class GoogleAuthenticationHandler(http.server.BaseHTTPRequestHandler):
		skey = "".join(random.choices(string.ascii_letters + string.digits, k=13))
		clientID = "NotSet"

		def do_HEAD(self):
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()

		def do_GET(self):
			if self.path == "/":
				self.send_response(200)
				self.send_header("Content-type", "text/html")
				self.end_headers()
				stream = QtCore.QFile(':resources/user_google_login.html')
				assert stream.open(QtCore.QFile.ReadOnly), "user_google_login.html missing from resource"
				data = str(stream.readAll(), 'utf-8')
				stream.close()
				self.wfile.write(data.replace("{{ clientID }}", self.clientID).replace("{{ skey }}", self.skey).encode("UTF-8"))
			elif self.path == "/user_google_login.js":
				stream = QtCore.QFile(':resources/user_google_login.js')
				assert stream.open(QtCore.QFile.ReadOnly), "user_google_login.js missing from resource"
				data = str(stream.readAll(), 'utf-8')
				stream.close()
				self.send_response(200)
				self.send_header("Content-type", "text/html")
				self.end_headers()
				self.wfile.write(data.encode("UTF-8"))

			elif self.path.startswith("/login?"):
				data = self.path.replace("/login?", "")
				token = skey = None
				for param in data.split("&"):
					if param.startswith("token="):
						print("token", param)
						token = param.replace("token=", "")
					elif param.startswith("skey="):
						skey = param.replace("skey=", "")
				if token and skey and skey == self.skey:
					print(("Okay", token, skey))
					self.send_response(200)
					self.send_header("Content-type", "text/html")
					self.end_headers()
					self.wfile.write(b"Okay")
					#self.authProvider.tokenReceived(token)
					self.qthread.tokenReceived.emit(token)
					#self.authProvider.loginSucceeded.emit()
				else:
					self.send_response(500)
					self.send_header("Content-type", "text/html")
					self.end_headers()
					self.wfile.write(b"Failed")
					self.qthread.tokenErrorOccured.emit("Unknown error")
			else:
				self.send_response(404)
				self.end_headers()
				print("%s not found" % self.path)


	class LocalAuthGoogleThread(QtCore.QThread):
		port = 9090
		tokenReceived = QtCore.pyqtSignal(str)
		tokenErrorOccured = QtCore.pyqtSignal(str)

		def start(self) -> None:
			self.httpdRef = None
			self.shouldStart = True
			super().start()

		def run(self):
			try:
				with socketserver.TCPServer(("localhost", self.port), GoogleAuthenticationHandler) as httpd:
					self.httpdRef = httpd
					GoogleAuthenticationHandler.qthread = self
					print("serving at port", self.port)
					webbrowser.open("http://%s:%s" % ("localhost", self.port))
					if self.shouldStart:
						httpd.serve_forever()
			except OSError as e:
				self.tokenErrorOccured.emit(str(e))

		def abort(self):
			if self.httpdRef:
				self.httpdRef.shutdown()
			else:
				self.shouldStart = False
				sleep(1)
				if self.httpdRef:
					self.httpdRef.shutdown()
			self.wait()


	class OAuth2AuthenticationHandler(http.server.BaseHTTPRequestHandler):
		skey = "".join(random.choices(string.ascii_letters + string.digits, k=13))
		redirUrl = "NotSet"

		def do_HEAD(self):
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()

		def do_GET(self):
			if self.path == "/":
				self.send_response(302)
				self.send_header("Location", self.redirUrl)
				self.end_headers()
			elif self.path.startswith("/login?"):
				data = self.path.replace("/login?", "")
				token = skey = None
				for param in data.split("&"):
					if param.startswith("code="):
						print("token", param)
						token = param.replace("code=", "")
					elif param.startswith("session_state="):
						skey = param.replace("session_state=", "")
				if token: # and skey and skey == self.skey: FIXME: We can't pass an skey along here...
					self.send_response(200)
					self.send_header("Content-type", "text/html")
					self.end_headers()
					self.wfile.write(b"Okay")
					self.qthread.tokenReceived.emit(token)
				else:
					self.send_response(500)
					self.send_header("Content-type", "text/html")
					self.end_headers()
					self.wfile.write(b"Failed")
					self.qthread.tokenErrorOccured.emit("Unknown error")
			else:
				self.send_response(404)
				self.end_headers()
				print("%s not found" % self.path)


	class LocalAuthOAuthThread(QtCore.QThread):
		port = 9090
		tokenReceived = QtCore.pyqtSignal(str)
		tokenErrorOccured = QtCore.pyqtSignal(str)

		def start(self) -> None:
			self.httpdRef = None
			self.shouldStart = True
			super().start()

		def run(self):
			try:
				with socketserver.TCPServer(("localhost", self.port), OAuth2AuthenticationHandler) as httpd:
					self.httpdRef = httpd
					OAuth2AuthenticationHandler.qthread = self
					print("serving at port", self.port)
					webbrowser.open("http://%s:%s" % ("localhost", self.port))
					if self.shouldStart:
						httpd.serve_forever()
			except OSError as e:
				self.tokenErrorOccured.emit(str(e))

		def abort(self):
			if self.httpdRef:
				self.httpdRef.shutdown()
			else:
				self.shouldStart = False
				sleep(1)
				if self.httpdRef:
					self.httpdRef.shutdown()
			self.wait()


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
		self.authThread = None
		GoogleAuthenticationHandler.authProvider = self
		if isWizard:
			self.startAuthenticating()



	def startAuthenticating(self) -> None:
		print("LoginTask using method x-google")
		logger.debug("LoginTask using method x-google")
		if self.authThread:
			self.authThread.abort()
		# Fetch the HTML-File and extract the ClientID from it
		NetworkService.request("/user/auth_googleaccount/login", successHandler=self.onClientIDAvailable,
							   failureHandler=self.onError)

	def onClientIDAvailable(self, req):
		# Double-Check that we don't have an authThread running
		if self.authThread:
			self.authThread.abort()
		htmlData = req.readAll().data().decode("utf-8")
		# FIXME: This string-matching is fragile...
		if "google-signin-client_id" in htmlData:
			# This is the old Google-Sign-in
			tokenStart = htmlData.find("content=", htmlData.find("google-signin-client_id"))+9
			tokenEnd = htmlData.find("\"", tokenStart+5)
		else:
			# Hopefully the new identity services
			tokenStart = htmlData.find("data-client_id=\"")+16
			tokenEnd = htmlData.find("\"", tokenStart+5)
		token = htmlData[tokenStart:tokenEnd]
		# Prevent possible XSS-Attacks from a compromised project
		assert not any([x not in string.ascii_letters+string.digits+".-_@" for x in token]), "Invalid Token!"
		GoogleAuthenticationHandler.clientID = token
		self.authThread = LocalAuthGoogleThread()
		self.authThread.tokenReceived.connect(self.tokenReceived)
		self.authThread.tokenErrorOccured.connect(self.tokenErrorOccured)
		self.authThread.start()

	def tokenErrorOccured(self, error: str):
		if self.authThread:
			self.authThread.abort()
			self.authThread = None
		self.loginFailed.emit(error)

	def tokenReceived(self, token: str):
		"""
			Callback from the GoogleAuthenticationHandler.
			We received a token and now going to exchange it with the server for a session
		"""
		if self.authThread:
			self.authThread.abort()
			self.authThread = None
		NetworkService.request("/user/auth_googleaccount/login", {"token": token}, secure=True,
							   successHandler=self.authStatusCallback, failureHandler=self.onError)


	def authStatusCallback(self, nsReq: RequestWrapper) -> None:
		data = NetworkService.decode(nsReq)
		logger.debug("authStatusCallback: %r", data)
		okayFound = data.find("OKAY")
		logger.debug("checkAuthenticationStatus: %r", okayFound)
		if okayFound != -1:
			self.loginSucceeded.emit()
		elif data.find("X-VIUR-2FACTOR-") != -1:
			html = self.webView.page().mainFrame().toHtml()
			startPos = html.find("X-VIUR-2FACTOR-")
			secondFactorType = html[startPos, html.find("\"", startPos + 1)]
			secondFactorType = secondFactorType.replace("X-VIUR-2FACTOR-", "")
			self.secondFactorRequired.emit(secondFactorType)

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


class AuthOauth2(AuthProviderBase):
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
		super(AuthOauth2, self).__init__(
			currentPortalConfig=currentPortalConfig,
			isWizard=isWizard,
			parent=parent)
		self.didSucceed = False
		self.authThread = None
		OAuth2AuthenticationHandler.authProvider = self
		if isWizard:
			self.startAuthenticating()

	def startAuthenticating(self) -> None:
		logger.debug("LoginTask using method X-VIUR-AUTH-OAuth2")
		if self.authThread:
			self.authThread.abort()
		# Fetch the HTML-File and extract the ClientID from it
		NetworkService.request("/user/auth_oauth2/login", secure=True, successHandler=self.onRedirectUrlAvailable,
							   failureHandler=self.onError)

	def onRedirectUrlAvailable(self, req):
		# Double-Check that we don't have an authThread running
		if self.authThread:
			self.authThread.abort()
		redirUrl = req.request.header(QtNetwork.QNetworkRequest.LocationHeader).toString()
		if self.authThread:
			self.authThread.abort()
		OAuth2AuthenticationHandler.redirUrl = redirUrl
		self.authThread = LocalAuthOAuthThread()
		self.authThread.tokenReceived.connect(self.tokenReceived)
		self.authThread.tokenErrorOccured.connect(self.tokenErrorOccured)
		self.authThread.start()

	def tokenErrorOccured(self, error: str):
		if self.authThread:
			self.authThread.abort()
			self.authThread = None
		self.loginFailed.emit(error)

	def tokenReceived(self, token: str):
		"""
			Callback from the OAuth2AuthenticationHandler.
			We received a token and now going to exchange it with the server for a session
		"""
		if self.authThread:
			self.authThread.abort()
			self.authThread = None
		NetworkService.request("/user/auth_oauth2/login", {"code": token}, secure=True,
							   successHandler=self.authStatusCallback, failureHandler=self.onError)


	def authStatusCallback(self, nsReq: RequestWrapper) -> None:
		data = NetworkService.decode(nsReq)
		logger.debug("authStatusCallback: %r", data)
		okayFound = data.find("OKAY")
		logger.debug("checkAuthenticationStatus: %r", okayFound)
		if okayFound != -1:
			self.loginSucceeded.emit()
		elif data.find("X-VIUR-2FACTOR-") != -1:
			html = self.webView.page().mainFrame().toHtml()
			startPos = html.find("X-VIUR-2FACTOR-")
			secondFactorType = html[startPos, html.find("\"", startPos + 1)]
			secondFactorType = secondFactorType.replace("X-VIUR-2FACTOR-", "")
			self.secondFactorRequired.emit(secondFactorType)

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
		"X-VIUR-AUTH-Google-Account": AuthGoogle,
		"X-VIUR-AUTH-OAuth2": AuthOauth2
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
		# Fix icons
		self.ui.btnLogin.setIcon(loadIcon("login"))
		self.portalWizard = None # Reference to an add portal wizard (if any)
		self.helpBrowser = None
		self.loginTask = None
		self.isFirstShown = True  # Don't reopen the add wizard a second time if aborted
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
		self.ui.cbLanguages.blockSignals(False)
		self.ui.btnLogin.clicked.connect(self.onBtnLoginReleased)
		self.ui.cbLanguages.currentIndexChanged.connect(self.onCbLanguagesCurrentIndexChanged)
		self.ui.actionAddPortal.triggered.connect(self.openPortalWizard)
		self.ui.actionDeletePortal.triggered.connect(self.deletePortal)
		self.ui.actionEditPortal.triggered.connect(self.editPortal)

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
			cb.addItem(AccountItem(account))
			if account["name"] == currentPortalName:
				currentIndex = ix
		if len(config.conf.accounts) > 0:
			cb.setCurrentRow(currentIndex)
			self.onCbPortalCurrentRowChanged(currentIndex)
			cb.setFocus()
			self.ui.actionEditPortal.setDisabled(False)
			self.ui.actionDeletePortal.setDisabled(False)
		elif self.isFirstShown:
			self.isFirstShown = False
			self.openPortalWizard()
		else:
			self.ui.actionEditPortal.setDisabled(True)
			self.ui.actionDeletePortal.setDisabled(True)

	def editPortal(self, *args, **kwargs):
		try:
			account = config.conf.accounts[self.ui.cbPortal.currentIndex().row()]
		except:
			return
		self.openPortalWizard(account)

	def deletePortal(self, *args, **kwargs):
		try:
			account = config.conf.accounts[self.ui.cbPortal.currentIndex().row()]
		except:
			return
		self.requestDeleteBox = QtWidgets.QMessageBox(
			QtWidgets.QMessageBox.Question,
			QtCore.QCoreApplication.translate("Login", "Confirm delete"),
			QtCore.QCoreApplication.translate("Login", "Delete Portal %s?") % account["name"],
			(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No),
			self
		)
		self.requestDeleteBox.buttonClicked.connect(self.reqDeleteCallback)
		self.requestDeleteBox.open()
		QtGui.QGuiApplication.processEvents()
		self.requestDeleteBox.adjustSize()
		self.requestDeleteBox.deleteList = account

	def reqDeleteCallback(self, clickedBtn, *args, **kwargs):
		if clickedBtn == self.requestDeleteBox.button(self.requestDeleteBox.Yes):
			config.conf.accounts.remove(self.requestDeleteBox.deleteList)
			self.isFirstShown = False
			self.loadAccounts()
		self.requestDeleteBox = None

	def openPortalWizard(self, portalData=None):
		self.portalWizard = AddPortalWizard(portalData)
		self.portalWizard.show()
		self.setDisabled(True)
		self.portalWizard.finished.connect(self.onPortalWizardFinished)
		self.portalWizard.raise_()
		self.portalWizard.activateWindow()

	def onPortalWizardFinished(self, *args, **kwargs):
		self.setDisabled(False)
		self.loadAccounts()
		securityTokenProvider.staticSecurityKey = None  # Reset a maybe set static skey


	def onCbPortalCurrentRowChanged(self, index: Any) -> None:
		if isinstance(index, str):
			return
		if self.ui.cbPortal.currentIndex() == -1:
			activeaccount = {"name": "", "user": "", "password": "", "server": ""}
		else:
			try:
				activeaccount = config.conf.accounts[self.ui.cbPortal.currentIndex().row()]
			except:
				return
			config.conf.adminConfig["currentPortalName"] = activeaccount["name"]
			config.conf.saveConfig()

	def onLoginSucceeded(self) -> None:
		logger.debug("onLoginSucceeded")
		self.overlay.inform(self.overlay.SUCCESS, QtCore.QCoreApplication.translate("Login", "Login successful"))
		# config.conf.loadPortalConfig(NetworkService.url, withCookies=False)
		event.emit("loginSucceeded")
		self.setDisabled(False)
		self.hide()

	def statusMessageUpdate(self, type: str, message: str) -> None:
		self.ui.statusbar.showMessage(message, 5000)

	def onEditPasswordReturnPressed(self) -> None:
		self.onBtnLoginReleased()

	def onBtnLoginReleased(self) -> None:
		self.setDisabled(True)
		QtGui.QGuiApplication.processEvents()
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
		#self.overlay.inform(self.overlay.ERROR, msg)
		self.setDisabled(False)
		QtWidgets.QMessageBox.warning(self, "Error logging in", msg)
		self.loadAccounts()

	def enableForm(self, msg: str = None) -> None:
		self.setDisabled(False)
		if msg:
			QtWidgets.QMessageBox.warning(self, "Error logging in", msg)
			#self.overlay.inform(self.overlay.ERROR, msg)
		else:
			#self.overlay.clear()
			pass
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
		self.ui.googleLoginBtn.clicked.connect(self.onBtnGoogleLoginReleased)
		self.setDisabled(True)
		self.ui.statusLbl.setText("Please login")
		self.loginTask = None
		self.ui.label_4.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		self.pixMap = QtGui.QPixmap(":icons/login.png")
		self.resizeEvent()
		NetworkService.request("/user/view/self", successHandler=self.onHasSession, failureHandler=self.onNoSession, failSilent=True)

	def resizeEvent(self, event = None):
		if event:
			super().resizeEvent(event)
		self.ui.label_4.setPixmap(self.pixMap.scaled(self.ui.label_4.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

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
		#/user/getAuthMethods
		NetworkService.request("/user/getAuthMethods", successHandler=self.onAuthMethodsKnown, failureHandler=self.onLoginFailed)
		#self.setDisabled(False)

	def onBtnGoogleLoginReleased(self, *args, **kwargs):
		import js
		js.window.location.href = "/admin/user/auth_googleaccount/login"

	def onAuthMethodsKnown(self, req: RequestWrapper):
		data = NetworkService.decode(req)
		userPassword = google = False
		try:
			for authMethod in data:
				if authMethod[0] == "X-VIUR-AUTH-Google-Account":
					google = True
				elif authMethod[0] == "X-VIUR-AUTH-User-Password":
					userPassword = True
		except:
			raise
		if google and userPassword:
			# FIXME: Button to login with both?
			self.onLoginFailed("2 Auth Methods")
			self.ui.googleLoginBtn.setDisabled(False)
		elif google:
			self.onBtnGoogleLoginReleased()
		else: # Either neither - or user-password
			self.ui.googleLoginBtn.setDisabled(True)
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

