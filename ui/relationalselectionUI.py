# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'relationalselection.ui'
#
# Created: Mon Jul 22 11:57:37 2013
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

class Ui_relationalSelector(object):
    def setupUi(self, relationalSelector):
        relationalSelector.setObjectName(_fromUtf8("relationalSelector"))
        relationalSelector.resize(857, 612)
        self.verticalLayout_3 = QtGui.QVBoxLayout(relationalSelector)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.scrollArea = QtGui.QScrollArea(relationalSelector)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName(_fromUtf8("scrollArea"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 843, 598))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.tableWidget = QtGui.QWidget(self.scrollAreaWidgetContents)
        self.tableWidget.setObjectName(_fromUtf8("tableWidget"))
        self.horizontalLayout.addWidget(self.tableWidget)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.lblSelected = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.lblSelected.setObjectName(_fromUtf8("lblSelected"))
        self.verticalLayout.addWidget(self.lblSelected)
        self.listSelected = QtGui.QWidget(self.scrollAreaWidgetContents)
        self.listSelected.setObjectName(_fromUtf8("listSelected"))
        self.verticalLayout.addWidget(self.listSelected)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.btnCancel = QtGui.QPushButton(self.scrollAreaWidgetContents)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/cancel_small.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnCancel.setIcon(icon)
        self.btnCancel.setObjectName(_fromUtf8("btnCancel"))
        self.horizontalLayout_2.addWidget(self.btnCancel)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.btnSelect = QtGui.QPushButton(self.scrollAreaWidgetContents)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/accept.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSelect.setIcon(icon1)
        self.btnSelect.setObjectName(_fromUtf8("btnSelect"))
        self.horizontalLayout_2.addWidget(self.btnSelect)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_3.addWidget(self.scrollArea)

        self.retranslateUi(relationalSelector)
        QtCore.QMetaObject.connectSlotsByName(relationalSelector)

    def retranslateUi(self, relationalSelector):
        relationalSelector.setWindowTitle(_translate("relationalSelector", "Form", None))
        self.lblSelected.setText(_translate("relationalSelector", "Selected:", None))
        self.btnCancel.setText(_translate("relationalSelector", "Abort", None))
        self.btnSelect.setText(_translate("relationalSelector", "Apply", None))

