#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from queue import Queue
import urllib, urllib.request, urllib.error, urllib.parse
from urllib.parse import quote_plus
import sys, os, os.path, time
from config import conf
import json
import mimetypes
import ssl
import string,  random
from threading import local, Lock
import http.cookiejar
import base64
from queue import Queue, Empty as QEmpty, Full as QFull
from hashlib import sha1
from PySide import QtCore, QtGui
from PySide.QtCore import QUrl, QObject
from PySide.QtNetwork import QNetworkAccessManager, QNetworkRequest, QSslConfiguration, QSslCertificate, QNetworkReply
import traceback
import logging
import weakref

##Setup the SSL-Configuration. We accept only the two known Certificates from google; reject all other
try:
	certs = open("cacert.pem", "r").read()
except:
	certs = None
if certs:
	baseSslConfig = QSslConfiguration.defaultConfiguration()
	baseSslConfig.setCaCertificates( QSslCertificate.fromData( certs ) )
	QSslConfiguration.setDefaultConfiguration( baseSslConfig )
	nam = QNetworkAccessManager()
	_isSecureSSL = True
else:
	#We got no valid certificate file - accept all SSL connections
	nam = QNetworkAccessManager()
	class SSLFIX( QtCore.QObject ):
		def onSSLError(self, networkReply,  sslErros ):
			networkReply.ignoreSslErrors()
	_SSLFIX = SSLFIX()
	_SSLFIX.connect( nam, QtCore.SIGNAL("sslErrors(QNetworkReply *,const QList<QSslError>&)" ), _SSLFIX.onSSLError )
	_isSecureSSL = False

mimetypes.init()
if os.path.exists("mime.types"):
	mimetypes.types_map.update( mimetypes.read_mime_types("mime.types") )

class SecurityTokenProvider( QObject ):
	"""
		Provides an pool of valid securitykeys.
		As they dont have to be requested before the original request can be send,
		the whole process speeds up
	"""
	errorCount = 0
	
	def __init__(self, *args, **kwargs ):
		super( SecurityTokenProvider, self ).__init__( *args, **kwargs )
		self.logger = logging.getLogger( "RequestWrapper" )
		self.queue = Queue( 5 ) #Queue of valid tokens
		self.isRequesting = False
	
	def reset(self):
		"""
			Flushes the cache and tries to rebuild it
		"""
		self.logger.debug("Reset" )
		while not self.queue.empty():
			self.queue.get( False )
		self.req = NetworkService.request("/skey" )
		self.connect( self.req, QtCore.SIGNAL("finished()"), self.onSkeyAvailable )
	
	def fetchNext( self ):
		"""
			Requests a new SKey if theres currently no request pending
		"""
		if not self.isRequesting:
			if SecurityTokenProvider.errorCount>5: #We got 5 Errors in a row
				raise RuntimeError("Error-limit exceeded on fetching skey")
			self.logger.debug( "Fetching new skey" )
			self.isRequesting = True
			NetworkService.request("/skey", successHandler=self.onSkeyAvailable, failureHandler=self.onError )
	
	def onError(self, request, error ):
		SecurityTokenProvider.errorCount += 1
		self.logger.warning( "Error fetching skey: %s", str(error) )
		self.isRequesting = False
	
	def onSkeyAvailable(self, request=None ):
		"""
			New SKey got avaiable
		"""
		self.isRequesting = False
		if SecurityTokenProvider.errorCount>0:
			SecurityTokenProvider.errorCount = 0
		try:
			skey = NetworkService.decode( request )
		except:
			skey = None
		self.isRequesting = False
		if not skey:
			return
		try:
			self.queue.put( skey, False )
		except QFull:
			print( "Err: Queue FULL" )
	
	def getKey(self):
		"""
			Returns a fresh, valid SKey from the pool.
			Blocks and requests a new one if the Pool is currently empty.
		"""
		self.logger.debug( "Consuming a new skey" )
		skey = None
		while not skey:
			self.fetchNext()
			try:
				skey = self.queue.get( False )
			except QEmpty:
				self.logger.debug( "Empty cache! Please wait..." )
				QtCore.QCoreApplication.processEvents()
		self.logger.debug( "Using skey: %s", skey )
		return( skey )
	
securityTokenProvider = SecurityTokenProvider()

class RequestWrapper( QtCore.QObject ):
	requestSucceeded = QtCore.Signal( QtCore.QObject )
	finished = QtCore.Signal( QtCore.QObject )

	def __init__(self, request, successHandler=None, failureHandler=None, finishedHandler=None ):
		super( RequestWrapper, self ).__init__()

		self.logger = logging.getLogger( "RequestWrapper" )
		self.logger.debug("New network request: %s", str(self) )
		self.request = request
		self.requestStatus = None #None => In progress, True => Succeeded, QNetworkError => Failure
		if successHandler and "__self__" in dir( successHandler ):
			print("connecting ", successHandler )
			self.requestSucceeded.connect( successHandler )
		if failureHandler and "__self__" in dir( failureHandler ):
			failureHandler.__self__.connect( self, QtCore.SIGNAL("error(PyQt_PyObject,QNetworkReply::NetworkError)"), failureHandler )
		if finishedHandler and "__self__" in dir( finishedHandler ):
			self.finished.connect( finishedHandler )
		self.connect( request, QtCore.SIGNAL("downloadProgress(qint64,qint64)"), self.onDownloadProgress )
		self.connect( request, QtCore.SIGNAL("uploadProgress(qint64,qint64)"), self.onUploadProgress )
		self.connect( request, QtCore.SIGNAL("error(QNetworkReply::NetworkError)"), self.onError )
		self.connect( request, QtCore.SIGNAL("finished()"), self.onFinished )
		NetworkService.currentRequests.append( self )
	
	def onDownloadProgress(self, bytesReceived, bytesTotal ):
		if bytesReceived == bytesTotal:
			self.requestStatus = True
		self.emit( QtCore.SIGNAL("downloadProgress(qint64,qint64)"),  bytesReceived, bytesTotal )
		self.emit( QtCore.SIGNAL("downloadProgress(PyQt_PyObject,qint64,qint64)"), self, bytesReceived, bytesTotal )
	
	
	def onUploadProgress(self, bytesSend, bytesTotal ):
		if bytesSend == bytesTotal:
			self.requestStatus = True
		self.emit( QtCore.SIGNAL("uploadProgress(qint64,qint64)"),  bytesSend, bytesTotal )
		self.emit( QtCore.SIGNAL("uploadProgress(PyQt_PyObject,qint64,qint64)"), self, bytesSend, bytesTotal )

	def onError(self, error):
		self.requestStatus = error
	
	def onFinished(self ):
		if self.requestStatus==True:
			self.requestSucceeded.emit( self )
			#self.emit( QtCore.SIGNAL("requestSucceeded(PyQt_PyObject)"), self )
		elif self.requestStatus==None: #We neither got a up/download-progress nor an error first :/
			pass
			#self.emit( QtCore.SIGNAL("error(QNetworkReply::NetworkError)"), QNetworkReply.ProtocolUnknownError )
			#self.emit( QtCore.SIGNAL("error(PyQt_PyObject,QNetworkReply::NetworkError)"), self, QNetworkReply.ProtocolUnknownError )
		else: 
			pass
			#self.emit( QtCore.SIGNAL("error(QNetworkReply::NetworkError)"), self.requestStatus )
			#self.emit( QtCore.SIGNAL("error(PyQt_PyObject,QNetworkReply::NetworkError)"), self, self.requestStatus )
		#self.emit( QtCore.SIGNAL("finished()") )
		#self.emit( QtCore.SIGNAL("finished(PyQt_PyObject)"), self )
		self.finished.emit( self )
		self.logger.debug("Request finished: %s", str(self) )
		NetworkService.currentRequests.remove( self )
		self.logger.debug("Remaining requests: %s",  len(NetworkService.currentRequests) )
		self.request.deleteLater()
		self.request = None
		self.successHandler = None
		self.failureHandler = None
		self.finishedHandler = None
		self.deleteLater()
	
	def readAll(self):
		return( self.request.readAll() )

class RequestGroup( QtCore.QObject ):
	"""
		Aggregates multiple RequestWrapper into one place.
		Informs the creator whenever an Query finishes processing and allows
		easy checking if there are more queries pending.
	"""
	
	def __init__(self, successHandler=None, failureHandler=None, finishedHandler=None, *args, **kwargs ):
		super( RequestGroup, self ).__init__(*args, **kwargs)
		self.querys = []
		self.successHandler = successHandler
		self.failureHandler = failureHandler
		self.finishedHandler = finishedHandler
		self.maxQueryCount = 0
		NetworkService.currentRequests.append( self )

	def addQuery( self, query ):
		"""
			Add an RequestWrapper to the Group
		"""
		self.maxQueryCount += 1
		self.querys.append( query )
		self.connect( query, QtCore.SIGNAL("downloadProgress(PyQt_PyObject,qint64,qint64)"), self.onProgress )
		self.connect( query, QtCore.SIGNAL("error(PyQt_PyObject,QNetworkReply::NetworkError)"), self.onError )
		self.connect( query, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.onFinished )
	
	def onProgress(self, request, bytesReceived, bytesTotal ):
		if bytesReceived == bytesTotal:
			if self.successHandler:
				self.successHandler( self, request )
			self.emit( QtCore.SIGNAL("progessUpdate(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self, self.maxQueryCount-len( self.querys ), self.maxQueryCount )
	
	def onError(self, request, error):
		if self.failureHandler:
			self.failureHandler( self, request, error )
		self.emit( QtCore.SIGNAL("progessUpdate(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self, self.maxQueryCount-len( self.querys ), self.maxQueryCount )
	
	def onFinished(self, queryWrapper ):
		self.querys.remove( queryWrapper )
		if len( self.querys ) == 0:
			if self.finishedHandler:
				self.finishedHandler( self )
			NetworkService.currentRequests.remove( self )
			self.successHandler = None
			self.failureHandler = None
			self.finishedHandler = None
			self.deleteLater()
	
	def isIdle(self):
		"""
			Check whenever no more querys are pending.
			@returns: Bool
		"""
		return( len(self.querys) == 0 )
	
	def abort(self):
		"""
			Abort all remaining queries.
			If there was at least one running query, the finishedHandler will be called shortly after.
		"""
		for req in self.querys:
			req.abort()


class RemoteFile( QtCore.QObject ):
	"""
		Allows easy access to remote files by their DL-Key.
		Its loads a File from the server if needed and Caches it locally sothat further requests will 
		not bother the server again
	"""
	maxBlockTime = 30 #Maximum seconds, we are willing to wait for a file to download in "blocking" mode
	
	def __init__(self, dlKey, successHandler=None, failureHandler=None, *args, **kwargs ):
		super( RemoteFile, self ).__init__(*args, **kwargs)
		self.logger = logging.getLogger( "RemoteFile" )
		self.logger.debug("New RemoteFile: %s for %s", str(self), str(dlKey) )
		if successHandler:
			self.successHandlerSelf = weakref.ref( successHandler.__self__)
			self.successHandlerName = successHandler.__name__
		if failureHandler:
			self.failureHandlerSelf = weakref.ref( failureHandler.__self__)
			self.failureHandlerName = failureHandler.__name__
		self.dlKey = dlKey
		fileName = os.path.join( conf.currentPortalConfigDirectory, sha1(dlKey.encode("UTF-8")).hexdigest() )
		if os.path.isfile( fileName ):
			self.logger.debug("We already have that file :)")
			self._delayTimer = QtCore.QTimer( self )
			self._delayTimer.singleShot( 250, self.onTimerEvent )
		else:
			self.logger.debug("Need to fetch that file")
			self.loadFile()
		NetworkService.currentRequests.append( self )

	def remove(self):
		"""
			Unregister this object, so it gets garbarge collected
		"""
		self.logger.debug("Checkpoint: remove")
		NetworkService.currentRequests.remove( self )
		self.successHandler = None
		self.failureHandler = None
		self.deleteLater()
		
	
	def onTimerEvent( self ):
		self.logger.debug("Checkpoint: onTimerEvent")
		s = self.successHandlerSelf()
		print( s )
		if s:
			try:
				getattr( s, self.successHandlerName )( self )
			except e:
				self.logger.exception( e )
		self._delayTimer.deleteLater()
		self._delayTimer = None
		self.remove()

	
	def loadFile(self ):
		dlKey = self.dlKey
		if not dlKey.lower().startswith("http://") and not dlKey.lower().startswith("https://"):
			dlKey = "/file/view/%s/file.dat" % dlKey
		req = NetworkService.request( dlKey, successHandler=self.onFileAvaiable  )

	def onFileAvaiable( self, request ):
		self.logger.debug("Checkpoint: onFileAvaiable")
		fileName = os.path.join( conf.currentPortalConfigDirectory, sha1( self.dlKey.encode("UTF-8")).hexdigest() )
		data = request.readAll()
		open( fileName, "w+b" ).write( data )
		s = self.successHandlerSelf()
		if s:
			try:
				getattr( s, self.successHandlerName )( self )
			except e:
				self.logger.exception( e )
		self.remove()

	def getFileName( self ):
		"""
			Returns the local fileName of our file, or none if downloading hasnt succeded yet
		"""
		fileName = os.path.join( conf.currentPortalConfigDirectory, sha1( self.dlKey.encode("UTF-8")).hexdigest() )
		if os.path.isfile( fileName ):
			return( fileName )
		return( "" )

	def getFileContents( self ):
		"""
			Returns the content of the file as bytes
		"""
		fileName = self.getFileName( )
		if not fileName:
			return( b"" )
		return( open( fileName, "rb" ).read() )

class NetworkService():
	url = None
	currentRequests = [] #A list of currently running requests
	
	@staticmethod
	def genReqStr( params ):
		boundary_str = "---"+''.join( [ random.choice(string.ascii_lowercase+string.ascii_uppercase + string.digits) for x in range(13) ] ) 
		boundary = boundary_str.encode("UTF-8")
		res = b'Content-Type: multipart/mixed; boundary="'+boundary+b'"\nMIME-Version: 1.0\n'
		res += b'\n--'+boundary
		for(key, value) in list(params.items()):
			if all( [x in dir( value ) for x in ["name", "read"] ] ): #File
				try:
					(type, encoding) = mimetypes.guess_type( value.name.decode( sys.getfilesystemencoding() ), strict=False )
					type = type or "application/octet-stream"
				except:
					type = "application/octet-stream"
				res += b'\nContent-Type: '+type.encode("UTF-8")+b'\nMIME-Version: 1.0\nContent-Disposition: form-data; name="'+key.encode("UTF-8")+b'"; filename="'+os.path.basename(value.name).decode(sys.getfilesystemencoding()).encode("UTF-8")+b'"\n\n'
				res += value.read()
				res += b'\n--'+boundary
			elif isinstance( value, list ):
				for val in value:
					res += b'\nContent-Type: application/octet-stream\nMIME-Version: 1.0\nContent-Disposition: form-data; name="'+key.encode("UTF-8")+b'"\n\n'
					res += str( val ).encode("UTF-8")
					res += b'\n--'+boundary
			else:
				res += b'\nContent-Type: application/octet-stream\nMIME-Version: 1.0\nContent-Disposition: form-data; name="'+key.encode("UTF-8")+b'"\n\n'
				res += str( value ).encode("UTF-8")
				res += b'\n--'+boundary
		res += b'--\n'
		return( res, boundary )

	@staticmethod
	def request( url, params=None, secure=False, extraHeaders=None, successHandler=None, failureHandler=None, finishedHandler=None ):
		global nam, _isSecureSSL
		if _isSecureSSL==False: #Warn the user of a potential security risk
			msgRes = QtGui.QMessageBox.warning(	None, QtCore.QCoreApplication.translate("NetworkService", "Insecure connection"),
											QtCore.QCoreApplication.translate("Updater", "The cacerts.pem file is missing or invalid. Your passwords and data will be send unsecured! Continue without encryption? If unsure, choose \"abort\"!"), 
											QtCore.QCoreApplication.translate("NetworkService", "Continue in unsecure mode"),
											QtCore.QCoreApplication.translate("NetworkService", "Abort") )
			if msgRes==0:
				_isSecureSSL=None
			else:
				sys.exit(1)
		if secure:
			key=securityTokenProvider.getKey()
			if "?" in url:
				url += "&skey=%s" % key 
			else:
				url += "?skey=%s" % key 
		if url.lower().startswith("http"):
			reqURL = QUrl(url)
		else:
			reqURL = QUrl( NetworkService.url+url )
		req = QNetworkRequest( reqURL )
		if extraHeaders:
			for k, v in extraHeaders.items():
				req.setRawHeader( k,  v )
		if params:
			if isinstance( params, dict):
				multipart, boundary = NetworkService.genReqStr( params )
				req.setRawHeader( "Content-Type", b'multipart/form-data; boundary='+boundary+b'; charset=utf-8')
			elif isinstance( params, bytes ):
				req.setRawHeader( "Content-Type",  b'application/x-www-form-urlencoded' )	
				multipart = params
			else:
				print( params )
				print( type( params ) )
			return( RequestWrapper( nam.post( req, multipart ), successHandler, failureHandler, finishedHandler) )
		else:
			return( RequestWrapper( nam.get( req ), successHandler, failureHandler, finishedHandler) )
	
	@staticmethod
	def decode( req ):
		return( json.loads( req.readAll().data().decode("UTF-8") ) )
	
	@staticmethod
	def setup( url, *args, **kwargs ):
		NetworkService.url = url
		securityTokenProvider.reset()

