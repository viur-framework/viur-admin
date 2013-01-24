# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'treeWidget.ui'
#
# Created: Thu Jan 24 15:27:51 2013
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

class Ui_TreeWidget(object):
    def setupUi(self, TreeWidget):
        TreeWidget.setObjectName(_fromUtf8("TreeWidget"))
        TreeWidget.resize(702, 530)
        self.verticalLayout = QtGui.QVBoxLayout(TreeWidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.pathlist = QtGui.QListWidget(TreeWidget)
        self.pathlist.setMaximumSize(QtCore.QSize(16777215, 32))
        self.pathlist.setAcceptDrops(True)
        self.pathlist.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.pathlist.setDragDropMode(QtGui.QAbstractItemView.DropOnly)
        self.pathlist.setFlow(QtGui.QListView.LeftToRight)
        self.pathlist.setObjectName(_fromUtf8("pathlist"))
        self.verticalLayout.addWidget(self.pathlist)
        self.listWidget = QtGui.QListWidget(TreeWidget)
        self.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.listWidget.setAcceptDrops(True)
        self.listWidget.setDragEnabled(True)
        self.listWidget.setDragDropMode(QtGui.QAbstractItemView.DropOnly)
        self.listWidget.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.listWidget.setAlternatingRowColors(False)
        self.listWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.listWidget.setIconSize(QtCore.QSize(48, 48))
        self.listWidget.setMovement(QtGui.QListView.Snap)
        self.listWidget.setLayoutMode(QtGui.QListView.Batched)
        self.listWidget.setGridSize(QtCore.QSize(128, 128))
        self.listWidget.setViewMode(QtGui.QListView.IconMode)
        self.listWidget.setUniformItemSizes(False)
        self.listWidget.setWordWrap(True)
        self.listWidget.setObjectName(_fromUtf8("listWidget"))
        self.verticalLayout.addWidget(self.listWidget)
        self.boxUpload = QtGui.QVBoxLayout()
        self.boxUpload.setObjectName(_fromUtf8("boxUpload"))
        self.verticalLayout.addLayout(self.boxUpload)

        self.retranslateUi(TreeWidget)
        QtCore.QMetaObject.connectSlotsByName(TreeWidget)

    def retranslateUi(self, TreeWidget):
        TreeWidget.setWindowTitle(_translate("TreeWidget", "Form", None))
        self.listWidget.setSortingEnabled(True)

