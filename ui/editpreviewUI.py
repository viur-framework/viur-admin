# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\editpreview.ui'
#
# Created: Thu Jul 18 16:19:44 2013
#      by: PyQt4 UI code generator 4.9.5
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_EditPreview(object):
    def setupUi(self, BasePreview):
        BasePreview.setObjectName(_fromUtf8("BasePreview"))
        BasePreview.resize(701, 482)
        BasePreview.setWindowTitle(_fromUtf8(""))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/ViURadmin.ico")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        BasePreview.setWindowIcon(icon)
        self.verticalLayout = QtGui.QVBoxLayout(BasePreview)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.cbUrls = QtGui.QComboBox(BasePreview)
        self.cbUrls.setObjectName(_fromUtf8("cbUrls"))
        self.horizontalLayout.addWidget(self.cbUrls)
        self.btnReload = QtGui.QPushButton(BasePreview)
        self.btnReload.setObjectName(_fromUtf8("btnReload"))
        self.horizontalLayout.addWidget(self.btnReload)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.webView = QtWebKit.QWebView(BasePreview)
        self.webView.setUrl(QtCore.QUrl(_fromUtf8("about:blank")))
        self.webView.setObjectName(_fromUtf8("webView"))
        self.verticalLayout.addWidget(self.webView)

        self.retranslateUi(BasePreview)
        QtCore.QMetaObject.connectSlotsByName(BasePreview)

    def retranslateUi(self, BasePreview):
        self.btnReload.setText(QtGui.QApplication.translate("BasePreview", "Reload", None, QtGui.QApplication.UnicodeUTF8))

from PyQt4 import QtWebKit

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    BasePreview = QtGui.QWidget()
    ui = Ui_BasePreview()
    ui.setupUi(BasePreview)
    BasePreview.show()
    sys.exit(app.exec_())
