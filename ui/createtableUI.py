# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'createtable.ui'
#
# Created: Tue Jun 11 11:36:48 2013
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

class Ui_DialogCreateTable(object):
    def setupUi(self, DialogCreateTable):
        DialogCreateTable.setObjectName(_fromUtf8("DialogCreateTable"))
        DialogCreateTable.setWindowModality(QtCore.Qt.ApplicationModal)
        DialogCreateTable.resize(238, 115)
        self.formLayout = QtGui.QFormLayout(DialogCreateTable)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label = QtGui.QLabel(DialogCreateTable)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.sboxRows = QtGui.QSpinBox(DialogCreateTable)
        self.sboxRows.setObjectName(_fromUtf8("sboxRows"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.sboxRows)
        self.label_2 = QtGui.QLabel(DialogCreateTable)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_2)
        self.sboxCols = QtGui.QSpinBox(DialogCreateTable)
        self.sboxCols.setObjectName(_fromUtf8("sboxCols"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.sboxCols)
        self.label_3 = QtGui.QLabel(DialogCreateTable)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label_3)
        self.cbAlignment = QtGui.QComboBox(DialogCreateTable)
        self.cbAlignment.setObjectName(_fromUtf8("cbAlignment"))
        self.cbAlignment.addItem(_fromUtf8(""))
        self.cbAlignment.addItem(_fromUtf8(""))
        self.cbAlignment.addItem(_fromUtf8(""))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.cbAlignment)
        self.buttonBox = QtGui.QDialogButtonBox(DialogCreateTable)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.buttonBox)

        self.retranslateUi(DialogCreateTable)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), DialogCreateTable.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), DialogCreateTable.reject)
        QtCore.QMetaObject.connectSlotsByName(DialogCreateTable)

    def retranslateUi(self, DialogCreateTable):
        DialogCreateTable.setWindowTitle(_translate("DialogCreateTable", "Create Table", None))
        self.label.setText(_translate("DialogCreateTable", "Rows", None))
        self.label_2.setText(_translate("DialogCreateTable", "Columns", None))
        self.label_3.setText(_translate("DialogCreateTable", "Alignment", None))
        self.cbAlignment.setItemText(0, _translate("DialogCreateTable", "Left", None))
        self.cbAlignment.setItemText(1, _translate("DialogCreateTable", "Center", None))
        self.cbAlignment.setItemText(2, _translate("DialogCreateTable", "Right", None))

