# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'accountmanager.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(480, 680)
        MainWindow.setMinimumSize(QtCore.QSize(480, 0))
        MainWindow.setMaximumSize(QtCore.QSize(480, 16777215))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/viur_logo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
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
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 480, 26))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Viur Accountmanager"))
        self.addAccBTN.setText(_translate("MainWindow", "New Account"))
        self.delAccBTN.setText(_translate("MainWindow", "Delete Account"))
        self.FinishedBTN.setText(_translate("MainWindow", "Back to Loginscreen"))


import viur_admin.ui.icons_rc
