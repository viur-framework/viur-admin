from ui.loginformUI import Ui_LoginWindow
from accountmanager import Accountmanager
from PyQt4 import QtCore, QtGui, QtWebKit
from network import NetworkService
from event import event
from config import conf
from utils import Overlay, showAbout
import urllib.parse
from urllib.error import HTTPError
from PyQt4 import QtCore
import json
from locales import ISO639CODES
import logging

class LoginTask( QtCore.QObject ):
	def __init__(self, username, password, captchaToken=None, captcha=None ):
		QtCore.QObject.__init__( self )
		self.logger = logging.getLogger( "LoginTask" )
		self.logger.debug("Starting LoginTask")
		try:
			event.emit( QtCore.SIGNAL( "loginStarted(PyQt_PyObject, PyQt_PyObject, PyQt_PyObject, PyQt_PyObject)" ), username, password, captchaToken, captcha )
		except StopIteration:
			logging.info("Login aborted by StopIteration")
			return
		self.username = username
		self.password = password
		self.captcha = captcha
		self.captchaToken = captchaToken
		conf.currentUsername = username
		conf.currentPassword = password
		self.req = None
		self.accountType = None
		self.isLocalServer = False
		self.hostName = urllib.parse.urlparse( NetworkService.url ).hostname or NetworkService.url
		if urllib.parse.urlparse( NetworkService.url ).port: #Assume local Development
			logging.debug("Assuming local development Server")
			self.isLocalServer = True
			NetworkService.request("http://%s:%s/_ah/login" % ( self.hostName, urllib.parse.urlparse( NetworkService.url ).port, ), successHandler=self.onWarmup, failureHandler=self.onError )
		else:
			self.onWarmup()

	
	def onWarmup(self, request=None): #Warmup request has finished
		self.logger.debug("Checkpoint: onWarmup")
		if self.isLocalServer:
			NetworkService.request("http://%s:%s/admin/user/getAuthMethod" % ( self.hostName, urllib.parse.urlparse( NetworkService.url ).port, ), finishedHandler=self.onAuthMethodKnown )
		else:
			NetworkService.request("https://%s/admin/user/getAuthMethod" % ( self.hostName, ), finishedHandler=self.onAuthMethodKnown )
	
	def onAuthMethodKnown(self, request ):
		self.logger.debug("Checkpoint: onAuthMethodKnown")
		method = bytes( request.readAll() ).decode("UTF-8").lower()
		if method == "x-viur-internal":
			logging.debug("LoginTask using method x-viur-internal")
			NetworkService.request("/user/login", {"name": self.username, "password": self.password}, secure=True, successHandler=self.onViurAuth, failureHandler=self.onError )
		else: #Fallback to google account auth
			logging.debug("LoginTask using method x-google-account")
			if self.isLocalServer:
				argsStr = urllib.parse.urlencode( {"email": self.username, "admin": "True", "action":"Login"} )
				NetworkService.request("http://%s:%s/_ah/login?%s" % ( self.hostName, urllib.parse.urlparse( NetworkService.url ).port, argsStr ), None, finishedHandler=self.onLocalAuth  )
			else:
				credDict = {	"Email": self.username,
							"Passwd":self.password,
							"source":"ViUR-Admin",
							"accountType":"HOSTED_OR_GOOGLE",
							"service":"ah" }
				if self.captcha and self.captchaToken:
					credDict["logintoken"] = self.captchaToken
					credDict["logincaptcha"] = self.captcha
				credStr = urllib.parse.urlencode( credDict )
				NetworkService.request( "https://www.google.com/accounts/ClientLogin", credStr.encode("UTF-8"), successHandler=self.onGoogleAuthSuccess, failureHandler=self.onError )

	def onViurAuth(self, request): # We recived an response to our auth request
		self.logger.debug("Checkpoint: onViurAuth")
		try:
			res = NetworkService.decode( request )
		except: #Something went wrong
			self.onError( msg = "Unable to decode response!" )
			return
		if str(res).lower()=="okay":
			self.loadConfig()
		else:
			self.onError( msg = "Recived response!=\"okay\"!" )

	def onLocalAuth(self, request):
		self.logger.debug("Checkpoint: onLocalAuth")
		NetworkService.request("http://%s:%s/admin/user/login" % ( self.hostName, urllib.parse.urlparse( NetworkService.url ).port ), None, successHandler=self.loadConfig, failureHandler=self.onError )
		
	def loadConfig(self, request=None):
		self.logger.debug("Checkpoint: loadConfig")
		NetworkService.request("/config", successHandler=self.onLoadConfig, failureHandler=self.onError )
		
	def onLoadConfig(self, request):
		self.logger.debug("Checkpoint: onLoadConfig")
		try:
			conf.serverConfig = NetworkService.decode( request )
		except ValueError:
			self.onError( msg = "Unable to decode response!" )
			return
		event.emit( QtCore.SIGNAL("loginSucceeded()") )

	def onGoogleAuthSuccess( self, request ):
		self.logger.debug("Checkpoint: onGoogleAuthSuccess")
		res = bytes( request.readAll() ).decode("UTF-8")
		authToken=None
		for line in res.splitlines():
			if line.lower().startswith("auth="):
				authToken = line[ 5: ].strip()
		self.logger.debug("LoginTask got AuthToken: %s...", authToken[:6] if authToken else authToken )
		if not authToken:
			if "CaptchaRequired".lower() in res.lower():
				self.logger.info( "Need captcha" )
				captchaToken = None
				captchaURL = None
				for line in res.splitlines():
					if line.lower().startswith("captchatoken"):
						captchaToken = line[ 13: ]
					elif line.lower().startswith("captchaurl"):
						captchaURL = line[ 11: ]
				assert captchaToken and captchaURL
				self.emit(QtCore.SIGNAL("reqCaptcha(PyQt_PyObject,PyQt_PyObject)"), captchaToken, captchaURL)
				return
			else:
				self.onError( msg="Found no authToken in response!" )
				return
		# Normalizing the URL we use
		url = NetworkService.url.lower()
		if url.endswith("/"): #Remove tailing /
			url = url[ : -1]
		if not url.endswith("/admin"):
			url = url + "/admin"
		if not url.startswith("https://"): #Assert that a secure protocol is specified
			if url.startswith("http://"):
				if not urllib.parse.urlparse( url ).port: # Dosnt look like development Server
					url = "https://"+url[ 7: ] # Dont use insecure protocol on live server
			else:
				url = "https://"+url
		argsStr = urllib.parse.urlencode( {"continue": url+"/user/login", "auth": authToken} )
		NetworkService.request("https://%s/_ah/login?%s" % ( self.hostName, argsStr ), successHandler=self.onGAEAuth, failureHandler=self.onError )
	
	def onGAEAuth( self, request=None ):
		self.logger.debug("Checkpoint: onGAEAuth")
		self.req = NetworkService.request( "/user/login", successHandler=self.loadConfig, failureHandler=self.onError )
	
	def onError( self, request=None, error=None, msg=None ):
		event.emit( QtCore.SIGNAL("loginFailed(PyQt_PyObject)"), QtCore.QCoreApplication.translate("Login", msg or str( error ) ) )
		self.emit( QtCore.SIGNAL("loginFailed(PyQt_PyObject)"), msg or str( error ) )
		

	

class Login( QtGui.QMainWindow ):
	def __init__( self, *args, **kwargs ):
		QtGui.QMainWindow.__init__(self, *args, **kwargs )
		self.ui = Ui_LoginWindow()
		self.ui.setupUi( self )
		self.accman = None #Reference to our Account-MGR
		self.helpBrowser = None
		self.connect( event, QtCore.SIGNAL('resetLoginWindow()'), self.enableForm )
		self.connect( event, QtCore.SIGNAL('statusMessage(PyQt_PyObject,PyQt_PyObject)'), self.statusMessageUpdate )
		self.connect( event, QtCore.SIGNAL('loginSucceeded()'), self.closeWindow )
		self.connect( event, QtCore.SIGNAL('accountListChanged()'), self.loadAccounts )
		self.ui.lblCaptcha.setText( QtCore.QCoreApplication.translate("Login", "Not required"))
		self.ui.editCaptcha.hide()
		self.captchaToken = None
		self.loadAccounts()
		self.overlay = Overlay( self )
		shortCut = QtGui.QShortcut( self )
		shortCut.setKey("Return")
		self.connect( shortCut, QtCore.SIGNAL("activated()"), self.on_btnLogin_released )
		#Populate the language-selector
		self.langKeys = list( conf.availableLanguages.keys() )
		self.ui.cbLanguages.blockSignals( True )
		for k in self.langKeys:
			self.ui.cbLanguages.addItem( ISO639CODES[ k ] )
		currentLang = "en"
		if "language" in conf.adminConfig.keys():
			currentLang = conf.adminConfig["language"]
		if currentLang in self.langKeys:
			self.ui.cbLanguages.setCurrentIndex( self.langKeys.index( currentLang ) )
		self.ui.cbLanguages.blockSignals( False )
		
	def changeEvent(self, *args, **kwargs):
		super( Login, self ).changeEvent( *args, **kwargs )
		self.ui.retranslateUi( self )
	
	def loadAccounts(self):
		cb = self.ui.cbPortal
		cb.clear()
		for account in conf.accounts:
			cb.addItem(account["name"])
		if len( conf.accounts ) > 0:
			cb.setCurrentIndex( 0 )
			self.on_cbPortal_currentIndexChanged( 0 )
		if self.accman:
			self.accman.deleteLater()
			self.accman = None

	def on_cbPortal_currentIndexChanged (self, index):
		if isinstance(index, str):
			return
		if ( self.ui.cbPortal.currentIndex() == -1 ):
			activeaccount = {"name":"","user":"","password":"","url":""}
		else:
			activeaccount=conf.accounts[ self.ui.cbPortal.currentIndex() ]
		self.ui.editUsername.setText(activeaccount["user"])
		self.ui.editPassword.setText(activeaccount["password"])
		self.ui.editUrl.setText(activeaccount["url"])

	def closeWindow(self):
		self.hide()

	def statusMessageUpdate(self, type, message ):
		self.ui.statusbar.showMessage( message, 5000 )
		
	def on_editPassword_returnPressed (self):
		self.on_btnLogin_released()

	def on_btnLogin_released( self ):
		url = self.ui.editUrl.displayText()
		username =self.ui.editUsername.text()
		password = self.ui.editPassword.text()
		cb = self.ui.cbPortal
		if (cb.currentIndex()==-1):
			reply = QtGui.QMessageBox.question(self, QtCore.QCoreApplication.translate("Login", "Save this account"),QtCore.QCoreApplication.translate("Login", "Save this account permanently?"), QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
			if reply==QtGui.QMessageBox.Yes:
				pw=password
				accname, okaypressed = QtGui.QInputDialog.getText(self, QtCore.QCoreApplication.translate("Login", "Save this account") ,QtCore.QCoreApplication.translate("Login", "Enter a name for this account") )
				if okaypressed:
					reply = QtGui.QMessageBox.question(self, QtCore.QCoreApplication.translate("Login", "Save this account"), QtCore.QCoreApplication.translate("Login", "Save the password, too?"), QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
					if reply==QtGui.QMessageBox.No:
						pw=""
					saveacc={"name":accname,
					"user":username,
					"password":pw,
					"url":url
					}
					conf.accounts.append(saveacc)
		elif cb.currentIndex()!=0: #Move this account to the beginning, so it will be selected on the next start of apex
			account = conf.accounts[ cb.currentIndex() ]
			conf.accounts.remove( account )
			conf.accounts.insert(0, account)
		NetworkService.setup( url )
		if self.captchaToken:
			captcha = self.ui.editCaptcha.text()
		else:
			captcha = None
		self.overlay.inform( self.overlay.BUSY, QtCore.QCoreApplication.translate("Login", "Login in progress") )
		if self.accman:
			self.accman.deleteLater()
			self.accman = None
		if self.helpBrowser:
			self.helpBrowser.deleteLater()
			self.helpBrowser = None
		self.login( username, password, captcha )

	def on_startAccManagerBTN_released(self):
		if self.accman:
			self.accman.deleteLater()
			self.accman = None
		self.accman = Accountmanager()
		self.accman.show()
		
	def on_actionAccountmanager_triggered(self):
		self.on_startAccManagerBTN_released()
	
	def on_actionAbout_triggered(self, checked=None):
		if checked is None: return
		showAbout( self )
		
	def on_actionHelp_triggered(self):
		if self.helpBrowser:
			self.helpBrowser.deleteLater()
		self.helpBrowser = QtWebKit.QWebView( )
		self.helpBrowser.setUrl( QtCore.QUrl( "http://www.viur.is/site/Admin-Dokumentation" ) )
		self.helpBrowser.setWindowTitle( QtCore.QCoreApplication.translate("Help", "Help") )
		self.helpBrowser.setWindowIcon( QtGui.QIcon( QtGui.QPixmap( "icons/menu/help.png" ) ) )
		self.helpBrowser.show()
	
	def setCaptcha( self, token, url ):
		self.captchaToken = token
		self.captchaReq = NetworkService.request("https://www.google.com/accounts/"+url)
		self.connect( self.captchaReq, QtCore.SIGNAL("finished()"), self.onCaptchaAvaiable )

	def onCaptchaAvaiable(self):
		pixmap = QtGui.QPixmap()
		data = bytes( self.captchaReq.readAll() )
		pixmap.loadFromData( data )
		self.ui.lblCaptcha.setPixmap( pixmap )
		self.ui.editCaptcha.show()
		self.ui.editCaptcha.setText("")
		self.overlay.inform( self.overlay.ERROR, QtCore.QCoreApplication.translate("Login", "Captcha required") )
		self.captchaReq.deleteLater()
		self.captchaReq = None

	def login( self, username, password, captcha=None ):
		"""
		Then:
		Download Modulconfiguration from Server and set things up.
		Calls L{resetLoginWindow} on failure, L{applyConfig} otherwise
		"""
		self.overlay.inform( self.overlay.BUSY )
		if captcha:
			self.loginTask = LoginTask( username, password, self.captchaToken, captcha )
		else:
			self.loginTask = LoginTask( username, password )
		self.connect( self.loginTask, QtCore.SIGNAL("reqCaptcha(PyQt_PyObject,PyQt_PyObject)"), self.setCaptcha )
		self.connect( self.loginTask, QtCore.SIGNAL("loginFailed(PyQt_PyObject)"), self.enableForm )
		self.connect( event, QtCore.SIGNAL("loginSucceeded()"), self.loginSucceeded )


	def loginSucceeded( self ):
		self.overlay.inform( self.overlay.SUCCESS, QtCore.QCoreApplication.translate("Login", "Login successful") )
		conf.loadPortalConfig( NetworkService.url )
	
	def enableForm(self, msg=None):
		if msg:
			self.overlay.inform( self.overlay.ERROR, msg )
		else:
			self.overlay.clear()
		self.show()

	def on_cbLanguages_currentIndexChanged(self, index):
		if not isinstance( index, int):
			return
		for v in conf.availableLanguages.values(): #Fixme: Removes all (even unloaded) translations
			QtCore.QCoreApplication.removeTranslator( v )
		newLanguage =  self.langKeys[ index ]
		QtCore.QCoreApplication.installTranslator( conf.availableLanguages[ newLanguage ] )
		conf.adminConfig["language"] = newLanguage
		
