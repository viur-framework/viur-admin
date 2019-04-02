# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'list.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_List(object):
    def setupUi(self, List):
        List.setObjectName("List")
        List.resize(771, 525)
        self.verticalLayout = QtWidgets.QVBoxLayout(List)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.boxActions = QtWidgets.QHBoxLayout()
        self.boxActions.setContentsMargins(0, 0, 0, 0)
        self.boxActions.setObjectName("boxActions")
        self.verticalLayout.addLayout(self.boxActions)
        self.layoutToolBar = QtWidgets.QHBoxLayout()
        self.layoutToolBar.setObjectName("layoutToolBar")
        self.editSearch = QtWidgets.QLineEdit(List)
        self.editSearch.setMinimumSize(QtCore.QSize(0, 32))
        self.editSearch.setText("")
        self.editSearch.setObjectName("editSearch")
        self.layoutToolBar.addWidget(self.editSearch)
        self.btnPrefixSearch = QtWidgets.QPushButton(List)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":icons/actions/search.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnPrefixSearch.setIcon(icon)
        self.btnPrefixSearch.setObjectName("btnPrefixSearch")
        self.layoutToolBar.addWidget(self.btnPrefixSearch)
        self.searchBTN = QtWidgets.QPushButton(List)
        self.searchBTN.setMinimumSize(QtCore.QSize(0, 32))
        self.searchBTN.setIcon(icon)
        self.searchBTN.setObjectName("searchBTN")
        self.layoutToolBar.addWidget(self.searchBTN)
        self.verticalLayout.addLayout(self.layoutToolBar)
        self.tableWidget = QtWidgets.QWidget(List)
        self.tableWidget.setObjectName("tableWidget")
        self.verticalLayout.addWidget(self.tableWidget)

        self.retranslateUi(List)
        QtCore.QMetaObject.connectSlotsByName(List)

    def retranslateUi(self, List):
        _translate = QtCore.QCoreApplication.translate
        List.setWindowTitle(_translate("List", "Form"))
        self.editSearch.setPlaceholderText(_translate("List", "Search"))
        self.btnPrefixSearch.setText(_translate("List", "Prefix search"))
        self.searchBTN.setText(_translate("List", "Fulltext search"))


import viur_admin.ui.icons_rc
