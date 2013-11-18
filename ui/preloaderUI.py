# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'preloader.ui'
#
# Created: Wed Jun 12 17:05:02 2013
#      by: PyQt4 UI code generator 4.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Preloader(object):
    def setupUi(self, Preloader):
        Preloader.setObjectName(_fromUtf8("Preloader"))
        Preloader.resize(525, 426)
        self.verticalLayout = QtGui.QVBoxLayout(Preloader)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(Preloader)
        self.label.setText(_fromUtf8(""))
        self.label.setPixmap(QtGui.QPixmap(_fromUtf8("icons/login.png")))
        self.label.setScaledContents(True)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.progressBar = QtGui.QProgressBar(Preloader)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.verticalLayout.addWidget(self.progressBar)

        self.retranslateUi(Preloader)
        QtCore.QMetaObject.connectSlotsByName(Preloader)

    def retranslateUi(self, Preloader):
        Preloader.setWindowTitle(_translate("Preloader", "Loading...", None))

