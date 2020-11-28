# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'configuration_migration_wizard.ui'
#
# Created by: PyQt5 UI code generator 5.13.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_configMigrationWizard(object):
    def setupUi(self, configMigrationWizard):
        configMigrationWizard.setObjectName("configMigrationWizard")
        configMigrationWizard.setWindowModality(QtCore.Qt.ApplicationModal)
        configMigrationWizard.resize(400, 300)
        configMigrationWizard.setWizardStyle(QtWidgets.QWizard.ModernStyle)
        self.wizardPage1 = QtWidgets.QWizardPage()
        self.wizardPage1.setObjectName("wizardPage1")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.wizardPage1)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label_3 = QtWidgets.QLabel(self.wizardPage1)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.pathSelector = QtWidgets.QComboBox(self.wizardPage1)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.pathSelector.sizePolicy().hasHeightForWidth())
        self.pathSelector.setSizePolicy(sizePolicy)
        self.pathSelector.setObjectName("pathSelector")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.pathSelector)
        self.label_2 = QtWidgets.QLabel(self.wizardPage1)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.changedInput = QtWidgets.QDateTimeEdit(self.wizardPage1)
        self.changedInput.setObjectName("changedInput")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.changedInput)
        self.label = QtWidgets.QLabel(self.wizardPage1)
        self.label.setObjectName("label")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label)
        self.versionInput = QtWidgets.QLineEdit(self.wizardPage1)
        self.versionInput.setObjectName("versionInput")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.versionInput)
        self.verticalLayout.addLayout(self.formLayout)
        configMigrationWizard.addPage(self.wizardPage1)
        self.wizardPage2 = QtWidgets.QWizardPage()
        self.wizardPage2.setObjectName("wizardPage2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.wizardPage2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.textBrowser = QtWidgets.QTextBrowser(self.wizardPage2)
        self.textBrowser.setObjectName("textBrowser")
        self.verticalLayout_2.addWidget(self.textBrowser)
        configMigrationWizard.addPage(self.wizardPage2)

        self.retranslateUi(configMigrationWizard)
        QtCore.QMetaObject.connectSlotsByName(configMigrationWizard)

    def retranslateUi(self, configMigrationWizard):
        _translate = QtCore.QCoreApplication.translate
        configMigrationWizard.setWindowTitle(_translate("configMigrationWizard", "Viur Admin - Configuration Migration Wizard"))
        self.wizardPage1.setTitle(_translate("configMigrationWizard", "Choose directory to import settings"))
        self.wizardPage1.setSubTitle(_translate("configMigrationWizard", "found viur_admin configuration directories"))
        self.label_3.setText(_translate("configMigrationWizard", "Path"))
        self.label_2.setText(_translate("configMigrationWizard", "Last changed"))
        self.changedInput.setDisplayFormat(_translate("configMigrationWizard", "dd.MM.yyyy HH:mm"))
        self.label.setText(_translate("configMigrationWizard", "Version"))
        self.wizardPage2.setTitle(_translate("configMigrationWizard", "Migration completed"))
        self.wizardPage2.setSubTitle(_translate("configMigrationWizard", "migrated following portals"))
