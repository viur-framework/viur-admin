#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt4 import QtCore
from network import NetworkService, RequestGroup, RequestWrapper
from time import time
import weakref
from priorityqueue import protocolWrapperClassSelector, protocolWrapperInstanceSelector
from collections import OrderedDict

class SingletonWrapper( QtCore.QObject ):
	maxCacheTime = 60 #Cache results for max. 60 Seconds
	updateDelay = 1500 #1,5 Seconds gracetime before reloading
	
	updatingSucceeded = QtCore.pyqtSignal( (str,) ) #Adding/Editing an entry succeeded
	updatingFailedError = QtCore.pyqtSignal( (str,) ) #Adding/Editing an entry failed due to network/server error
	updatingDataAvaiable = QtCore.pyqtSignal( (str, dict, bool) ) #Adding/Editing an entry failed due to missing fields
	modulStructureAvaiable = QtCore.pyqtSignal() #We fetched the structure for this modul and that data is now avaiable
	busyStateChanged = QtCore.pyqtSignal( (bool,) ) #If true, im busy right now
	
	def __init__( self, modul, *args, **kwargs ):
		super( SingletonWrapper, self ).__init__()
		self.modul = modul
		self.busy = True
		self.editStructure = None
		self.viewStructure = None
		protocolWrapperInstanceSelector.insert( 1, self.checkForOurModul, self )
		self.deferedTaskQueue = []
		req = NetworkService.request( "/getStructure/%s" % (self.modul), successHandler=self.onStructureAvaiable )

	def checkForOurModul( self, modulName ):
		return( self.modul==modulName )
	
	def onStructureAvaiable( self, req ):
		tmp = NetworkService.decode( req )
		if tmp is None:
			self.checkBusyStatus()
			return
		for stype, structlist in tmp.items():
			structure = OrderedDict()
			for k,v in structlist:
				structure[ k ] = v
			if stype=="viewSkel":
				self.viewStructure = structure
			elif stype=="editSkel":
				self.editStructure = structure
		self.modulStructureAvaiable.emit()
		self.checkBusyStatus()


	def edit( self, **kwargs ):
		req = NetworkService.request("/%s/edit" % ( self.modul ), kwargs, secure=(len(kwargs.keys())>0), finishedHandler=self.onSaveResult )
		if not kwargs:
			# This is our first request to fetch the data, dont show a missing hint
			req.wasInitial = True
		else:
			req.wasInitial = False
		self.checkBusyStatus()
		return( str( id( req ) ) )


	def onSaveResult( self, req ):
		try:
			data = NetworkService.decode( req )
		except: #Something went wrong, call ErrorHandler
			self.updatingFailedError.emit( str( id( req ) ) )
			return
		if data["action"] in ["editSuccess", "deleteSuccess"]: #Saving succeeded
			self.updatingSucceeded.emit( str( id( req ) ) )
			self.checkBusyStatus()
		else: #There were missing fields
			self.updatingDataAvaiable.emit( str( id( req ) ), data, req.wasInitial )
		self.checkBusyStatus()

	def checkBusyStatus( self ):
		busy = False
		for child in self.children():
			if isinstance( child, RequestWrapper ) or isinstance( child, RequestGroup ):
				if not child.hasFinished:
					busy = True
					break
		if busy != self.busy:
			self.busy = busy
			self.busyStateChanged.emit( busy )


def CheckForSingletonModul( modulName, modulList ):
	modulData = modulList[ modulName ]
	if "handler" in modulData.keys() and (modulData["handler"]=="singleton" or modulData["handler"].startswith("singleton.")):
		return( True )
	return( False )
	
protocolWrapperClassSelector.insert( 0, CheckForSingletonModul, SingletonWrapper )
