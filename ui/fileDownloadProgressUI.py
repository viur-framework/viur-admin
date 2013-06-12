# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'fileDownloadProgress.ui'
#
# Created: Tue Jun 11 11:37:52 2013
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

class Ui_FileDownloadProgress(object):
    def setupUi(self, FileDownloadProgress):
        FileDownloadProgress.setObjectName(_fromUtf8("FileDownloadProgress"))
        FileDownloadProgress.resize(400, 300)
        self.horizontalLayout = QtGui.QHBoxLayout(FileDownloadProgress)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.ExpandingFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label = QtGui.QLabel(FileDownloadProgress)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.pbarTotal = QtGui.QProgressBar(FileDownloadProgress)
        self.pbarTotal.setProperty("value", 24)
        self.pbarTotal.setObjectName(_fromUtf8("pbarTotal"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.pbarTotal)
        self.verticalLayout.addLayout(self.formLayout)
        self.lblProgress = QtGui.QLabel(FileDownloadProgress)
        self.lblProgress.setObjectName(_fromUtf8("lblProgress"))
        self.verticalLayout.addWidget(self.lblProgress)
        self.horizontalLayout.addLayout(self.verticalLayout)
        spacerItem = QtGui.QSpacerItem(124, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btnCancel = QtGui.QPushButton(FileDownloadProgress)
        self.btnCancel.setObjectName(_fromUtf8("btnCancel"))
        self.horizontalLayout.addWidget(self.btnCancel)

        self.retranslateUi(FileDownloadProgress)
        QtCore.QMetaObject.connectSlotsByName(FileDownloadProgress)

    def retranslateUi(self, FileDownloadProgress):
        FileDownloadProgress.setWindowTitle(_translate("FileDownloadProgress", "Form", None))
        self.label.setText(_translate("FileDownloadProgress", "ProgressTotal", None))
        self.lblProgress.setText(_translate("FileDownloadProgress", "Progress", None))
        self.btnCancel.setText(_translate("FileDownloadProgress", "Cancel", None))

