# -*- coding: utf-8 -*-
from typing import Any

__author__ = 'Stefan Kögl'

import os.path
import logging
from datetime import datetime
from PyQt5.QtWidgets import QLabel

logger = None
statusBarRef = None
statusBarLabel = None

def logToUser(message):
	global statusBarRef, statusBarLabel
	if not statusBarLabel and statusBarRef:
		statusBarLabel = QLabel()
		statusBarRef.addWidget(statusBarLabel)
		statusBarRef.addWidget(QLabel("     "))  # Spacer Item...
	if not statusBarLabel:
		return
	statusBarLabel.setText("[%s] %s" % (datetime.now().strftime("%H:%M:%S"), message))

def getStatusBar():
	global statusBarRef
	return statusBarRef

def prepareLogger(level: int) -> None:
	if level == "info":
		level = logging.INFO
	elif level == "debug":
		level = logging.DEBUG
	elif level == "warning":
		level = logging.WARNING
	elif level == "error":
		level = logging.ERROR
	elif level == "critical":
		level = logging.CRITICAL
	else:
		level = logging.DEBUG

	global logger
	if logger:
		return
	logger = logging.getLogger()
	# create logger with 'spam_application'
	logger.setLevel(level)
	# create file handler which logs even debug messages
	fh = logging.FileHandler(os.path.expanduser('~/.viur_admin.log'))
	fh.setLevel(logging.DEBUG)
	# create console handler with a higher log level
	ch = logging.StreamHandler()
	ch.setLevel(level)
	# create formatter and add it to the handlers
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s')
	fh.setFormatter(formatter)
	ch.setFormatter(formatter)
	# add the handlers to the logger
	logger.addHandler(fh)
	logger.addHandler(ch)


def getLogger(module: str) -> Any:
	global logger
	return logger.getChild(module)
