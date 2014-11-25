#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, date, time, tzinfo

from PyQt5 import QtCore, QtGui, QtWidgets
from event import event
from priorityqueue import editBoneSelector
from utils import wheelEventFilter


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s


class FixedDateTimeEdit(QtWidgets.QDateTimeEdit):
    """
        Subclass of SpinBox which doesn't accept QWheelEvents if it doesnt have focus
    """

    def __init__(self, *args, **kwargs):
        super(FixedDateTimeEdit, self).__init__(*args, **kwargs)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.installEventFilter(wheelEventFilter)

    def focusInEvent(self, e):
        self.setFocusPolicy(QtCore.Qt.WheelFocus)
        super(FixedDateTimeEdit, self).focusInEvent(e)

    def focusOutEvent(self, e):
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        super(FixedDateTimeEdit, self).focusOutEvent(e)


class FixedDateEdit(QtWidgets.QDateEdit):
    """
        Subclass of SpinBox which doesn't accept QWheelEvents if it doesnt have focus
    """

    def __init__(self, *args, **kwargs):
        super(FixedDateEdit, self).__init__(*args, **kwargs)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.installEventFilter(wheelEventFilter)

    def focusInEvent(self, e):
        self.setFocusPolicy(QtCore.Qt.WheelFocus)
        super(FixedDateEdit, self).focusInEvent(e)

    def focusOutEvent(self, e):
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        super(FixedDateEdit, self).focusOutEvent(e)


class FixedTimeEdit(QtWidgets.QTimeEdit):
    """
        Subclass of SpinBox which doesn't accept QWheelEvents if it doesnt have focus
    """

    def __init__(self, *args, **kwargs):
        super(FixedTimeEdit, self).__init__(*args, **kwargs)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.installEventFilter(wheelEventFilter)

    def focusInEvent(self, e):
        self.setFocusPolicy(QtCore.Qt.WheelFocus)
        super(FixedTimeEdit, self).focusInEvent(e)

    def focusOutEvent(self, e):
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        super(FixedTimeEdit, self).focusOutEvent(e)


class DateEditBone(QtWidgets.QWidget):
    def __init__(self, modulName, boneName, readOnly, hasDate, hasTime, *args, **kwargs):
        super(DateEditBone, self).__init__(*args, **kwargs)

        self.boneName = boneName
        self.layout = QtGui.QHBoxLayout(self)

        self.time = hasTime
        self.date = hasDate

        # builds inputspecific Widgets
        if (self.time and self.date):  #(...skelStructure ...) #date AND time
            self.lineEdit = FixedDateTimeEdit(self)
            self.lineEdit.setGeometry(QtCore.QRect(170, 50, 173, 20))
            self.lineEdit.setAccelerated(False)
            self.lineEdit.setCalendarPopup(True)
        elif (self.date):  # date only
            self.lineEdit = FixedDateEdit(self)
            self.lineEdit.setGeometry(QtCore.QRect(190, 90, 110, 22))
            self.lineEdit.setCalendarPopup(True)
        else:  # time only
            self.lineEdit = FixedTimeEdit(self)
            self.lineEdit.setGeometry(QtCore.QRect(190, 190, 118, 22))

        self.lineEdit.setObjectName(_fromUtf8(boneName))
        self.layout.addWidget(self.lineEdit)
        self.lineEdit.show()

    @staticmethod
    def fromSkelStructure(modulName, boneName, skelStructure):
        readOnly = "readonly" in skelStructure[boneName].keys() and skelStructure[boneName]["readonly"]
        hasDate = skelStructure[boneName]["date"]
        hasTime = skelStructure[boneName]["time"]
        return ( DateEditBone(modulName, boneName, readOnly, hasDate, hasTime) )

    def unserialize(self, data):
        value = None
        if self.boneName in data.keys():
            value = str(data[self.boneName])
        self.dt = datetime.now()
        if (self.time and self.date):  # date AND time
            try:
                self.dt = datetime.strptime(value, "%d.%m.%Y %H:%M:%S")
            except:
                pass
            self.lineEdit.setDateTime(QtCore.QDateTime(QtCore.QDate(self.dt.year, self.dt.month, self.dt.day),
                                                       QtCore.QTime(self.dt.hour, self.dt.minute, self.dt.second)))
        elif (self.date):  # date only
            try:
                self.dt = datetime.strptime(value, "%d.%m.%Y")
            except:
                pass
            self.lineEdit.setDate(QtCore.QDate(self.dt.year, self.dt.month, self.dt.day))
        else:  # time only
            try:
                self.dt = datetime.strptime(value, "%H:%M:%S")
            except:
                pass
            self.lineEdit.setTime(QtCore.QTime(self.dt.hour, self.dt.minute, self.dt.second))

    def serializeForPost(self):
        erg = ""
        if (self.time and self.date):  # date AND time
            erg = self.lineEdit.dateTime().toString("dd.MM.yyyy hh:mm:ss")
        elif (self.date):  # date only
            erg = self.lineEdit.date().toString("dd.MM.yyyy")
        else:  # time only
            erg = self.lineEdit.time().toString("hh:mm:ss")
        return ( {self.boneName: erg} )

    def serializeForDocument(self):
        return ( self.serialize() )


def CheckForDateBone(modulName, boneName, skelStucture):
    return ( skelStucture[boneName]["type"] == "date" )


editBoneSelector.insert(2, CheckForDateBone, DateEditBone)
