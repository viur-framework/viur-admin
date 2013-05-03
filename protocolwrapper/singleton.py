#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt4 import QtCore
from network import NetworkService, RequestGroup
from time import time
import weakref
from priorityqueue import protocolWrapperClassSelector, protocolWrapperInstanceSelector
from collections import OrderedDict

class SingletonWrapper( QtCore.QObject ):
	maxCacheTime = 60 #Cache results for max. 60 Seconds
	updateDelay = 1500 #1,5 Seconds gracetime before reloading
	
	def __init__( self, modul, *args, **kwargs ):
		super( SingletonWrapper, self ).__init__()
		self.modul = modul
		self.structure = None
		NetworkService.request( "/%s/edit" % self.modul, successHandler=self.onStructureAvaiable )
		print("Initializing SingletonWrapper for modul %s" % self.modul )
		protocolWrapperInstanceSelector.insert( 1, self.checkForOurModul, self )
		self.deferedTaskQueue = []

	def checkForOurModul( self, modulName ):
		return( self.modul==modulName )
	
	def onStructureAvaiable( self, req ):
		tmp = NetworkService.decode( req )
		self.structure = OrderedDict()
		for k,v in tmp["structure"]:
			self.structure[ k ] = v
		self.emit( QtCore.SIGNAL("onModulStructureAvaiable()") )
	
	def callDefered( self, callback, *args, **kwargs ):
		self.deferedTaskQueue.append( ( weakref.ref( callback.__self__), callback.__name__, args, kwargs ) )
		QtCore.QTimer.singleShot( 25, self.doCallDefered )
	
	def doCallDefered( self, *args, **kwargs ):
		weakSelf, callName, fargs, fkwargs = self.deferedTaskQueue.pop(0)
		callFunc = weakSelf()
		if callFunc is not None:
			targetFunc = getattr( callFunc, callName )
			targetFunc( *fargs, **fkwargs )

	def edit( self, cbSuccess, cbMissing, cbError, **kwargs ):
		req = NetworkService.request("/%s/edit/" % ( self.modul ), kwargs, secure=True, finishedHandler=self.onSaveResult )
		req.wrapperCbSuccessFuncSelf = weakref.ref( cbSuccess.__self__)
		req.wrapperCbSuccessFuncName = cbSuccess.__name__
		req.wrapperCbMissingFuncSelf = weakref.ref( cbMissing.__self__)
		req.wrapperCbMissingFuncName = cbMissing.__name__
		req.wrapperCbErrorFuncSelf = weakref.ref( cbError.__self__)
		req.wrapperCbErrorFuncName = cbError.__name__

	def delayEmitEntriesChanged( self, *args, **kwargs ):
		"""
			Give the GAE a chance to apply recent changes and then
			force all open views of that modul to reload its data
		"""
		QtCore.QTimer.singleShot( self.updateDelay, self.emitEntriesChanged )

	def onSaveResult( self, req ):
		try:
			data = NetworkService.decode( req )
		except: #Something went wrong, call ErrorHandler
			errorFuncSelf = req.wrapperCbErrorFuncSelf()
			if errorFuncSelf:
				errorFunc = getattr( errorFuncSelf, req.wrapperCbErrorFuncName )
				errorFunc( QtCore.QCoreApplication.translate("ListWrapper", "There was an error saving your changes") )
		if data=="OKAY": #Saving succeeded
			QtCore.QTimer.singleShot( self.updateDelay, self.emitEntriesChanged )
			successFuncSelf = req.wrapperCbSuccessFuncSelf()
			if successFuncSelf:
				successFunc = getattr( successFuncSelf, req.wrapperCbSuccessFuncName )
				successFunc()
		else: #There were missing fields
			missingFuncSelf = req.wrapperCbMissingFuncSelf()
			if missingFuncSelf:
				missingFunc = getattr( missingFuncSelf, req.wrapperCbMissingFuncName )
				missingFunc( data )
	
	def emitEntriesChanged( self, *args, **kwargs ):
		self.emit( QtCore.SIGNAL("entitiesChanged()") )

		
def CheckForSingletonModul( modulName, modulList ):
	modulData = modulList[ modulName ]
	if "handler" in modulData.keys() and (modulData["handler"]=="singleton" or modulData["handler"].startswith("singleton.")):
		return( True )
	return( False )
	
protocolWrapperClassSelector.insert( 0, CheckForSingletonModul, SingletonWrapper )
