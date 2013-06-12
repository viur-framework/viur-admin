# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'task.ui'
#
# Created: Tue Jun 11 11:39:08 2013
#      by: PyQt4 UI code generator 4.10.1
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

class Ui_Task(object):
    def setupUi(self, Task):
        Task.setObjectName(_fromUtf8("Task"))
        Task.resize(554, 300)
        self.horizontalLayout = QtGui.QHBoxLayout(Task)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.listWidget = QtGui.QListWidget(Task)
        self.listWidget.setObjectName(_fromUtf8("listWidget"))
        self.horizontalLayout.addWidget(self.listWidget)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.lblName = QtGui.QLabel(Task)
        self.lblName.setObjectName(_fromUtf8("lblName"))
        self.verticalLayout.addWidget(self.lblName)
        self.lblDescr = QtGui.QTextBrowser(Task)
        self.lblDescr.setObjectName(_fromUtf8("lblDescr"))
        self.verticalLayout.addWidget(self.lblDescr)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.btnExecute = QtGui.QPushButton(Task)
        self.btnExecute.setObjectName(_fromUtf8("btnExecute"))
        self.verticalLayout.addWidget(self.btnExecute)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.retranslateUi(Task)
        QtCore.QMetaObject.connectSlotsByName(Task)

    def retranslateUi(self, Task):
        Task.setWindowTitle(_translate("Task", "Form", None))
        self.lblName.setText(_translate("Task", "TextLabel", None))
        self.btnExecute.setText(_translate("Task", "Execute", None))

