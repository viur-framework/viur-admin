# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'editpreview.ui'
#
# Created: Mon Nov 24 18:30:24 2014
#      by: PyQt5 UI code generator 5.3.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_BasePreview(object):
    def setupUi(self, BasePreview):
        BasePreview.setObjectName("BasePreview")
        BasePreview.resize(701, 482)
        BasePreview.setWindowTitle("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/ViURadmin.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        BasePreview.setWindowIcon(icon)
        self.verticalLayout = QtWidgets.QVBoxLayout(BasePreview)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.cbUrls = QtWidgets.QComboBox(BasePreview)
        self.cbUrls.setObjectName("cbUrls")
        self.horizontalLayout.addWidget(self.cbUrls)
        self.btnReload = QtWidgets.QPushButton(BasePreview)
        self.btnReload.setObjectName("btnReload")
        self.horizontalLayout.addWidget(self.btnReload)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.webView = QtWebKitWidgets.QWebView(BasePreview)
        self.webView.setUrl(QtCore.QUrl("about:blank"))
        self.webView.setObjectName("webView")
        self.verticalLayout.addWidget(self.webView)

        self.retranslateUi(BasePreview)
        QtCore.QMetaObject.connectSlotsByName(BasePreview)

    def retranslateUi(self, BasePreview):
        _translate = QtCore.QCoreApplication.translate
        self.btnReload.setText(_translate("BasePreview", "Reload"))

from PyQt5 import QtWebKitWidgets
