# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'textedit.ui'
#
# Created: Tue Jun 11 11:39:16 2013
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

class Ui_textEditWindow(object):
    def setupUi(self, textEditWindow):
        textEditWindow.setObjectName(_fromUtf8("textEditWindow"))
        textEditWindow.resize(625, 475)
        self.centralwidget = QtGui.QWidget(textEditWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.textEdit = QtGui.QTextEdit(self.centralwidget)
        self.textEdit.setObjectName(_fromUtf8("textEdit"))
        self.verticalLayout.addWidget(self.textEdit)
        self.btnSave = QtGui.QPushButton(self.centralwidget)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/accept.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSave.setIcon(icon)
        self.btnSave.setObjectName(_fromUtf8("btnSave"))
        self.verticalLayout.addWidget(self.btnSave)
        textEditWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(textEditWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 625, 22))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        textEditWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(textEditWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        textEditWindow.setStatusBar(self.statusbar)

        self.retranslateUi(textEditWindow)
        QtCore.QMetaObject.connectSlotsByName(textEditWindow)

    def retranslateUi(self, textEditWindow):
        textEditWindow.setWindowTitle(_translate("textEditWindow", "MainWindow", None))
        self.btnSave.setText(_translate("textEditWindow", "Apply", None))

