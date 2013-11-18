# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'calenderlist.ui'
#
# Created: Tue Jun 11 11:36:38 2013
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
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.editSearch = QtGui.QLineEdit(List)
        self.editSearch.setObjectName(_fromUtf8("editSearch"))
        self.horizontalLayout_2.addWidget(self.editSearch)
        self.searchBTN = QtGui.QPushButton(List)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/search.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.searchBTN.setIcon(icon)
        self.searchBTN.setObjectName(_fromUtf8("searchBTN"))
        self.horizontalLayout_2.addWidget(self.searchBTN)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.cbFilterType = QtGui.QComboBox(List)
        self.cbFilterType.setObjectName(_fromUtf8("cbFilterType"))
        self.horizontalLayout.addWidget(self.cbFilterType)
        self.line = QtGui.QFrame(List)
        self.line.setFrameShape(QtGui.QFrame.VLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.horizontalLayout.addWidget(self.line)
        self.deFilter = QtGui.QDateEdit(List)
        self.deFilter.setCurrentSection(QtGui.QDateTimeEdit.DaySection)
        self.deFilter.setCalendarPopup(False)
        self.deFilter.setObjectName(_fromUtf8("deFilter"))
        self.horizontalLayout.addWidget(self.deFilter)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.tableView = QtGui.QTableView(List)
        self.tableView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableView.setSortingEnabled(True)
        self.tableView.setObjectName(_fromUtf8("tableView"))
        self.verticalLayout.addWidget(self.tableView)

        self.retranslateUi(List)
        QtCore.QMetaObject.connectSlotsByName(List)

    def retranslateUi(self, List):
        List.setWindowTitle(_translate("List", "Form", None))
        self.editSearch.setText(_translate("List", "Search", None))
        self.searchBTN.setText(_translate("List", "Search", None))
        self.deFilter.setDisplayFormat(_translate("List", "dd.MM.yyyy", None))

