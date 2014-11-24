# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'hierarchy.ui'
#
# Created: Mon Nov 24 18:30:24 2014
#      by: PyQt5 UI code generator 5.3.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Hierarchy(object):
    def setupUi(self, Hierarchy):
        Hierarchy.setObjectName("Hierarchy")
        Hierarchy.resize(878, 719)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Hierarchy.sizePolicy().hasHeightForWidth())
        Hierarchy.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(Hierarchy)
        self.verticalLayout.setSpacing(-1)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.boxActions = QtWidgets.QHBoxLayout()
        self.boxActions.setObjectName("boxActions")
        self.verticalLayout.addLayout(self.boxActions)
        self.splitter = QtWidgets.QSplitter(Hierarchy)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.treeWidget = QtWidgets.QWidget(self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.treeWidget.sizePolicy().hasHeightForWidth())
        self.treeWidget.setSizePolicy(sizePolicy)
        self.treeWidget.setObjectName("treeWidget")
        self.webView = QtWebKitWidgets.QWebView(self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.webView.sizePolicy().hasHeightForWidth())
        self.webView.setSizePolicy(sizePolicy)
        self.webView.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.webView.setBaseSize(QtCore.QSize(300, 300))
        self.webView.setUrl(QtCore.QUrl("about:blank"))
        self.webView.setZoomFactor(0.800000011921)
        self.webView.setObjectName("webView")
        self.verticalLayout.addWidget(self.splitter)

        self.retranslateUi(Hierarchy)
        QtCore.QMetaObject.connectSlotsByName(Hierarchy)

    def retranslateUi(self, Hierarchy):
        _translate = QtCore.QCoreApplication.translate
        Hierarchy.setWindowTitle(_translate("Hierarchy", "Form"))

from PyQt5 import QtWebKitWidgets
