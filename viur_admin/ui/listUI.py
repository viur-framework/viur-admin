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
        List.resize(1018, 804)
        self.verticalLayout = QtWidgets.QVBoxLayout(List)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.boxActions = QtWidgets.QHBoxLayout()
        self.boxActions.setContentsMargins(0, 0, 0, 0)
        self.boxActions.setSpacing(0)
        self.boxActions.setObjectName("boxActions")
        self.verticalLayout.addLayout(self.boxActions)
        self.layoutToolBar = QtWidgets.QHBoxLayout()
        self.layoutToolBar.setSpacing(0)
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
        self.extendedSearchBTN = QtWidgets.QPushButton(List)
        self.extendedSearchBTN.setIcon(icon)
        self.extendedSearchBTN.setCheckable(True)
        self.extendedSearchBTN.setObjectName("extendedSearchBTN")
        self.layoutToolBar.addWidget(self.extendedSearchBTN)
        self.verticalLayout.addLayout(self.layoutToolBar)
        self.tableAreaLayout = QtWidgets.QHBoxLayout()
        self.tableAreaLayout.setObjectName("tableAreaLayout")
        self.tableWidget = QtWidgets.QWidget(List)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableWidget.sizePolicy().hasHeightForWidth())
        self.tableWidget.setSizePolicy(sizePolicy)
        self.tableWidget.setObjectName("tableWidget")
        self.tableAreaLayout.addWidget(self.tableWidget)
        self.extendedSearchArea = QtWidgets.QWidget(List)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.extendedSearchArea.sizePolicy().hasHeightForWidth())
        self.extendedSearchArea.setSizePolicy(sizePolicy)
        self.extendedSearchArea.setObjectName("extendedSearchArea")
        self.extendedSearchLayout = QtWidgets.QVBoxLayout(self.extendedSearchArea)
        self.extendedSearchLayout.setContentsMargins(0, 0, 0, 0)
        self.extendedSearchLayout.setSpacing(0)
        self.extendedSearchLayout.setObjectName("extendedSearchLayout")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.extendedSearchLayout.addItem(spacerItem)
        self.tableAreaLayout.addWidget(self.extendedSearchArea)
        self.verticalLayout.addLayout(self.tableAreaLayout)

        self.retranslateUi(List)
        QtCore.QMetaObject.connectSlotsByName(List)

    def retranslateUi(self, List):
        _translate = QtCore.QCoreApplication.translate
        List.setWindowTitle(_translate("List", "Form"))
        self.editSearch.setPlaceholderText(_translate("List", "Search"))
        self.btnPrefixSearch.setText(_translate("List", "Prefix search"))
        self.searchBTN.setText(_translate("List", "Fulltext search"))
        self.extendedSearchBTN.setText(_translate("List", "Extended Search"))


import viur_admin.ui.icons_rc
