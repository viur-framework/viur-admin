# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'admin.ui'
#
# Created: Mon Nov 24 18:30:24 2014
# by: PyQt5 UI code generator 5.3.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(983, 707)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/viur_logo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setIconSize(QtCore.QSize(32, 32))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_2.setSpacing(30)
        self.horizontalLayout_2.setContentsMargins(15, 15, 15, 20)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.treeWidget = QtWidgets.QTreeWidget(self.centralwidget)
        self.treeWidget.setMinimumSize(QtCore.QSize(300, 0))
        self.treeWidget.setMaximumSize(QtCore.QSize(300, 16777215))
        self.treeWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.treeWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.treeWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.treeWidget.setColumnCount(2)
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(1, "2")
        self.treeWidget.header().setVisible(False)
        self.horizontalLayout_2.addWidget(self.treeWidget)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.widget = QtWidgets.QWidget(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setMinimumSize(QtCore.QSize(0, 100))
        self.widget.setMaximumSize(QtCore.QSize(16777215, 100))
        self.widget.setObjectName("widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.iconLbl = QtWidgets.QLabel(self.widget)
        self.iconLbl.setObjectName("iconLbl")
        self.horizontalLayout.addWidget(self.iconLbl)
        self.modulLbl = QtWidgets.QLabel(self.widget)
        font = QtGui.QFont()
        font.setPointSize(22)
        font.setBold(False)
        font.setWeight(50)
        self.modulLbl.setFont(font)
        self.modulLbl.setObjectName("modulLbl")
        self.horizontalLayout.addWidget(self.modulLbl)
        spacerItem = QtWidgets.QSpacerItem(368, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addWidget(self.widget)
        self.stackedWidget = QtWidgets.QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName("stackedWidget")
        self.verticalLayout.addWidget(self.stackedWidget)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setEnabled(True)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 983, 22))
        self.menubar.setObjectName("menubar")
        self.menuInfo = QtWidgets.QMenu(self.menubar)
        self.menuInfo.setObjectName("menuInfo")
        self.menuErweitert = QtWidgets.QMenu(self.menubar)
        self.menuErweitert.setObjectName("menuErweitert")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionQuit = QtWidgets.QAction(MainWindow)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("icons/onebiticonset/onebit_35.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionQuit.setIcon(icon1)
        self.actionQuit.setObjectName("actionQuit")
        self.actionErste_Schritte = QtWidgets.QAction(MainWindow)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("icons/onebiticonset/021.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionErste_Schritte.setIcon(icon2)
        self.actionErste_Schritte.setObjectName("actionErste_Schritte")
        self.actionHelp = QtWidgets.QAction(MainWindow)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("icons/onebiticonset/022.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionHelp.setIcon(icon3)
        self.actionHelp.setShortcut("")
        self.actionHelp.setObjectName("actionHelp")
        self.actionAbout = QtWidgets.QAction(MainWindow)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap("icons/viur_win.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionAbout.setIcon(icon4)
        self.actionAbout.setObjectName("actionAbout")
        self.actionLogout = QtWidgets.QAction(MainWindow)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap("icons/onebiticonset/onebit_24.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionLogout.setIcon(icon5)
        self.actionLogout.setObjectName("actionLogout")
        self.actionTasks = QtWidgets.QAction(MainWindow)
        self.actionTasks.setObjectName("actionTasks")
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
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "ViUR Admin"))
        self.treeWidget.setSortingEnabled(False)
        self.treeWidget.headerItem().setText(0, _translate("MainWindow", "Module"))
        self.iconLbl.setText(_translate("MainWindow", "TextLabel"))
        self.modulLbl.setText(_translate("MainWindow", "TextLabel"))
        self.menuInfo.setTitle(_translate("MainWindow", "Info"))
        self.menuErweitert.setTitle(_translate("MainWindow", "Advanced"))
        self.actionQuit.setText(_translate("MainWindow", "Beenden"))
        self.actionErste_Schritte.setText(_translate("MainWindow", "Erste Schritte"))
        self.actionHelp.setText(_translate("MainWindow", "Help"))
        self.actionAbout.setText(_translate("MainWindow", "About"))
        self.actionLogout.setText(_translate("MainWindow", "Ausloggen"))
        self.actionTasks.setText(_translate("MainWindow", "Tasks"))

