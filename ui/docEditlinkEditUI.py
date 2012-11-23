# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'linkEdit.ui'
#
# Created: Sat Nov 26 12:22:47 2011
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_LinkEdit(object):
    def setupUi(self, LinkEdit):
        LinkEdit.setObjectName(_fromUtf8("LinkEdit"))
        LinkEdit.resize(333, 73)
        self.formLayout = QtGui.QFormLayout(LinkEdit)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label = QtGui.QLabel(LinkEdit)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.editHref = QtGui.QLineEdit(LinkEdit)
        self.editHref.setObjectName(_fromUtf8("editHref"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.editHref)
        self.checkBoxNewWindow = QtGui.QCheckBox(LinkEdit)
        self.checkBoxNewWindow.setObjectName(_fromUtf8("checkBoxNewWindow"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.checkBoxNewWindow)

        self.retranslateUi(LinkEdit)
        QtCore.QMetaObject.connectSlotsByName(LinkEdit)

    def retranslateUi(self, LinkEdit):
        LinkEdit.setWindowTitle(QtGui.QApplication.translate("LinkEdit", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("LinkEdit", "Verknüpfungsziel", None, QtGui.QApplication.UnicodeUTF8))
        self.checkBoxNewWindow.setText(QtGui.QApplication.translate("LinkEdit", "In neuem Fenster öffnen", None, QtGui.QApplication.UnicodeUTF8))

