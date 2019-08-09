# -*- coding: utf-8 -*-
from typing import Any, Dict, List

from PyQt5 import QtGui, QtWidgets


class DefaultWidget(QtWidgets.QWidget):
	"""Displayes the ViUR Logo
	"""

	def __init__(self, *args: Any, **kwargs: Any):
		super(DefaultWidget, self).__init__(*args, **kwargs)
		layout = QtWidgets.QVBoxLayout()
		self.setLayout(layout)
		layout.setContentsMargins(0, 0, 0, 0)
		scrollArea = QtWidgets.QScrollArea(self)
		self.layout().addWidget(scrollArea)
		imgLbl = QtWidgets.QLabel(scrollArea)
		imgLbl.setPixmap(QtGui.QPixmap(":icons/viur_splash.png"))
		scrollArea.setWidget(imgLbl)
