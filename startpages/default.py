#!/usr/bin/python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from config import conf

"""
	Displayes the ViUR Logo
"""

class DefaultWidget(QtGui.QWidget):

	def __init__(self):
		super(DefaultWidget, self).__init__()
		layout = QtGui.QVBoxLayout()
		self.setLayout( layout )
		scrollArea = QtGui.QScrollArea( self )
		self.layout().addWidget( scrollArea )
		imgLbl = QtGui.QLabel( scrollArea )
		imgLbl.setPixmap( QtGui.QPixmap( "icons/viur_splash.png" ) )
		scrollArea.setWidget( imgLbl )

