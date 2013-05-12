# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'fileUploadProgress.ui'
#
# Created: Sat May 11 13:49:31 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_FileUploadProgress(object):
    def setupUi(self, FileUploadProgress):
        FileUploadProgress.setObjectName("FileUploadProgress")
        FileUploadProgress.resize(400, 300)
        self.horizontalLayout = QtGui.QHBoxLayout(FileUploadProgress)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label = QtGui.QLabel(FileUploadProgress)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.pbarTotal = QtGui.QProgressBar(FileUploadProgress)
        self.pbarTotal.setProperty("value", 24)
        self.pbarTotal.setObjectName("pbarTotal")
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.pbarTotal)
        self.label_2 = QtGui.QLabel(FileUploadProgress)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_2)
        self.pbarFile = QtGui.QProgressBar(FileUploadProgress)
        self.pbarFile.setProperty("value", 24)
        self.pbarFile.setObjectName("pbarFile")
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.pbarFile)
        self.verticalLayout.addLayout(self.formLayout)
        self.lblProgress = QtGui.QLabel(FileUploadProgress)
        self.lblProgress.setObjectName("lblProgress")
        self.verticalLayout.addWidget(self.lblProgress)
        self.horizontalLayout.addLayout(self.verticalLayout)
        spacerItem = QtGui.QSpacerItem(124, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btnCancel = QtGui.QPushButton(FileUploadProgress)
        self.btnCancel.setObjectName("btnCancel")
        self.horizontalLayout.addWidget(self.btnCancel)

        self.retranslateUi(FileUploadProgress)
        QtCore.QMetaObject.connectSlotsByName(FileUploadProgress)

    def retranslateUi(self, FileUploadProgress):
        FileUploadProgress.setWindowTitle(QtGui.QApplication.translate("FileUploadProgress", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("FileUploadProgress", "ProgressTotal", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("FileUploadProgress", "ProgressFile", None, QtGui.QApplication.UnicodeUTF8))
        self.lblProgress.setText(QtGui.QApplication.translate("FileUploadProgress", "Progress", None, QtGui.QApplication.UnicodeUTF8))
        self.btnCancel.setText(QtGui.QApplication.translate("FileUploadProgress", "Cancel", None, QtGui.QApplication.UnicodeUTF8))

