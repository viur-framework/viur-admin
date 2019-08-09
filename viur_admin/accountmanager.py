from time import time
from typing import Union, Callable, Any, Dict, List

from PyQt5 import QtCore, QtGui, QtWidgets

from viur_admin.login import LoginTask, AuthProviderBase
from viur_admin.config import conf
from viur_admin.event import event
from viur_admin.log import getLogger
from viur_admin.network import NetworkService, RequestWrapper
from viur_admin.ui.accountmanagerUI import Ui_AccountManager
from viur_admin.ui.addportalwizardUI import Ui_AddPortalWizard

"""
	Allows editing the local accountlist.
"""

logger = getLogger(__name__)


class AddPortalWizard(QtWidgets.QWizard):
	def __init__(
			self,
			currentPortalConfig: Union[Dict[str, Any], None] = None,
			parent: Union[QtWidgets.QWidget, None] = None) -> None:
		super(AddPortalWizard, self).__init__(parent=parent)
		self.ui = Ui_AddPortalWizard()
		self.ui.setupUi(self)
		self.forcePageFlip = False
		self.validAuthMethods: Dict[str, Any] = dict()
		self.loginTask: Union[LoginTask, None] = None
		self.authProvider: Union[AuthProviderBase, None] = None
		if currentPortalConfig:
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

	def validateCurrentPage(self) -> bool:
		if self.forcePageFlip:
			self.forcePageFlip = False
			return True

		currentId = self.currentId()
		if currentId == 2 and isinstance(self.authProvider, AuthProviderBase) and self.authProvider.advancesAutomatically:
			return False
		if currentId == 0:
			if not self.ui.editTitle.text():
				logger.error("AddPortalWizard.validateCurrentPage: no title")
				return False
			server = self.ui.editServer.text()
			if not server or not (server.startswith("http://") or server.startswith("https://")):
				logger.error("AddPortalWizard.validateCurrentPage: invalid url")
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
		elif currentId == 1:
			self.currentPortalConfig["authMethod"] = self.validAuthMethods[self.ui.cbAuthSelector.currentText()]
			logger.debug("AddPortalWizard.validateCurrentPage: %r, %r", currentId, self.currentPortalConfig)
		elif currentId == 2:
			if isinstance(self.loginTask, LoginTask):
				self.currentPortalConfig.update(self.loginTask.getUpdatedPortalConfig())
				logger.debug("AddPortalWizard.validateCurrentPage: %r, %r", currentId, self.currentPortalConfig)
				self.loginTask.startAuthenticationFlow()
			return False
		return True

	def initializePage(self, pageId: int) -> None:
		from viur_admin.login import LoginTask
		logger.debug("initializePage: %r", pageId)
		super(AddPortalWizard, self).initializePage(pageId)
		# self.button(QtWidgets.QWizard.NextButton).setEnabled(True)
		if pageId == 0:
			try:
				self.ui.editTitle.setText(self.currentPortalConfig["name"])
				self.ui.editServer.setText(self.currentPortalConfig["server"])
			except Exception as err:
				logger.exception(err)
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
			self.authProvider = self.loginTask.startSetup()
			self.ui.scrollArea.setWidget(self.authProvider)
			if self.authProvider:
				if self.authProvider.advancesAutomatically:
					self.button(QtWidgets.QWizard.NextButton).setDisabled(True)
				self.authProvider.show()

	def onAuthMethodsKnown(self, req: RequestWrapper) -> None:
		data = NetworkService.decode(req)
		logger.debug("onAuthMethodsKnown: %r", data)
		self.ui.cbAuthSelector.clear()
		seenList: List[str] = []
		self.validAuthMethods = {}
		for authMethod, verificationMethod in data:
			if authMethod not in seenList:
				seenList.append(authMethod)
				self.validAuthMethods[authMethod] = authMethod
				self.ui.cbAuthSelector.addItem(authMethod)
		self.setDisabled(False)
		self.forcePageFlip = True
		self.next()

	def onError(self, req: RequestWrapper) -> None:
		logger.error("AddPortalWizard.onError: %s", req)
		self.setDisabled(False)

	def onloginSucceeded(self) -> None:
		logger.debug("AddPortalWizard: onloginSucceeded")
		self.setDisabled(False)
		self.forcePageFlip = True
		self.next()

	def onLoginFailed(self, msg: str) -> None:
		logger.error("AddPortalWizard.onLoginFailed: %r", msg)
		QtWidgets.QMessageBox.warning(self, "Login failed", msg)
		self.setDisabled(False)

	def accept(self) -> None:
		if not self.editMode:
			conf.accounts.insert(0, self.currentPortalConfig)
		super(AddPortalWizard, self).accept()


class AccountItem(QtWidgets.QListWidgetItem):
	def __init__(self, account: Dict[str, Any], parent: QtWidgets.QWidget = None) -> None:
		super(AccountItem, self).__init__(
			QtGui.QIcon(":icons/profile.png"),
			account["name"],
			parent=parent)
		self.account = account

	def update(self, accountData: Dict[str, Any]) -> None:
		self.account = accountData
		self.setText(self.account["name"])


class AccountManager(QtWidgets.QMainWindow):
	def __init__(self, parent: QtWidgets.QWidget = None):
		super(AccountManager, self).__init__(parent=parent)
		self.ui = Ui_AccountManager()
		self.ui.setupUi(self)
		self.loadAccountList()
		self.oldAccountName = None
		self.portalWizard: Union[AddPortalWizard, None] = None
		self.ui.addAccBTN.released.connect(self.onAddAccBTNReleased)
		self.ui.acclistWidget.itemClicked.connect(self.onAcclistWidgetItemClicked)
		self.ui.acclistWidget.itemDoubleClicked.connect(self.onEditAccount)
		self.ui.delAccBTN.released.connect(self.onDelAccBTNReleased)
		self.ui.FinishedBTN.released.connect(self.onFinishedBTNReleased)
		if len(conf.accounts) == 0:
			self.onAddAccBTNReleased()

	def loadAccountList(self) -> None:
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

	def closeEvent(self, e: QtGui.QCloseEvent) -> None:
		conf.accounts = []
		for itemIndex in range(0, self.ui.acclistWidget.count()):
			conf.accounts.append(self.ui.acclistWidget.item(itemIndex).account)
		conf.saveConfig()
		event.emit("accountListChanged()")
		self.close()

	def onAddAccBTNReleased(self) -> None:
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
	# 			"name": QtCore.QCoreApplication.translate("AccountManager", "New"),
	# 			"user": "",
	# 			"password": "",
	# 			"server": ""
	# 		}
	# )
	# guiList.addItem(item)
	# guiList.setCurrentItem(item)
	# self.updateUI()

	def onPortalWizardFinished(self) -> None:
		logger.debug("AddPortalWizard.onPortalWizardFinished")
		self.setDisabled(False)
		self.loadAccountList()

	def onAcclistWidgetItemClicked(self, clickedItem: Union[AccountItem, None] = None) -> None:
		self.updateUI()

	def onDelAccBTNReleased(self) -> None:
		item = self.ui.acclistWidget.currentItem()
		if not item:
			return

		reply = QtWidgets.QMessageBox.question(
			self.centralWidget(),
			QtCore.QCoreApplication.translate("AccountManager", "Account deletion"),
			QtCore.QCoreApplication.translate("AccountManager", 'Really delete the account "%s"?' % item.account["name"]),
			QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
			QtWidgets.QMessageBox.No)
		if reply == QtWidgets.QMessageBox.No:
			return
		self.ui.acclistWidget.takeItem(self.ui.acclistWidget.row(item))
		self.updateUI()

	def onEditAccount(self, clickedItem: AccountItem) -> None:
		logger.debug("onEditAccount")
		if self.portalWizard:
			self.portalWizard.deleteLater()
			self.portalWizard = None
		self.portalWizard = AddPortalWizard(currentPortalConfig=self.ui.acclistWidget.currentItem().account)
		self.portalWizard.show()
		self.setDisabled(True)
		self.portalWizard.finished.connect(self.onPortalWizardFinished)

	def updateUI(self) -> None:
		item = self.ui.acclistWidget.currentItem()
		self.ui.acclistWidget.sortItems()
		if not item:
			self.ui.delAccBTN.setEnabled(False)
		else:

			self.oldAccountName = item.account["name"]
			self.ui.delAccBTN.setEnabled(True)

	def onFinishedBTNReleased(self) -> None:
		logger.debug("onFinishedBTNReleased")
		conf.accounts = []
		for itemIndex in range(0, self.ui.acclistWidget.count()):
			conf.accounts.append(self.ui.acclistWidget.item(itemIndex).account)
		event.emit("accountListChanged")
		self.close()
