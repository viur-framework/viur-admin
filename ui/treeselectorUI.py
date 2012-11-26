# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\treeselector.ui'
#
# Created: Mon Nov 26 19:34:50 2012
#      by: PyQt4 UI code generator 4.9.5
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_TreeSelector(object):
    def setupUi(self, TreeSelector):
        TreeSelector.setObjectName(_fromUtf8("TreeSelector"))
        TreeSelector.resize(597, 640)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/windowicon.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        TreeSelector.setWindowIcon(icon)
        self.verticalLayout_3 = QtGui.QVBoxLayout(TreeSelector)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.scrollArea = QtGui.QScrollArea(TreeSelector)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName(_fromUtf8("scrollArea"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 583, 620))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.wdgActions = QtGui.QWidget(self.scrollAreaWidgetContents)
        self.wdgActions.setObjectName(_fromUtf8("wdgActions"))
        self.verticalLayout = QtGui.QVBoxLayout(self.wdgActions)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.boxActions = QtGui.QVBoxLayout()
        self.boxActions.setObjectName(_fromUtf8("boxActions"))
        self.boxContainer = QtGui.QHBoxLayout()
        self.boxContainer.setObjectName(_fromUtf8("boxContainer"))
        self.cbRootNode = QtGui.QComboBox(self.wdgActions)
        self.cbRootNode.setMinimumSize(QtCore.QSize(200, 0))
        self.cbRootNode.setMaximumSize(QtCore.QSize(300, 16777215))
        self.cbRootNode.setObjectName(_fromUtf8("cbRootNode"))
        self.boxContainer.addWidget(self.cbRootNode)
        self.pathlist = QtGui.QListWidget(self.wdgActions)
        self.pathlist.setMaximumSize(QtCore.QSize(16777215, 27))
        self.pathlist.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.pathlist.setFlow(QtGui.QListView.LeftToRight)
        self.pathlist.setObjectName(_fromUtf8("pathlist"))
        self.boxContainer.addWidget(self.pathlist)
        self.boxActions.addLayout(self.boxContainer)
        self.listWidget = QtGui.QListWidget(self.wdgActions)
        self.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.listWidget.setAcceptDrops(False)
        self.listWidget.setDragEnabled(False)
        self.listWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.listWidget.setIconSize(QtCore.QSize(96, 96))
        self.listWidget.setMovement(QtGui.QListView.Snap)
        self.listWidget.setLayoutMode(QtGui.QListView.Batched)
        self.listWidget.setGridSize(QtCore.QSize(128, 128))
        self.listWidget.setViewMode(QtGui.QListView.IconMode)
        self.listWidget.setUniformItemSizes(False)
        self.listWidget.setWordWrap(True)
        self.listWidget.setObjectName(_fromUtf8("listWidget"))
        self.boxActions.addWidget(self.listWidget)
        self.verticalLayout.addLayout(self.boxActions)
        self.verticalLayout_2.addWidget(self.wdgActions)
        self.btnAddSelected = QtGui.QPushButton(self.scrollAreaWidgetContents)
        self.btnAddSelected.setObjectName(_fromUtf8("btnAddSelected"))
        self.verticalLayout_2.addWidget(self.btnAddSelected)
        self.lblSelected = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.lblSelected.setObjectName(_fromUtf8("lblSelected"))
        self.verticalLayout_2.addWidget(self.lblSelected)
        self.listSelected = QtGui.QListWidget(self.scrollAreaWidgetContents)
        self.listSelected.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.listSelected.setObjectName(_fromUtf8("listSelected"))
        self.verticalLayout_2.addWidget(self.listSelected)
        self.btnSelect = QtGui.QPushButton(self.scrollAreaWidgetContents)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/relationalselect.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSelect.setIcon(icon1)
        self.btnSelect.setObjectName(_fromUtf8("btnSelect"))
        self.verticalLayout_2.addWidget(self.btnSelect)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_3.addWidget(self.scrollArea)
        self.boxUpload = QtGui.QVBoxLayout()
        self.boxUpload.setObjectName(_fromUtf8("boxUpload"))
        self.verticalLayout_3.addLayout(self.boxUpload)

        self.retranslateUi(TreeSelector)
        QtCore.QMetaObject.connectSlotsByName(TreeSelector)

    def retranslateUi(self, TreeSelector):
        TreeSelector.setWindowTitle(QtGui.QApplication.translate("TreeSelector", "File selection", None, QtGui.QApplication.UnicodeUTF8))
        self.btnAddSelected.setText(QtGui.QApplication.translate("TreeSelector", "Add to selected", None, QtGui.QApplication.UnicodeUTF8))
        self.lblSelected.setText(QtGui.QApplication.translate("TreeSelector", "Selected:", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSelect.setText(QtGui.QApplication.translate("TreeSelector", "Apply", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    TreeSelector = QtGui.QWidget()
    ui = Ui_TreeSelector()
    ui.setupUi(TreeSelector)
    TreeSelector.show()
    sys.exit(app.exec_())

