# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'extendedDateRangeFilterPlugin.ui'
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
        self.fromDatePickerLabel = QtWidgets.QLabel(Form)
        self.fromDatePickerLabel.setObjectName("fromDatePickerLabel")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.fromDatePickerLabel)
        self.fromDatePicker = QtWidgets.QDateTimeEdit(Form)
        self.fromDatePicker.setObjectName("fromDatePicker")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.fromDatePicker)
        self.toDatePickerLabel = QtWidgets.QLabel(Form)
        self.toDatePickerLabel.setObjectName("toDatePickerLabel")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.toDatePickerLabel)
        self.toDatePicker = QtWidgets.QDateTimeEdit(Form)
        self.toDatePicker.setObjectName("toDatePicker")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.toDatePicker)
        self.clearFilter = QtWidgets.QPushButton(Form)
        self.clearFilter.setFlat(False)
        self.clearFilter.setObjectName("clearFilter")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.clearFilter)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        Form.setTitle(_translate("Form", "Filter Name"))
        self.fromDatePickerLabel.setText(_translate("Form", "Start Date"))
        self.toDatePickerLabel.setText(_translate("Form", "End Date"))
        self.clearFilter.setText(_translate("Form", "Filter entfernen"))


