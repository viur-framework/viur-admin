# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\relationalselection.ui'
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

class Ui_relationalSelector(object):
    def setupUi(self, relationalSelector):
        relationalSelector.setObjectName(_fromUtf8("relationalSelector"))
        relationalSelector.resize(857, 612)
        self.verticalLayout = QtGui.QVBoxLayout(relationalSelector)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.editSearch = QtGui.QLineEdit(relationalSelector)
        self.editSearch.setObjectName(_fromUtf8("editSearch"))
        self.horizontalLayout.addWidget(self.editSearch)
        self.btnSearch = QtGui.QPushButton(relationalSelector)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/search.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSearch.setIcon(icon)
        self.btnSearch.setObjectName(_fromUtf8("btnSearch"))
        self.horizontalLayout.addWidget(self.btnSearch)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.scrollArea = QtGui.QScrollArea(relationalSelector)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName(_fromUtf8("scrollArea"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 831, 542))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.tableView = QtGui.QTableView(self.scrollAreaWidgetContents)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableView.sizePolicy().hasHeightForWidth())
        self.tableView.setSizePolicy(sizePolicy)
        self.tableView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableView.setSortingEnabled(True)
        self.tableView.setObjectName(_fromUtf8("tableView"))
        self.verticalLayout_2.addWidget(self.tableView)
        self.lblSelected = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.lblSelected.setObjectName(_fromUtf8("lblSelected"))
        self.verticalLayout_2.addWidget(self.lblSelected)
        self.tableSelected = QtGui.QTableView(self.scrollAreaWidgetContents)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableSelected.sizePolicy().hasHeightForWidth())
        self.tableSelected.setSizePolicy(sizePolicy)
        self.tableSelected.setSizeIncrement(QtCore.QSize(0, 0))
        self.tableSelected.setBaseSize(QtCore.QSize(0, 0))
        self.tableSelected.setObjectName(_fromUtf8("tableSelected"))
        self.verticalLayout_2.addWidget(self.tableSelected)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.btnCancel = QtGui.QPushButton(self.scrollAreaWidgetContents)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/delete.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnCancel.setIcon(icon1)
        self.btnCancel.setObjectName(_fromUtf8("btnCancel"))
        self.horizontalLayout_2.addWidget(self.btnCancel)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.btnSelect = QtGui.QPushButton(self.scrollAreaWidgetContents)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/save.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSelect.setIcon(icon2)
        self.btnSelect.setObjectName(_fromUtf8("btnSelect"))
        self.horizontalLayout_2.addWidget(self.btnSelect)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)

        self.retranslateUi(relationalSelector)
        QtCore.QMetaObject.connectSlotsByName(relationalSelector)

    def retranslateUi(self, relationalSelector):
        relationalSelector.setWindowTitle(QtGui.QApplication.translate("relationalSelector", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.editSearch.setText(QtGui.QApplication.translate("relationalSelector", "Search", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSearch.setText(QtGui.QApplication.translate("relationalSelector", "Search", None, QtGui.QApplication.UnicodeUTF8))
        self.lblSelected.setText(QtGui.QApplication.translate("relationalSelector", "Selected:", None, QtGui.QApplication.UnicodeUTF8))
        self.btnCancel.setText(QtGui.QApplication.translate("relationalSelector", "Abort", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSelect.setText(QtGui.QApplication.translate("relationalSelector", "Save", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    relationalSelector = QtGui.QWidget()
    ui = Ui_relationalSelector()
    ui.setupUi(relationalSelector)
    relationalSelector.show()
    sys.exit(app.exec_())

