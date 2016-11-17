# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'loginform.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_LoginWindow(object):
    def setupUi(self, LoginWindow):
        LoginWindow.setObjectName("LoginWindow")
        LoginWindow.resize(480, 707)
        LoginWindow.setMinimumSize(QtCore.QSize(480, 0))
        LoginWindow.setMaximumSize(QtCore.QSize(480, 16777215))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/viur_logo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        LoginWindow.setWindowIcon(icon)
        self.logincentralwidget = QtWidgets.QWidget(LoginWindow)
        self.logincentralwidget.setObjectName("logincentralwidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.logincentralwidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setFormAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.formLayout.setContentsMargins(0, -1, -1, -1)
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(self.logincentralwidget)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.cbLanguages = QtWidgets.QComboBox(self.logincentralwidget)
        self.cbLanguages.setObjectName("cbLanguages")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.cbLanguages)
        self.portalLabel = QtWidgets.QLabel(self.logincentralwidget)
        self.portalLabel.setObjectName("portalLabel")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.portalLabel)
        self.cbPortal = QtWidgets.QListWidget(self.logincentralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(4)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbPortal.sizePolicy().hasHeightForWidth())
        self.cbPortal.setSizePolicy(sizePolicy)
        self.cbPortal.setObjectName("cbPortal")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.cbPortal)
        self.accountManagerLabel = QtWidgets.QLabel(self.logincentralwidget)
        self.accountManagerLabel.setObjectName("accountManagerLabel")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.accountManagerLabel)
        self.startAccManagerBTN = QtWidgets.QPushButton(self.logincentralwidget)
        self.startAccManagerBTN.setMinimumSize(QtCore.QSize(0, 32))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("icons/accounts.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.startAccManagerBTN.setIcon(icon1)
        self.startAccManagerBTN.setObjectName("startAccManagerBTN")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.startAccManagerBTN)
        self.verticalLayout_2.addLayout(self.formLayout)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.verticalLayout_2.addItem(spacerItem)
        self.btnLogin = QtWidgets.QPushButton(self.logincentralwidget)
        self.btnLogin.setMinimumSize(QtCore.QSize(0, 64))
        self.btnLogin.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("icons/actions/login.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnLogin.setIcon(icon2)
        self.btnLogin.setObjectName("btnLogin")
        self.verticalLayout_2.addWidget(self.btnLogin)
        LoginWindow.setCentralWidget(self.logincentralwidget)
        self.menubar = QtWidgets.QMenuBar(LoginWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 480, 27))
        self.menubar.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.menubar.setObjectName("menubar")
        self.menuInfo = QtWidgets.QMenu(self.menubar)
        self.menuInfo.setObjectName("menuInfo")
        self.menuEinstellungen = QtWidgets.QMenu(self.menubar)
        self.menuEinstellungen.setObjectName("menuEinstellungen")
        LoginWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(LoginWindow)
        self.statusbar.setObjectName("statusbar")
        LoginWindow.setStatusBar(self.statusbar)
        self.actionErste_Schritte = QtWidgets.QAction(LoginWindow)
        self.actionErste_Schritte.setObjectName("actionErste_Schritte")
        self.actionHelp = QtWidgets.QAction(LoginWindow)
        self.actionHelp.setObjectName("actionHelp")
        self.actionAbout = QtWidgets.QAction(LoginWindow)
        self.actionAbout.setObjectName("actionAbout")
        self.actionSettings = QtWidgets.QAction(LoginWindow)
        self.actionSettings.setObjectName("actionSettings")
        self.actionAccountmanager = QtWidgets.QAction(LoginWindow)
        self.actionAccountmanager.setObjectName("actionAccountmanager")
        self.menuInfo.addAction(self.actionHelp)
        self.menuInfo.addSeparator()
        self.menuInfo.addAction(self.actionAbout)
        self.menuEinstellungen.addAction(self.actionAccountmanager)
        self.menubar.addAction(self.menuInfo.menuAction())
        self.menubar.addAction(self.menuEinstellungen.menuAction())

        self.retranslateUi(LoginWindow)
        QtCore.QMetaObject.connectSlotsByName(LoginWindow)

    def retranslateUi(self, LoginWindow):
        _translate = QtCore.QCoreApplication.translate
        LoginWindow.setWindowTitle(_translate("LoginWindow", "ViurAdmin – Login"))
        self.label.setText(_translate("LoginWindow", "Language"))
        self.portalLabel.setText(_translate("LoginWindow", "Portal"))
        self.accountManagerLabel.setText(_translate("LoginWindow", "Account Manager"))
        self.startAccManagerBTN.setText(_translate("LoginWindow", "Accountmannager"))
        self.btnLogin.setText(_translate("LoginWindow", "Login"))
        self.menuInfo.setTitle(_translate("LoginWindow", "&Info"))
        self.menuEinstellungen.setTitle(_translate("LoginWindow", "Setti&ngs"))
        self.actionErste_Schritte.setText(_translate("LoginWindow", "Erste Schritte"))
        self.actionHelp.setText(_translate("LoginWindow", "&Help"))
        self.actionAbout.setText(_translate("LoginWindow", "&About this Software"))
        self.actionSettings.setText(_translate("LoginWindow", "Generel settigs"))
        self.actionAccountmanager.setText(_translate("LoginWindow", "&Accountmanager"))

