# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'fileDownloadProgress.ui'
#
# Created: Sat May 11 13:49:20 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_FileDownloadProgress(object):
    def setupUi(self, FileDownloadProgress):
        FileDownloadProgress.setObjectName("FileDownloadProgress")
        FileDownloadProgress.resize(400, 300)
        self.horizontalLayout = QtGui.QHBoxLayout(FileDownloadProgress)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.ExpandingFieldsGrow)
        self.formLayout.setObjectName("formLayout")
        self.label = QtGui.QLabel(FileDownloadProgress)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.pbarTotal = QtGui.QProgressBar(FileDownloadProgress)
        self.pbarTotal.setProperty("value", 24)
        self.pbarTotal.setObjectName("pbarTotal")
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.pbarTotal)
        self.verticalLayout.addLayout(self.formLayout)
        self.lblProgress = QtGui.QLabel(FileDownloadProgress)
        self.lblProgress.setObjectName("lblProgress")
        self.verticalLayout.addWidget(self.lblProgress)
        self.horizontalLayout.addLayout(self.verticalLayout)
        spacerItem = QtGui.QSpacerItem(124, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btnCancel = QtGui.QPushButton(FileDownloadProgress)
        self.btnCancel.setObjectName("btnCancel")
        self.horizontalLayout.addWidget(self.btnCancel)

        self.retranslateUi(FileDownloadProgress)
        QtCore.QMetaObject.connectSlotsByName(FileDownloadProgress)

    def retranslateUi(self, FileDownloadProgress):
        FileDownloadProgress.setWindowTitle(QtGui.QApplication.translate("FileDownloadProgress", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("FileDownloadProgress", "ProgressTotal", None, QtGui.QApplication.UnicodeUTF8))
        self.lblProgress.setText(QtGui.QApplication.translate("FileDownloadProgress", "Progress", None, QtGui.QApplication.UnicodeUTF8))
        self.btnCancel.setText(QtGui.QApplication.translate("FileDownloadProgress", "Cancel", None, QtGui.QApplication.UnicodeUTF8))

