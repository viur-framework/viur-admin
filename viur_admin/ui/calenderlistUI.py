# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'calenderlist.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_List(object):
    def setupUi(self, List):
        List.setObjectName("List")
        List.resize(690, 525)
        self.verticalLayout = QtWidgets.QVBoxLayout(List)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.boxActions = QtWidgets.QHBoxLayout()
        self.boxActions.setObjectName("boxActions")
        self.verticalLayout.addLayout(self.boxActions)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.editSearch = QtWidgets.QLineEdit(List)
        self.editSearch.setObjectName("editSearch")
        self.horizontalLayout_2.addWidget(self.editSearch)
        self.searchBTN = QtWidgets.QPushButton(List)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":icons/actions/search.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.searchBTN.setIcon(icon)
        self.searchBTN.setObjectName("searchBTN")
        self.horizontalLayout_2.addWidget(self.searchBTN)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.cbFilterType = QtWidgets.QComboBox(List)
        self.cbFilterType.setObjectName("cbFilterType")
        self.horizontalLayout.addWidget(self.cbFilterType)
        self.line = QtWidgets.QFrame(List)
        self.line.setFrameShape(QtWidgets.QFrame.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.horizontalLayout.addWidget(self.line)
        self.deFilter = QtWidgets.QDateEdit(List)
        self.deFilter.setCurrentSection(QtWidgets.QDateTimeEdit.DaySection)
        self.deFilter.setCalendarPopup(False)
        self.deFilter.setObjectName("deFilter")
        self.horizontalLayout.addWidget(self.deFilter)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.tableView = QtWidgets.QTableView(List)
        self.tableView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tableView.setSortingEnabled(True)
        self.tableView.setObjectName("tableView")
        self.verticalLayout.addWidget(self.tableView)

        self.retranslateUi(List)
        QtCore.QMetaObject.connectSlotsByName(List)

    def retranslateUi(self, List):
        _translate = QtCore.QCoreApplication.translate
        List.setWindowTitle(_translate("List", "Form"))
        self.editSearch.setText(_translate("List", "Search"))
        self.searchBTN.setText(_translate("List", "Search"))
        self.deFilter.setDisplayFormat(_translate("List", "dd.MM.yyyy"))

import viur_admin.ui.icons_rc
