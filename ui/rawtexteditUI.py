# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\rawtextedit.ui'
#
# Created: Mon Nov 26 19:34:49 2012
#      by: PySide UI code generator 4.9.5
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_rawTextEditWindow(object):
    def setupUi(self, rawTextEditWindow):
        rawTextEditWindow.setObjectName(_fromUtf8("rawTextEditWindow"))
        rawTextEditWindow.resize(625, 475)
        self.centralwidget = QtGui.QWidget(rawTextEditWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.textEdit = Qsci.QsciScintilla(self.centralwidget)
        self.textEdit.setObjectName(_fromUtf8("textEdit"))
        self.verticalLayout.addWidget(self.textEdit)
        self.btnSave = QtGui.QPushButton(self.centralwidget)
        self.btnSave.setObjectName(_fromUtf8("btnSave"))
        self.verticalLayout.addWidget(self.btnSave)
        rawTextEditWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(rawTextEditWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 625, 22))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        rawTextEditWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(rawTextEditWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        rawTextEditWindow.setStatusBar(self.statusbar)

        self.retranslateUi(rawTextEditWindow)
        QtCore.QMetaObject.connectSlotsByName(rawTextEditWindow)

    def retranslateUi(self, rawTextEditWindow):
        rawTextEditWindow.setWindowTitle(QtGui.QApplication.translate("rawTextEditWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSave.setText(QtGui.QApplication.translate("rawTextEditWindow", "Apply", None, QtGui.QApplication.UnicodeUTF8))



if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    rawTextEditWindow = QtGui.QMainWindow()
    ui = Ui_rawTextEditWindow()
    ui.setupUi(rawTextEditWindow)
    rawTextEditWindow.show()
    sys.exit(app.exec_())

