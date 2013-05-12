# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'list.ui'
#
# Created: Sat May 11 13:50:09 2013
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
        self.tableWidget = QtGui.QWidget(List)
        self.tableWidget.setObjectName("tableWidget")
        self.verticalLayout.addWidget(self.tableWidget)
        self.layoutToolBar = QtGui.QHBoxLayout()
        self.layoutToolBar.setObjectName("layoutToolBar")
        self.editSearch = QtGui.QLineEdit(List)
        self.editSearch.setMinimumSize(QtCore.QSize(0, 32))
        self.editSearch.setObjectName("editSearch")
        self.layoutToolBar.addWidget(self.editSearch)
        self.searchBTN = QtGui.QPushButton(List)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/actions/search_small.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.searchBTN.setIcon(icon)
        self.searchBTN.setObjectName("searchBTN")
        self.layoutToolBar.addWidget(self.searchBTN)
        self.verticalLayout.addLayout(self.layoutToolBar)

        self.retranslateUi(List)
        QtCore.QMetaObject.connectSlotsByName(List)

    def retranslateUi(self, List):
        List.setWindowTitle(QtGui.QApplication.translate("List", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.editSearch.setText(QtGui.QApplication.translate("List", "Search", None, QtGui.QApplication.UnicodeUTF8))
        self.searchBTN.setText(QtGui.QApplication.translate("List", "Search", None, QtGui.QApplication.UnicodeUTF8))

