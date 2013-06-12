# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'docEditlinkEdit.ui'
#
# Created: Tue Jun 11 11:37:13 2013
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
        LinkEdit.setWindowTitle(_translate("LinkEdit", "Form", None))
        self.label.setText(_translate("LinkEdit", "Verknüpfungsziel", None))
        self.checkBoxNewWindow.setText(_translate("LinkEdit", "In neuem Fenster öffnen", None))

