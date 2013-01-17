# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'hierarchy.ui'
#
# Created: Mon Jan 14 16:06:01 2013
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

class Ui_Hierarchy(object):
    def setupUi(self, Hierarchy):
        Hierarchy.setObjectName(_fromUtf8("Hierarchy"))
        Hierarchy.resize(878, 543)
        self.verticalLayout = QtGui.QVBoxLayout(Hierarchy)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.boxActions = QtGui.QHBoxLayout()
        self.boxActions.setObjectName(_fromUtf8("boxActions"))
        self.verticalLayout.addLayout(self.boxActions)
        self.splitter = QtGui.QSplitter(Hierarchy)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.treeWidget = QtGui.QWidget(self.splitter)
        self.treeWidget.setObjectName(_fromUtf8("treeWidget"))
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

        self.retranslateUi(Hierarchy)
        QtCore.QMetaObject.connectSlotsByName(Hierarchy)

    def retranslateUi(self, Hierarchy):
        Hierarchy.setWindowTitle(_translate("Hierarchy", "Form", None))

from PyQt4 import QtWebKit
