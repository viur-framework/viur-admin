# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'createtable.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_DialogCreateTable(object):
    def setupUi(self, DialogCreateTable):
        DialogCreateTable.setObjectName("DialogCreateTable")
        DialogCreateTable.setWindowModality(QtCore.Qt.ApplicationModal)
        DialogCreateTable.resize(238, 115)
        self.formLayout = QtWidgets.QFormLayout(DialogCreateTable)
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(DialogCreateTable)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.sboxRows = QtWidgets.QSpinBox(DialogCreateTable)
        self.sboxRows.setObjectName("sboxRows")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.sboxRows)
        self.label_2 = QtWidgets.QLabel(DialogCreateTable)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.sboxCols = QtWidgets.QSpinBox(DialogCreateTable)
        self.sboxCols.setObjectName("sboxCols")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.sboxCols)
        self.label_3 = QtWidgets.QLabel(DialogCreateTable)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.cbAlignment = QtWidgets.QComboBox(DialogCreateTable)
        self.cbAlignment.setObjectName("cbAlignment")
        self.cbAlignment.addItem("")
        self.cbAlignment.addItem("")
        self.cbAlignment.addItem("")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.cbAlignment)
        self.buttonBox = QtWidgets.QDialogButtonBox(DialogCreateTable)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.buttonBox)

        self.retranslateUi(DialogCreateTable)
        self.buttonBox.accepted.connect(DialogCreateTable.accept)
        self.buttonBox.rejected.connect(DialogCreateTable.reject)
        QtCore.QMetaObject.connectSlotsByName(DialogCreateTable)

    def retranslateUi(self, DialogCreateTable):
        _translate = QtCore.QCoreApplication.translate
        DialogCreateTable.setWindowTitle(_translate("DialogCreateTable", "Create Table"))
        self.label.setText(_translate("DialogCreateTable", "Rows"))
        self.label_2.setText(_translate("DialogCreateTable", "Columns"))
        self.label_3.setText(_translate("DialogCreateTable", "Alignment"))
        self.cbAlignment.setItemText(0, _translate("DialogCreateTable", "Left"))
        self.cbAlignment.setItemText(1, _translate("DialogCreateTable", "Center"))
        self.cbAlignment.setItemText(2, _translate("DialogCreateTable", "Right"))

