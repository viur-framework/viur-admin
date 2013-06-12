#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from event import event
from datetime import datetime, date, time, tzinfo
from priorityqueue import editBoneSelector

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class DateBone:
	pass


class DateEditBone( QtGui.QWidget ):
	def __init__(self, modulName, boneName, readOnly, hasDate, hasTime, *args, **kwargs ):
		super( DateEditBone,  self ).__init__( *args, **kwargs )
		
		self.boneName = boneName
		self.layout = QtGui.QHBoxLayout( self ) 
		
		self.time = hasDate
		self.date = hasTime
		
		#builds inputspecific Widgets
		if (self.time and self.date):#(...skelStructure ...) #date AND time
			self.lineEdit = QtGui.QDateTimeEdit(self)
			self.lineEdit.setGeometry(QtCore.QRect(170, 50, 173, 20))
			self.lineEdit.setAccelerated(False)
			self.lineEdit.setCalendarPopup(True)
		elif (self.date): # date only
			self.lineEdit = QtGui.QDateEdit(self)
			self.lineEdit.setGeometry(QtCore.QRect(190, 90, 110, 22))
			self.lineEdit.setCalendarPopup(True)
		else: # time only
			self.lineEdit = QtGui.QTimeEdit(self)
			self.lineEdit.setGeometry(QtCore.QRect(190, 190, 118, 22))
			
		self.lineEdit.setObjectName(_fromUtf8(boneName))
		self.layout.addWidget( self.lineEdit )
		self.lineEdit.show()
		
	@staticmethod
	def fromSkelStructure( modulName, boneName, skelStructure ):
		readOnly = "readonly" in skelStructure[ boneName ].keys() and skelStructure[ boneName ]["readonly"]
		hasDate = skelStructure[boneName]["date"]
		hasTime = skelStructure[boneName]["time"]
		return( DateEditBone( modulName, boneName, readOnly, hasDate, hasTime ) )
	
	def unserialize(self, data):
		value = None
		if self.boneName in data.keys():
			value =  str(data[ self.boneName ])
		self.dt = datetime.now()
		if (self.time and self.date):#date AND time
			try:
				self.dt = datetime.strptime( value, "%d.%m.%Y %H:%M:%S" )
			except:
				pass
			self.lineEdit.setDateTime(QtCore.QDateTime(QtCore.QDate(self.dt.year, self.dt.month, self.dt.day), QtCore.QTime(self.dt.hour, self.dt.minute, self.dt.second)))
		elif (self.date): # date only
			try:
				self.dt = datetime.strptime( value, "%d.%m.%Y" )
			except:
				pass
			self.lineEdit.setDate(QtCore.QDate(self.dt.year, self.dt.month, self.dt.day))
		else: # time only
			try:
				self.dt = datetime.strptime( value, "%H:%M:%S" )
			except:
				pass
			self.lineEdit.setTime(QtCore.QTime(self.dt.hour, self.dt.minute, self.dt.second))
	
	def serializeForPost(self):
		erg=""
		if (self.time and self.date):#date AND time
			erg=self.lineEdit.dateTime().toString("dd.MM.yyyy hh:mm:ss")
		elif (self.date): # date only
			erg=self.lineEdit.date().toString("dd.MM.yyyy")
		else: # time only
			erg=self.lineEdit.time().toString("hh:mm:ss")
		return( { self.boneName: erg} )

	def serializeForDocument(self):
		return( self.serialize( ) )

def CheckForDateBone(  modulName, boneName, skelStucture ):
	return( skelStucture[boneName]["type"]=="date" )

editBoneSelector.insert( 2, CheckForDateBone, DateEditBone )
