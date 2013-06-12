# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'fileUploadProgress.ui'
#
# Created: Tue Jun 11 11:38:01 2013
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

class Ui_FileUploadProgress(object):
    def setupUi(self, FileUploadProgress):
        FileUploadProgress.setObjectName(_fromUtf8("FileUploadProgress"))
        FileUploadProgress.resize(400, 300)
        self.horizontalLayout = QtGui.QHBoxLayout(FileUploadProgress)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label = QtGui.QLabel(FileUploadProgress)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.pbarTotal = QtGui.QProgressBar(FileUploadProgress)
        self.pbarTotal.setProperty("value", 24)
        self.pbarTotal.setObjectName(_fromUtf8("pbarTotal"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.pbarTotal)
        self.label_2 = QtGui.QLabel(FileUploadProgress)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_2)
        self.pbarFile = QtGui.QProgressBar(FileUploadProgress)
        self.pbarFile.setProperty("value", 24)
        self.pbarFile.setObjectName(_fromUtf8("pbarFile"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.pbarFile)
        self.verticalLayout.addLayout(self.formLayout)
        self.lblProgress = QtGui.QLabel(FileUploadProgress)
        self.lblProgress.setObjectName(_fromUtf8("lblProgress"))
        self.verticalLayout.addWidget(self.lblProgress)
        self.horizontalLayout.addLayout(self.verticalLayout)
        spacerItem = QtGui.QSpacerItem(124, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btnCancel = QtGui.QPushButton(FileUploadProgress)
        self.btnCancel.setObjectName(_fromUtf8("btnCancel"))
        self.horizontalLayout.addWidget(self.btnCancel)

        self.retranslateUi(FileUploadProgress)
        QtCore.QMetaObject.connectSlotsByName(FileUploadProgress)

    def retranslateUi(self, FileUploadProgress):
        FileUploadProgress.setWindowTitle(_translate("FileUploadProgress", "Form", None))
        self.label.setText(_translate("FileUploadProgress", "ProgressTotal", None))
        self.label_2.setText(_translate("FileUploadProgress", "ProgressFile", None))
        self.lblProgress.setText(_translate("FileUploadProgress", "Progress", None))
        self.btnCancel.setText(_translate("FileUploadProgress", "Cancel", None))

