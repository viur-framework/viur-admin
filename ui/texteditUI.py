# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\textedit.ui'
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

class Ui_textEditWindow(object):
    def setupUi(self, textEditWindow):
        textEditWindow.setObjectName(_fromUtf8("textEditWindow"))
        textEditWindow.resize(625, 475)
        self.centralwidget = QtGui.QWidget(textEditWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.textEdit = QtGui.QTextEdit(self.centralwidget)
        self.textEdit.setObjectName(_fromUtf8("textEdit"))
        self.verticalLayout.addWidget(self.textEdit)
        self.btnSave = QtGui.QPushButton(self.centralwidget)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/accept.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSave.setIcon(icon)
        self.btnSave.setObjectName(_fromUtf8("btnSave"))
        self.verticalLayout.addWidget(self.btnSave)
        textEditWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(textEditWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 625, 22))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        textEditWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(textEditWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        textEditWindow.setStatusBar(self.statusbar)

        self.retranslateUi(textEditWindow)
        QtCore.QMetaObject.connectSlotsByName(textEditWindow)

    def retranslateUi(self, textEditWindow):
        textEditWindow.setWindowTitle(QtGui.QApplication.translate("textEditWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSave.setText(QtGui.QApplication.translate("textEditWindow", "Apply", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    textEditWindow = QtGui.QMainWindow()
    ui = Ui_textEditWindow()
    ui.setupUi(textEditWindow)
    textEditWindow.show()
    sys.exit(app.exec_())

