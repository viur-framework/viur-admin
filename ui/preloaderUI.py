# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'preloader.ui'
#
# Created: Sun Jun  2 02:39:41 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Preloader(object):
    def setupUi(self, Preloader):
        Preloader.setObjectName("Preloader")
        Preloader.resize(525, 426)
        self.verticalLayout = QtGui.QVBoxLayout(Preloader)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtGui.QLabel(Preloader)
        self.label.setText("")
        self.label.setPixmap(QtGui.QPixmap("icons/login.png"))
        self.label.setScaledContents(True)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.listWidget = QtGui.QListWidget(Preloader)
        self.listWidget.setMinimumSize(QtCore.QSize(0, 300))
        self.listWidget.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.listWidget.setIconSize(QtCore.QSize(64, 64))
        self.listWidget.setFlow(QtGui.QListView.LeftToRight)
        self.listWidget.setProperty("isWrapping", True)
        self.listWidget.setGridSize(QtCore.QSize(94, 94))
        self.listWidget.setViewMode(QtGui.QListView.IconMode)
        self.listWidget.setObjectName("listWidget")
        self.verticalLayout.addWidget(self.listWidget)

        self.retranslateUi(Preloader)
        QtCore.QMetaObject.connectSlotsByName(Preloader)

    def retranslateUi(self, Preloader):
        Preloader.setWindowTitle(QtGui.QApplication.translate("Preloader", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.listWidget.setSortingEnabled(True)

