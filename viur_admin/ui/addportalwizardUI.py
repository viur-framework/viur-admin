# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'addportalwizard.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_AddPortalWizard(object):
    def setupUi(self, AddPortalWizard):
        AddPortalWizard.setObjectName("AddPortalWizard")
        AddPortalWizard.resize(400, 300)
        self.wizardPage0 = QtWidgets.QWizardPage()
        self.wizardPage0.setObjectName("wizardPage0")
        self.formLayout = QtWidgets.QFormLayout(self.wizardPage0)
        self.formLayout.setObjectName("formLayout")
        self.editServer = QtWidgets.QLineEdit(self.wizardPage0)
        self.editServer.setObjectName("editServer")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.editServer)
        self.lblServer = QtWidgets.QLabel(self.wizardPage0)
        self.lblServer.setObjectName("lblServer")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.lblServer)
        self.label = QtWidgets.QLabel(self.wizardPage0)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.editTitle = QtWidgets.QLineEdit(self.wizardPage0)
        self.editTitle.setObjectName("editTitle")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.editTitle)
        AddPortalWizard.addPage(self.wizardPage0)
        self.wizardPage1 = QtWidgets.QWizardPage()
        self.wizardPage1.setObjectName("wizardPage1")
        self.formLayout_2 = QtWidgets.QFormLayout(self.wizardPage1)
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_2 = QtWidgets.QLabel(self.wizardPage1)
        self.label_2.setObjectName("label_2")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.cbAuthSelector = QtWidgets.QComboBox(self.wizardPage1)
        self.cbAuthSelector.setObjectName("cbAuthSelector")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.cbAuthSelector)
        AddPortalWizard.addPage(self.wizardPage1)
        self.wizardPage2 = QtWidgets.QWizardPage()
        self.wizardPage2.setObjectName("wizardPage2")
        self.formLayout_3 = QtWidgets.QFormLayout(self.wizardPage2)
        self.formLayout_3.setObjectName("formLayout_3")
        self.lblUsername = QtWidgets.QLabel(self.wizardPage2)
        self.lblUsername.setObjectName("lblUsername")
        self.formLayout_3.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.lblUsername)
        self.editUsername = QtWidgets.QLineEdit(self.wizardPage2)
        self.editUsername.setObjectName("editUsername")
        self.formLayout_3.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.editUsername)
        self.editPassword = QtWidgets.QLineEdit(self.wizardPage2)
        self.editPassword.setObjectName("editPassword")
        self.formLayout_3.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.editPassword)
        self.lblPassword = QtWidgets.QLabel(self.wizardPage2)
        self.lblPassword.setObjectName("lblPassword")
        self.formLayout_3.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.lblPassword)
        self.cbSavePw = QtWidgets.QCheckBox(self.wizardPage2)
        self.cbSavePw.setObjectName("cbSavePw")
        self.formLayout_3.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.cbSavePw)
        AddPortalWizard.addPage(self.wizardPage2)
        self.wizardPage3 = QtWidgets.QWizardPage()
        self.wizardPage3.setObjectName("wizardPage3")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.wizardPage3)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_3 = QtWidgets.QLabel(self.wizardPage3)
        self.label_3.setObjectName("label_3")
        self.verticalLayout.addWidget(self.label_3)
        AddPortalWizard.addPage(self.wizardPage3)

        self.retranslateUi(AddPortalWizard)
        QtCore.QMetaObject.connectSlotsByName(AddPortalWizard)

    def retranslateUi(self, AddPortalWizard):
        _translate = QtCore.QCoreApplication.translate
        AddPortalWizard.setWindowTitle(_translate("AddPortalWizard", "Wizard"))
        self.editServer.setText(_translate("AddPortalWizard", "http://127.0.0.1:8080/"))
        self.lblServer.setText(_translate("AddPortalWizard", "Server"))
        self.label.setText(_translate("AddPortalWizard", "Title"))
        self.editTitle.setText(_translate("AddPortalWizard", "test"))
        self.label_2.setText(_translate("AddPortalWizard", "Select Authentication"))
        self.lblUsername.setText(_translate("AddPortalWizard", "Username"))
        self.lblPassword.setText(_translate("AddPortalWizard", "Password"))
        self.cbSavePw.setText(_translate("AddPortalWizard", "Save Password?"))
        self.label_3.setText(_translate("AddPortalWizard", "Success"))

