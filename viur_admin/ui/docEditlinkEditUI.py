# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'docEditlinkEdit.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_LinkEdit(object):
    def setupUi(self, LinkEdit):
        LinkEdit.setObjectName("LinkEdit")
        LinkEdit.resize(333, 73)
        self.formLayout = QtWidgets.QFormLayout(LinkEdit)
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(LinkEdit)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.editHref = QtWidgets.QLineEdit(LinkEdit)
        self.editHref.setObjectName("editHref")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.editHref)
        self.checkBoxNewWindow = QtWidgets.QCheckBox(LinkEdit)
        self.checkBoxNewWindow.setObjectName("checkBoxNewWindow")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.checkBoxNewWindow)

        self.retranslateUi(LinkEdit)
        QtCore.QMetaObject.connectSlotsByName(LinkEdit)

    def retranslateUi(self, LinkEdit):
        _translate = QtCore.QCoreApplication.translate
        LinkEdit.setWindowTitle(_translate("LinkEdit", "Form"))
        self.label.setText(_translate("LinkEdit", "Verknüpfungsziel"))
        self.checkBoxNewWindow.setText(_translate("LinkEdit", "In neuem Fenster öffnen"))

