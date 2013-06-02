# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'relationalselection.ui'
#
# Created: Sun Jun  2 00:28:25 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_relationalSelector(object):
    def setupUi(self, relationalSelector):
        relationalSelector.setObjectName("relationalSelector")
        relationalSelector.resize(857, 612)
        self.verticalLayout = QtGui.QVBoxLayout(relationalSelector)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.editSearch = QtGui.QLineEdit(relationalSelector)
        self.editSearch.setObjectName("editSearch")
        self.horizontalLayout.addWidget(self.editSearch)
        self.btnSearch = QtGui.QPushButton(relationalSelector)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/actions/search.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSearch.setIcon(icon)
        self.btnSearch.setObjectName("btnSearch")
        self.horizontalLayout.addWidget(self.btnSearch)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.scrollArea = QtGui.QScrollArea(relationalSelector)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 843, 567))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.tableWidget = QtGui.QWidget(self.scrollAreaWidgetContents)
        self.tableWidget.setObjectName("tableWidget")
        self.verticalLayout_2.addWidget(self.tableWidget)
        self.lblSelected = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.lblSelected.setObjectName("lblSelected")
        self.verticalLayout_2.addWidget(self.lblSelected)
        self.listSelected = QtGui.QWidget(self.scrollAreaWidgetContents)
        self.listSelected.setObjectName("listSelected")
        self.verticalLayout_2.addWidget(self.listSelected)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.btnCancel = QtGui.QPushButton(self.scrollAreaWidgetContents)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("icons/actions/delete.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnCancel.setIcon(icon1)
        self.btnCancel.setObjectName("btnCancel")
        self.horizontalLayout_2.addWidget(self.btnCancel)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.btnSelect = QtGui.QPushButton(self.scrollAreaWidgetContents)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("icons/actions/accept.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSelect.setIcon(icon2)
        self.btnSelect.setObjectName("btnSelect")
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
        self.btnSelect.setText(QtGui.QApplication.translate("relationalSelector", "Apply", None, QtGui.QApplication.UnicodeUTF8))

