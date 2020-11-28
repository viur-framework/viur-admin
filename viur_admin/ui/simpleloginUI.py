# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'simplelogin.ui'
#
# Created by: PyQt5 UI code generator 5.13.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_simpleLogin(object):
    def setupUi(self, simpleLogin):
        simpleLogin.setObjectName("simpleLogin")
        simpleLogin.resize(501, 319)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":icons/viup.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        simpleLogin.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(simpleLogin)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setObjectName("label_3")
        self.verticalLayout.addWidget(self.label_3)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.usernameEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.usernameEdit.setEchoMode(QtWidgets.QLineEdit.Normal)
        self.usernameEdit.setObjectName("usernameEdit")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.usernameEdit)
        self.passwordEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.passwordEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.passwordEdit.setObjectName("passwordEdit")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.passwordEdit)
        self.verticalLayout.addLayout(self.formLayout)
        self.loginBtn = QtWidgets.QPushButton(self.centralwidget)
        self.loginBtn.setObjectName("loginBtn")
        self.verticalLayout.addWidget(self.loginBtn)
        simpleLogin.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(simpleLogin)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 501, 29))
        self.menubar.setObjectName("menubar")
        simpleLogin.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(simpleLogin)
        self.statusbar.setObjectName("statusbar")
        simpleLogin.setStatusBar(self.statusbar)

        self.retranslateUi(simpleLogin)
        QtCore.QMetaObject.connectSlotsByName(simpleLogin)

    def retranslateUi(self, simpleLogin):
        _translate = QtCore.QCoreApplication.translate
        simpleLogin.setWindowTitle(_translate("simpleLogin", "ViUR Admin Updater"))
        self.label_3.setText(_translate("simpleLogin", "Login :)"))
        self.label.setText(_translate("simpleLogin", "Username"))
        self.label_2.setText(_translate("simpleLogin", "Password"))
        self.loginBtn.setText(_translate("simpleLogin", "Login"))
