# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'authuserpassword.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_AuthUserPassword(object):
    def setupUi(self, AuthUserPassword):
        AuthUserPassword.setObjectName("AuthUserPassword")
        AuthUserPassword.resize(400, 300)
        self.formLayout = QtWidgets.QFormLayout(AuthUserPassword)
        self.formLayout.setObjectName("formLayout")
        self.lblUsername = QtWidgets.QLabel(AuthUserPassword)
        self.lblUsername.setObjectName("lblUsername")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.lblUsername)
        self.lblPassword = QtWidgets.QLabel(AuthUserPassword)
        self.lblPassword.setObjectName("lblPassword")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.lblPassword)
        self.editUsername = QtWidgets.QLineEdit(AuthUserPassword)
        self.editUsername.setText("")
        self.editUsername.setObjectName("editUsername")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.editUsername)
        self.editPassword = QtWidgets.QLineEdit(AuthUserPassword)
        self.editPassword.setText("")
        self.editPassword.setObjectName("editPassword")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.editPassword)
        self.cbSavePassword = QtWidgets.QCheckBox(AuthUserPassword)
        self.cbSavePassword.setObjectName("cbSavePassword")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.cbSavePassword)

        self.retranslateUi(AuthUserPassword)
        QtCore.QMetaObject.connectSlotsByName(AuthUserPassword)

    def retranslateUi(self, AuthUserPassword):
        _translate = QtCore.QCoreApplication.translate
        AuthUserPassword.setWindowTitle(_translate("AuthUserPassword", "Form"))
        self.lblUsername.setText(_translate("AuthUserPassword", "Username"))
        self.lblPassword.setText(_translate("AuthUserPassword", "Password"))
        self.cbSavePassword.setText(_translate("AuthUserPassword", "Save Password?"))
