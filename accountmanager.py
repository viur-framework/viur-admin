from ui.accountmanagerUI import Ui_MainWindow
from PyQt4 import Qt
import sys
from PyQt4 import QtCore, QtGui
from event import event
from config import conf
import json

"""
	Allows editing the local accountlist.
"""

class AccountItem(QtGui.QListWidgetItem):
	def __init__(self, account, *args, **kwargs ):
		super(AccountItem,self).__init__( QtGui.QIcon("icons/profile.png"), account["name"], *args, **kwargs )
		self.account = account

	def update(self, accountData):
		self.account = accountData
		self.setText( self.account["name"] )

class Accountmanager( QtGui.QMainWindow ):

	def __init__( self, *args, **kwargs ):
		QtGui.QMainWindow.__init__(self, *args, **kwargs )
		self.ui = Ui_MainWindow()
		self.ui.setupUi( self )
		self.connect( event, QtCore.SIGNAL('statusMessage(PyQt_PyObject,PyQt_PyObject)'), self.statusMessageUpdate )
		self.loadAccountList()
		if len (conf.accounts)==0:
			self.on_addAccBTN_released()

		
	def loadAccountList(self):
		guiList = self.ui.acclistWidget
		guiList.setIconSize( QtCore.QSize( 128, 128 ) )
		guiList.clear()
		for account in conf.accounts:
			item=AccountItem( account )
			guiList.addItem( item )
		if len( conf.accounts ) > 0:
			guiList.setCurrentRow( 0 )
			self.on_acclistWidget_itemClicked( None )

	def closeEvent(self, e):
		conf.accounts = []
		for itemIndex in range(0, self.ui.acclistWidget.count() ):
			conf.accounts.append( self.ui.acclistWidget.item( itemIndex ).account )
		event.emit( QtCore.SIGNAL( "accountListChanged()" ) )
		conf.saveConfig()
		self.close()

	def statusMessageUpdate(self, type, message ):
		self.ui.statusbar.showMessage( message, 5000 )

	def on_addAccBTN_released (self):
		guiList = self.ui.acclistWidget
		item=AccountItem( {"name": QtCore.QCoreApplication.translate("Accountmanager", "New"), "user":"", "password":"", "url":"" } )
		guiList.addItem( item )
		guiList.setCurrentItem( item )
		self.updateUI()
	
	def on_acclistWidget_itemClicked (self,clickeditem):
		self.updateUI( )
		
	def  on_delAccBTN_released(self):
		item = self.ui.acclistWidget.currentItem()
		if not item:
			return
		reply = QtGui.QMessageBox.question(self, QtCore.QCoreApplication.translate("Accountmanager", "Account deletion"), QtCore.QCoreApplication.translate("Accountmanager", "Really delete the account \"%s\"?") % item.account["name"], QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
		if reply==QtGui.QMessageBox.No:
			return
		self.ui.acclistWidget.takeItem( self.ui.acclistWidget.row( item ) )
		self.updateUI()

		
	def updateUI( self ):
		item = self.ui.acclistWidget.currentItem()
		if not item:
			self.ui.editAccountName.setText( "" )
			self.ui.editUrl.setText( "" )
			self.ui.editUserName.setText( "" )
			self.ui.editPassword.setText( "" )
			self.ui.editAccountName.setEnabled( False )
			self.ui.editUrl.setEnabled( False )
			self.ui.editUserName.setEnabled( False )
			self.ui.editPassword.setEnabled( False )
			self.ui.delAccBTN.setEnabled(False)
		else:
			self.ui.editAccountName.blockSignals( True )
			self.ui.editUrl.blockSignals( True )
			self.ui.editUserName.blockSignals( True )
			self.ui.editPassword.blockSignals( True )
			self.ui.editAccountName.setText( item.account["name"] )
			self.ui.editUrl.setText( item.account["url"] )
			self.ui.editUserName.setText( item.account["user"] )
			self.ui.editPassword.setText( item.account["password"] )
			self.ui.editAccountName.setEnabled( True )
			self.ui.editUrl.setEnabled( True )
			self.ui.editUserName.setEnabled( True )
			self.ui.editPassword.setEnabled( True )
			self.ui.delAccBTN.setEnabled( True )
			self.ui.editAccountName.blockSignals( False )
			self.ui.editUrl.blockSignals( False )
			self.ui.editUserName.blockSignals( False )
			self.ui.editPassword.blockSignals( False )
			if (item.account["password"]!=""):
				self.ui.accSavePWcheckBox.setCheckState(2)
		
	def on_accSavePWcheckBox_stateChanged (self,state):
		self.ui.editPassword.setEnabled(state)
		if (state==0):
			self.ui.editPassword.setText("")
			
	
	def saveAccount(self):
		item = self.ui.acclistWidget.currentItem()
		if not item:
			return
		url=self.ui.editUrl.text()
		if (url.find("http")==-1):
			url="https://"+url
		if (url.find("/admin")==-1):
			url+="/admin"
		account={"name":self.ui.editAccountName.text(),
				"user":self.ui.editUserName.text(),
				"password":self.ui.editPassword.text(),
				"url":url
				}
		item.update( account )
	
	
	def on_editAccountName_textChanged (self):
		self.saveAccount()
		
	def on_editUserName_textChanged (self):
		self.saveAccount()
		
	def on_editPassword_textChanged(self):
		self.saveAccount()
		
	def on_editUrl_textChanged(self):
		self.saveAccount()
			
	
	def on_FinishedBTN_released(self):
		conf.accounts = []
		for itemIndex in range(0, self.ui.acclistWidget.count() ):
			conf.accounts.append( self.ui.acclistWidget.item( itemIndex ).account )
		event.emit( QtCore.SIGNAL( "accountListChanged()" ) )
		self.close()
		



