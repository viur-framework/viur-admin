from time import time

from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.config import conf
from viur_admin.event import event
from viur_admin.log import getLogger
from viur_admin.network import NetworkService
from viur_admin.ui.accountmanagerUI import Ui_MainWindow
from viur_admin.ui.addportalwizardUI import Ui_AddPortalWizard

"""
	Allows editing the local accountlist.
"""

logger = getLogger(__name__)


class AddPortalWizard(QtWidgets.QWizard):
	def __init__(self, currentPortalConfig=None, *args, **kwargs):
		super(AddPortalWizard, self).__init__(*args, **kwargs)
		self.ui = Ui_AddPortalWizard()
		self.ui.setupUi(self)
		self.forcePageFlip = False
		self.validAuthMethods = None
		self.loginTask = None
		if "currentPortalConfig":
			self.editMode = True
			self.currentPortalConfig = currentPortalConfig
		else:
			self.currentPortalConfig = {
				"name": "",
				"key": int(time()),
				"server": "",
				"authMethod": ""
			}
			self.editMode = False

	def validateCurrentPage(self):
		if self.forcePageFlip:
			self.forcePageFlip = False
			return True
		if self.currentId() == 2 and self.tmp.advancesAutomatically:
			return False
		if self.currentId() == 0:
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
		elif self.currentId() == 1:
			self.currentPortalConfig["authMethod"] = self.validAuthMethods[self.ui.cbAuthSelector.currentText()]
			print("SELECTED AUTH METHOD")
			print(self.currentPortalConfig)
		elif self.currentId() == 2:
			self.currentPortalConfig.update(self.loginTask.getUpdatedPortalConfig())
			print("********")
			print(self.currentPortalConfig)
			self.loginTask.startAuthenticationFlow()
			# self.setDisabled(True)
			return False
		return True

	def initializePage(self, pageId):
		from viur_admin.login import LoginTask
		print("initializePage", pageId)
		super(AddPortalWizard, self).initializePage(pageId)
		# self.button(QtWidgets.QWizard.NextButton).setEnabled(True)
		if pageId == 0:
			self.ui.editTitle.setText(self.currentPortalConfig["name"])
			self.ui.editServer.setText(self.currentPortalConfig["server"])
		if pageId == 1:
			logger.debug(self.validAuthMethods)
			try:
				self.ui.cbAuthSelector.setCurrentText(self.currentPortalConfig["authMethod"])
			except Exception as err:
				logger.exception(err)
		if pageId == 2:
			if self.loginTask:
				self.loginTask.deleteLater()
				self.loginTask = None
			self.loginTask = LoginTask(self.currentPortalConfig, isWizard=True)
			self.loginTask.loginSucceeded.connect(self.onloginSucceeded)
			self.loginTask.loginFailed.connect(self.onLoginFailed)
			self.tmp = self.loginTask.startSetup()
			self.ui.scrollArea.setWidget(self.tmp)
			if self.tmp.advancesAutomatically:
				self.button(QtWidgets.QWizard.NextButton).setDisabled(True)
			# self.ui.wizardPage1.layout().addWidget(self.tmp)
			self.tmp.show()

	def onAuthMethodsKnown(self, req):
		data = NetworkService.decode(req)
		logger.debug("onAuthMethodsKnown: %r", data)
		self.ui.cbAuthSelector.clear()
		seenList = []
		self.validAuthMethods = {}
		for authMethod, verificationMethod in data:
			if authMethod not in seenList:
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
		if not self.editMode:
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
		super(Accountmanager, self).__init__(*args, **kwargs)
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)
		self.loadAccountList()
		self.oldAccountName = None
		self.portalWizard = None
		self.ui.addAccBTN.released.connect(self.onAddAccBTNReleased)
		self.ui.acclistWidget.itemClicked.connect(self.onAcclistWidgetItemClicked)
		self.ui.acclistWidget.itemDoubleClicked.connect(self.onEditAccount)
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

	# guiList = self.ui.acclistWidget
	# item = AccountItem(
	# 		{
	# 			"name": QtCore.QCoreApplication.translate("Accountmanager", "New"),
	# 			"user": "",
	# 			"password": "",
	# 			"server": ""
	# 		}
	# )
	# guiList.addItem(item)
	# guiList.setCurrentItem(item)
	# self.updateUI()

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

	def onEditAccount(self, clickedItem):
		logger.debug("onEditAccount")
		if self.portalWizard:
			self.portalWizard.deleteLater()
			self.portalWizard = None
		self.portalWizard = AddPortalWizard(currentPortalConfig=self.ui.acclistWidget.currentItem().account)
		self.portalWizard.show()
		self.setDisabled(True)
		self.portalWizard.finished.connect(self.onPortalWizardFinished)

	def updateUI(self):
		item = self.ui.acclistWidget.currentItem()
		self.ui.acclistWidget.sortItems()
		if not item:
			self.ui.delAccBTN.setEnabled(False)
		else:

			self.oldAccountName = item.account["name"]
			self.ui.delAccBTN.setEnabled(True)

	def onFinishedBTNReleased(self):
		print("onFinishedBTNReleased")
		conf.accounts = []
		for itemIndex in range(0, self.ui.acclistWidget.count()):
			conf.accounts.append(self.ui.acclistWidget.item(itemIndex).account)
		event.emit("accountListChanged")
		self.close()
