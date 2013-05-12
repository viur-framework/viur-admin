# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'treeselector.ui'
#
# Created: Sat May 11 13:51:09 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_TreeSelector(object):
    def setupUi(self, TreeSelector):
        TreeSelector.setObjectName("TreeSelector")
        TreeSelector.resize(597, 640)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/windowicon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        TreeSelector.setWindowIcon(icon)
        self.verticalLayout = QtGui.QVBoxLayout(TreeSelector)
        self.verticalLayout.setObjectName("verticalLayout")
        self.scrollArea = QtGui.QScrollArea(TreeSelector)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 583, 626))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.listWidget = QtGui.QWidget(self.scrollAreaWidgetContents)
        self.listWidget.setObjectName("listWidget")
        self.verticalLayout_2.addWidget(self.listWidget)
        self.btnAddSelected = QtGui.QPushButton(self.scrollAreaWidgetContents)
        self.btnAddSelected.setObjectName("btnAddSelected")
        self.verticalLayout_2.addWidget(self.btnAddSelected)
        self.lblSelected = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.lblSelected.setObjectName("lblSelected")
        self.verticalLayout_2.addWidget(self.lblSelected)
        self.listSelected = QtGui.QWidget(self.scrollAreaWidgetContents)
        self.listSelected.setObjectName("listSelected")
        self.verticalLayout_2.addWidget(self.listSelected)
        self.btnSelect = QtGui.QPushButton(self.scrollAreaWidgetContents)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("icons/actions/relationalselect.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSelect.setIcon(icon1)
        self.btnSelect.setObjectName("btnSelect")
        self.verticalLayout_2.addWidget(self.btnSelect)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)

        self.retranslateUi(TreeSelector)
        QtCore.QMetaObject.connectSlotsByName(TreeSelector)

    def retranslateUi(self, TreeSelector):
        TreeSelector.setWindowTitle(QtGui.QApplication.translate("TreeSelector", "File selection", None, QtGui.QApplication.UnicodeUTF8))
        self.btnAddSelected.setText(QtGui.QApplication.translate("TreeSelector", "Add to selected", None, QtGui.QApplication.UnicodeUTF8))
        self.lblSelected.setText(QtGui.QApplication.translate("TreeSelector", "Selected:", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSelect.setText(QtGui.QApplication.translate("TreeSelector", "Apply", None, QtGui.QApplication.UnicodeUTF8))

