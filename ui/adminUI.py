# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'admin.ui'
#
# Created: Tue Jun 11 11:36:30 2013
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

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(926, 707)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/viur_logo.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setIconSize(QtCore.QSize(32, 32))
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.treeWidget = QtGui.QTreeWidget(self.centralwidget)
        self.treeWidget.setMinimumSize(QtCore.QSize(300, 0))
        self.treeWidget.setMaximumSize(QtCore.QSize(300, 16777215))
        self.treeWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.treeWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.treeWidget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.treeWidget.setColumnCount(2)
        self.treeWidget.setObjectName(_fromUtf8("treeWidget"))
        self.treeWidget.headerItem().setText(1, _fromUtf8("2"))
        self.treeWidget.header().setVisible(False)
        self.horizontalLayout_2.addWidget(self.treeWidget)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.widget = QtGui.QWidget(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setMinimumSize(QtCore.QSize(0, 100))
        self.widget.setMaximumSize(QtCore.QSize(16777215, 100))
        self.widget.setObjectName(_fromUtf8("widget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.widget)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.iconLbl = QtGui.QLabel(self.widget)
        self.iconLbl.setObjectName(_fromUtf8("iconLbl"))
        self.horizontalLayout.addWidget(self.iconLbl)
        self.modulLbl = QtGui.QLabel(self.widget)
        font = QtGui.QFont()
        font.setPointSize(22)
        font.setBold(False)
        font.setWeight(50)
        self.modulLbl.setFont(font)
        self.modulLbl.setObjectName(_fromUtf8("modulLbl"))
        self.horizontalLayout.addWidget(self.modulLbl)
        spacerItem = QtGui.QSpacerItem(368, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addWidget(self.widget)
        self.stackedWidget = QtGui.QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName(_fromUtf8("stackedWidget"))
        self.verticalLayout.addWidget(self.stackedWidget)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setEnabled(True)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 926, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuInfo = QtGui.QMenu(self.menubar)
        self.menuInfo.setObjectName(_fromUtf8("menuInfo"))
        self.menuErweitert = QtGui.QMenu(self.menubar)
        self.menuErweitert.setObjectName(_fromUtf8("menuErweitert"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.actionQuit = QtGui.QAction(MainWindow)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8("icons/onebiticonset/onebit_35.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionQuit.setIcon(icon1)
        self.actionQuit.setObjectName(_fromUtf8("actionQuit"))
        self.actionErste_Schritte = QtGui.QAction(MainWindow)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8("icons/onebiticonset/021.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionErste_Schritte.setIcon(icon2)
        self.actionErste_Schritte.setObjectName(_fromUtf8("actionErste_Schritte"))
        self.actionHelp = QtGui.QAction(MainWindow)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(_fromUtf8("icons/onebiticonset/022.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionHelp.setIcon(icon3)
        self.actionHelp.setShortcut(_fromUtf8(""))
        self.actionHelp.setObjectName(_fromUtf8("actionHelp"))
        self.actionAbout = QtGui.QAction(MainWindow)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(_fromUtf8("icons/Apexico_black.ico")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionAbout.setIcon(icon4)
        self.actionAbout.setObjectName(_fromUtf8("actionAbout"))
        self.actionLogout = QtGui.QAction(MainWindow)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(_fromUtf8("icons/onebiticonset/onebit_24.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionLogout.setIcon(icon5)
        self.actionLogout.setObjectName(_fromUtf8("actionLogout"))
        self.actionTasks = QtGui.QAction(MainWindow)
        self.actionTasks.setObjectName(_fromUtf8("actionTasks"))
        self.menuInfo.addAction(self.actionHelp)
        self.menuInfo.addSeparator()
        self.menuInfo.addAction(self.actionAbout)
        self.menuErweitert.addAction(self.actionTasks)
        self.menubar.addAction(self.menuInfo.menuAction())
        self.menubar.addAction(self.menuErweitert.menuAction())

        self.retranslateUi(MainWindow)
        self.stackedWidget.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "ViUR Admin", None))
        self.treeWidget.setSortingEnabled(False)
        self.treeWidget.headerItem().setText(0, _translate("MainWindow", "Module", None))
        self.iconLbl.setText(_translate("MainWindow", "TextLabel", None))
        self.modulLbl.setText(_translate("MainWindow", "TextLabel", None))
        self.menuInfo.setTitle(_translate("MainWindow", "Info", None))
        self.menuErweitert.setTitle(_translate("MainWindow", "Advanced", None))
        self.actionQuit.setText(_translate("MainWindow", "Beenden", None))
        self.actionErste_Schritte.setText(_translate("MainWindow", "Erste Schritte", None))
        self.actionHelp.setText(_translate("MainWindow", "Help", None))
        self.actionAbout.setText(_translate("MainWindow", "About", None))
        self.actionLogout.setText(_translate("MainWindow", "Ausloggen", None))
        self.actionTasks.setText(_translate("MainWindow", "Tasks", None))

