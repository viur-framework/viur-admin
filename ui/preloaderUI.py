# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'preloader.ui'
#
# Created: Mon Nov 24 18:30:24 2014
# by: PyQt5 UI code generator 5.3.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Preloader(object):
    def setupUi(self, Preloader):
        Preloader.setObjectName("Preloader")
        Preloader.resize(525, 426)
        self.verticalLayout = QtWidgets.QVBoxLayout(Preloader)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(Preloader)
        self.label.setText("")
        self.label.setPixmap(QtGui.QPixmap("icons/login.png"))
        self.label.setScaledContents(True)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.progressBar = QtWidgets.QProgressBar(Preloader)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName("progressBar")
        self.verticalLayout.addWidget(self.progressBar)

        self.retranslateUi(Preloader)
        QtCore.QMetaObject.connectSlotsByName(Preloader)

    def retranslateUi(self, Preloader):
        _translate = QtCore.QCoreApplication.translate
        Preloader.setWindowTitle(_translate("Preloader", "Loading..."))

