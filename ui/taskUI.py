# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'task.ui'
#
# Created: Sat May 11 13:50:47 2013
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Task(object):
    def setupUi(self, Task):
        Task.setObjectName("Task")
        Task.resize(554, 300)
        self.horizontalLayout = QtGui.QHBoxLayout(Task)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.listWidget = QtGui.QListWidget(Task)
        self.listWidget.setObjectName("listWidget")
        self.horizontalLayout.addWidget(self.listWidget)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.lblName = QtGui.QLabel(Task)
        self.lblName.setObjectName("lblName")
        self.verticalLayout.addWidget(self.lblName)
        self.lblDescr = QtGui.QTextBrowser(Task)
        self.lblDescr.setObjectName("lblDescr")
        self.verticalLayout.addWidget(self.lblDescr)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.btnExecute = QtGui.QPushButton(Task)
        self.btnExecute.setObjectName("btnExecute")
        self.verticalLayout.addWidget(self.btnExecute)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.retranslateUi(Task)
        QtCore.QMetaObject.connectSlotsByName(Task)

    def retranslateUi(self, Task):
        Task.setWindowTitle(QtGui.QApplication.translate("Task", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.lblName.setText(QtGui.QApplication.translate("Task", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.btnExecute.setText(QtGui.QApplication.translate("Task", "Execute", None, QtGui.QApplication.UnicodeUTF8))

