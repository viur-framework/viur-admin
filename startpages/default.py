#!/usr/bin/python
# -*- coding: utf-8 -*-
from PySide import QtGui, QtCore
from config import conf

"""
	Displayes the ViUR Logo
"""

class DefaultWidget(QtGui.QWidget):

	def __init__(self):
		super(DefaultWidget, self).__init__()
		self.layout = QtGui.QVBoxLayout()
		self.setLayout( self.layout )
		self.imgLbl = QtGui.QLabel( self )
		self.imgLbl.setPixmap( QtGui.QPixmap( "icons/viur_splash.png" ) )
		self.layout.addWidget( self.imgLbl )

