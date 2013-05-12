# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'calenderlist.ui'
#
# Created: Sat May 11 13:48:42 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_List(object):
    def setupUi(self, List):
        List.setObjectName("List")
        List.resize(690, 525)
        self.verticalLayout = QtGui.QVBoxLayout(List)
        self.verticalLayout.setObjectName("verticalLayout")
        self.boxActions = QtGui.QHBoxLayout()
        self.boxActions.setObjectName("boxActions")
        self.verticalLayout.addLayout(self.boxActions)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.editSearch = QtGui.QLineEdit(List)
        self.editSearch.setObjectName("editSearch")
        self.horizontalLayout_2.addWidget(self.editSearch)
        self.searchBTN = QtGui.QPushButton(List)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/actions/search_small.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.searchBTN.setIcon(icon)
        self.searchBTN.setObjectName("searchBTN")
        self.horizontalLayout_2.addWidget(self.searchBTN)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.cbFilterType = QtGui.QComboBox(List)
        self.cbFilterType.setObjectName("cbFilterType")
        self.horizontalLayout.addWidget(self.cbFilterType)
        self.line = QtGui.QFrame(List)
        self.line.setFrameShape(QtGui.QFrame.VLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName("line")
        self.horizontalLayout.addWidget(self.line)
        self.deFilter = QtGui.QDateEdit(List)
        self.deFilter.setCurrentSection(QtGui.QDateTimeEdit.DaySection)
        self.deFilter.setCalendarPopup(False)
        self.deFilter.setObjectName("deFilter")
        self.horizontalLayout.addWidget(self.deFilter)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.tableView = QtGui.QTableView(List)
        self.tableView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableView.setSortingEnabled(True)
        self.tableView.setObjectName("tableView")
        self.verticalLayout.addWidget(self.tableView)

        self.retranslateUi(List)
        QtCore.QMetaObject.connectSlotsByName(List)

    def retranslateUi(self, List):
        List.setWindowTitle(QtGui.QApplication.translate("List", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.editSearch.setText(QtGui.QApplication.translate("List", "Search", None, QtGui.QApplication.UnicodeUTF8))
        self.searchBTN.setText(QtGui.QApplication.translate("List", "Search", None, QtGui.QApplication.UnicodeUTF8))
        self.deFilter.setDisplayFormat(QtGui.QApplication.translate("List", "dd.MM.yyyy", None, QtGui.QApplication.UnicodeUTF8))

