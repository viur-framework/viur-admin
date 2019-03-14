# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'task.ui'
#
# Created by: PyQt5 UI code generator 5.12.dev1812231618
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Task(object):
    def setupUi(self, Task):
        Task.setObjectName("Task")
        Task.resize(554, 300)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Task)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.listWidget = QtWidgets.QListWidget(Task)
        self.listWidget.setObjectName("listWidget")
        self.horizontalLayout.addWidget(self.listWidget)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.lblName = QtWidgets.QLabel(Task)
        self.lblName.setObjectName("lblName")
        self.verticalLayout.addWidget(self.lblName)
        self.lblDescr = QtWidgets.QTextBrowser(Task)
        self.lblDescr.setObjectName("lblDescr")
        self.verticalLayout.addWidget(self.lblDescr)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.btnExecute = QtWidgets.QPushButton(Task)
        self.btnExecute.setObjectName("btnExecute")
        self.verticalLayout.addWidget(self.btnExecute)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.retranslateUi(Task)
        QtCore.QMetaObject.connectSlotsByName(Task)

    def retranslateUi(self, Task):
        _translate = QtCore.QCoreApplication.translate
        Task.setWindowTitle(_translate("Task", "Form"))
        self.lblName.setText(_translate("Task", "TextLabel"))
        self.btnExecute.setText(_translate("Task", "Execute"))

