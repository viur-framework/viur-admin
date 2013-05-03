#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt4 import QtCore
from network import NetworkService, RequestGroup
from time import time
import weakref
from priorityqueue import protocolWrapperClassSelector, protocolWrapperInstanceSelector
from collections import OrderedDict


class TreeWrapper( QtCore.QObject ):
	maxCacheTime = 60 #Cache results for max. 60 Seconds
	updateDelay = 1500 #1,5 Seconds gracetime before reloading
	protocolWrapperInstancePriority = 1
	
	def __init__( self, modul, *args, **kwargs ):
		super( TreeWrapper, self ).__init__()
		self.modul = modul
		self.dataCache = {}
		self.structure = None
		self.rootNodes = None
		NetworkService.request( "/%s/add" % self.modul, successHandler=self.onStructureAvaiable )
		NetworkService.request( "/%s/listRootNodes" % self.modul, successHandler=self.onRootNodesAvaiable )
		print("Initializing TreeWrapper for modul %s" % self.modul )
		protocolWrapperInstanceSelector.insert( self.protocolWrapperInstancePriority, self.checkForOurModul, self )
		self.deferedTaskQueue = []

	def checkForOurModul( self, modulName ):
		return( self.modul==modulName )
	
	def onStructureAvaiable( self, req ):
		tmp = NetworkService.decode( req )
		self.structure = OrderedDict()
		for k,v in tmp["structure"]:
			self.structure[ k ] = v
		self.emit( QtCore.SIGNAL("onModulStructureAvaiable()") )
		
	def onRootNodesAvaiable( self, req ):
		tmp = NetworkService.decode( req )
		if isinstance( tmp, list ):
			self.rootNodes = tmp
		self.emit( QtCore.SIGNAL("onRootNodesAvaiable()") )

	
	def cacheKeyFromFilter( self, rootNode, path, filters ):
		tmp = { k:v for k,v in filters.keys()}
		tmp["rootNode"] = rootNode
		tmp["path"] = "/".join( path ) if path else "/"
		tmpList = list( tmp.items() )
		tmpList.sort( key=lambda x: x[0] )
		return( "&".join( [ "%s=%s" % (k,v) for (k,v) in tmpList] ) )
	
	def queryData( self, callback, rootNode, path, **kwargs ):
		key = self.cacheKeyFromFilter( rootNode, path, kwargs )
		if key in self.dataCache.keys():
			ctime, data, cursor = self.dataCache[ key ]
			if ctime+self.maxCacheTime>time(): #This cache-entry is still valid
				self.deferedTaskQueue.append( ( weakref.ref( callback.__self__), callback.__name__, key ) )
				QtCore.QTimer.singleShot( 25, self.execDefered )
				#callback( None, data, cursor )
				return( key )
		#Its a cache-miss or cache too old
		tmp = { k:v for k,v in kwargs.keys()}
		tmp["rootNode"] = rootNode
		tmp["path"] = "/".join( path ) if path else "/"
		r = NetworkService.request( "/%s/list" % self.modul, tmp, successHandler=self.addCacheData )
		r.wrapperCbTargetFuncSelf = weakref.ref( callback.__self__)
		r.wrapperCbTargetFuncName = callback.__name__
		r.wrapperCbCacheKey = key
		return( key )
	
	def execDefered( self, *args, **kwargs ):
		weakSelf, callName, key = self.deferedTaskQueue.pop(0)
		callFunc = weakSelf()
		if callFunc is not None:
			targetFunc = getattr( callFunc, callName )
			ctime, data, cursor = self.dataCache[ key ]
			targetFunc( key, data, cursor )
	
	def addCacheData( self, req ):
		data = NetworkService.decode( req )
		cursor = None
		if "cursor" in data.keys():
			cursor=data["cursor"]
		self.dataCache[ req.wrapperCbCacheKey ] = (time(), data, cursor)
		targetSelf = req.wrapperCbTargetFuncSelf()
		if targetSelf is not None:
			targetFunc = getattr( targetSelf, req.wrapperCbTargetFuncName )
			targetFunc( req.wrapperCbCacheKey, data, cursor )
			
	def add( self, cbSuccess, cbMissing, cbError, rootNone, path, **kwargs ):
		tmp = {k:v for (k,v) in kwargs.items() }
		tmp["rootNode"] = rootNone
		tmp["path"] = path
		req = NetworkService.request("/%s/add/" % ( self.modul ), tmp, secure=True, finishedHandler=self.onSaveResult )
		req.wrapperCbSuccessFuncSelf = weakref.ref( cbSuccess.__self__)
		req.wrapperCbSuccessFuncName = cbSuccess.__name__
		req.wrapperCbMissingFuncSelf = weakref.ref( cbMissing.__self__)
		req.wrapperCbMissingFuncName = cbMissing.__name__
		req.wrapperCbErrorFuncSelf = weakref.ref( cbError.__self__)
		req.wrapperCbErrorFuncName = cbError.__name__

	def edit( self, cbSuccess, cbMissing, cbError, id, **kwargs ):
		req = NetworkService.request("/%s/edit/%s" % ( self.modul, id ), kwargs, secure=True, finishedHandler=self.onSaveResult )
		req.wrapperCbSuccessFuncSelf = weakref.ref( cbSuccess.__self__)
		req.wrapperCbSuccessFuncName = cbSuccess.__name__
		req.wrapperCbMissingFuncSelf = weakref.ref( cbMissing.__self__)
		req.wrapperCbMissingFuncName = cbMissing.__name__
		req.wrapperCbErrorFuncSelf = weakref.ref( cbError.__self__)
		req.wrapperCbErrorFuncName = cbError.__name__


	def mkdir(self, rootNode, path, dirName):
		"""
			Creates a new directory on the server.
			
			@param rootNode: rootNode to create the directory under.
			@type rootNode: String
			@param path: Path to create the directory in
			@type path: String
			@param dirName: Name of the new directory
			@type dirName: String
		"""
		request = NetworkService.request("/%s/mkDir"% self.modul, {"rootNode":rootNode, "path":path, "dirname":dirName}, successHandler=self.onRequestSucceeded, failureHandler=self.showError )
		#request.flushList = [ lambda*args, **kwargs: self.flushCache(rootNode, path) ]

	def delete( self, rootNode, path, entries, dirs ):
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
			request.addQuery( NetworkService.request("/%s/delete" % self.modul, {	"rootNode":rootNode, 
										"path": path, 
										"name": entry, 
										"type": "entry" } ) )
		for dir in dirs:
			request.addQuery( NetworkService.request("/%s/delete" % self.modul, {	"rootNode":rootNode, 
										"path": path, 
										"name": dir, 
										"type": "dir" } ) )
		#request.flushList = [ lambda *args, **kwargs:  self.flushCache( rootNode, path ) ]
		request.queryType = "delete"
		#self.connect( request, QtCore.SIGNAL("progessUpdate(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self.onProgessUpdate )


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
		request = RequestGroup( finishedHandler=self.delayEmitEntriesChanged)
		for file in files:
			request.addQuery( NetworkService.request( "/%s/copy" % self.modul , {"srcrepo": srcRootNode,
									"srcpath": srcPath,
									"name": file,
									"destrepo": destRootNode,
									"destpath": destPath,
									"deleteold": "1" if doMove else "0",
									"type":"entry"} ) )
		for dir in dirs:
			request.addQuery( NetworkService.request( "/%s/copy" % self.modul, {"srcrepo": srcRootNode,
									"srcpath": srcPath,
									"name": dir,
									"destrepo": destRootNode,
									"destpath": destPath,
									"deleteold": "1" if doMove else "0",
									"type":"dir"} ) )
		request.queryType = "move" if doMove else "copy"
		#self.connect( request, QtCore.SIGNAL("progessUpdate(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self.onProgessUpdate )
		#self.overlay.inform( self.overlay.BUSY )
	
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
		request = NetworkService.request( "/%s/rename" % self.modul , {"rootNode":rootNode, "path":path, "src": oldName, "dest":newName }, finishedHandler=self.delayEmitEntriesChanged )

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
		for k,v in self.dataCache.items():
			# Invalidate the cache. We dont clear that dict sothat execDefered calls dont fail
			ctime, data, cursor = v
			self.dataCache[ k ] = (1, data, cursor )
		self.emit( QtCore.SIGNAL("entitiesChanged()") )

		
def CheckForTreeModul( modulName, modulList ):
	modulData = modulList[ modulName ]
	if "handler" in modulData.keys() and modulData["handler"].startswith("tree."):
		return( True )
	return( False )
	
protocolWrapperClassSelector.insert( 0, CheckForTreeModul, TreeWrapper )
