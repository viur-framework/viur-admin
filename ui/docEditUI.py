# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'docEdit.ui'
#
# Created: Tue Jun 11 11:37:24 2013
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

class Ui_DocEdit(object):
    def setupUi(self, DocEdit):
        DocEdit.setObjectName(_fromUtf8("DocEdit"))
        DocEdit.resize(531, 543)
        self.horizontalLayout_2 = QtGui.QHBoxLayout(DocEdit)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.btnImport = QtGui.QPushButton(DocEdit)
        self.btnImport.setObjectName(_fromUtf8("btnImport"))
        self.verticalLayout.addWidget(self.btnImport)
        self.treeWidget = QtGui.QTreeWidget(DocEdit)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.treeWidget.sizePolicy().hasHeightForWidth())
        self.treeWidget.setSizePolicy(sizePolicy)
        self.treeWidget.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.treeWidget.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.treeWidget.setObjectName(_fromUtf8("treeWidget"))
        self.treeWidget.headerItem().setText(0, _fromUtf8("Structure"))
        self.verticalLayout.addWidget(self.treeWidget)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.btnNewHeading = QtGui.QPushButton(DocEdit)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/text/headline_add.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnNewHeading.setIcon(icon)
        self.btnNewHeading.setObjectName(_fromUtf8("btnNewHeading"))
        self.gridLayout.addWidget(self.btnNewHeading, 0, 0, 1, 1)
        self.btnNewImage = QtGui.QPushButton(DocEdit)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/text/image_add.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnNewImage.setIcon(icon1)
        self.btnNewImage.setObjectName(_fromUtf8("btnNewImage"))
        self.gridLayout.addWidget(self.btnNewImage, 1, 0, 1, 1)
        self.btnNewText = QtGui.QPushButton(DocEdit)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/text/text_add.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnNewText.setIcon(icon2)
        self.btnNewText.setObjectName(_fromUtf8("btnNewText"))
        self.gridLayout.addWidget(self.btnNewText, 0, 1, 1, 1)
        self.btnSave = QtGui.QPushButton(DocEdit)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(_fromUtf8("icons/success.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnSave.setIcon(icon3)
        self.btnSave.setObjectName(_fromUtf8("btnSave"))
        self.gridLayout.addWidget(self.btnSave, 3, 0, 1, 2)
        self.btnNewTable = QtGui.QPushButton(DocEdit)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(_fromUtf8("icons/actions/text/table_add.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnNewTable.setIcon(icon4)
        self.btnNewTable.setObjectName(_fromUtf8("btnNewTable"))
        self.gridLayout.addWidget(self.btnNewTable, 1, 1, 1, 1)
        self.boxExtensions = QtGui.QGroupBox(DocEdit)
        self.boxExtensions.setObjectName(_fromUtf8("boxExtensions"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.boxExtensions)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.widget = QtGui.QWidget(self.boxExtensions)
        self.widget.setObjectName(_fromUtf8("widget"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.widget)
        self.verticalLayout_3.setMargin(0)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.cbExtensions = QtGui.QComboBox(self.widget)
        self.cbExtensions.setObjectName(_fromUtf8("cbExtensions"))
        self.verticalLayout_3.addWidget(self.cbExtensions)
        self.btnAddExtension = QtGui.QPushButton(self.widget)
        self.btnAddExtension.setObjectName(_fromUtf8("btnAddExtension"))
        self.verticalLayout_3.addWidget(self.btnAddExtension)
        self.verticalLayout_2.addWidget(self.widget)
        self.gridLayout.addWidget(self.boxExtensions, 2, 0, 1, 2)
        self.verticalLayout.addLayout(self.gridLayout)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.scrollArea = QtGui.QScrollArea(DocEdit)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName(_fromUtf8("scrollArea"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 253, 527))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.horizontalLayout.addWidget(self.scrollArea)
        self.horizontalLayout_2.addLayout(self.horizontalLayout)

        self.retranslateUi(DocEdit)
        QtCore.QMetaObject.connectSlotsByName(DocEdit)

    def retranslateUi(self, DocEdit):
        DocEdit.setWindowTitle(_translate("DocEdit", "Form", None))
        self.btnImport.setText(_translate("DocEdit", "Import/Export", None))
        self.treeWidget.setSortingEnabled(False)
        self.btnNewHeading.setText(_translate("DocEdit", "New caption", None))
        self.btnNewImage.setText(_translate("DocEdit", "New Image", None))
        self.btnNewText.setText(_translate("DocEdit", "New Text", None))
        self.btnSave.setText(_translate("DocEdit", "Apply", None))
        self.btnNewTable.setText(_translate("DocEdit", "New Table", None))
        self.boxExtensions.setTitle(_translate("DocEdit", "Extensions", None))
        self.btnAddExtension.setText(_translate("DocEdit", "Add", None))

