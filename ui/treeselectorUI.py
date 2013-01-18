# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'treeselector.ui'
#
# Created: Fri Jan 18 15:30:58 2013
#      by: PyQt4 UI code generator 4.9.6
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

class Ui_TreeSelector(object):
    def setupUi(self, TreeSelector):
        TreeSelector.setObjectName(_fromUtf8("TreeSelector"))
        TreeSelector.resize(597, 640)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/windowicon.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        TreeSelector.setWindowIcon(icon)
        self.verticalLayout = QtGui.QVBoxLayout(TreeSelector)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.scrollArea = QtGui.QScrollArea(TreeSelector)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName(_fromUtf8("scrollArea"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 583, 626))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.listWidget = QtGui.QWidget(self.scrollAreaWidgetContents)
        self.listWidget.setObjectName(_fromUtf8("listWidget"))
        self.verticalLayout_2.addWidget(self.listWidget)
        self.btnAddSelected = QtGui.QPushButton(self.scrollAreaWidgetContents)
        self.btnAddSelected.setObjectName(_fromUtf8("btnAddSelected"))
        self.verticalLayout_2.addWidget(self.btnAddSelected)
        self.lblSelected = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.lblSelected.setObjectName(_fromUtf8("lblSelected"))
        self.verticalLayout_2.addWidget(self.lblSelected)
        self.listSelected = QtGui.QWidget(self.scrollAreaWidgetContents)
        self.listSelected.setObjectName(_fromUtf8("listSelected"))
        self.verticalLayout_2.addWidget(self.listSelected)
        self.btnSelect = QtGui.QPushButton(self.scrollAreaWidgetContents)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/relationalselect.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSelect.setIcon(icon1)
        self.btnSelect.setObjectName(_fromUtf8("btnSelect"))
        self.verticalLayout_2.addWidget(self.btnSelect)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)

        self.retranslateUi(TreeSelector)
        QtCore.QMetaObject.connectSlotsByName(TreeSelector)

    def retranslateUi(self, TreeSelector):
        TreeSelector.setWindowTitle(_translate("TreeSelector", "File selection", None))
        self.btnAddSelected.setText(_translate("TreeSelector", "Add to selected", None))
        self.lblSelected.setText(_translate("TreeSelector", "Selected:", None))
        self.btnSelect.setText(_translate("TreeSelector", "Apply", None))

