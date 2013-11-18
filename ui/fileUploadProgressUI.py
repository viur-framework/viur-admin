# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\fileUploadProgress.ui'
#
# Created: Thu Jul 18 16:20:30 2013
#      by: PyQt4 UI code generator 4.9.5
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_FileUploadProgress(object):
    def setupUi(self, FileUploadProgress):
        FileUploadProgress.setObjectName(_fromUtf8("FileUploadProgress"))
        FileUploadProgress.resize(400, 300)
        self.horizontalLayout = QtGui.QHBoxLayout(FileUploadProgress)
        self.horizontalLayout.setMargin(0)
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
        FileUploadProgress.setWindowTitle(QtGui.QApplication.translate("FileUploadProgress", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("FileUploadProgress", "ProgressTotal", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("FileUploadProgress", "ProgressFile", None, QtGui.QApplication.UnicodeUTF8))
        self.lblProgress.setText(QtGui.QApplication.translate("FileUploadProgress", "Progress", None, QtGui.QApplication.UnicodeUTF8))
        self.btnCancel.setText(QtGui.QApplication.translate("FileUploadProgress", "Cancel", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    FileUploadProgress = QtGui.QWidget()
    ui = Ui_FileUploadProgress()
    ui.setupUi(FileUploadProgress)
    FileUploadProgress.show()
    sys.exit(app.exec_())

