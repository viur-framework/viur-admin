# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\calenderlist.ui'
#
# Created: Mon Nov 26 19:34:47 2012
#      by: PyQt4 UI code generator 4.9.5
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
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.lineEdit = QtGui.QLineEdit(List)
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))
        self.horizontalLayout_2.addWidget(self.lineEdit)
        self.searchBTN = QtGui.QPushButton(List)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/search.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
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
        List.setWindowTitle(QtGui.QApplication.translate("List", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.lineEdit.setText(QtGui.QApplication.translate("List", "Search", None, QtGui.QApplication.UnicodeUTF8))
        self.searchBTN.setText(QtGui.QApplication.translate("List", "Search", None, QtGui.QApplication.UnicodeUTF8))
        self.deFilter.setDisplayFormat(QtGui.QApplication.translate("List", "dd.MM.yyyy", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    List = QtGui.QWidget()
    ui = Ui_List()
    ui.setupUi(List)
    List.show()
    sys.exit(app.exec_())

