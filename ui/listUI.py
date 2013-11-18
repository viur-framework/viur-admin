# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'list.ui'
#
# Created: Tue Oct 22 14:28:41 2013
#      by: PyQt4 UI code generator 4.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_List(object):
    def setupUi(self, List):
        List.setObjectName(_fromUtf8("List"))
        List.resize(771, 525)
        self.verticalLayout = QtGui.QVBoxLayout(List)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.boxActions = QtGui.QHBoxLayout()
        self.boxActions.setMargin(0)
        self.boxActions.setObjectName(_fromUtf8("boxActions"))
        self.verticalLayout.addLayout(self.boxActions)
        self.tableWidget = QtGui.QWidget(List)
        self.tableWidget.setObjectName(_fromUtf8("tableWidget"))
        self.verticalLayout.addWidget(self.tableWidget)
        self.layoutToolBar = QtGui.QHBoxLayout()
        self.layoutToolBar.setObjectName(_fromUtf8("layoutToolBar"))
        self.editSearch = QtGui.QLineEdit(List)
        self.editSearch.setMinimumSize(QtCore.QSize(0, 32))
        self.editSearch.setObjectName(_fromUtf8("editSearch"))
        self.layoutToolBar.addWidget(self.editSearch)
        self.btnPrefixSearch = QtGui.QPushButton(List)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/search.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnPrefixSearch.setIcon(icon)
        self.btnPrefixSearch.setObjectName(_fromUtf8("btnPrefixSearch"))
        self.layoutToolBar.addWidget(self.btnPrefixSearch)
        self.searchBTN = QtGui.QPushButton(List)
        self.searchBTN.setMinimumSize(QtCore.QSize(0, 32))
        self.searchBTN.setIcon(icon)
        self.searchBTN.setObjectName(_fromUtf8("searchBTN"))
        self.layoutToolBar.addWidget(self.searchBTN)
        self.verticalLayout.addLayout(self.layoutToolBar)

        self.retranslateUi(List)
        QtCore.QMetaObject.connectSlotsByName(List)

    def retranslateUi(self, List):
        List.setWindowTitle(_translate("List", "Form", None))
        self.editSearch.setText(_translate("List", "Search", None))
        self.btnPrefixSearch.setText(_translate("List", "Prefix search", None))
        self.searchBTN.setText(_translate("List", "Fulltext search", None))

