# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'csvexport.ui'
#
# Created by: PyQt5 UI code generator 5.15.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_CsvExport(object):
    def setupUi(self, CsvExport):
        CsvExport.setObjectName("CsvExport")
        CsvExport.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(CsvExport)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.encodingLabel = QtWidgets.QLabel(CsvExport)
        self.encodingLabel.setObjectName("encodingLabel")
        self.horizontalLayout.addWidget(self.encodingLabel)
        self.encodingComboBox = QtWidgets.QComboBox(CsvExport)
        self.encodingComboBox.setObjectName("encodingComboBox")
        self.encodingComboBox.addItem("")
        self.encodingComboBox.addItem("")
        self.horizontalLayout.addWidget(self.encodingComboBox)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.seperatorLabel = QtWidgets.QLabel(CsvExport)
        self.seperatorLabel.setObjectName("seperatorLabel")
        self.horizontalLayout_2.addWidget(self.seperatorLabel)
        self.langComboBox = QtWidgets.QComboBox(CsvExport)
        self.langComboBox.setObjectName("langComboBox")
        self.horizontalLayout_2.addWidget(self.langComboBox)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.filenameLabel = QtWidgets.QLabel(CsvExport)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.filenameLabel.sizePolicy().hasHeightForWidth())
        self.filenameLabel.setSizePolicy(sizePolicy)
        self.filenameLabel.setSizeIncrement(QtCore.QSize(0, 0))
        self.filenameLabel.setObjectName("filenameLabel")
        self.horizontalLayout_4.addWidget(self.filenameLabel)
        spacerItem = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem)
        self.filenameName = QtWidgets.QLineEdit(CsvExport)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.filenameName.sizePolicy().hasHeightForWidth())
        self.filenameName.setSizePolicy(sizePolicy)
        self.filenameName.setSizeIncrement(QtCore.QSize(0, 0))
        self.filenameName.setObjectName("filenameName")
        self.horizontalLayout_4.addWidget(self.filenameName)
        self.filenameDialogAction = QtWidgets.QToolButton(CsvExport)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.filenameDialogAction.sizePolicy().hasHeightForWidth())
        self.filenameDialogAction.setSizePolicy(sizePolicy)
        self.filenameDialogAction.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.filenameDialogAction.setObjectName("filenameDialogAction")
        self.horizontalLayout_4.addWidget(self.filenameDialogAction)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        spacerItem1 = QtWidgets.QSpacerItem(20, 189, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label = QtWidgets.QLabel(CsvExport)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.horizontalLayout_3.addWidget(self.label)
        self.countLabel = QtWidgets.QLabel(CsvExport)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.countLabel.setFont(font)
        self.countLabel.setObjectName("countLabel")
        self.horizontalLayout_3.addWidget(self.countLabel)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem2)
        self.buttonBox = QtWidgets.QDialogButtonBox(CsvExport)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout_3.addWidget(self.buttonBox)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.encodingLabel.setBuddy(self.encodingComboBox)
        self.seperatorLabel.setBuddy(self.langComboBox)

        self.retranslateUi(CsvExport)
        QtCore.QMetaObject.connectSlotsByName(CsvExport)

    def retranslateUi(self, CsvExport):
        _translate = QtCore.QCoreApplication.translate
        CsvExport.setWindowTitle(_translate("CsvExport", "Form"))
        self.encodingLabel.setText(_translate("CsvExport", "Encoding"))
        self.encodingComboBox.setItemText(0, _translate("CsvExport", "UTF-8"))
        self.encodingComboBox.setItemText(1, _translate("CsvExport", "ISO-8859-15"))
        self.seperatorLabel.setText(_translate("CsvExport", "Language"))
        self.filenameLabel.setText(_translate("CsvExport", "Filename"))
        self.filenameDialogAction.setText(_translate("CsvExport", "..."))
        self.label.setText(_translate("CsvExport", "entries"))
        self.countLabel.setText(_translate("CsvExport", "0"))
import viur_admin.ui.icons_rc
