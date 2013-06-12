# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'hierarchySelector.ui'
#
# Created: Tue Jun 11 11:38:15 2013
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

class Ui_HierarchySelector(object):
    def setupUi(self, HierarchySelector):
        HierarchySelector.setObjectName(_fromUtf8("HierarchySelector"))
        HierarchySelector.resize(1041, 599)
        self.verticalLayout = QtGui.QVBoxLayout(HierarchySelector)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.hierarchyWidget = QtGui.QWidget(HierarchySelector)
        self.hierarchyWidget.setObjectName(_fromUtf8("hierarchyWidget"))
        self.verticalLayout.addWidget(self.hierarchyWidget)
        self.lblSelected = QtGui.QLabel(HierarchySelector)
        self.lblSelected.setObjectName(_fromUtf8("lblSelected"))
        self.verticalLayout.addWidget(self.lblSelected)
        self.listSelected = QtGui.QWidget(HierarchySelector)
        self.listSelected.setObjectName(_fromUtf8("listSelected"))
        self.verticalLayout.addWidget(self.listSelected)
        self.btnSelect = QtGui.QPushButton(HierarchySelector)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/relationalselect.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSelect.setIcon(icon)
        self.btnSelect.setObjectName(_fromUtf8("btnSelect"))
        self.verticalLayout.addWidget(self.btnSelect)

        self.retranslateUi(HierarchySelector)
        QtCore.QMetaObject.connectSlotsByName(HierarchySelector)

    def retranslateUi(self, HierarchySelector):
        HierarchySelector.setWindowTitle(_translate("HierarchySelector", "Form", None))
        self.lblSelected.setText(_translate("HierarchySelector", "Selected:", None))
        self.btnSelect.setText(_translate("HierarchySelector", "Apply", None))

