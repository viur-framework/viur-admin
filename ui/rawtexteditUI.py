# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'rawtextedit.ui'
#
# Created: Tue Jun 11 11:38:52 2013
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

class Ui_rawTextEditWindow(object):
    def setupUi(self, rawTextEditWindow):
        rawTextEditWindow.setObjectName(_fromUtf8("rawTextEditWindow"))
        rawTextEditWindow.resize(400, 300)
        self.verticalLayout = QtGui.QVBoxLayout(rawTextEditWindow)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.textEdit = QtGui.QTextEdit(rawTextEditWindow)
        self.textEdit.setObjectName(_fromUtf8("textEdit"))
        self.verticalLayout.addWidget(self.textEdit)
        self.btnSave = QtGui.QPushButton(rawTextEditWindow)
        self.btnSave.setObjectName(_fromUtf8("btnSave"))
        self.verticalLayout.addWidget(self.btnSave)

        self.retranslateUi(rawTextEditWindow)
        QtCore.QMetaObject.connectSlotsByName(rawTextEditWindow)

    def retranslateUi(self, rawTextEditWindow):
        rawTextEditWindow.setWindowTitle(_translate("rawTextEditWindow", "Form", None))
        self.btnSave.setText(_translate("rawTextEditWindow", "Apply", None))

