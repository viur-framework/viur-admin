# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'rawtextedit.ui'
#
# Created: Wed Jun  5 17:46:16 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_rawTextEditWindow(object):
    def setupUi(self, rawTextEditWindow):
        rawTextEditWindow.setObjectName("rawTextEditWindow")
        rawTextEditWindow.resize(400, 300)
        self.verticalLayout = QtGui.QVBoxLayout(rawTextEditWindow)
        self.verticalLayout.setObjectName("verticalLayout")
        self.textEdit = QtGui.QTextEdit(rawTextEditWindow)
        self.textEdit.setObjectName("textEdit")
        self.verticalLayout.addWidget(self.textEdit)
        self.btnSave = QtGui.QPushButton(rawTextEditWindow)
        self.btnSave.setObjectName("btnSave")
        self.verticalLayout.addWidget(self.btnSave)

        self.retranslateUi(rawTextEditWindow)
        QtCore.QMetaObject.connectSlotsByName(rawTextEditWindow)

    def retranslateUi(self, rawTextEditWindow):
        rawTextEditWindow.setWindowTitle(QtGui.QApplication.translate("rawTextEditWindow", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSave.setText(QtGui.QApplication.translate("rawTextEditWindow", "Apply", None, QtGui.QApplication.UnicodeUTF8))

