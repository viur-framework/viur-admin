# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'editpreview.ui'
#
# Created: Sat May 11 13:49:05 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_EditPreview(object):
    def setupUi(self, BasePreview):
        BasePreview.setObjectName("BasePreview")
        BasePreview.setGeometry(QtCore.QRect(0, 0, 701, 482))
        BasePreview.setWindowTitle("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/ViURadmin.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        BasePreview.setWindowIcon(icon)
        self.verticalLayout = QtGui.QVBoxLayout(BasePreview)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.cbUrls = QtGui.QComboBox(BasePreview)
        self.cbUrls.setObjectName("cbUrls")
        self.horizontalLayout.addWidget(self.cbUrls)
        self.btnReload = QtGui.QPushButton(BasePreview)
        self.btnReload.setObjectName("btnReload")
        self.horizontalLayout.addWidget(self.btnReload)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.webView = QtWebKit.QWebView(BasePreview)
        self.webView.setUrl(QtCore.QUrl("about:blank"))
        self.webView.setObjectName("webView")
        self.verticalLayout.addWidget(self.webView)

        self.retranslateUi(BasePreview)
        QtCore.QMetaObject.connectSlotsByName(BasePreview)

    def retranslateUi(self, BasePreview):
        self.btnReload.setText(QtGui.QApplication.translate("EditPreview", "Reload", None, QtGui.QApplication.UnicodeUTF8))

from PySide import QtWebKit
