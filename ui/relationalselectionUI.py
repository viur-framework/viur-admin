# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'relationalselection.ui'
#
# Created: Wed Jan 23 10:47:03 2013
#      by: PySide UI code generator 4.9.6
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

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
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 843, 567))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.tableWidget = QtGui.QWidget(self.scrollAreaWidgetContents)
        self.tableWidget.setObjectName(_fromUtf8("tableWidget"))
        self.verticalLayout_2.addWidget(self.tableWidget)
        self.lblSelected = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.lblSelected.setObjectName(_fromUtf8("lblSelected"))
        self.verticalLayout_2.addWidget(self.lblSelected)
        self.listSelected = QtGui.QWidget(self.scrollAreaWidgetContents)
        self.listSelected.setObjectName(_fromUtf8("listSelected"))
        self.verticalLayout_2.addWidget(self.listSelected)
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
        relationalSelector.setWindowTitle(_translate("relationalSelector", "Form", None))
        self.editSearch.setText(_translate("relationalSelector", "Search", None))
        self.btnSearch.setText(_translate("relationalSelector", "Search", None))
        self.lblSelected.setText(_translate("relationalSelector", "Selected:", None))
        self.btnCancel.setText(_translate("relationalSelector", "Abort", None))
        self.btnSelect.setText(_translate("relationalSelector", "Save", None))

