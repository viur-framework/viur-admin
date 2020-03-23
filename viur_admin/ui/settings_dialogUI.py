# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'settings_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.debug_group = QtWidgets.QGroupBox(Dialog)
        self.debug_group.setObjectName("debug_group")
        self.formLayout = QtWidgets.QFormLayout(self.debug_group)
        self.formLayout.setObjectName("formLayout")
        self.debug_level_label = QtWidgets.QLabel(self.debug_group)
        self.debug_level_label.setObjectName("debug_level_label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.debug_level_label)
        self.debug_level_value = QtWidgets.QComboBox(self.debug_group)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.debug_level_value.sizePolicy().hasHeightForWidth())
        self.debug_level_value.setSizePolicy(sizePolicy)
        self.debug_level_value.setObjectName("debug_level_value")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.debug_level_value)
        self.verticalLayout.addWidget(self.debug_group)
        self.style_group = QtWidgets.QGroupBox(Dialog)
        self.style_group.setObjectName("style_group")
        self.formLayout_2 = QtWidgets.QFormLayout(self.style_group)
        self.formLayout_2.setObjectName("formLayout_2")
        self.ui_style_label = QtWidgets.QLabel(self.style_group)
        self.ui_style_label.setObjectName("ui_style_label")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.ui_style_label)
        self.ui_style_value = QtWidgets.QComboBox(self.style_group)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ui_style_value.sizePolicy().hasHeightForWidth())
        self.ui_style_value.setSizePolicy(sizePolicy)
        self.ui_style_value.setObjectName("ui_style_value")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.ui_style_value)
        self.verticalLayout.addWidget(self.style_group)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.debug_group.setTitle(_translate("Dialog", "Debug Settings"))
        self.debug_level_label.setText(_translate("Dialog", "Debug Verbosity"))
        self.style_group.setTitle(_translate("Dialog", "Appearance"))
        self.ui_style_label.setText(_translate("Dialog", "UI Style"))
