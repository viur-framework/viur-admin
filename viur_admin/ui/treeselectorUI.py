# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'treeselector.ui'
#
# Created by: PyQt5 UI code generator 5.13.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_TreeSelector(object):
    def setupUi(self, TreeSelector):
        TreeSelector.setObjectName("TreeSelector")
        TreeSelector.resize(597, 640)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":icons/windowicon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        TreeSelector.setWindowIcon(icon)
        self.verticalLayout = QtWidgets.QVBoxLayout(TreeSelector)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.scrollArea = QtWidgets.QScrollArea(TreeSelector)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 595, 638))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.listWidget = QtWidgets.QWidget(self.scrollAreaWidgetContents)
        self.listWidget.setObjectName("listWidget")
        self.verticalLayout_2.addWidget(self.listWidget)
        self.btnAddSelected = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.btnAddSelected.setObjectName("btnAddSelected")
        self.verticalLayout_2.addWidget(self.btnAddSelected)
        self.lblSelected = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.lblSelected.setObjectName("lblSelected")
        self.verticalLayout_2.addWidget(self.lblSelected)
        self.listSelected = QtWidgets.QWidget(self.scrollAreaWidgetContents)
        self.listSelected.setObjectName("listSelected")
        self.verticalLayout_2.addWidget(self.listSelected)
        self.btnSelect = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":icons/actions/relationalselect.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSelect.setIcon(icon1)
        self.btnSelect.setObjectName("btnSelect")
        self.verticalLayout_2.addWidget(self.btnSelect)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)

        self.retranslateUi(TreeSelector)
        QtCore.QMetaObject.connectSlotsByName(TreeSelector)

    def retranslateUi(self, TreeSelector):
        _translate = QtCore.QCoreApplication.translate
        TreeSelector.setWindowTitle(_translate("TreeSelector", "File selection"))
        self.btnAddSelected.setText(_translate("TreeSelector", "Add to selected"))
        self.lblSelected.setText(_translate("TreeSelector", "Selected:"))
        self.btnSelect.setText(_translate("TreeSelector", "Apply"))
import viur_admin.ui.icons_rc
