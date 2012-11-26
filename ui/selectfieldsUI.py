# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\selectfields.ui'
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

class Ui_SelectFields(object):
    def setupUi(self, SelectFields):
        SelectFields.setObjectName(_fromUtf8("SelectFields"))
        SelectFields.resize(507, 685)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/viur.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        SelectFields.setWindowIcon(icon)
        self.centralwidget = QtGui.QWidget(SelectFields)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label_2 = QtGui.QLabel(self.centralwidget)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout.addWidget(self.label_2)
        self.listAvaiableFields = QtGui.QListWidget(self.centralwidget)
        self.listAvaiableFields.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked|QtGui.QAbstractItemView.EditKeyPressed|QtGui.QAbstractItemView.SelectedClicked)
        self.listAvaiableFields.setProperty("showDropIndicator", False)
        self.listAvaiableFields.setDragEnabled(False)
        self.listAvaiableFields.setDragDropMode(QtGui.QAbstractItemView.NoDragDrop)
        self.listAvaiableFields.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.listAvaiableFields.setIconSize(QtCore.QSize(30, 30))
        self.listAvaiableFields.setViewMode(QtGui.QListView.ListMode)
        self.listAvaiableFields.setModelColumn(0)
        self.listAvaiableFields.setSelectionRectVisible(False)
        self.listAvaiableFields.setObjectName(_fromUtf8("listAvaiableFields"))
        self.verticalLayout.addWidget(self.listAvaiableFields)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btnApply = QtGui.QPushButton(self.centralwidget)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/save.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnApply.setIcon(icon1)
        self.btnApply.setObjectName(_fromUtf8("btnApply"))
        self.horizontalLayout.addWidget(self.btnApply)
        self.verticalLayout.addLayout(self.horizontalLayout)
        SelectFields.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(SelectFields)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 507, 22))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        SelectFields.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(SelectFields)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        SelectFields.setStatusBar(self.statusbar)

        self.retranslateUi(SelectFields)
        QtCore.QMetaObject.connectSlotsByName(SelectFields)

    def retranslateUi(self, SelectFields):
        SelectFields.setWindowTitle(QtGui.QApplication.translate("SelectFields", "Sort columns and show/hide /", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("SelectFields", "List of attributes", None, QtGui.QApplication.UnicodeUTF8))
        self.btnApply.setText(QtGui.QApplication.translate("SelectFields", "Apply", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    SelectFields = QtGui.QMainWindow()
    ui = Ui_SelectFields()
    ui.setupUi(SelectFields)
    SelectFields.show()
    sys.exit(app.exec_())

