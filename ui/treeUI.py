# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tree.ui'
#
# Created: Mon May 27 12:10:29 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Tree(object):
    def setupUi(self, Tree):
        Tree.setObjectName("Tree")
        Tree.resize(659, 479)
        self.verticalLayout = QtGui.QVBoxLayout(Tree)
        self.verticalLayout.setObjectName("verticalLayout")
        self.boxActions = QtGui.QHBoxLayout()
        self.boxActions.setObjectName("boxActions")
        self.verticalLayout.addLayout(self.boxActions)
        self.pathListBox = QtGui.QVBoxLayout()
        self.pathListBox.setObjectName("pathListBox")
        self.verticalLayout.addLayout(self.pathListBox)
        self.verticalLayout_3 = QtGui.QWidget(Tree)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.verticalLayout_3)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.listWidgetBox = QtGui.QVBoxLayout()
        self.listWidgetBox.setObjectName("listWidgetBox")
        self.verticalLayout_2.addLayout(self.listWidgetBox)
        self.boxUpload = QtGui.QVBoxLayout()
        self.boxUpload.setObjectName("boxUpload")
        self.verticalLayout_2.addLayout(self.boxUpload)
        self.verticalLayout.addWidget(self.verticalLayout_3)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.editSearch = QtGui.QLineEdit(Tree)
        self.editSearch.setObjectName("editSearch")
        self.horizontalLayout.addWidget(self.editSearch)
        self.btnSearch = QtGui.QPushButton(Tree)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/actions/search_small.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSearch.setIcon(icon)
        self.btnSearch.setObjectName("btnSearch")
        self.horizontalLayout.addWidget(self.btnSearch)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Tree)
        QtCore.QMetaObject.connectSlotsByName(Tree)

    def retranslateUi(self, Tree):
        Tree.setWindowTitle(QtGui.QApplication.translate("Tree", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.editSearch.setText(QtGui.QApplication.translate("Tree", "Search", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSearch.setText(QtGui.QApplication.translate("Tree", "Search", None, QtGui.QApplication.UnicodeUTF8))

