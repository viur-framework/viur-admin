# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tree.ui'
#
# Created: Mon Nov 24 18:30:24 2014
# by: PyQt5 UI code generator 5.3.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Tree(object):
    def setupUi(self, Tree):
        Tree.setObjectName("Tree")
        Tree.resize(659, 479)
        self.verticalLayout = QtWidgets.QVBoxLayout(Tree)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.boxActions = QtWidgets.QHBoxLayout()
        self.boxActions.setObjectName("boxActions")
        self.verticalLayout.addLayout(self.boxActions)
        self.pathListBox = QtWidgets.QVBoxLayout()
        self.pathListBox.setContentsMargins(-1, 10, -1, 10)
        self.pathListBox.setObjectName("pathListBox")
        self.verticalLayout.addLayout(self.pathListBox)
        self.verticalLayout_3 = QtWidgets.QWidget(Tree)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.verticalLayout_3)
        self.verticalLayout_2.setContentsMargins(0, 10, 0, 10)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.listWidgetBox = QtWidgets.QVBoxLayout()
        self.listWidgetBox.setContentsMargins(0, 0, 0, 0)
        self.listWidgetBox.setObjectName("listWidgetBox")
        self.verticalLayout_2.addLayout(self.listWidgetBox)
        self.boxUpload = QtWidgets.QVBoxLayout()
        self.boxUpload.setObjectName("boxUpload")
        self.verticalLayout_2.addLayout(self.boxUpload)
        self.verticalLayout.addWidget(self.verticalLayout_3)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.editSearch = QtWidgets.QLineEdit(Tree)
        self.editSearch.setObjectName("editSearch")
        self.horizontalLayout.addWidget(self.editSearch)
        self.btnSearch = QtWidgets.QPushButton(Tree)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/actions/search.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSearch.setIcon(icon)
        self.btnSearch.setObjectName("btnSearch")
        self.horizontalLayout.addWidget(self.btnSearch)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Tree)
        QtCore.QMetaObject.connectSlotsByName(Tree)

    def retranslateUi(self, Tree):
        _translate = QtCore.QCoreApplication.translate
        Tree.setWindowTitle(_translate("Tree", "Form"))
        self.editSearch.setText(_translate("Tree", "Search"))
        self.btnSearch.setText(_translate("Tree", "Search"))

