from PyQt4 import QtCore
import threading

"""
	Just a small EventDispatcher to distribute application-wide events.
"""

class EventDispatcher(  QtCore.QObject ):
	pass

event = EventDispatcher()

