#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide import QtCore
from network import NetworkService, RequestGroup, RequestWrapper
from time import time
import weakref
from priorityqueue import protocolWrapperClassSelector, protocolWrapperInstanceSelector
from collections import OrderedDict


class TreeWrapper( QtCore.QObject ):
	maxCacheTime = 60 #Cache results for max. 60 Seconds
	updateDelay = 1500 #1,5 Seconds gracetime before reloading
	protocolWrapperInstancePriority = 1
	entitiesChanged = QtCore.Signal( (str,) ) # Node,
	rootNodesAvaiable = QtCore.Signal()
	busyStateChanged = QtCore.Signal( (bool,) ) #If true, im busy right now
	updatingSucceeded = QtCore.Signal( (str,) ) #Adding/Editing an entry succeeded
	updatingFailedError = QtCore.Signal( (str,) ) #Adding/Editing an entry failed due to network/server error
	updatingDataAvaiable = QtCore.Signal( (str, dict, bool) ) #Adding/Editing an entry failed due to missing fields
	
	def __init__( self, modul, *args, **kwargs ):
		super( TreeWrapper, self ).__init__()
		self.modul = modul
		self.dataCache = {}
		#self.parentMap = {} #Stores references from child -> parent
		self.viewStructure = None
		self.addStructure = None
		self.editStructure = None
		self.rootNodes = None
		self.busy = True
		for stype in ["view","edit","add"]:
			req = NetworkService.request( "/getStructure/%s/%s" % (self.modul,stype), successHandler=self.onStructureAvaiable )
			req.structureType = stype
		NetworkService.request( "/%s/listRootNodes" % self.modul, successHandler=self.onRootNodesAvaiable )
		print("Initializing TreeWrapper for modul %s" % self.modul )
		protocolWrapperInstanceSelector.insert( self.protocolWrapperInstancePriority, self.checkForOurModul, self )
		self.deferedTaskQueue = []

	def checkBusyStatus( self ):
		busy = False
		for child in self.children():
			if isinstance( child, RequestWrapper ):
				if not child.hasFinished:
					busy = True
					break
		if busy != self.busy:
			self.busy = busy
			self.busyStateChanged.emit( busy )


	def checkForOurModul( self, modulName ):
		return( self.modul==modulName )


	def clearCache( self ):
		"""
			Resets our Cache.
			Does not emit entitiesChanged!
		"""
		self.dataCache = {}
		for node in self.rootNodes:
			node = node.copy()
			node["_type"] = "node"
			node["id"] = node["key"]
			node["_isRootNode"] = 1
			node["parentdir"] = None
			self.dataCache[ node["key"] ] = node
		
	def onStructureAvaiable( self, req ):
		tmp = NetworkService.decode( req )
		if tmp is None:
			return
		structure = OrderedDict()
		for k,v in tmp:
			structure[ k ] = v
		if req.structureType=="view":
			self.viewStructure = structure
		elif req.structureType=="edit":
			self.editStructure = structure
		elif req.structureType=="add":
			self.addStructure = structure
		self.emit( QtCore.SIGNAL("onModulStructureAvaiable()") )
		self.checkBusyStatus()
		
	def onRootNodesAvaiable( self, req ):
		tmp = NetworkService.decode( req )
		if isinstance( tmp, list ):
			self.rootNodes = tmp
		#for node in tmp:
		#	self.dataCache[ node["key"] ] = None #Rootnodes dont have a parent
		print( "nodes avaiable")
		print( tmp )
		self.clearCache()
		print( self.dataCache )
		self.rootNodesAvaiable.emit()
		self.checkBusyStatus()

	
	def cacheKeyFromFilter( self, node, filters ):
		tmp = { k:v for k,v in filters.keys()}
		tmp["node"] = node
		tmpList = list( tmp.items() )
		tmpList.sort( key=lambda x: x[0] )
		return( "&".join( [ "%s=%s" % (k,v) for (k,v) in tmpList] ) )
	
	def queryData( self, node, **kwargs ):
		key = self.cacheKeyFromFilter( node, kwargs )
		if 0 and key in self.dataCache.keys():
			ctime, data, cursor = self.dataCache[ key ]
			if ctime+self.maxCacheTime>time(): #This cache-entry is still valid
				self.deferedTaskQueue.append( ( node ) )
				QtCore.QTimer.singleShot( 25, self.execDefered )
				#callback( None, data, cursor )
				return( key )
		#Its a cache-miss or cache too old
		tmp = { k:v for k,v in kwargs.keys()}
		tmp["node"] = node
		for skelType in ["node","leaf"]:
			tmp["skelType"] = skelType
			r = NetworkService.request( "/%s/list" % self.modul, tmp, successHandler=self.addCacheData )
			r.wrapperCacheKey = key
			r.skelType =skelType
			r.node = node
		if not node in [ x["key"] for x in self.rootNodes ]: #Dont query rootNodes again..
			r = NetworkService.request( "/%s/view/%s/node" % (self.modul, node), successHandler=self.addCacheData )
			r.skelType = "node"
			r.node = node
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
	
	def findParentNode( self, nodeKey ):
		for key, item in self.dataCache.items():
			for node in item["nodes"]:
				if node["id"] == nodeKey:
					return( key, item )
		return( None )
	
	def childrenForNode( self, node ):
		assert isinstance( node, str )
		res = []
		for item in self.dataCache.values():
			if item["parentdir"] == node:
				res.append( item )
		return( res )
	
	def addCacheData( self, req ):
		data = NetworkService.decode( req )
		cursor = None
		if "cursor" in data.keys():
			cursor=data["cursor"]
		if data["action"] == "list":
			for skel in data["skellist"]:
				skel["_type"] = req.skelType
				self.dataCache[ skel["id"] ] = skel
		elif data["action"] == "view":
			skel = data["values"]
			skel["_type"] = req.skelType
			self.dataCache[ skel["id"] ] = skel
		self.entitiesChanged.emit( req.node )
		self.checkBusyStatus()
			
	def add( self, node, skelType, **kwargs ):
		tmp = {k:v for (k,v) in kwargs.items() }
		tmp["node"] = node
		tmp["skelType"] = skelType
		req = NetworkService.request("/%s/add/" % ( self.modul ), tmp, secure=True, finishedHandler=self.onSaveResult )
		if not kwargs:
			# This is our first request to fetch the data, dont show a missing hint
			req.wasInitial = True
		else:
			req.wasInitial = False
		self.checkBusyStatus()
		return( str( id( req ) ) )

	def edit( self, key, skelType, **kwargs ):
		req = NetworkService.request("/%s/edit/%s/%s" % ( self.modul, key, skelType ), kwargs, secure=True, finishedHandler=self.onSaveResult )
		if not kwargs:
			# This is our first request to fetch the data, dont show a missing hint
			req.wasInitial = True
		else:
			req.wasInitial = False
		self.checkBusyStatus()
		return( str( id( req ) ) )

	def mkdir(self, node, dirName):
		"""
			Creates a new directory on the server.
			
			@param rootNode: rootNode to create the directory under.
			@type rootNode: String
			@param path: Path to create the directory in
			@type path: String
			@param dirName: Name of the new directory
			@type dirName: String
		"""
		req = NetworkService.request("/%s/add"% self.modul, {"node":node, "skelType":"node", "name":dirName}, secure=True, successHandler=self.delayEmitEntriesChanged )
		self.checkBusyStatus()
		return( str( id( req ) ) )

	def delete( self, entries, dirs ):
		"""
			Delete files and/or directories from the server.
			Directories dont need to be empty, the server handles that case internally.
			
			@param rootNode: rootNode to delete from
			@type rootNode: String
			@param path: Path (relative to the rootNode) which contains the elements which should be deleted.
			@type path: String
			@param entries: List of filenames in that directory.
			@type entries: List
			@param dirs: List of directories in that directory.
			@type dirs: List
		"""
		request = RequestGroup( finishedHandler=self.delayEmitEntriesChanged)
		for entry in entries:
			request.addQuery( NetworkService.request("/%s/delete" % self.modul, {	"id": entry["id"], 
												"skelType": "leaf" }, parent=self ) )
		for dir in dirs:
			request.addQuery( NetworkService.request("/%s/delete" % self.modul, {	"id":dir["id"], 
												"skelType": "node" }, parent=self ) )
		#request.flushList = [ lambda *args, **kwargs:  self.flushCache( rootNode, path ) ]
		request.queryType = "delete"
		self.checkBusyStatus()
		return( str( id( request ) ) )


	def copy(self, srcRootNode, srcPath, files, dirs, destRootNode, destPath, doMove ):
		"""
			Copy or move elements to the given rootNode/path.
			
			@param clipboard: Tuple holding all informations about the elements which get moved/copied
			@type clipboard: (srcRepo, srcPath, doMove, entities, dirs)
			@param rootNode: Destination rootNode
			@type rootNode: String
			@param path: Destination path
			@type path: String
		"""
		print( srcRootNode, srcPath, files, dirs, destRootNode, destPath, doMove )
		drequest = RequestGroup( finishedHandler=self.delayEmitEntriesChanged)
		for file in files:
			request.addQuery( NetworkService.request( "/%s/copy" % self.modul , {"srcrepo": srcRootNode,
									"srcpath": ("/".join(srcPath) if srcPath else "/"),
									"name": file,
									"destrepo": destRootNode,
									"destpath": ("/".join(destPath) if destPath else "/"),
									"deleteold": "1" if doMove else "0",
									"type":"entry"}, parent=self ) )
		for dir in dirs:
			request.addQuery( NetworkService.request( "/%s/copy" % self.modul, {"srcrepo": srcRootNode,
									"srcpath": ("/".join(srcPath) if srcPath else "/"),
									"name": dir,
									"destrepo": destRootNode,
									"destpath": ("/".join(destPath) if destPath else "/"),
									"deleteold": "1" if doMove else "0",
									"type":"dir"}, parent=self ) )
		request.queryType = "move" if doMove else "copy"
		self.checkBusyStatus()
		return( str( id( request ) ) )

	def rename(self, rootNode, path, oldName, newName ):
		"""
			Rename an entity or directory.
			
			@param rootNode: rootNode the element is in
			@type rootNode: String
			@param path: Path to that element.
			@type path: String
			@param oldName: Old name of the element
			@type oldName: String
			@param newName: The new name for that element
			@type newName: String
		"""
		request = NetworkService.request( "/%s/rename" % self.modul , {"rootNode":rootNode, "path": ("/".join(path) if path else "/"), "src": oldName, "dest":newName }, finishedHandler=self.delayEmitEntriesChanged )
		self.checkBusyStatus()
		return( str( id( request ) ) )
	
	def onProgessUpdate(self, request, done, maximum ):
		if request.queryType == "move":
			descr =  QtCore.QCoreApplication.translate("TreeWidget", "Moving: %s of %s finished.")
		elif request.queryType == "copy":
			descr =  QtCore.QCoreApplication.translate("TreeWidget", "Copying: %s of %s finished.")
		elif request.queryType == "delete":
			descr =  QtCore.QCoreApplication.translate("TreeWidget", "Deleting: %s of %s removed.")
		else:
			raise NotImplementedError()
		self.overlay.inform( self.overlay.BUSY, descr % (done, maximum) )
	
	def delayEmitEntriesChanged( self, req=None, *args, **kwargs ):
		"""
			Give the GAE a chance to apply recent changes and then
			force all open views of that modul to reload its data
		"""
		if req is not None:
			try:
				print( NetworkService.decode( req ) )
			except:
				print("error decoding response")
		QtCore.QTimer.singleShot( self.updateDelay, self.emitEntriesChanged )

	def onSaveResult( self, req ):
		try:
			data = NetworkService.decode( req )
		except: #Something went wrong, call ErrorHandler
			self.updatingFailedError.emit( str( id( req ) ) )
			return
		if data=="OKAY": #Saving succeeded
			QtCore.QTimer.singleShot( self.updateDelay, self.emitEntriesChanged )
			self.updatingSucceeded.emit( str( id( req ) ) )
		else: #There were missing fields
			self.updatingDataAvaiable.emit( str( id( req ) ), data, req.wasInitial )
		self.checkBusyStatus()
	
	def emitEntriesChanged( self, *args, **kwargs ):
		self.clearCache()
		self.entitiesChanged.emit( None )
		self.checkBusyStatus()
		#for k,v in self.dataCache.items():
		#	# Invalidate the cache. We dont clear that dict sothat execDefered calls dont fail
		#	ctime, data, cursor = v
		#	self.dataCache[ k ] = (1, data, cursor )
		#self.entitiesChanged.emit( None )
		#self.emit( QtCore.SIGNAL("entitiesChanged()") )

		
def CheckForTreeModul( modulName, modulList ):
	modulData = modulList[ modulName ]
	if "handler" in modulData.keys() and ( modulData["handler"]=="tree" or modulData["handler"].startswith("tree.")):
		return( True )
	return( False )
	
protocolWrapperClassSelector.insert( 0, CheckForTreeModul, TreeWrapper )
