# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'rawtextedit.ui'
#
# Created: Mon Nov 24 18:30:24 2014
# by: PyQt5 UI code generator 5.3.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtWidgets


class Ui_rawTextEditWindow(object):
    def setupUi(self, rawTextEditWindow):
        rawTextEditWindow.setObjectName("rawTextEditWindow")
        rawTextEditWindow.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(rawTextEditWindow)
        self.verticalLayout.setObjectName("verticalLayout")
        self.textEdit = QtWidgets.QTextEdit(rawTextEditWindow)
        self.textEdit.setObjectName("textEdit")
        self.verticalLayout.addWidget(self.textEdit)
        self.btnSave = QtWidgets.QPushButton(rawTextEditWindow)
        self.btnSave.setObjectName("btnSave")
        self.verticalLayout.addWidget(self.btnSave)

        self.retranslateUi(rawTextEditWindow)
        QtCore.QMetaObject.connectSlotsByName(rawTextEditWindow)

    def retranslateUi(self, rawTextEditWindow):
        _translate = QtCore.QCoreApplication.translate
        rawTextEditWindow.setWindowTitle(_translate("rawTextEditWindow", "Form"))
        self.btnSave.setText(_translate("rawTextEditWindow", "Apply"))
