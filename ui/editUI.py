# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'edit.ui'
#
# Created: Thu Jul 17 15:20:42 2014
#      by: PyQt4 UI code generator 4.10.2
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

class Ui_Edit(object):
    def setupUi(self, Edit):
        Edit.setObjectName(_fromUtf8("Edit"))
        Edit.resize(820, 621)
        self.verticalLayout = QtGui.QVBoxLayout(Edit)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tabWidget = QtGui.QTabWidget(Edit)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.verticalLayout.addWidget(self.tabWidget)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.btnReset = QtGui.QPushButton(Edit)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/undo_small.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnReset.setIcon(icon)
        self.btnReset.setObjectName(_fromUtf8("btnReset"))
        self.horizontalLayout_2.addWidget(self.btnReset)
        self.btnClose = QtGui.QPushButton(Edit)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/cancel_small.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnClose.setIcon(icon1)
        self.btnClose.setObjectName(_fromUtf8("btnClose"))
        self.horizontalLayout_2.addWidget(self.btnClose)
        spacerItem = QtGui.QSpacerItem(254, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.btnPreview = QtGui.QPushButton(Edit)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/preview.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnPreview.setIcon(icon2)
        self.btnPreview.setObjectName(_fromUtf8("btnPreview"))
        self.horizontalLayout_2.addWidget(self.btnPreview)
        spacerItem1 = QtGui.QSpacerItem(254, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.btnSaveClose = QtGui.QPushButton(Edit)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/save_new.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSaveClose.setIcon(icon3)
        self.btnSaveClose.setObjectName(_fromUtf8("btnSaveClose"))
        self.horizontalLayout_2.addWidget(self.btnSaveClose)
        self.btnSaveContinue = QtGui.QPushButton(Edit)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/save_continue.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSaveContinue.setIcon(icon4)
        self.btnSaveContinue.setObjectName(_fromUtf8("btnSaveContinue"))
        self.horizontalLayout_2.addWidget(self.btnSaveContinue)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(Edit)
        self.tabWidget.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(Edit)

    def retranslateUi(self, Edit):
        Edit.setWindowTitle(_translate("Edit", "Form", None))
        self.btnReset.setText(_translate("Edit", "Reset", None))
        self.btnClose.setText(_translate("Edit", "Close", None))
        self.btnPreview.setText(_translate("Edit", "Preview", None))
        self.btnSaveClose.setText(_translate("Edit", "Save and close", None))
        self.btnSaveContinue.setText(_translate("Edit", "Save and continue", None))

