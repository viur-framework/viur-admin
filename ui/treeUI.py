# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tree.ui'
#
# Created: Mon May  6 18:49:02 2013
#      by: PyQt4 UI code generator 4.10
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
        self.verticalLayout_3 = QtGui.QWidget(Tree)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.verticalLayout_3)
        self.verticalLayout_2.setMargin(0)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.pathlist = QtGui.QListWidget(self.verticalLayout_3)
        self.pathlist.setMaximumSize(QtCore.QSize(16777215, 32))
        self.pathlist.setAcceptDrops(True)
        self.pathlist.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.pathlist.setDragDropMode(QtGui.QAbstractItemView.DropOnly)
        self.pathlist.setFlow(QtGui.QListView.LeftToRight)
        self.pathlist.setObjectName(_fromUtf8("pathlist"))
        self.verticalLayout_2.addWidget(self.pathlist)
        self.listWidget = QtGui.QListWidget(self.verticalLayout_3)
        self.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.listWidget.setAcceptDrops(True)
        self.listWidget.setDragEnabled(True)
        self.listWidget.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
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
        self.verticalLayout_2.addWidget(self.listWidget)
        self.boxUpload = QtGui.QVBoxLayout()
        self.boxUpload.setObjectName(_fromUtf8("boxUpload"))
        self.verticalLayout_2.addLayout(self.boxUpload)
        self.verticalLayout.addWidget(self.verticalLayout_3)
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
        self.listWidget.setSortingEnabled(True)
        self.editSearch.setText(_translate("Tree", "Search", None))
        self.btnSearch.setText(_translate("Tree", "Search", None))

