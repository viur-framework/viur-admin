# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'hierarchy.ui'
#
# Created: Sat May 11 13:50:00 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Hierarchy(object):
    def setupUi(self, Hierarchy):
        Hierarchy.setObjectName("Hierarchy")
        Hierarchy.resize(878, 543)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Hierarchy.sizePolicy().hasHeightForWidth())
        Hierarchy.setSizePolicy(sizePolicy)
        self.verticalLayout = QtGui.QVBoxLayout(Hierarchy)
        self.verticalLayout.setObjectName("verticalLayout")
        self.boxActions = QtGui.QHBoxLayout()
        self.boxActions.setObjectName("boxActions")
        self.verticalLayout.addLayout(self.boxActions)
        self.splitter = QtGui.QSplitter(Hierarchy)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.treeWidget = QtGui.QWidget(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.treeWidget.sizePolicy().hasHeightForWidth())
        self.treeWidget.setSizePolicy(sizePolicy)
        self.treeWidget.setObjectName("treeWidget")
        self.webView = QtWebKit.QWebView(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.webView.sizePolicy().hasHeightForWidth())
        self.webView.setSizePolicy(sizePolicy)
        self.webView.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.webView.setBaseSize(QtCore.QSize(300, 300))
        self.webView.setProperty("url", QtCore.QUrl("about:blank"))
        self.webView.setProperty("zoomFactor", 0.800000011921)
        self.webView.setObjectName("webView")
        self.verticalLayout.addWidget(self.splitter)

        self.retranslateUi(Hierarchy)
        QtCore.QMetaObject.connectSlotsByName(Hierarchy)

    def retranslateUi(self, Hierarchy):
        Hierarchy.setWindowTitle(QtGui.QApplication.translate("Hierarchy", "Form", None, QtGui.QApplication.UnicodeUTF8))

from PySide import QtWebKit
