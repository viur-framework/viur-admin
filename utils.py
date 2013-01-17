#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
import math
import os, os.path
import os
from config import conf
from network import NetworkService

class RegisterQueue():
	"""
	Propagates through the QT-Eventqeue and collects all Handlers able to scope with the current request
	"""
	def __init__( self ):
		self.queue = {}
	
	def registerHandler( self, priority, handler ):
		"""
		Registers an Object with given priority
		
		@type priority: int
		@param priority: Priority of the handler. The higest one wins.
		@type handler: Object
		"""
		if not priority in self.queue.keys():
			self.queue[ priority ] = []
		self.queue[ priority ].append( handler )
	
	def getBest(self):
		"""
		Returns the handler with the higest priority.
		If 2 or more handlers claim the same higest priority, the first one is returned
		
		@return: Object
		"""
		prios = [ x for x in self.queue.keys() ]
		prios.sort()
		return( self.queue[ prios[-1] ][0] )
	
	def getAll(self):
		"""
		Returns all handlers in ascending order
		
		@return: [Object]
		"""
		prios = [ x for x in self.queue.keys() ]
		prios.sort()
		res = []
		for p in prios:
			for item in self.queue[p]:
				res.append(item)
		return( res )


class Overlay(QtGui.QWidget):
	"""
	Blocks its parent widget by displaying a busy or a short message over
	the parent.
	"""
	
	BUSY = "busy"
	MISSING = "missing"
	ERROR = "error"
	SUCCESS = "okay"
	
	INFO_DURATION = 20 # 2 seconds
	WARNING_DURATION = 20
	ERROR_DURATION = 20
	
	def __init__(self, parent = None):
		"""
		@type parent: QWidget
		"""
		QtGui.QWidget.__init__(self, parent)
		palette = QtGui.QPalette(self.palette())
		palette.setColor(palette.Background, QtCore.Qt.transparent)
		self.setPalette(palette)
		self.status = None
		animIdx= 0
		self.okayImage = QtGui.QImage( "icons/status/success.png" )
		self.missingImage = QtGui.QImage( "icons/status/missing.png" )
		self.errorImage = QtGui.QImage( "icons/status/error.png" )
		self.timer = None
		self.resize( QtCore.QSize( 1, 1) )
		self.hide()

	def paintEvent(self, event):
		"""
		Draws the message/busy overlay
		
		See http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/html/qwidget.html#paintEvent
		"""
		painter = QtGui.QPainter()
		painter.begin(self)
		painter.setRenderHint(QtGui.QPainter.Antialiasing)
		if self.status == self.BUSY:
			#painter.fillRect(event.rect(), QtGui.QBrush(QtGui.QColor(0, 0, 0, 128) ) )
			animIdx= int( (self.counter)%32 )
			painter.pen().setWidth( 4 )
			for i in range(32):
				color = QtGui.QColor( max( 127, 255-6*((animIdx-i)%32)), 0, 0, min(255, self.counter*10) )
				painter.setPen( color )
				painter.drawLine(
					self.width()/2 + 30 * math.cos(2 * math.pi * i / 32.0),
					self.height()/2 + 30 * math.sin(2 * math.pi * i / 32.0),
					self.width()/2 + 40 * math.cos(2 * math.pi * i / 32.0),
					self.height()/2 + 40 * math.sin(2 * math.pi * i / 32.0),
					)
			painter.pen().setWidth( 1 )
			painter.setPen(QtGui.QColor( 0,0,0, min(255, self.counter*10) ))
			fm = QtGui.QFontMetrics( painter.font() )
			fontWidth = fm.width(self.message)
			painter.drawText( self.width()/2-fontWidth/2, (self.height()/2)+55, self.message )
		elif self.status==self.SUCCESS:
			if self.counter>self.INFO_DURATION-10:
				painter.setOpacity((20-self.counter)/10.0)
			#painter.fillRect(event.rect(), QtGui.QBrush(QtGui.QColor(0, 0, 0, 128) ) )
			painter.drawImage( (self.width()/2-self.okayImage.width()/2),(self.height()/2-self.okayImage.height()/2), self.okayImage )
			fm = QtGui.QFontMetrics( painter.font() )
			fontWidth = fm.width(self.message)
			painter.setPen(QtGui.QColor( 0,0,0 ))
			painter.drawText( self.width()/2-fontWidth/2, (self.height()/2+self.okayImage.height()/2)+25, self.message )
			if self.counter > self.INFO_DURATION:
				self.clear(True)
		elif self.status==self.MISSING:
			if self.counter>self.WARNING_DURATION-10:
				painter.setOpacity((20-self.counter)/10.0)
			#painter.fillRect(event.rect(), QtGui.QBrush(QtGui.QColor(0, 0, 0, 128) ) )
			painter.drawImage( (self.width()/2-self.missingImage.width()/2),(self.height()/2-self.missingImage.height()/2), self.missingImage )
			fm = QtGui.QFontMetrics( painter.font() )
			fontWidth = fm.width(self.message)
			painter.setPen(QtGui.QColor( 0,0,0 ))
			painter.drawText( self.width()/2-fontWidth/2, (self.height()/2+self.missingImage.height()/2)+25, self.message )
			if self.counter > self.WARNING_DURATION:
				self.clear(True)
		elif self.status==self.ERROR:
			if self.counter>self.ERROR_DURATION-10:
				painter.setOpacity((20-self.counter)/10.0)
			painter.fillRect(event.rect(), QtGui.QBrush(QtGui.QColor(0, 0, 0, 128) ) )
			painter.drawImage( (self.width()/2-self.errorImage.width()/2),(self.height()/2-self.errorImage.height()/2), self.errorImage )
			fm = QtGui.QFontMetrics( painter.font() )
			fontWidth = fm.width(self.message)
			painter.setPen(QtGui.QColor( 0,0,0 ))
			painter.drawText( self.width()/2-fontWidth/2, (self.height()/2+self.errorImage.height()/2)+25, self.message )
			if self.counter > self.ERROR_DURATION:
				self.clear(True)
		painter.end()

	def start( self ):
		"""
		Starts displaying.
		Dont call this directly
		"""
		if self.timer:
			self.show()
			return
		self.resize( self.parent().size() )
		self.parent().setEnabled(False)
		self.counter = 0
		self.first = True
		self.timer = self.startTimer(100)
		self.show()

	def clear( self, force=False ):
		"""
		Clears the overlay.
		Its parent becomes accessible again
		@param force: If True, it clears the overlay istantly. Otherwise, only overlays in state busy will be cleared; if there currently displaying an error/success message, the will persist (for the rest of thair display-time)
		@type force: Bool
		"""
		if not (force or self.status==self.BUSY):
			return
		if self.timer:
			self.killTimer(self.timer)
			self.timer = None
		self.status = None
		self.resize( QtCore.QSize( 1, 1) )
		self.parent().setEnabled(True)
		self.hide()

	def inform( self, status, message="" ):
		"""
		Draws a informal message over its parent-widget's area.
		If type is not Overlay.BUSY, it clears automaticaly after a few seconds.
		
		@type status: One of [Overlay.BUSY, Overlay.MISSING, Overlay.ERROR, Overlay.SUCCESS]
		@param status: Type of the message displayed. Sets the icon and the display duration.
		@type message: string
		@param message: Text to display
		"""
		assert( status in [ self.BUSY, self.MISSING, self.ERROR, self.SUCCESS ] )
		self.status = status
		self.message = message
		if status!=self.BUSY:
			self.counter = 0
		self.start()
		
	def timerEvent(self, event):
		"""
		Draws the next frame in the animation.
		
		See http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/html/qobject.html#timerEvent
		"""
		self.resize( self.parent().size() )
		if self.first: #Give the parent a chance to find its final size
			self.first = False
			return
		self.counter += 1
		if self.counter>max( [self.ERROR_DURATION, self.INFO_DURATION, self.WARNING_DURATION] ) \
		and self.status!=self.BUSY:
			self.clear(True)
			return
		self.update()


def formatString( format, data, prefix=None ):
	""" Parses a String given by format and substitutes Placeholders using values specified by data.
	Syntax for Placeholders is $(%s). Its possible to traverse to subdictionarys by using a dot as seperator.
	If data is a list, the result each element from this list applied to the given string; joined by ", ".
	Example:
	data = {"name": "Test","subdict": {"a":"1","b":"2"}}
	formatString = "Name: $(name), subdict.a: $(subdict.a)"
	Result: "Name: Test, subdict.a: 1"
	
	@type format: String
	@param format: String contining the format
	@type data: List or Dict
	@param data: Data applied to the format String
	@return: String
	"""
	prefix = prefix or []
	if isinstance( data,  list ):
		return(", ".join( [ formatString( format, x, prefix ) for x in data ] ) )
	res = format
	if isinstance( data, str ):
		return( data )
	if not data:
		return( "" )
	for key in data.keys():
		if isinstance( data[ key ], dict ):
			res = formatString( res, data[key], prefix + [key] )
		elif isinstance( data[ key ], list ) and len( data[ key ] )>0 and isinstance( data[ key ][0], dict) :
			res = formatString( res, data[key][0], prefix + [key] )
		else:
			res = res.replace( "$(%s)" % (".".join( prefix + [key] ) ), str(data[key]) )
	return( res )

def showAbout( parent=None ):
	"""
	Shows the about-dialog
	"""
	try:
		import BUILD_CONSTANTS
		version = BUILD_CONSTANTS.BUILD_RELEASE_STRING
		vdate = BUILD_CONSTANTS.BUILD_TIMESTAMP
	except: #Local development or not a freezed Version
		vdate = "development version"
		version = "unknown"
		try:
			gitHead = open(".git/FETCH_HEAD", "r").read()
			for line in gitHead.splitlines():
				line = line.replace("\t", " ")
				if "branch 'master'" in line:
					version = line.split(" ")[0]
		except:
			pass
	appName = "Viur Informationssystem - Administration"
	appDescr = "© Mausbrand Informationssysteme GmbH\n"
	appDescr += "Version: %s\n" % vdate
	appDescr += "Revision: %s" % version
	QtGui.QMessageBox.about( parent, appName, appDescr )


