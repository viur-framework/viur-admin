# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'fileUploadProgress.ui'
#
# Created: Mon Nov 24 18:30:24 2014
# by: PyQt5 UI code generator 5.3.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtWidgets


class Ui_FileUploadProgress(object):
    def setupUi(self, FileUploadProgress):
        FileUploadProgress.setObjectName("FileUploadProgress")
        FileUploadProgress.resize(400, 300)
        self.horizontalLayout = QtWidgets.QHBoxLayout(FileUploadProgress)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(FileUploadProgress)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.pbarTotal = QtWidgets.QProgressBar(FileUploadProgress)
        self.pbarTotal.setProperty("value", 24)
        self.pbarTotal.setObjectName("pbarTotal")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.pbarTotal)
        self.label_2 = QtWidgets.QLabel(FileUploadProgress)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.pbarFile = QtWidgets.QProgressBar(FileUploadProgress)
        self.pbarFile.setProperty("value", 24)
        self.pbarFile.setObjectName("pbarFile")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.pbarFile)
        self.verticalLayout.addLayout(self.formLayout)
        self.lblProgress = QtWidgets.QLabel(FileUploadProgress)
        self.lblProgress.setObjectName("lblProgress")
        self.verticalLayout.addWidget(self.lblProgress)
        self.horizontalLayout.addLayout(self.verticalLayout)
        spacerItem = QtWidgets.QSpacerItem(124, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btnCancel = QtWidgets.QPushButton(FileUploadProgress)
        self.btnCancel.setObjectName("btnCancel")
        self.horizontalLayout.addWidget(self.btnCancel)

        self.retranslateUi(FileUploadProgress)
        QtCore.QMetaObject.connectSlotsByName(FileUploadProgress)

    def retranslateUi(self, FileUploadProgress):
        _translate = QtCore.QCoreApplication.translate
        FileUploadProgress.setWindowTitle(_translate("FileUploadProgress", "Form"))
        self.label.setText(_translate("FileUploadProgress", "ProgressTotal"))
        self.label_2.setText(_translate("FileUploadProgress", "ProgressFile"))
        self.lblProgress.setText(_translate("FileUploadProgress", "Progress"))
        self.btnCancel.setText(_translate("FileUploadProgress", "Cancel"))

