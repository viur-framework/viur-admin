# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'rawtextedit.ui'
#
# Created: Sat May 11 13:50:25 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_rawTextEditWindow(object):
    def setupUi(self, rawTextEditWindow):
        rawTextEditWindow.setObjectName("rawTextEditWindow")
        rawTextEditWindow.resize(625, 475)
        self.centralwidget = QtGui.QWidget(rawTextEditWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.textEdit = QsciScintilla(self.centralwidget)
        self.textEdit.setObjectName("textEdit")
        self.verticalLayout.addWidget(self.textEdit)
        self.btnSave = QtGui.QPushButton(self.centralwidget)
        self.btnSave.setObjectName("btnSave")
        self.verticalLayout.addWidget(self.btnSave)
        rawTextEditWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(rawTextEditWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 625, 22))
        self.menubar.setObjectName("menubar")
        rawTextEditWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(rawTextEditWindow)
        self.statusbar.setObjectName("statusbar")
        rawTextEditWindow.setStatusBar(self.statusbar)

        self.retranslateUi(rawTextEditWindow)
        QtCore.QMetaObject.connectSlotsByName(rawTextEditWindow)

    def retranslateUi(self, rawTextEditWindow):
        rawTextEditWindow.setWindowTitle(QtGui.QApplication.translate("rawTextEditWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSave.setText(QtGui.QApplication.translate("rawTextEditWindow", "Apply", None, QtGui.QApplication.UnicodeUTF8))

from qsciscintilla import QsciScintilla
