# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'list.ui'
#
# Created: Tue Dec  4 11:44:06 2012
#      by: PyQt4 UI code generator 4.8.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_List(object):
    def setupUi(self, List):
        List.setObjectName(_fromUtf8("List"))
        List.resize(690, 525)
        List.setWindowTitle(QtGui.QApplication.translate("List", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.verticalLayout = QtGui.QVBoxLayout(List)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.boxActions = QtGui.QHBoxLayout()
        self.boxActions.setObjectName(_fromUtf8("boxActions"))
        self.verticalLayout.addLayout(self.boxActions)
        self.tableView = QtGui.QTableView(List)
        self.tableView.setAlternatingRowColors(True)
        self.tableView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableView.setSortingEnabled(True)
        self.tableView.setObjectName(_fromUtf8("tableView"))
        self.verticalLayout.addWidget(self.tableView)
        self.layoutToolBar = QtGui.QHBoxLayout()
        self.layoutToolBar.setObjectName(_fromUtf8("layoutToolBar"))
        self.editSearch = QtGui.QLineEdit(List)
        self.editSearch.setMinimumSize(QtCore.QSize(0, 32))
        self.editSearch.setText(QtGui.QApplication.translate("List", "Search", None, QtGui.QApplication.UnicodeUTF8))
        self.editSearch.setObjectName(_fromUtf8("editSearch"))
        self.layoutToolBar.addWidget(self.editSearch)
        self.searchBTN = QtGui.QPushButton(List)
        self.searchBTN.setText(QtGui.QApplication.translate("List", "Search", None, QtGui.QApplication.UnicodeUTF8))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/search_small.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.searchBTN.setIcon(icon)
        self.searchBTN.setObjectName(_fromUtf8("searchBTN"))
        self.layoutToolBar.addWidget(self.searchBTN)
        self.verticalLayout.addLayout(self.layoutToolBar)

        self.retranslateUi(List)
        QtCore.QMetaObject.connectSlotsByName(List)

    def retranslateUi(self, List):
        pass

