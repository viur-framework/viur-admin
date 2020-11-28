# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'accountmanager.ui'
#
# Created by: PyQt5 UI code generator 5.13.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_AccountManager(object):
    def setupUi(self, AccountManager):
        AccountManager.setObjectName("AccountManager")
        AccountManager.resize(480, 680)
        AccountManager.setMinimumSize(QtCore.QSize(480, 0))
        AccountManager.setMaximumSize(QtCore.QSize(480, 16777215))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/viur_logo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        AccountManager.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(AccountManager)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.acclistWidget = QtWidgets.QListWidget(self.centralwidget)
        self.acclistWidget.setMinimumSize(QtCore.QSize(450, 250))
        self.acclistWidget.setObjectName("acclistWidget")
        self.verticalLayout.addWidget(self.acclistWidget)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.addAccBTN = QtWidgets.QPushButton(self.centralwidget)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/actions/add.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.addAccBTN.setIcon(icon1)
        self.addAccBTN.setObjectName("addAccBTN")
        self.horizontalLayout_3.addWidget(self.addAccBTN)
        self.delAccBTN = QtWidgets.QPushButton(self.centralwidget)
        self.delAccBTN.setEnabled(False)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/actions/delete.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.delAccBTN.setIcon(icon2)
        self.delAccBTN.setObjectName("delAccBTN")
        self.horizontalLayout_3.addWidget(self.delAccBTN)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.FinishedBTN = QtWidgets.QPushButton(self.centralwidget)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/icons/actions/accept.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.FinishedBTN.setIcon(icon3)
        self.FinishedBTN.setObjectName("FinishedBTN")
        self.verticalLayout_3.addWidget(self.FinishedBTN)
        self.verticalLayout_2.addLayout(self.verticalLayout_3)
        AccountManager.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(AccountManager)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 480, 26))
        self.menubar.setObjectName("menubar")
        AccountManager.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(AccountManager)
        self.statusbar.setObjectName("statusbar")
        AccountManager.setStatusBar(self.statusbar)

        self.retranslateUi(AccountManager)
        QtCore.QMetaObject.connectSlotsByName(AccountManager)

    def retranslateUi(self, AccountManager):
        _translate = QtCore.QCoreApplication.translate
        AccountManager.setWindowTitle(_translate("AccountManager", "Account manager"))
        self.addAccBTN.setText(_translate("AccountManager", "New Account"))
        self.delAccBTN.setText(_translate("AccountManager", "Delete Account"))
        self.FinishedBTN.setText(_translate("AccountManager", "Back to Loginscreen"))
import viur_admin.ui.icons_rc
