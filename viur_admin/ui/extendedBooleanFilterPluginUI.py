# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'extendedBooleanFilterPlugin.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(400, 300)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        Form.setFont(font)
        self.formLayout = QtWidgets.QFormLayout(Form)
        self.formLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName("formLayout")
        self.booleanLabel = QtWidgets.QLabel(Form)
        self.booleanLabel.setObjectName("booleanLabel")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.booleanLabel)
        self.values = QtWidgets.QComboBox(Form)
        self.values.setObjectName("values")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.values)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        Form.setTitle(_translate("Form", "Filter Name"))
        self.booleanLabel.setText(_translate("Form", "Value"))


