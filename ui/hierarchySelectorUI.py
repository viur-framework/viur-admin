# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'hierarchySelector.ui'
#
# Created: Sat May 11 13:49:54 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_HierarchySelector(object):
    def setupUi(self, HierarchySelector):
        HierarchySelector.setObjectName("HierarchySelector")
        HierarchySelector.resize(1041, 599)
        self.verticalLayout = QtGui.QVBoxLayout(HierarchySelector)
        self.verticalLayout.setObjectName("verticalLayout")
        self.hierarchyWidget = QtGui.QWidget(HierarchySelector)
        self.hierarchyWidget.setObjectName("hierarchyWidget")
        self.verticalLayout.addWidget(self.hierarchyWidget)
        self.lblSelected = QtGui.QLabel(HierarchySelector)
        self.lblSelected.setObjectName("lblSelected")
        self.verticalLayout.addWidget(self.lblSelected)
        self.listSelected = QtGui.QWidget(HierarchySelector)
        self.listSelected.setObjectName("listSelected")
        self.verticalLayout.addWidget(self.listSelected)
        self.btnSelect = QtGui.QPushButton(HierarchySelector)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/actions/relationalselect.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSelect.setIcon(icon)
        self.btnSelect.setObjectName("btnSelect")
        self.verticalLayout.addWidget(self.btnSelect)

        self.retranslateUi(HierarchySelector)
        QtCore.QMetaObject.connectSlotsByName(HierarchySelector)

    def retranslateUi(self, HierarchySelector):
        HierarchySelector.setWindowTitle(QtGui.QApplication.translate("HierarchySelector", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.lblSelected.setText(QtGui.QApplication.translate("HierarchySelector", "Selected:", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSelect.setText(QtGui.QApplication.translate("HierarchySelector", "Apply", None, QtGui.QApplication.UnicodeUTF8))

