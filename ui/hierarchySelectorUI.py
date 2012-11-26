# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\hierarchySelector.ui'
#
# Created: Mon Nov 26 19:34:48 2012
#      by: PyQt4 UI code generator 4.9.5
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_HierarchySelector(object):
    def setupUi(self, HierarchySelector):
        HierarchySelector.setObjectName(_fromUtf8("HierarchySelector"))
        HierarchySelector.resize(793, 494)
        self.verticalLayout = QtGui.QVBoxLayout(HierarchySelector)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.splitter = QtGui.QSplitter(HierarchySelector)
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
        self.webView.setUrl(QtCore.QUrl(_fromUtf8("about:blank")))
        self.webView.setZoomFactor(0.800000011920929)
        self.webView.setObjectName(_fromUtf8("webView"))
        self.verticalLayout.addWidget(self.splitter)
        self.lblSelected = QtGui.QLabel(HierarchySelector)
        self.lblSelected.setObjectName(_fromUtf8("lblSelected"))
        self.verticalLayout.addWidget(self.lblSelected)
        self.listSelected = QtGui.QListWidget(HierarchySelector)
        self.listSelected.setObjectName(_fromUtf8("listSelected"))
        self.verticalLayout.addWidget(self.listSelected)
        self.btnSelect = QtGui.QPushButton(HierarchySelector)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/relationalselect.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSelect.setIcon(icon)
        self.btnSelect.setObjectName(_fromUtf8("btnSelect"))
        self.verticalLayout.addWidget(self.btnSelect)

        self.retranslateUi(HierarchySelector)
        QtCore.QMetaObject.connectSlotsByName(HierarchySelector)

    def retranslateUi(self, HierarchySelector):
        HierarchySelector.setWindowTitle(QtGui.QApplication.translate("HierarchySelector", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.setSortingEnabled(True)
        self.lblSelected.setText(QtGui.QApplication.translate("HierarchySelector", "Selected:", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSelect.setText(QtGui.QApplication.translate("HierarchySelector", "Apply", None, QtGui.QApplication.UnicodeUTF8))

from PyQt4 import QtWebKit

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    HierarchySelector = QtGui.QWidget()
    ui = Ui_HierarchySelector()
    ui.setupUi(HierarchySelector)
    HierarchySelector.show()
    sys.exit(app.exec_())

