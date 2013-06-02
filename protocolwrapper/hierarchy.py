#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide import QtCore
from network import NetworkService, RequestGroup, RequestWrapper
from time import time
import weakref
from priorityqueue import protocolWrapperClassSelector, protocolWrapperInstanceSelector
from collections import OrderedDict


class HierarchyWrapper( QtCore.QObject ):
	maxCacheTime = 60 #Cache results for max. 60 Seconds
	updateDelay = 1500 #1,5 Seconds gracetime before reloading
	entitiesChanged = QtCore.Signal()
	busyStateChanged = QtCore.Signal( (bool,) ) #If true, im busy right now
	updatingSucceeded = QtCore.Signal( (str,) ) #Adding/Editing an entry succeeded
	updatingFailedError = QtCore.Signal( (str,) ) #Adding/Editing an entry failed due to network/server error
	updatingDataAvaiable = QtCore.Signal( (str, dict, bool) ) #Adding/Editing an entry failed due to missing fields
	
	def __init__( self, modul, *args, **kwargs ):
		super( HierarchyWrapper, self ).__init__()
		self.modul = modul
		self.dataCache = {}
		self.rootNodes = None
		self.structure = None
		self.busy = True
		NetworkService.request( "/%s/listRootNodes" % self.modul, successHandler=self.onRootNodesAvaiable )
		print("Initializing HierarchyWrapper for modul %s" % self.modul )
		protocolWrapperInstanceSelector.insert( 1, self.checkForOurModul, self )
		self.deferedTaskQueue = []

	def checkBusyStatus( self ):
		busy = False
		for child in self.children():
			if isinstance( child, RequestWrapper ) and not child.hasFinished:
				busy = True
				break
		if busy != self.busy:
			self.busy = busy
			print("EMIGING ", busy )
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

	def onRootNodesAvaiable( self, req ):
		tmp = NetworkService.decode( req )
		if isinstance( tmp, list ):
			self.rootNodes = tmp
			if self.structure is None and len(tmp)>0: #Load the structure
				NetworkService.request( "/%s/add/%s" % (self.modul, tmp[0]["key"]), successHandler=self.onStructureAvaiable )
		else:
			self.rootNodes = []
		if "wrapperCbTargetFuncSelf" in dir( req ):
			targetSelf = req.wrapperCbTargetFuncSelf()
			if targetSelf is not None:
				targetFunc = getattr( targetSelf, req.wrapperCbTargetFuncName )
				targetFunc( self.rootNodes )
		self.emit( QtCore.SIGNAL("onRootNodesAvaiable()") )
		self.checkBusyStatus()
		
	def getRootNodes( self, callback ):
		if self.rootNodes is not None:
			self.callDefered( callback, self.rootNodes )
		else:
			r = NetworkService.request( "/%s/listRootNodes" % self.modul, successHandler=self.onRootNodesAvaiable )
			r.wrapperCbTargetFuncSelf = weakref.ref( callback.__self__)
			r.wrapperCbTargetFuncName = callback.__name__
		self.checkBusyStatus()
	
	def cacheKeyFromFilter( self, filters, node ):
		tmpList = list( filters.items() )
		tmpList.append( ("node", node) )
		tmpList.sort( key=lambda x: x[0] )
		return( "&".join( [ "%s=%s" % (k,v) for (k,v) in tmpList] ) )
	
	def queryData( self, callback, node, **kwargs ):
		key = self.cacheKeyFromFilter( kwargs, node )
		if key in self.dataCache.keys():
			ctime, data, cursor = self.dataCache[ key ]
			if ctime+self.maxCacheTime>time(): #This cache-entry is still valid
				self.callDefered( callback, key, data, None )
				#self.deferedTaskQueue.append( ( weakref.ref( callback.__self__), callback.__name__, key ) )
				#QtCore.QTimer.singleShot( 25, self.execDefered )
				#callback( None, data, cursor )
				return( key )
		#Its a cache-miss or cache too old
		r = NetworkService.request( "/%s/list/%s" % (self.modul, node), kwargs, successHandler=self.addCacheData )
		r.wrapperCbTargetFuncSelf = weakref.ref( callback.__self__)
		r.wrapperCbTargetFuncName = callback.__name__
		r.wrapperCbCacheKey = key
		self.checkBusyStatus()
		return( key )
	
	def callDefered( self, callback, *args, **kwargs ):
		self.deferedTaskQueue.append( ( weakref.ref( callback.__self__), callback.__name__, args, kwargs ) )
		QtCore.QTimer.singleShot( 25, self.doCallDefered )
	
	def doCallDefered( self, *args, **kwargs ):
		weakSelf, callName, fargs, fkwargs = self.deferedTaskQueue.pop(0)
		callFunc = weakSelf()
		if callFunc is not None:
			targetFunc = getattr( callFunc, callName )
			targetFunc( *fargs, **fkwargs )
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
			
	def add( self, parent, **kwargs ):
		tmp = {k:v for (k,v) in kwargs.items() }
		tmp["parent"] = parent
		req = NetworkService.request("/%s/add/" % ( self.modul ), tmp, secure=True, finishedHandler=self.onSaveResult )
		if not kwargs:
			# This is our first request to fetch the data, dont show a missing hint
			req.wasInitial = True
		else:
			req.wasInitial = False
		self.checkBusyStatus()
		return( str( id( req ) ) )

	def edit( self, key, **kwargs ):
		req = NetworkService.request("/%s/edit/%s" % ( self.modul, key ), kwargs, secure=True, finishedHandler=self.onSaveResult )
		if not kwargs:
			# This is our first request to fetch the data, dont show a missing hint
			req.wasInitial = True
		else:
			req.wasInitial = False
		self.checkBusyStatus()
		return( str( id( req ) ) )

	def delete( self, ids ):
		if isinstance( ids, list ):
			req = RequestGroup( finishedHandler=self.delayEmitEntriesChanged )
			for id in ids:
				r = NetworkService.request( "/%s/delete/%s" % ( self.modul, id ), secure=True )
				req.addQuery( r )
		else: #We just delete one
			NetworkService.request( "/%s/delete/%s" % ( self.modul, id ), secure=True, finishedHandler=self.delayEmitEntriesChanged )
		self.checkBusyStatus()

	def updateSortIndex(self, itemKey, newIndex):
		self.request = NetworkService.request( "/%s/setIndex" % self.modul, { "item": itemKey, "index": newIndex }, True, finishedHandler=self.delayEmitEntriesChanged )
		self.checkBusyStatus()

	def reparent(self, itemKey, destParent):
		NetworkService.request( "/%s/reparent" % self.modul, { "item": itemKey, "dest": destParent }, True, finishedHandler=self.delayEmitEntriesChanged )
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
			self.updatingFailedError.emit( str( id( req ) ) )
			return
		if data["action"] in ["addSuccess", "editSuccess","deleteSuccess"]: #Saving succeeded
			QtCore.QTimer.singleShot( self.updateDelay, self.emitEntriesChanged )
			self.updatingSucceeded.emit( str( id( req ) ) )
		else: #There were missing fields
			self.updatingDataAvaiable.emit( str( id( req ) ), data, req.wasInitial )
		self.checkBusyStatus()
	
	def emitEntriesChanged( self, *args, **kwargs ):
		for k,v in self.dataCache.items():
			# Invalidate the cache. We dont clear that dict sothat execDefered calls dont fail
			ctime, data, cursor = v
			self.dataCache[ k ] = (1, data, cursor )
		#self.emit( QtCore.SIGNAL("entitiesChanged()") )
		self.entitiesChanged.emit()
		self.checkBusyStatus()

		
def CheckForHierarchyModul( modulName, modulList ):
	modulData = modulList[ modulName ]
	if "handler" in modulData.keys() and ( modulData["handler"] == "hierarchy" or modulData["handler"].startswith("hierarchy.")):
		return( True )
	return( False )
	
protocolWrapperClassSelector.insert( 2, CheckForHierarchyModul, HierarchyWrapper )
