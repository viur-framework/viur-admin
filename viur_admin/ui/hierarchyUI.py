# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'hierarchy.ui'
#
# Created by: PyQt5 UI code generator 5.13.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Hierarchy(object):
    def setupUi(self, Hierarchy):
        Hierarchy.setObjectName("Hierarchy")
        Hierarchy.resize(878, 719)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Hierarchy.sizePolicy().hasHeightForWidth())
        Hierarchy.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(Hierarchy)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.boxActions = QtWidgets.QHBoxLayout()
        self.boxActions.setObjectName("boxActions")
        self.verticalLayout.addLayout(self.boxActions)
        self.splitter = QtWidgets.QSplitter(Hierarchy)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.treeWidget = QtWidgets.QWidget(self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.treeWidget.sizePolicy().hasHeightForWidth())
        self.treeWidget.setSizePolicy(sizePolicy)
        self.treeWidget.setObjectName("treeWidget")
        self.verticalLayout.addWidget(self.splitter)

        self.retranslateUi(Hierarchy)
        QtCore.QMetaObject.connectSlotsByName(Hierarchy)

    def retranslateUi(self, Hierarchy):
        _translate = QtCore.QCoreApplication.translate
        Hierarchy.setWindowTitle(_translate("Hierarchy", "Form"))
