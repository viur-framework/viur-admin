#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt4 import QtCore
from network import NetworkService, RequestGroup, RequestWrapper
from priorityqueue import protocolWrapperInstanceSelector

class TaskWrapper( QtCore.QObject ):
	maxCacheTime = 60 #Cache results for max. 60 Seconds
	updateDelay = 1500 #1,5 Seconds gracetime before reloading
	
	updatingSucceeded = QtCore.pyqtSignal( (str,) ) #Adding/Editing an entry succeeded
	updatingFailedError = QtCore.pyqtSignal( (str,) ) #Adding/Editing an entry failed due to network/server error
	updatingDataAvaiable = QtCore.pyqtSignal( (str, dict, bool) ) #Adding/Editing an entry failed due to missing fields
	modulStructureAvaiable = QtCore.pyqtSignal() #We fetched the structure for this modul and that data is now avaiable
	busyStateChanged = QtCore.pyqtSignal( (bool,) ) #If true, im busy right now
	
	def __init__( self, modul, *args, **kwargs ):
		super( TaskWrapper, self ).__init__()
		self.modul = modul
		self.busy = False
		#self.editStructure = None # Warning: This depends on the currently edited task!!
		protocolWrapperInstanceSelector.insert( 1, self.checkForOurModul, self )

	def checkForOurModul( self, modulName ):
		return( self.modul==modulName )
	

	def edit( self, key, **kwargs ):
		req = NetworkService.request("/%s/execute/%s" % ( self.modul, key ), kwargs, secure=(len(kwargs.keys())>0), finishedHandler=self.onSaveResult )
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
		if data["action"] in ["addSuccess"]: #Saving succeeded
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


TaskWrapper("_tasks") #We statically instance exactly one taskWrapper