# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'list.ui'
#
# Created: Tue Jun 11 11:38:29 2013
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
        List.resize(690, 525)
        self.verticalLayout = QtGui.QVBoxLayout(List)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.boxActions = QtGui.QHBoxLayout()
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
        self.searchBTN = QtGui.QPushButton(List)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/search_small.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.searchBTN.setIcon(icon)
        self.searchBTN.setObjectName(_fromUtf8("searchBTN"))
        self.layoutToolBar.addWidget(self.searchBTN)
        self.verticalLayout.addLayout(self.layoutToolBar)

        self.retranslateUi(List)
        QtCore.QMetaObject.connectSlotsByName(List)

    def retranslateUi(self, List):
        List.setWindowTitle(_translate("List", "Form", None))
        self.editSearch.setText(_translate("List", "Search", None))
        self.searchBTN.setText(_translate("List", "Search", None))

