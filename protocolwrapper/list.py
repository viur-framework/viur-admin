#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide import QtCore
from network import NetworkService, RequestGroup, RequestWrapper
from time import time
import weakref
from priorityqueue import protocolWrapperClassSelector, protocolWrapperInstanceSelector
from collections import OrderedDict

class ListWrapper( QtCore.QObject ):
	maxCacheTime = 60 #Cache results for max. 60 Seconds
	updateDelay = 1500 #1,5 Seconds gracetime before reloading
	entitiesChanged = QtCore.Signal()
	busyStateChanged = QtCore.Signal( (bool,) ) #If true, im busy right now
	
	def __init__( self, modul, *args, **kwargs ):
		super( ListWrapper, self ).__init__()
		self.modul = modul
		self.dataCache = {}
		self.structure = None
		self.busy = False
		NetworkService.request( "/%s/edit/0" % self.modul, successHandler=self.onStructureAvaiable )
		print("Initializing ListWrapper for modul %s" % self.modul )
		protocolWrapperInstanceSelector.insert( 1, self.checkForOurModul, self )
		self.deferedTaskQueue = []
		self.checkBusyStatus()

	def checkBusyStatus( self ):
		busy = False
		for child in self.children():
			if isinstance( child, RequestWrapper ) and not child.hasFinished:
				busy = True
				break
		if busy != self.busy:
			self.busy = busy
			self.busyStateChanged.emit( busy )

	def checkForOurModul( self, modulName ):
		return( self.modul==modulName )
	
	def onStructureAvaiable( self, req ):
		tmp = NetworkService.decode( req )
		self.structure = OrderedDict()
		for k,v in tmp["structure"]:
			self.structure[ k ] = v
		self.emit( QtCore.SIGNAL("onModulStructureAvaiable()") )
		self.checkBusyStatus()
	
	def cacheKeyFromFilter( self, filters ):
		tmpList = list( filters.items() )
		tmpList.sort( key=lambda x: x[0] )
		return( "&".join( [ "%s=%s" % (k,v) for (k,v) in tmpList] ) )
	
	def queryData( self, callback, **kwargs ):
		print( "Querying data")
		key = self.cacheKeyFromFilter( kwargs )
		if key in self.dataCache.keys():
			ctime, data, cursor = self.dataCache[ key ]
			if ctime+self.maxCacheTime>time(): #This cache-entry is still valid
				self.deferedTaskQueue.append( ( weakref.ref( callback.__self__), callback.__name__, key ) )
				QtCore.QTimer.singleShot( 25, self.execDefered )
				#callback( None, data, cursor )
				return( key )
		#Its a cache-miss or cache too old
		r = NetworkService.request( "/%s/list" % self.modul, kwargs, successHandler=self.addCacheData )
		r.wrapperCbTargetFuncSelf = weakref.ref( callback.__self__)
		r.wrapperCbTargetFuncName = callback.__name__
		r.wrapperCbCacheKey = key
		self.checkBusyStatus()
		return( key )
	
	def execDefered( self, *args, **kwargs ):
		weakSelf, callName, key = self.deferedTaskQueue.pop(0)
		callFunc = weakSelf()
		if callFunc is not None:
			targetFunc = getattr( callFunc, callName )
			ctime, data, cursor = self.dataCache[ key ]
			targetFunc( key, data, cursor )
		self.checkBusyStatus()
	
	def addCacheData( self, req ):
		data = NetworkService.decode( req )
		cursor = None
		if "cursor" in data.keys():
			cursor=data["cursor"]
		self.dataCache[ req.wrapperCbCacheKey ] = (time(), data["skellist"], cursor)
		targetSelf = req.wrapperCbTargetFuncSelf()
		if targetSelf is not None:
			targetFunc = getattr( targetSelf, req.wrapperCbTargetFuncName )
			targetFunc( req.wrapperCbCacheKey, data["skellist"], cursor )
		self.checkBusyStatus()
			
	def add( self, cbSuccess, cbMissing, cbError, **kwargs ):
		req = NetworkService.request("/%s/add/" % ( self.modul ), kwargs, secure=True, finishedHandler=self.onSaveResult )
		req.wrapperCbSuccessFuncSelf = weakref.ref( cbSuccess.__self__)
		req.wrapperCbSuccessFuncName = cbSuccess.__name__
		req.wrapperCbMissingFuncSelf = weakref.ref( cbMissing.__self__)
		req.wrapperCbMissingFuncName = cbMissing.__name__
		req.wrapperCbErrorFuncSelf = weakref.ref( cbError.__self__)
		req.wrapperCbErrorFuncName = cbError.__name__
		self.checkBusyStatus()

	def edit( self, cbSuccess, cbMissing, cbError, id, **kwargs ):
		req = NetworkService.request("/%s/edit/%s" % ( self.modul, id ), kwargs, secure=True, finishedHandler=self.onSaveResult )
		req.wrapperCbSuccessFuncSelf = weakref.ref( cbSuccess.__self__)
		req.wrapperCbSuccessFuncName = cbSuccess.__name__
		req.wrapperCbMissingFuncSelf = weakref.ref( cbMissing.__self__)
		req.wrapperCbMissingFuncName = cbMissing.__name__
		req.wrapperCbErrorFuncSelf = weakref.ref( cbError.__self__)
		req.wrapperCbErrorFuncName = cbError.__name__
		self.checkBusyStatus()

	def delete( self, ids ):
		if isinstance( ids, list ):
			req = RequestGroup( finishedHandler=self.delayEmitEntriesChanged )
			for id in ids:
				r = NetworkService.request( "/%s/delete/%s" % ( self.modul, id ), secure=True )
				req.addQuery( r )
		else: #We just delete one
			NetworkService.request( "/%s/delete/%s" % ( self.modul, id ), secure=True, finishedHandler=self.delayEmitEntriesChanged )
		self.checkBusyStatus()

	def delayEmitEntriesChanged( self, *args, **kwargs ):
		"""
			Give the GAE a chance to apply recent changes and then
			force all open views of that modul to reload its data
		"""
		QtCore.QTimer.singleShot( self.updateDelay, self.emitEntriesChanged )
		self.checkBusyStatus()

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
		self.checkBusyStatus()
	
	def emitEntriesChanged( self, *args, **kwargs ):
		for k,v in self.dataCache.items():
			# Invalidate the cache. We dont clear that dict sothat execDefered calls dont fail
			ctime, data, cursor = v
			self.dataCache[ k ] = (1, data, cursor )
		self.entitiesChanged.emit()
		self.checkBusyStatus()
		#self.emit( QtCore.SIGNAL("entitiesChanged()") )

		
def CheckForListModul( modulName, modulList ):
	modulData = modulList[ modulName ]
	if "handler" in modulData.keys() and (modulData["handler"]=="base" or modulData["handler"]=="list" or modulData["handler"].startswith("list.")):
		return( True )
	return( False )
	
protocolWrapperClassSelector.insert( 0, CheckForListModul, ListWrapper )
