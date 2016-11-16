from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.log import getLogger

logger = getLogger(__name__)
from viur_admin.config import conf
from viur_admin.event import event
from viur_admin.ui.accountmanagerUI import Ui_MainWindow
from viur_admin.ui.addportalwizardUI import Ui_AddPortalWizard
from viur_admin.network import NetworkService

"""
	Allows editing the local accountlist.
"""


class AddPortalWizard(QtWidgets.QWizard):
	def __init__(self, *args, **kwargs):
		super(AddPortalWizard, self).__init__(*args, **kwargs)
		self.ui = Ui_AddPortalWizard()
		self.ui.setupUi(self)
		self.forcePageFlip = False
		self.validAuthMethods = None
		self.loginTask = None
		self.currentPortalConfig = {"key": 1234.56}

	def validateCurrentPage(self):
		if self.forcePageFlip:
			self.forcePageFlip = False
			return True
		if self.currentId()==2 and self.tmp.advancesAutomatically:
			return False
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
			self.currentPortalConfig["server"] = server
			self.currentPortalConfig["name"] = self.ui.editTitle.text()
			NetworkService.url = server + "admin"
			NetworkService.request(
				"/user/getAuthMethods", successHandler=self.onAuthMethodsKnown, failureHandler=self.onError)
			self.setDisabled(True)
			return False
		elif self.currentId()==1:
			self.currentPortalConfig["authMethod"] = self.validAuthMethods[self.ui.cbAuthSelector.currentText()]
			print("SELECTED AUTH METHOD")
			print(self.currentPortalConfig)
		elif self.currentId()==2:
			self.currentPortalConfig.update(self.loginTask.getUpdatedPortalConfig())
			print("********")
			print(self.currentPortalConfig)
			self.loginTask.startAuthenticationFlow()
			#self.setDisabled(True)
			return False
		return True

	def initializePage(self, pageId):
		from viur_admin.login import LoginTask
		print("initializePage", pageId)
		super(AddPortalWizard, self).initializePage(pageId)
		#self.button(QtWidgets.QWizard.NextButton).setEnabled(True)
		if pageId==2:
			if self.loginTask:
				self.loginTask.deleteLater()
				self.loginTask = None
			self.loginTask = LoginTask(self.currentPortalConfig)
			self.loginTask.loginSucceeded.connect(self.onloginSucceeded)
			self.loginTask.loginFailed.connect(self.onLoginFailed)
			self.tmp = self.loginTask.startSetup()
			self.ui.scrollArea.setWidget(self.tmp)
			if self.tmp.advancesAutomatically:
				self.button(QtWidgets.QWizard.NextButton).setDisabled(True)
			#self.ui.wizardPage1.layout().addWidget(self.tmp)
			self.tmp.show()

	def onAuthMethodsKnown(self, req):
		data = NetworkService.decode(req)
		print(data)
		self.ui.cbAuthSelector.clear()
		seenList = []
		self.validAuthMethods = {}
		for authMethod, verificationMethod in data:
			if not authMethod in seenList:
				seenList.append(authMethod)
				self.validAuthMethods[authMethod] = authMethod
				self.ui.cbAuthSelector.addItem(authMethod)
		self.setDisabled(False)
		self.forcePageFlip = True
		self.next()

	def onError(self, req):
		print("***ERROR***")
		print(req)
		self.setDisabled(False)

	def onloginSucceeded(self, *args, **kwargs):
		print("xxxxxxxxxxxxxxxxxxxxxxxxxx")
		print("AddPortalWizard: onloginSucceeded")
		self.setDisabled(False)
		self.forcePageFlip = True
		self.next()

	def onLoginFailed(self, msg, *args, **kwargs):
		print("AddPortalWizard.onLoginFailed", msg)
		tmp = QtWidgets.QMessageBox.warning(self, "Login failed", msg)
		self.setDisabled(False)

	def accept(self):
		conf.accounts.insert(0, self.currentPortalConfig)
		super(AddPortalWizard, self).accept()



class AccountItem(QtWidgets.QListWidgetItem):
	def __init__(self, account, *args, **kwargs):
		super(AccountItem, self).__init__(QtGui.QIcon(":icons/profile.png"), account["name"], *args, **kwargs)
		self.account = account

	def update(self, accountData):
		self.account = accountData
		self.setText(self.account["name"])


class Accountmanager(QtWidgets.QMainWindow):
	def __init__(self, *args, **kwargs):
		QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)
		self.loadAccountList()
		self.oldAccountName = None
		self.portalWizard = None
		self.ui.addAccBTN.released.connect(self.onAddAccBTNReleased)
		self.ui.acclistWidget.itemClicked.connect(self.onAcclistWidgetItemClicked)
		self.ui.delAccBTN.released.connect(self.onDelAccBTNReleased)
		self.ui.FinishedBTN.released.connect(self.onFinishedBTNReleased)
		if len(conf.accounts) == 0:
			self.onAddAccBTNReleased()

	def loadAccountList(self):
		guiList = self.ui.acclistWidget
		guiList.setIconSize(QtCore.QSize(128, 128))
		guiList.clear()
		currentPortalName = conf.adminConfig.get("currentPortalName")
		logger.debug("currentPortalName %r", currentPortalName)
		currentIndex = 0
		for ix, account in enumerate(conf.accounts):
			if account["name"] == currentPortalName:
				currentIndex = ix
			item = AccountItem(account)
			guiList.addItem(item)
		if len(conf.accounts) > 0:
			guiList.setCurrentRow(currentIndex)
			self.onAcclistWidgetItemClicked(None)

	def closeEvent(self, e):
		conf.accounts = []
		for itemIndex in range(0, self.ui.acclistWidget.count()):
			conf.accounts.append(self.ui.acclistWidget.item(itemIndex).account)
		conf.saveConfig()
		event.emit("accountListChanged()")
		self.close()

	def onAddAccBTNReleased(self):
		if self.portalWizard:
			self.portalWizard.deleteLater()
			self.portalWizard = None
		self.portalWizard = AddPortalWizard()
		self.portalWizard.show()
		self.setDisabled(True)
		self.portalWizard.finished.connect(self.onPortalWizardFinished)
		"""
		guiList = self.ui.acclistWidget
		item = AccountItem(
				{
					"name": QtCore.QCoreApplication.translate("Accountmanager", "New"),
					"user": "", "password": "",
					"url": ""
				}
		)
		guiList.addItem(item)
		guiList.setCurrentItem(item)
		self.updateUI()
		"""

	def onPortalWizardFinished(self, *args, **kwargs):
		print("onPortalWizardFinished")
		self.setDisabled(False)
		self.loadAccountList()

	def onAcclistWidgetItemClicked(self, clickeditem):
		self.updateUI()

	def onDelAccBTNReleased(self):
		item = self.ui.acclistWidget.currentItem()
		if not item:
			return
		reply = QtWidgets.QMessageBox.question(
				self,
				QtCore.QCoreApplication.translate("Accountmanager", "Account deletion"),
				QtCore.QCoreApplication.translate("Accountmanager",
				                                  "Really delete the account \"%s\"?") %
				item.account["name"],
				QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
				QtWidgets.QMessageBox.No)
		if reply == QtWidgets.QMessageBox.No:
			return
		self.ui.acclistWidget.takeItem(self.ui.acclistWidget.row(item))
		self.updateUI()

	def updateUI(self):
		item = self.ui.acclistWidget.currentItem()
		self.ui.acclistWidget.sortItems()
		if not item:
			self.ui.delAccBTN.setEnabled(False)
		else:

			self.oldAccountName = item.account["name"]
			self.ui.delAccBTN.setEnabled(True)


	def onAccSavePWcheckBoxStateChanged(self, state):
		self.ui.editPassword.setEnabled(state)
		if state == 0:
			self.ui.editPassword.setText("")

	def saveAccount(self):
		item = self.ui.acclistWidget.currentItem()
		if not item:
			return
		url = self.ui.editUrl.text()
		url = url.rstrip("/")
		if url.find("http") == -1:
			url = "https://" + url
		if url.find("/admin") == -1:
			url += "/admin"
		account = {
			"name": self.ui.editAccountName.text(),
			"user": self.ui.editUserName.text(),
			"password": self.ui.editPassword.text(),
			"url": url
		}
		cpn = conf.adminConfig.get("currentPortalName")
		name = account["name"]
		if cpn == self.oldAccountName:
			self.oldAccountName = conf.adminConfig["currentPortalName"] = name
			conf.saveConfig()
		item.update(account)

	def onEditAccountNameTextChanged(self):
		self.saveAccount()

	def onEditUserNameTextChanged(self):
		self.saveAccount()

	def onEditPasswordTextChanged(self):
		self.saveAccount()

	def onEditUrlTextChanged(self):
		self.saveAccount()

	def onFinishedBTNReleased(self):
		conf.accounts = []
		for itemIndex in range(0, self.ui.acclistWidget.count()):
			conf.accounts.append(self.ui.acclistWidget.item(itemIndex).account)
		event.emit("accountListChanged")
		self.close()
