# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\fileDownloadProgress.ui'
#
# Created: Mon Nov 26 19:34:48 2012
#      by: PySide UI code generator 4.9.5
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

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
        FileDownloadProgress.setWindowTitle(QtGui.QApplication.translate("FileDownloadProgress", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("FileDownloadProgress", "ProgressTotal", None, QtGui.QApplication.UnicodeUTF8))
        self.lblProgress.setText(QtGui.QApplication.translate("FileDownloadProgress", "Progress", None, QtGui.QApplication.UnicodeUTF8))
        self.btnCancel.setText(QtGui.QApplication.translate("FileDownloadProgress", "Cancel", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    FileDownloadProgress = QtGui.QWidget()
    ui = Ui_FileDownloadProgress()
    ui.setupUi(FileDownloadProgress)
    FileDownloadProgress.show()
    sys.exit(app.exec_())

