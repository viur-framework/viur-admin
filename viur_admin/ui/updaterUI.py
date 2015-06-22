# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'updater.ui'
#
# Created: Mon Nov 24 18:30:25 2014
# by: PyQt5 UI code generator 5.3.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Updater(object):
    def setupUi(self, Updater):
        Updater.setObjectName("Updater")
        Updater.resize(175, 258)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":icons/viup.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Updater.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(Updater)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setText("")
        self.label.setPixmap(QtGui.QPixmap(":icons/viur-updater.png"))
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.textLog = QtWidgets.QTextEdit(self.centralwidget)
        self.textLog.setReadOnly(True)
        self.textLog.setObjectName("textLog")
        self.verticalLayout.addWidget(self.textLog)
        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName("progressBar")
        self.verticalLayout.addWidget(self.progressBar)
        self.btnCheck = QtWidgets.QPushButton(self.centralwidget)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":icons/actions/search.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnCheck.setIcon(icon1)
        self.btnCheck.setObjectName("btnCheck")
        self.verticalLayout.addWidget(self.btnCheck)
        self.btnUpdate = QtWidgets.QPushButton(self.centralwidget)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":icons/actions/accept.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnUpdate.setIcon(icon2)
        self.btnUpdate.setObjectName("btnUpdate")
        self.verticalLayout.addWidget(self.btnUpdate)
        self.btnExit = QtWidgets.QPushButton(self.centralwidget)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":icons/actions/cancel.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnExit.setIcon(icon3)
        self.btnExit.setObjectName("btnExit")
        self.verticalLayout.addWidget(self.btnExit)
        Updater.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(Updater)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 175, 21))
        self.menubar.setObjectName("menubar")
        Updater.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(Updater)
        self.statusbar.setObjectName("statusbar")
        Updater.setStatusBar(self.statusbar)

        self.retranslateUi(Updater)
        QtCore.QMetaObject.connectSlotsByName(Updater)

    def retranslateUi(self, Updater):
        _translate = QtCore.QCoreApplication.translate
        Updater.setWindowTitle(_translate("Updater", "ViUR Admin Updater"))
        self.btnCheck.setText(_translate("Updater", "Check for Updates"))
        self.btnUpdate.setText(_translate("Updater", "Update now"))
        self.btnExit.setText(_translate("Updater", "Exit"))

