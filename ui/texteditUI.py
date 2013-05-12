# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'textedit.ui'
#
# Created: Sat May 11 13:50:57 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_textEditWindow(object):
    def setupUi(self, textEditWindow):
        textEditWindow.setObjectName("textEditWindow")
        textEditWindow.resize(625, 475)
        self.centralwidget = QtGui.QWidget(textEditWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.textEdit = QtGui.QTextEdit(self.centralwidget)
        self.textEdit.setObjectName("textEdit")
        self.verticalLayout.addWidget(self.textEdit)
        self.btnSave = QtGui.QPushButton(self.centralwidget)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/actions/accept.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSave.setIcon(icon)
        self.btnSave.setObjectName("btnSave")
        self.verticalLayout.addWidget(self.btnSave)
        textEditWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(textEditWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 625, 22))
        self.menubar.setObjectName("menubar")
        textEditWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(textEditWindow)
        self.statusbar.setObjectName("statusbar")
        textEditWindow.setStatusBar(self.statusbar)

        self.retranslateUi(textEditWindow)
        QtCore.QMetaObject.connectSlotsByName(textEditWindow)

    def retranslateUi(self, textEditWindow):
        textEditWindow.setWindowTitle(QtGui.QApplication.translate("textEditWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSave.setText(QtGui.QApplication.translate("textEditWindow", "Apply", None, QtGui.QApplication.UnicodeUTF8))

