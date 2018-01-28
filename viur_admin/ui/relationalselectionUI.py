# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'relationalselection.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_relationalSelector(object):
    def setupUi(self, relationalSelector):
        relationalSelector.setObjectName("relationalSelector")
        relationalSelector.resize(857, 612)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(relationalSelector)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.scrollArea = QtWidgets.QScrollArea(relationalSelector)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 843, 598))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.tableWidget = QtWidgets.QWidget(self.scrollAreaWidgetContents)
        self.tableWidget.setObjectName("tableWidget")
        self.horizontalLayout.addWidget(self.tableWidget)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.lblSelected = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.lblSelected.setObjectName("lblSelected")
        self.verticalLayout.addWidget(self.lblSelected)
        self.listSelected = QtWidgets.QWidget(self.scrollAreaWidgetContents)
        self.listSelected.setObjectName("listSelected")
        self.verticalLayout.addWidget(self.listSelected)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.btnCancel = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":icons/actions/cancel_small.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnCancel.setIcon(icon)
        self.btnCancel.setObjectName("btnCancel")
        self.horizontalLayout_2.addWidget(self.btnCancel)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.btnSelect = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":icons/actions/accept.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSelect.setIcon(icon1)
        self.btnSelect.setObjectName("btnSelect")
        self.horizontalLayout_2.addWidget(self.btnSelect)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_3.addWidget(self.scrollArea)

        self.retranslateUi(relationalSelector)
        QtCore.QMetaObject.connectSlotsByName(relationalSelector)

    def retranslateUi(self, relationalSelector):
        _translate = QtCore.QCoreApplication.translate
        relationalSelector.setWindowTitle(_translate("relationalSelector", "Form"))
        self.lblSelected.setText(_translate("relationalSelector", "Selected:"))
        self.btnCancel.setText(_translate("relationalSelector", "Abort"))
        self.btnSelect.setText(_translate("relationalSelector", "Apply"))

import viur_admin.ui.icons_rc
