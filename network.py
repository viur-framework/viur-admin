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

from PyQt4 import QtCore
from PyQt4.QtCore import QUrl, QVariant, QObject
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest, QSslConfiguration, QSslCertificate

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

if os.path.exists("mime.types"):
	mimetypes.read_mime_types("mime.types")

class SecurityTokenProvider( QObject ):
	"""
		Provides an pool of valid securitykeys.
		As they dont have to be requested before the original request can be send,
		the whole process speeds up
	"""
	
	refreshIntervall = 10*60*1000 #10 Mins
	def __init__(self, *args, **kwargs ):
		super( SecurityTokenProvider, self ).__init__( *args, **kwargs )
		self.queue = Queue( 5 ) #Queue of valid tokens
		self.req = None
		self.timer = None
	
	def reset(self):
		"""
			Flushes the cache and tries to rebuild it
		"""
		while not self.queue.empty():
			self.queue.get( False )
		self.req = NetworkService.request("/skey" )
		self.connect( self.req, QtCore.SIGNAL("finished()"), self.onSkeyAvailable )
		if not self.timer:
			self.startTimer( self.refreshIntervall )
	
	def fetchNext( self ):
		"""
			Requests a new SKey if theres currently no request pending
		"""
		if not self.req:
			self.req = NetworkService.request("/skey" )
			self.connect( self.req, QtCore.SIGNAL("finished()"), self.onSkeyAvailable )
	
	def onSkeyAvailable(self):
		"""
			New SKey got avaiable
		"""
		if not self.req:
			return
		try:
			skey = NetworkService.decode( self.req )
		except:
			skey = None
		self.req.deleteLater()
		self.req = None
		if not skey:
			return
		try:
			self.queue.put( skey, False )
		except QFull:
			print( "Err: Queue FULL" )
		if self.queue.qsize()<3:
			self.fetchNext()
	
	def getKey(self):
		"""
			Returns a fresh, valid SKey from the pool.
			Blocks and requests a new one if the Pool is currently empty.
		"""
		skey = None
		while not skey:
			self.fetchNext()
			try:
				skey = self.queue.get( False )
			except QEmpty:
				QtCore.QCoreApplication.processEvents()
		return( skey )
	
	def timerEvent(self, event):
		"""
			Ensures that the session stays alive and the Keys are valid.
			Well cache a key for a maximum of self.refreshIntervall Minutes
		"""
		if self.queue.qsize()<3:
			self.fetchNext()
		else:
			self.getKey()
		
securityTokenProvider = SecurityTokenProvider()
	
class NetworkService():
	url = None
	
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
	def request( url, params=None, secure=False, extraHeaders=None ):
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
			return( nam.post( req, multipart ) )
		else:
			return( nam.get( req ) )
	
	@staticmethod
	def decode( req ):
		return( json.loads( bytes( req.readAll() ).decode("UTF-8") ) )
	
	@staticmethod
	def setup( url, *args, **kwargs ):
		NetworkService.url = url
		securityTokenProvider.reset()

