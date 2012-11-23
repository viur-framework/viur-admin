# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'hierarchy.ui'
#
# Created: Tue Nov 20 12:08:13 2012
#      by: PyQt4 UI code generator 4.8.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Hierarchy(object):
    def setupUi(self, HierarchyApp):
        HierarchyApp.setObjectName(_fromUtf8("HierarchyApp"))
        HierarchyApp.setGeometry(QtCore.QRect(0, 0, 793, 494))
        HierarchyApp.setWindowTitle(QtGui.QApplication.translate("Hierarchy", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.verticalLayout = QtGui.QVBoxLayout(HierarchyApp)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.boxActions = QtGui.QHBoxLayout()
        self.boxActions.setObjectName(_fromUtf8("boxActions"))
        self.verticalLayout.addLayout(self.boxActions)
        self.splitter = QtGui.QSplitter(HierarchyApp)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.treeWidget = QtGui.QTreeWidget(self.splitter)
        self.treeWidget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.treeWidget.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        self.treeWidget.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.treeWidget.setAlternatingRowColors(True)
        self.treeWidget.setRootIsDecorated(True)
        self.treeWidget.setUniformRowHeights(True)
        self.treeWidget.setHeaderHidden(True)
        self.treeWidget.setObjectName(_fromUtf8("treeWidget"))
        self.treeWidget.headerItem().setText(0, _fromUtf8("1"))
        self.webView = QtWebKit.QWebView(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.webView.sizePolicy().hasHeightForWidth())
        self.webView.setSizePolicy(sizePolicy)
        self.webView.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.webView.setBaseSize(QtCore.QSize(300, 300))
        self.webView.setProperty("url", QtCore.QUrl(_fromUtf8("about:blank")))
        self.webView.setProperty("zoomFactor", 0.800000011921)
        self.webView.setObjectName(_fromUtf8("webView"))
        self.verticalLayout.addWidget(self.splitter)

        self.retranslateUi(HierarchyApp)
        QtCore.QMetaObject.connectSlotsByName(HierarchyApp)

    def retranslateUi(self, HierarchyApp):
        self.treeWidget.setSortingEnabled(True)

from PyQt4 import QtWebKit
