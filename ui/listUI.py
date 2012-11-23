# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\list.ui'
#
# Created: Thu Nov 15 17:35:22 2012
#      by: PyQt4 UI code generator 4.8.4
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
        self.lineEdit = QtGui.QLineEdit(List)
        self.lineEdit.setMinimumSize(QtCore.QSize(0, 32))
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))
        self.layoutToolBar.addWidget(self.lineEdit)
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
        List.setWindowTitle(QtGui.QApplication.translate("List", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.lineEdit.setText(QtGui.QApplication.translate("List", "Search", None, QtGui.QApplication.UnicodeUTF8))
        self.searchBTN.setText(QtGui.QApplication.translate("List", "Search", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    List = QtGui.QWidget()
    ui = Ui_List()
    ui.setupUi(List)
    List.show()
    sys.exit(app.exec_())

