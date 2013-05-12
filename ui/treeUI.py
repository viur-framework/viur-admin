# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tree.ui'
#
# Created: Sat May 11 13:51:17 2013
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
        self.verticalLayout_3 = QtGui.QWidget(Tree)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.verticalLayout_3)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.pathlist = QtGui.QListWidget(self.verticalLayout_3)
        self.pathlist.setMaximumSize(QtCore.QSize(16777215, 32))
        self.pathlist.setAcceptDrops(True)
        self.pathlist.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.pathlist.setDragDropMode(QtGui.QAbstractItemView.DropOnly)
        self.pathlist.setFlow(QtGui.QListView.LeftToRight)
        self.pathlist.setObjectName("pathlist")
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
        self.listWidget.setObjectName("listWidget")
        self.verticalLayout_2.addWidget(self.listWidget)
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
        self.listWidget.setSortingEnabled(True)
        self.editSearch.setText(QtGui.QApplication.translate("Tree", "Search", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSearch.setText(QtGui.QApplication.translate("Tree", "Search", None, QtGui.QApplication.UnicodeUTF8))

