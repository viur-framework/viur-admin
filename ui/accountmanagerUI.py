# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'accountmanager.ui'
#
# Created: Tue Jun 11 11:36:17 2013
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

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(480, 680)
        MainWindow.setMinimumSize(QtCore.QSize(480, 0))
        MainWindow.setMaximumSize(QtCore.QSize(480, 16777215))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/viur_logo.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.acclistWidget = QtGui.QListWidget(self.centralwidget)
        self.acclistWidget.setMinimumSize(QtCore.QSize(450, 250))
        self.acclistWidget.setObjectName(_fromUtf8("acclistWidget"))
        self.verticalLayout.addWidget(self.acclistWidget)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.addAccBTN = QtGui.QPushButton(self.centralwidget)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/add_white.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.addAccBTN.setIcon(icon1)
        self.addAccBTN.setObjectName(_fromUtf8("addAccBTN"))
        self.horizontalLayout_3.addWidget(self.addAccBTN)
        self.delAccBTN = QtGui.QPushButton(self.centralwidget)
        self.delAccBTN.setEnabled(False)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/delete_white.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.delAccBTN.setIcon(icon2)
        self.delAccBTN.setObjectName(_fromUtf8("delAccBTN"))
        self.horizontalLayout_3.addWidget(self.delAccBTN)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.label)
        self.editAccountName = QtGui.QLineEdit(self.centralwidget)
        self.editAccountName.setObjectName(_fromUtf8("editAccountName"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.editAccountName)
        self.label_2 = QtGui.QLabel(self.centralwidget)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout.setWidget(5, QtGui.QFormLayout.LabelRole, self.label_2)
        self.editUrl = QtGui.QLineEdit(self.centralwidget)
        self.editUrl.setObjectName(_fromUtf8("editUrl"))
        self.formLayout.setWidget(5, QtGui.QFormLayout.FieldRole, self.editUrl)
        self.label_5 = QtGui.QLabel(self.centralwidget)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.formLayout.setWidget(6, QtGui.QFormLayout.LabelRole, self.label_5)
        self.editUserName = QtGui.QLineEdit(self.centralwidget)
        self.editUserName.setObjectName(_fromUtf8("editUserName"))
        self.formLayout.setWidget(6, QtGui.QFormLayout.FieldRole, self.editUserName)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.formLayout.setLayout(10, QtGui.QFormLayout.FieldRole, self.horizontalLayout_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.formLayout.setLayout(16, QtGui.QFormLayout.LabelRole, self.horizontalLayout)
        self.editPassword = QtGui.QLineEdit(self.centralwidget)
        self.editPassword.setEnabled(True)
        self.editPassword.setEchoMode(QtGui.QLineEdit.Password)
        self.editPassword.setObjectName(_fromUtf8("editPassword"))
        self.formLayout.setWidget(7, QtGui.QFormLayout.FieldRole, self.editPassword)
        self.label_3 = QtGui.QLabel(self.centralwidget)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.formLayout.setWidget(7, QtGui.QFormLayout.LabelRole, self.label_3)
        self.accSavePWcheckBox = QtGui.QCheckBox(self.centralwidget)
        self.accSavePWcheckBox.setObjectName(_fromUtf8("accSavePWcheckBox"))
        self.formLayout.setWidget(8, QtGui.QFormLayout.FieldRole, self.accSavePWcheckBox)
        self.verticalLayout_2.addLayout(self.formLayout)
        self.verticalLayout_3 = QtGui.QVBoxLayout()
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.FinishedBTN = QtGui.QPushButton(self.centralwidget)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(_fromUtf8("icons/success_transparent.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.FinishedBTN.setIcon(icon3)
        self.FinishedBTN.setObjectName(_fromUtf8("FinishedBTN"))
        self.verticalLayout_3.addWidget(self.FinishedBTN)
        self.verticalLayout_2.addLayout(self.verticalLayout_3)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 480, 22))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "Viur Accountmanager", None))
        self.addAccBTN.setText(_translate("MainWindow", "New Account", None))
        self.delAccBTN.setText(_translate("MainWindow", "Delete Account", None))
        self.label.setText(_translate("MainWindow", "Account Name", None))
        self.label_2.setText(_translate("MainWindow", "Serveradress", None))
        self.label_5.setText(_translate("MainWindow", "Username", None))
        self.label_3.setText(_translate("MainWindow", "Userpassword", None))
        self.accSavePWcheckBox.setText(_translate("MainWindow", "Save Password", None))
        self.FinishedBTN.setText(_translate("MainWindow", "Back to Loginscreen", None))

