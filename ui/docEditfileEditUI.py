# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'docEditfileEdit.ui'
#
# Created: Tue Jun 11 11:37:00 2013
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

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(739, 639)
        self.verticalLayout_3 = QtGui.QVBoxLayout(Form)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.webView = QtWebKit.QWebView(Form)
        self.webView.setUrl(QtCore.QUrl(_fromUtf8("about:blank")))
        self.webView.setObjectName(_fromUtf8("webView"))
        self.verticalLayout_3.addWidget(self.webView)
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.editWidth = QtGui.QLineEdit(Form)
        self.editWidth.setInputMethodHints(QtCore.Qt.ImhDigitsOnly)
        self.editWidth.setAlignment(QtCore.Qt.AlignCenter)
        self.editWidth.setObjectName(_fromUtf8("editWidth"))
        self.horizontalLayout_2.addWidget(self.editWidth)
        self.label_3 = QtGui.QLabel(Form)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.horizontalLayout_2.addWidget(self.label_3)
        self.editHeight = QtGui.QLineEdit(Form)
        self.editHeight.setInputMethodHints(QtCore.Qt.ImhDigitsOnly)
        self.editHeight.setAlignment(QtCore.Qt.AlignCenter)
        self.editHeight.setObjectName(_fromUtf8("editHeight"))
        self.horizontalLayout_2.addWidget(self.editHeight)
        self.comboBoxUnits = QtGui.QComboBox(Form)
        self.comboBoxUnits.setObjectName(_fromUtf8("comboBoxUnits"))
        self.comboBoxUnits.addItem(_fromUtf8(""))
        self.comboBoxUnits.addItem(_fromUtf8(""))
        self.comboBoxUnits.addItem(_fromUtf8(""))
        self.horizontalLayout_2.addWidget(self.comboBoxUnits)
        self.formLayout.setLayout(2, QtGui.QFormLayout.FieldRole, self.horizontalLayout_2)
        self.label_2 = QtGui.QLabel(Form)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.editFile = QtGui.QLineEdit(Form)
        self.editFile.setObjectName(_fromUtf8("editFile"))
        self.horizontalLayout.addWidget(self.editFile)
        self.btnSelectFile = QtGui.QPushButton(Form)
        self.btnSelectFile.setObjectName(_fromUtf8("btnSelectFile"))
        self.horizontalLayout.addWidget(self.btnSelectFile)
        self.formLayout.setLayout(1, QtGui.QFormLayout.FieldRole, self.horizontalLayout)
        self.label = QtGui.QLabel(Form)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.comboBoxAlign = QtGui.QComboBox(Form)
        self.comboBoxAlign.setObjectName(_fromUtf8("comboBoxAlign"))
        self.comboBoxAlign.addItem(_fromUtf8(""))
        self.comboBoxAlign.addItem(_fromUtf8(""))
        self.comboBoxAlign.addItem(_fromUtf8(""))
        self.verticalLayout.addWidget(self.comboBoxAlign)
        self.checkBoxFloat = QtGui.QCheckBox(Form)
        self.checkBoxFloat.setObjectName(_fromUtf8("checkBoxFloat"))
        self.verticalLayout.addWidget(self.checkBoxFloat)
        self.formLayout.setLayout(3, QtGui.QFormLayout.FieldRole, self.verticalLayout)
        self.label_4 = QtGui.QLabel(Form)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.label_4)
        self.editTitle = QtGui.QLineEdit(Form)
        self.editTitle.setObjectName(_fromUtf8("editTitle"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.editTitle)
        self.editAlt = QtGui.QLineEdit(Form)
        self.editAlt.setObjectName(_fromUtf8("editAlt"))
        self.formLayout.setWidget(5, QtGui.QFormLayout.FieldRole, self.editAlt)
        self.label_5 = QtGui.QLabel(Form)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.LabelRole, self.label_5)
        self.label_6 = QtGui.QLabel(Form)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.formLayout.setWidget(5, QtGui.QFormLayout.LabelRole, self.label_6)
        self.label_7 = QtGui.QLabel(Form)
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.formLayout.setWidget(6, QtGui.QFormLayout.LabelRole, self.label_7)
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.comboBoxHRef = QtGui.QComboBox(Form)
        self.comboBoxHRef.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.comboBoxHRef.setEditable(True)
        self.comboBoxHRef.setObjectName(_fromUtf8("comboBoxHRef"))
        self.comboBoxHRef.addItem(_fromUtf8(""))
        self.comboBoxHRef.addItem(_fromUtf8(""))
        self.verticalLayout_2.addWidget(self.comboBoxHRef)
        self.checkboxHrefNewWindow = QtGui.QCheckBox(Form)
        self.checkboxHrefNewWindow.setObjectName(_fromUtf8("checkboxHrefNewWindow"))
        self.verticalLayout_2.addWidget(self.checkboxHrefNewWindow)
        self.formLayout.setLayout(6, QtGui.QFormLayout.FieldRole, self.verticalLayout_2)
        self.verticalLayout_3.addLayout(self.formLayout)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Form", None))
        self.label_3.setText(_translate("Form", "x", None))
        self.comboBoxUnits.setItemText(0, _translate("Form", "%", None))
        self.comboBoxUnits.setItemText(1, _translate("Form", "px", None))
        self.comboBoxUnits.setItemText(2, _translate("Form", "em", None))
        self.label_2.setText(_translate("Form", "Größe", None))
        self.btnSelectFile.setText(_translate("Form", "Auswählen", None))
        self.label.setText(_translate("Form", "Datei", None))
        self.comboBoxAlign.setItemText(0, _translate("Form", "Links", None))
        self.comboBoxAlign.setItemText(1, _translate("Form", "Mitte", None))
        self.comboBoxAlign.setItemText(2, _translate("Form", "Rechts", None))
        self.checkBoxFloat.setText(_translate("Form", "FolgendenText umfließen lassen", None))
        self.label_4.setText(_translate("Form", "Ausrichtung", None))
        self.label_5.setText(_translate("Form", "Titel", None))
        self.label_6.setText(_translate("Form", "Alternativ-Text", None))
        self.label_7.setText(_translate("Form", "Verknüpfen mit", None))
        self.comboBoxHRef.setItemText(0, _translate("Form", "-Keine Verlinkung-", None))
        self.comboBoxHRef.setItemText(1, _translate("Form", "Vergrößern", None))
        self.checkboxHrefNewWindow.setText(_translate("Form", "In neuem Fenster öffnen", None))

from PyQt4 import QtWebKit
