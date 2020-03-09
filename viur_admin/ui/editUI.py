# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'edit.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Edit(object):
    def setupUi(self, Edit):
        Edit.setObjectName("Edit")
        Edit.resize(820, 621)
        self.verticalLayout = QtWidgets.QVBoxLayout(Edit)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(Edit)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setObjectName("tabWidget")
        self.verticalLayout.addWidget(self.tabWidget)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.btnReset = QtWidgets.QPushButton(Edit)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/actions/undo.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnReset.setIcon(icon)
        self.btnReset.setObjectName("btnReset")
        self.horizontalLayout_2.addWidget(self.btnReset)
        self.btnClose = QtWidgets.QPushButton(Edit)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/actions/cancel.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnClose.setIcon(icon1)
        self.btnClose.setObjectName("btnClose")
        self.horizontalLayout_2.addWidget(self.btnClose)
        spacerItem = QtWidgets.QSpacerItem(254, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.btnSaveClose = QtWidgets.QPushButton(Edit)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/actions/save_new.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSaveClose.setIcon(icon2)
        self.btnSaveClose.setObjectName("btnSaveClose")
        self.horizontalLayout_2.addWidget(self.btnSaveClose)
        self.btnSaveContinue = QtWidgets.QPushButton(Edit)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/icons/actions/save_continue.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSaveContinue.setIcon(icon3)
        self.btnSaveContinue.setObjectName("btnSaveContinue")
        self.horizontalLayout_2.addWidget(self.btnSaveContinue)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(Edit)
        self.tabWidget.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(Edit)

    def retranslateUi(self, Edit):
        _translate = QtCore.QCoreApplication.translate
        Edit.setWindowTitle(_translate("Edit", "Form"))
        self.btnReset.setText(_translate("Edit", "Reset"))
        self.btnClose.setText(_translate("Edit", "Close"))
        self.btnSaveClose.setText(_translate("Edit", "Save and close"))
        self.btnSaveContinue.setText(_translate("Edit", "Save and continue"))


import viur_admin.ui.icons_rc
