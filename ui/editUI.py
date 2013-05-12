# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'edit.ui'
#
# Created: Sat May 11 13:49:11 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Edit(object):
    def setupUi(self, Edit):
        Edit.setObjectName("Edit")
        Edit.resize(820, 621)
        self.verticalLayout = QtGui.QVBoxLayout(Edit)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtGui.QTabWidget(Edit)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setObjectName("tabWidget")
        self.verticalLayout.addWidget(self.tabWidget)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.btnReset = QtGui.QPushButton(Edit)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/actions/undo_small.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnReset.setIcon(icon)
        self.btnReset.setObjectName("btnReset")
        self.horizontalLayout_2.addWidget(self.btnReset)
        self.btnClose = QtGui.QPushButton(Edit)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("icons/actions/delete_small.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnClose.setIcon(icon1)
        self.btnClose.setObjectName("btnClose")
        self.horizontalLayout_2.addWidget(self.btnClose)
        spacerItem = QtGui.QSpacerItem(254, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.btnPreview = QtGui.QPushButton(Edit)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("icons/actions/preview_small.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnPreview.setIcon(icon2)
        self.btnPreview.setObjectName("btnPreview")
        self.horizontalLayout_2.addWidget(self.btnPreview)
        spacerItem1 = QtGui.QSpacerItem(254, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.btnSaveClose = QtGui.QPushButton(Edit)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("icons/actions/save.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSaveClose.setIcon(icon3)
        self.btnSaveClose.setObjectName("btnSaveClose")
        self.horizontalLayout_2.addWidget(self.btnSaveClose)
        self.btnSaveContinue = QtGui.QPushButton(Edit)
        self.btnSaveContinue.setIcon(icon3)
        self.btnSaveContinue.setObjectName("btnSaveContinue")
        self.horizontalLayout_2.addWidget(self.btnSaveContinue)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(Edit)
        self.tabWidget.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(Edit)

    def retranslateUi(self, Edit):
        Edit.setWindowTitle(QtGui.QApplication.translate("Edit", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.btnReset.setText(QtGui.QApplication.translate("Edit", "Reset", None, QtGui.QApplication.UnicodeUTF8))
        self.btnClose.setText(QtGui.QApplication.translate("Edit", "Close", None, QtGui.QApplication.UnicodeUTF8))
        self.btnPreview.setText(QtGui.QApplication.translate("Edit", "Preview", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSaveClose.setText(QtGui.QApplication.translate("Edit", "Save and close", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSaveContinue.setText(QtGui.QApplication.translate("Edit", "Save and continue", None, QtGui.QApplication.UnicodeUTF8))

