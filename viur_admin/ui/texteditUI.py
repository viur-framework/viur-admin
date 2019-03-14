# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'textedit.ui'
#
# Created by: PyQt5 UI code generator 5.12.dev1812231618
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_textEditWindow(object):
    def setupUi(self, textEditWindow):
        textEditWindow.setObjectName("textEditWindow")
        textEditWindow.resize(625, 475)
        self.centralwidget = QtWidgets.QWidget(textEditWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.textEdit = QtWidgets.QTextEdit(self.centralwidget)
        self.textEdit.setObjectName("textEdit")
        self.verticalLayout.addWidget(self.textEdit)
        self.btnSave = QtWidgets.QPushButton(self.centralwidget)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":icons/actions/accept.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSave.setIcon(icon)
        self.btnSave.setObjectName("btnSave")
        self.verticalLayout.addWidget(self.btnSave)
        textEditWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(textEditWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 625, 22))
        self.menubar.setObjectName("menubar")
        textEditWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(textEditWindow)
        self.statusbar.setObjectName("statusbar")
        textEditWindow.setStatusBar(self.statusbar)

        self.retranslateUi(textEditWindow)
        QtCore.QMetaObject.connectSlotsByName(textEditWindow)

    def retranslateUi(self, textEditWindow):
        _translate = QtCore.QCoreApplication.translate
        textEditWindow.setWindowTitle(_translate("textEditWindow", "MainWindow"))
        self.btnSave.setText(_translate("textEditWindow", "Apply"))

import viur_admin.ui.icons_rc
