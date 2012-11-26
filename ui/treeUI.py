# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\tree.ui'
#
# Created: Mon Nov 26 19:34:49 2012
#      by: PyQt4 UI code generator 4.9.5
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Tree(object):
    def setupUi(self, Tree):
        Tree.setObjectName(_fromUtf8("Tree"))
        Tree.resize(659, 479)
        self.verticalLayout = QtGui.QVBoxLayout(Tree)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.boxActions = QtGui.QHBoxLayout()
        self.boxActions.setObjectName(_fromUtf8("boxActions"))
        self.verticalLayout.addLayout(self.boxActions)
        self.pathlist = QtGui.QListWidget(Tree)
        self.pathlist.setMaximumSize(QtCore.QSize(16777215, 32))
        self.pathlist.setAcceptDrops(True)
        self.pathlist.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.pathlist.setDragDropMode(QtGui.QAbstractItemView.DropOnly)
        self.pathlist.setFlow(QtGui.QListView.LeftToRight)
        self.pathlist.setObjectName(_fromUtf8("pathlist"))
        self.verticalLayout.addWidget(self.pathlist)
        self.listWidget = QtGui.QListWidget(Tree)
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
        self.boxUpload = QtGui.QVBoxLayout()
        self.boxUpload.setObjectName(_fromUtf8("boxUpload"))
        self.verticalLayout.addLayout(self.boxUpload)

        self.retranslateUi(Tree)
        QtCore.QMetaObject.connectSlotsByName(Tree)

    def retranslateUi(self, Tree):
        Tree.setWindowTitle(QtGui.QApplication.translate("Tree", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.listWidget.setSortingEnabled(True)
        self.btnSearch.setText(QtGui.QApplication.translate("Tree", "Search", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Tree = QtGui.QWidget()
    ui = Ui_Tree()
    ui.setupUi(Tree)
    Tree.show()
    sys.exit(app.exec_())

