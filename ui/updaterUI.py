# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'updater.ui'
#
# Created: Sat May 11 13:51:25 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Updater(object):
    def setupUi(self, Updater):
        Updater.setObjectName("Updater")
        Updater.resize(175, 258)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/viup.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Updater.setWindowIcon(icon)
        self.centralwidget = QtGui.QWidget(Updater)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setText("")
        self.label.setPixmap(QtGui.QPixmap("icons/viur-updater.png"))
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.textLog = QtGui.QTextEdit(self.centralwidget)
        self.textLog.setReadOnly(True)
        self.textLog.setObjectName("textLog")
        self.verticalLayout.addWidget(self.textLog)
        self.progressBar = QtGui.QProgressBar(self.centralwidget)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName("progressBar")
        self.verticalLayout.addWidget(self.progressBar)
        self.btnCheck = QtGui.QPushButton(self.centralwidget)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("icons/actions/search_small.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnCheck.setIcon(icon1)
        self.btnCheck.setObjectName("btnCheck")
        self.verticalLayout.addWidget(self.btnCheck)
        self.btnUpdate = QtGui.QPushButton(self.centralwidget)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("icons/actions/accept.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnUpdate.setIcon(icon2)
        self.btnUpdate.setObjectName("btnUpdate")
        self.verticalLayout.addWidget(self.btnUpdate)
        self.btnExit = QtGui.QPushButton(self.centralwidget)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("icons/actions/exit_small.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnExit.setIcon(icon3)
        self.btnExit.setObjectName("btnExit")
        self.verticalLayout.addWidget(self.btnExit)
        Updater.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(Updater)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 175, 21))
        self.menubar.setObjectName("menubar")
        Updater.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(Updater)
        self.statusbar.setObjectName("statusbar")
        Updater.setStatusBar(self.statusbar)

        self.retranslateUi(Updater)
        QtCore.QMetaObject.connectSlotsByName(Updater)

    def retranslateUi(self, Updater):
        Updater.setWindowTitle(QtGui.QApplication.translate("Updater", "ViUR Admin Updater", None, QtGui.QApplication.UnicodeUTF8))
        self.btnCheck.setText(QtGui.QApplication.translate("Updater", "Check for Updates", None, QtGui.QApplication.UnicodeUTF8))
        self.btnUpdate.setText(QtGui.QApplication.translate("Updater", "Update now", None, QtGui.QApplication.UnicodeUTF8))
        self.btnExit.setText(QtGui.QApplication.translate("Updater", "Exit", None, QtGui.QApplication.UnicodeUTF8))

