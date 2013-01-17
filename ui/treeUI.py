# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tree.ui'
#
# Created: Mon Jan 14 16:15:30 2013
#      by: PyQt4 UI code generator 4.9.6
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

class Ui_Tree(object):
    def setupUi(self, Tree):
        Tree.setObjectName(_fromUtf8("Tree"))
        Tree.resize(659, 479)
        self.verticalLayout = QtGui.QVBoxLayout(Tree)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.boxActions = QtGui.QHBoxLayout()
        self.boxActions.setObjectName(_fromUtf8("boxActions"))
        self.verticalLayout.addLayout(self.boxActions)
        self.listWidget = QtGui.QWidget(Tree)
        self.listWidget.setObjectName(_fromUtf8("listWidget"))
        self.verticalLayout.addWidget(self.listWidget)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.editSearch = QtGui.QLineEdit(Tree)
        self.editSearch.setObjectName(_fromUtf8("editSearch"))
        self.horizontalLayout.addWidget(self.editSearch)
        self.btnSearch = QtGui.QPushButton(Tree)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/search_small.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSearch.setIcon(icon)
        self.btnSearch.setObjectName(_fromUtf8("btnSearch"))
        self.horizontalLayout.addWidget(self.btnSearch)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Tree)
        QtCore.QMetaObject.connectSlotsByName(Tree)

    def retranslateUi(self, Tree):
        Tree.setWindowTitle(_translate("Tree", "Form", None))
        self.btnSearch.setText(_translate("Tree", "Search", None))

