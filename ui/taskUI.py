# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'task.ui'
#
# Created: Fri Nov 16 16:02:38 2012
#      by: PyQt4 UI code generator 4.8.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Task(object):
    def setupUi(self, Task):
        Task.setObjectName(_fromUtf8("Task"))
        Task.resize(554, 300)
        Task.setWindowTitle(QtGui.QApplication.translate("Task", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.horizontalLayout = QtGui.QHBoxLayout(Task)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.listWidget = QtGui.QListWidget(Task)
        self.listWidget.setObjectName(_fromUtf8("listWidget"))
        self.horizontalLayout.addWidget(self.listWidget)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.lblName = QtGui.QLabel(Task)
        self.lblName.setText(QtGui.QApplication.translate("Task", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.lblName.setObjectName(_fromUtf8("lblName"))
        self.verticalLayout.addWidget(self.lblName)
        self.lblDescr = QtGui.QTextBrowser(Task)
        self.lblDescr.setObjectName(_fromUtf8("lblDescr"))
        self.verticalLayout.addWidget(self.lblDescr)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.btnExecute = QtGui.QPushButton(Task)
        self.btnExecute.setText(QtGui.QApplication.translate("Task", "Execute", None, QtGui.QApplication.UnicodeUTF8))
        self.btnExecute.setObjectName(_fromUtf8("btnExecute"))
        self.verticalLayout.addWidget(self.btnExecute)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.retranslateUi(Task)
        QtCore.QMetaObject.connectSlotsByName(Task)

    def retranslateUi(self, Task):
        pass

