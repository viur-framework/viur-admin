#!/usr/bin/python
# -*- coding: utf-8 -*-
from PyQt5 import QtGui, QtWidgets

"""
	Displayes the ViUR Logo
"""


class DefaultWidget(QtWidgets.QWidget):
    def __init__(self):
        super(DefaultWidget, self).__init__()
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        scrollArea = QtWidgets.QScrollArea(self)
        self.layout().addWidget(scrollArea)
        imgLbl = QtWidgets.QLabel(scrollArea)
        imgLbl.setPixmap(QtGui.QPixmap(":icons/viur_splash.png"))
        scrollArea.setWidget(imgLbl)

