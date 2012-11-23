# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'updater.ui'
#
# Created: Mon Nov 19 15:33:33 2012
#      by: PyQt4 UI code generator 4.8.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Updater(object):
    def setupUi(self, Updater):
        Updater.setObjectName(_fromUtf8("Updater"))
        Updater.resize(175, 258)
        Updater.setWindowTitle(QtGui.QApplication.translate("Updater", "ViUR Admin Updater", None, QtGui.QApplication.UnicodeUTF8))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/viup.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Updater.setWindowIcon(icon)
        self.centralwidget = QtGui.QWidget(Updater)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setText(_fromUtf8(""))
        self.label.setPixmap(QtGui.QPixmap(_fromUtf8("icons/viur_logo.png")))
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.textLog = QtGui.QTextEdit(self.centralwidget)
        self.textLog.setReadOnly(True)
        self.textLog.setObjectName(_fromUtf8("textLog"))
        self.verticalLayout.addWidget(self.textLog)
        self.progressBar = QtGui.QProgressBar(self.centralwidget)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.verticalLayout.addWidget(self.progressBar)
        self.btnCheck = QtGui.QPushButton(self.centralwidget)
        self.btnCheck.setText(QtGui.QApplication.translate("Updater", "Check for Updates", None, QtGui.QApplication.UnicodeUTF8))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/search_small.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnCheck.setIcon(icon1)
        self.btnCheck.setObjectName(_fromUtf8("btnCheck"))
        self.verticalLayout.addWidget(self.btnCheck)
        self.btnUpdate = QtGui.QPushButton(self.centralwidget)
        self.btnUpdate.setText(QtGui.QApplication.translate("Updater", "Update now", None, QtGui.QApplication.UnicodeUTF8))
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/accept.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnUpdate.setIcon(icon2)
        self.btnUpdate.setObjectName(_fromUtf8("btnUpdate"))
        self.verticalLayout.addWidget(self.btnUpdate)
        self.btnExit = QtGui.QPushButton(self.centralwidget)
        self.btnExit.setText(QtGui.QApplication.translate("Updater", "Exit", None, QtGui.QApplication.UnicodeUTF8))
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/exit_small.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnExit.setIcon(icon3)
        self.btnExit.setObjectName(_fromUtf8("btnExit"))
        self.verticalLayout.addWidget(self.btnExit)
        Updater.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(Updater)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 175, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        Updater.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(Updater)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        Updater.setStatusBar(self.statusbar)

        self.retranslateUi(Updater)
        QtCore.QMetaObject.connectSlotsByName(Updater)

    def retranslateUi(self, Updater):
        pass

