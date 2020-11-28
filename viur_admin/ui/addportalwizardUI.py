# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'addportalwizard.ui'
#
# Created by: PyQt5 UI code generator 5.13.2
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
        self.editServer.setText("")
        self.editServer.setObjectName("editServer")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.editServer)
        self.lblServer = QtWidgets.QLabel(self.wizardPage0)
        self.lblServer.setObjectName("lblServer")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.lblServer)
        self.label = QtWidgets.QLabel(self.wizardPage0)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.editTitle = QtWidgets.QLineEdit(self.wizardPage0)
        self.editTitle.setText("")
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
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.wizardPage2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.scrollArea = QtWidgets.QScrollArea(self.wizardPage2)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 372, 227))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_2.addWidget(self.scrollArea)
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
        AddPortalWizard.setTabOrder(self.editTitle, self.editServer)
        AddPortalWizard.setTabOrder(self.editServer, self.cbAuthSelector)
        AddPortalWizard.setTabOrder(self.cbAuthSelector, self.scrollArea)

    def retranslateUi(self, AddPortalWizard):
        _translate = QtCore.QCoreApplication.translate
        AddPortalWizard.setWindowTitle(_translate("AddPortalWizard", "Wizard"))
        self.lblServer.setText(_translate("AddPortalWizard", "Server"))
        self.label.setText(_translate("AddPortalWizard", "Title"))
        self.label_2.setText(_translate("AddPortalWizard", "Select Authentication"))
        self.label_3.setText(_translate("AddPortalWizard", "Success"))
