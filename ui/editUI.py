# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\edit.ui'
#
# Created: Thu Jul 18 16:19:10 2013
#      by: PyQt4 UI code generator 4.9.5
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Edit(object):
    def setupUi(self, Edit):
        Edit.setObjectName(_fromUtf8("Edit"))
        Edit.resize(820, 621)
        self.verticalLayout = QtGui.QVBoxLayout(Edit)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tabWidget = QtGui.QTabWidget(Edit)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.verticalLayout.addWidget(self.tabWidget)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.btnReset = QtGui.QPushButton(Edit)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/undo_small.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnReset.setIcon(icon)
        self.btnReset.setObjectName(_fromUtf8("btnReset"))
        self.horizontalLayout_2.addWidget(self.btnReset)
        self.btnClose = QtGui.QPushButton(Edit)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/delete_small.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnClose.setIcon(icon1)
        self.btnClose.setObjectName(_fromUtf8("btnClose"))
        self.horizontalLayout_2.addWidget(self.btnClose)
        spacerItem = QtGui.QSpacerItem(254, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.btnPreview = QtGui.QPushButton(Edit)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/preview_small.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnPreview.setIcon(icon2)
        self.btnPreview.setObjectName(_fromUtf8("btnPreview"))
        self.horizontalLayout_2.addWidget(self.btnPreview)
        spacerItem1 = QtGui.QSpacerItem(254, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.btnSaveClose = QtGui.QPushButton(Edit)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/save.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSaveClose.setIcon(icon3)
        self.btnSaveClose.setObjectName(_fromUtf8("btnSaveClose"))
        self.horizontalLayout_2.addWidget(self.btnSaveClose)
        self.btnSaveContinue = QtGui.QPushButton(Edit)
        self.btnSaveContinue.setIcon(icon3)
        self.btnSaveContinue.setObjectName(_fromUtf8("btnSaveContinue"))
        self.horizontalLayout_2.addWidget(self.btnSaveContinue)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(Edit)
        self.tabWidget.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(Edit)

    def retranslateUi(self, Edit):
        Edit.setWindowTitle(QtGui.QApplication.translate("Edit", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.btnReset.setText(QtGui.QApplication.translate("Edit", "Reset", None, QtGui.QApplication.UnicodeUTF8))
        self.btnClose.setText(QtGui.QApplication.translate("Edit", "Close", None, QtGui.QApplication.UnicodeUTF8))
        self.btnPreview.setText(QtGui.QApplication.translate("Edit", "Preview", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSaveClose.setText(QtGui.QApplication.translate("Edit", "Save and close", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSaveContinue.setText(QtGui.QApplication.translate("Edit", "Save and continue", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Edit = QtGui.QWidget()
    ui = Ui_Edit()
    ui.setupUi(Edit)
    Edit.show()
    sys.exit(app.exec_())

