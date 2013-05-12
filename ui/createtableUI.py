# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'createtable.ui'
#
# Created: Sat May 11 13:48:53 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_DialogCreateTable(object):
    def setupUi(self, DialogCreateTable):
        DialogCreateTable.setObjectName("DialogCreateTable")
        DialogCreateTable.setWindowModality(QtCore.Qt.ApplicationModal)
        DialogCreateTable.resize(238, 115)
        self.formLayout = QtGui.QFormLayout(DialogCreateTable)
        self.formLayout.setObjectName("formLayout")
        self.label = QtGui.QLabel(DialogCreateTable)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.sboxRows = QtGui.QSpinBox(DialogCreateTable)
        self.sboxRows.setObjectName("sboxRows")
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.sboxRows)
        self.label_2 = QtGui.QLabel(DialogCreateTable)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_2)
        self.sboxCols = QtGui.QSpinBox(DialogCreateTable)
        self.sboxCols.setObjectName("sboxCols")
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.sboxCols)
        self.label_3 = QtGui.QLabel(DialogCreateTable)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label_3)
        self.cbAlignment = QtGui.QComboBox(DialogCreateTable)
        self.cbAlignment.setObjectName("cbAlignment")
        self.cbAlignment.addItem("")
        self.cbAlignment.addItem("")
        self.cbAlignment.addItem("")
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.cbAlignment)
        self.buttonBox = QtGui.QDialogButtonBox(DialogCreateTable)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.buttonBox)

        self.retranslateUi(DialogCreateTable)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), DialogCreateTable.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), DialogCreateTable.reject)
        QtCore.QMetaObject.connectSlotsByName(DialogCreateTable)

    def retranslateUi(self, DialogCreateTable):
        DialogCreateTable.setWindowTitle(QtGui.QApplication.translate("DialogCreateTable", "Create Table", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("DialogCreateTable", "Rows", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("DialogCreateTable", "Columns", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("DialogCreateTable", "Alignment", None, QtGui.QApplication.UnicodeUTF8))
        self.cbAlignment.setItemText(0, QtGui.QApplication.translate("DialogCreateTable", "Left", None, QtGui.QApplication.UnicodeUTF8))
        self.cbAlignment.setItemText(1, QtGui.QApplication.translate("DialogCreateTable", "Center", None, QtGui.QApplication.UnicodeUTF8))
        self.cbAlignment.setItemText(2, QtGui.QApplication.translate("DialogCreateTable", "Right", None, QtGui.QApplication.UnicodeUTF8))

