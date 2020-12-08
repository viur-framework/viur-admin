# -*- coding: utf-8 -*-

import json
import mimetypes
import os
import os.path
import sys
import time
import weakref
from hashlib import sha1
from queue import Empty as QEmpty, Full as QFull, Queue
from typing import Any, Callable, Dict, List, Union
from urllib import request
from viur_admin.pyodidehelper import isPyodide
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QObject, QUrl
import string, random
if isPyodide:
	from PyQt5.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkAccessManager, QNetworkReply, QNetworkRequest

	QNetworkCookieJar = QSslCertificate = QSslConfiguration = None

else:
	from PyQt5.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkAccessManager, QNetworkCookieJar, QNetworkReply, \
		QNetworkRequest, QSslCertificate, QSslConfiguration

import viur_admin.ui.icons_rc
from viur_admin.config import conf
from viur_admin.log import getLogger
import io
from functools import partial

logger = getLogger(__name__)
logger.debug("icons_rc found: %r", viur_admin.ui.icons_rc)  # import guard

if not isPyodide:
	# Setup the SSL-Configuration. We accept only the two known Certificates from google; reject all other
	try:
		css = QtCore.QFile(":icons/cacert.pem")
		css.open(QtCore.QFile.ReadOnly)
		certs = css.readAll()
	except:
		certs = None

	if certs:
		baseSslConfig = QSslConfiguration.defaultConfiguration()
		baseSslConfig.setCaCertificates(QSslCertificate.fromData(certs))
		QSslConfiguration.setDefaultConfiguration(baseSslConfig)
		nam = QNetworkAccessManager()
		_isSecureSSL = True
	else:
		# We got no valid certificate file - accept all SSL connections
		nam = QNetworkAccessManager()


		class SSLFIX(QtCore.QObject):
			def onSSLError(self, networkReply: Any, sslErros: Any) -> None:
				networkReply.ignoreSslErrors()


		_SSLFIX = SSLFIX()
		nam.sslErrors.connect(_SSLFIX.onSSLError)
		_isSecureSSL = False


	class MyCookieJar(QNetworkCookieJar):
		"""Needed for accessing protected methods"""
		pass

else:
	_isSecureSSL = True  # That is handled by your browser
	nam = QNetworkAccessManager()
	MyCookieJar = None



def getFileNameForUrl(dlKey: str) -> str:
	return os.path.join(conf.currentPortalConfigDirectory, sha1(dlKey.encode("UTF-8")).hexdigest())

if not isPyodide:
	nam.setCookieJar(MyCookieJar())

mimetypes.init()
if os.path.exists("mime.types"):
	mimetypes.types_map.update(mimetypes.read_mime_types("mime.types"))

# Source: http://srinikom.github.io/pyside-docs/PySide/QtNetwork/QNetworkReply.html
NetworkErrorDescrs = {
	"ConnectionRefusedError": "The remote server refused the connection (the server is not accepting requests)",
	"RemoteHostClosedError": "The remote server closed the connection prematurely, before the entire reply was received "
	                         "and processed",
	"HostNotFoundError": "The remote host name was not found (invalid hostname)",
	"TimeoutError": "The connection to the remote server timed out",
	"OperationCanceledError": "The operation was canceled via calls to PySide.QtNetwork.abort() or "
	                          "PySide.QtNetwork.close() before it was finished.",
	"SslHandshakeFailedError": "The SSL/TLS handshake failed and the encrypted channel could not be established. The "
	                           "PySide.QtNetwork.sslErrors() signal should have been emitted.",
	"TemporaryNetworkFailureError": "The connection was broken due to disconnection from the network, however the system "
	                                "has initiated roaming to another access point. The request should be resubmitted and "
	                                "will be processed as soon as the connection is re-established.",
	"ProxyConnectionRefusedError": "The connection to the proxy server was refused (the proxy server is not accepting "
	                               "requests)",
	"ProxyConnectionClosedError": "The proxy server closed the connection prematurely, before the entire reply was "
	                              "received and processed",
	"ProxyNotFoundError": "The proxy host name was not found (invalid proxy hostname)",
	"ProxyTimeoutError": "The connection to the proxy timed out or the proxy did not reply in time to the request sent",
	"ProxyAuthenticationRequiredError": "The proxy requires authentication in order to honour the request but did not "
	                                    "accept any credentials offered (if any)",
	"ContentAccessDenied": "The access to the remote content was denied (similar to HTTP error 401)",
	"ContentOperationNotPermittedError": "The operation requested on the remote content is not permitted",
	"ContentNotFoundError": "The remote content was not found at the server (similar to HTTP error 404)",
	"AuthenticationRequiredError": "The remote server requires authentication to serve the content but the credentials "
	                               "provided were not accepted (if any)",
	"ContentReSendError": "The request needed to be sent again, but this failed for example because the upload data could "
	                      "not be read a second time.",
	"ProtocolUnknownError": "The Network Access API cannot honor the request because the protocol is not known",
	"ProtocolInvalidOperationError": "The requested operation is invalid for this protocol",
	"UnknownNetworkError": "An unknown network-related error was detected",
	"UnknownProxyError": "An unknown proxy-related error was detected",
	"UnknownContentError": "An unknown error related to the remote content was detected",
	"ProtocolFailure": "A breakdown in protocol was detected (parsing error, invalid or unexpected responses, etc.)"
}

# Match keys of that array with the numeric values suppied by QT
for k, v in NetworkErrorDescrs.copy().items():
	try:
		NetworkErrorDescrs[getattr(QNetworkReply, k)] = v
	except:
		pass  # Some errors don't seem to exist on all Platforms (eg. TemporaryNetworkFailureError seems missing on
	# MacOs)
	del NetworkErrorDescrs[k]


class SecurityTokenProvider(QObject):
	def __init__(
			self,
			*args: Any,
			**kwargs: Any):
		super(SecurityTokenProvider, self).__init__(*args, **kwargs)
		self.queue = Queue()  # Queue of valid tokens
		self.currentRequest = None
		self.lockKey = None
		self.staticSecurityKey = None

	def addRequest(self, callback):
		self.queue.put(callback)
		if not self.currentRequest:
			self.fetchNext()

	def fetchNext(self):
		self.lockKey = "".join(random.choices(string.ascii_letters + string.digits, k=10))
		req = QNetworkRequest(QUrl("/admin/skey"))
		self.currentRequest = nam.get(req)
		self.currentRequest.finished.connect(self.onFinished)

	def onFinished(self, *args, **kwargs):
		lockKey = self.lockKey
		QtCore.QTimer.singleShot(3000, lambda: self.unlockKey(lockKey))
		if self.currentRequest.error() == self.currentRequest.NoError:
			skey = json.loads(self.currentRequest.readAll().data().decode("utf-8"))
			cb = self.queue.get()
			try:
				cb(skey, self.lockKey)
			except:
				print("Error calling SKEY CB")
				print(cb)
				print(skey)
		else:
			print("ERROR FETCHING SKEY")

	def unlockKey(self, lockKey):
		if lockKey != self.lockKey:
			return
		self.lockKey = None
		if not self.queue.empty():
			self.fetchNext()
		else:
			self.currentRequest = None

securityTokenProvider = SecurityTokenProvider()


class RequestWrapper(QtCore.QObject):
	GarbargeTypeName = "RequestWrapper"
	requestSucceeded = QtCore.pyqtSignal(QtCore.QObject)
	requestFailed = QtCore.pyqtSignal(QtCore.QObject, QNetworkReply.NetworkError)
	finished = QtCore.pyqtSignal(QtCore.QObject)
	uploadProgress = QtCore.pyqtSignal(QtCore.QObject, int, int)
	downloadProgress = QtCore.pyqtSignal(QtCore.QObject, int, int)

	def __init__(
			self,
			url: str,
			params: Union[dict, None] = None,
			secure: bool = False,
			extraHeaders: Union[dict, None] = None,
			successHandler: Union[Callable, None] = None,
			failureHandler: Union[Callable, None] = None,
			finishedHandler: Union[Callable, None] = None,
			parent: Union[QtCore.QObject, None] = None,
			failSilent: bool = False
			):
		super(RequestWrapper, self).__init__()
		logger.debug("New network request: %s", str(self))
		self.hasFinished = False
		self.url = url
		self.params = params
		self.extraHeaders = extraHeaders
		self.successHandler = successHandler
		self.failureHandler = failureHandler
		self.finishedHandler = finishedHandler
		self._parent = parent
		self.failSilent = failSilent
		self.unlockSkey = None
		if secure:
			if securityTokenProvider.staticSecurityKey and not isPyodide:
				if not self.extraHeaders:
					self.extraHeaders = {}
				self.extraHeaders["Sec-X-ViUR-StaticSKey"] = securityTokenProvider.staticSecurityKey
				if not self.params:
					self.params = {}
				self.params["skey"] = "staticSessionKey"
				self.startRequest()
			else:  # Wait for a fresh skey to arrive
				securityTokenProvider.addRequest(self.insertSkey)
		else:
			self.startRequest()

	def insertSkey(self, skey, unlockKey):
		self.unlockSkey = unlockKey
		if not self.params:
			self.params = {}
		self.params["skey"] = skey
		self.startRequest()

	def startRequest(self):
		self.startTime = time.time()
		if self.url.lower().startswith("http"):
			reqURL = QUrl(self.url)
		else:
			reqURL = QUrl(NetworkService.url + self.url)
		req = QNetworkRequest(reqURL)
		if self.extraHeaders:
			for k, v in self.extraHeaders.items():
				req.setRawHeader(k.encode("LATIN-1", "ignore"), v.encode("LATIN-1", "ignore"))
		if self.params:
			if isinstance(self.params, dict):
				multipart = NetworkService.genReqStr(self.params)
				request = nam.post(req, multipart)
				multipart.setParent(request)
				logger.debug("after reply setparent")
			elif isinstance(self.params, bytes):
				req.setRawHeader(b"Content-Type", b'application/x-www-form-urlencoded')
				request = nam.post(req, self.params)
				logger.debug("after nam post")
			else:
				raise ValueError("cannot differentiate headers to that param type")
			logger.debug("params: %r", self.params)
			logger.debug("reply: %r", request)
		else:
			request = nam.get(req)
		self.request = request
		request.setParent(self)
		parent = self._parent
		if self.successHandler and "__self__" in dir(self.successHandler) and isinstance(self.successHandler.__self__, QtCore.QObject):
			parent = parent or self.successHandler.__self__
			self.requestSucceeded.connect(self.successHandler)
		if self.failureHandler and "__self__" in dir(self.failureHandler) and isinstance(self.failureHandler.__self__, QtCore.QObject):
			parent = parent or self.failureHandler.__self__
			self.requestFailed.connect(self.failureHandler)
		if self.finishedHandler and "__self__" in dir(self.finishedHandler) and isinstance(self.finishedHandler.__self__, QtCore.QObject):
			parent = parent or self.finishedHandler.__self__
			self.finished.connect(self.finishedHandler)
		assert parent is not None
		self.setParent(parent)
		request.downloadProgress.connect(self.onDownloadProgress)
		request.uploadProgress.connect(self.onUploadProgress)
		request.finished.connect(self.onFinished)

	# logger.debug("RequestWrapper exit")

	def onDownloadProgress(self, bytesReceived: int, bytesTotal: int) -> None:
		# logger.debug("onDownloadProgress")
		if bytesReceived == bytesTotal:
			self.requestStatus = True
		self.downloadProgress.emit(self, bytesReceived, bytesTotal)

	# logger.debug("onDownloadProgress done")

	def onUploadProgress(self, bytesSend: int, bytesTotal: int) -> None:
		# logger.debug("onUploadProgress")
		if bytesSend == bytesTotal:
			self.requestStatus = True
		self.uploadProgress.emit(self, bytesSend, bytesTotal)

	# logger.debug("onUploadProgress done")

	def onFinished(self) -> None:
		# logger.debug("onFinished")
		if self.unlockSkey:
			securityTokenProvider.unlockKey(self.unlockSkey)
		self.hasFinished = True
		if self.request.error() == self.request.NoError:
			self.requestSucceeded.emit(self)
		else:
			try:
				errorDescr = NetworkErrorDescrs[self.request.error()]
			except:  # Unknown error
				errorDescr = None
			if errorDescr:
				if not self.failSilent and not isPyodide:
					QtWidgets.QMessageBox.warning(
						None,
						"Networkrequest Failed",
						'The request to {0!r} failed with: {1}'.format(self.url, errorDescr))
			self.requestFailed.emit(self, self.request.error())
		self.finished.emit(self)
		# self.logger.debug("Request finished: %r", self)
		# self.logger.debug("Remaining requests: %d", len(NetworkService.currentRequests))
		self.request = None
		self.successHandler = None
		self.failureHandler = None
		self.finishedHandler = None
		QtCore.QCoreApplication.processEvents()
		self.deleteLater()

	# logger.debug("onFinished exit")

	def readAll(self) -> str:
		# logger.debug("readAll")
		return self.request.readAll()

	def abort(self) -> None:
		# logger.debug("abort")
		self.request.abort()


class RequestGroup(QtCore.QObject):
	"""Aggregates multiple RequestWrapper into one place.

	Informs the creator whenever an Query finishes processing and allows
	easy checking if there are more queries pending.
	"""

	GarbargeTypeName = "RequestGroup"
	requestsSucceeded = QtCore.pyqtSignal((QtCore.QObject,))
	requestFailed = QtCore.pyqtSignal((QtCore.QObject,))  # FIXME.....What makes sense here?
	finished = QtCore.pyqtSignal((QtCore.QObject,))
	progressUpdate = QtCore.pyqtSignal((QtCore.QObject, int, int))
	cancel = QtCore.pyqtSignal()

	def __init__(
			self,
			successHandler: Callable = None,
			failureHandler: Callable = None,
			finishedHandler: Callable = None,
			parent: Union[QtCore.QObject, None] = None,
			*args: Any,
			**kwargs: Any):
		super(RequestGroup, self).__init__(*args, **kwargs)
		if successHandler is not None:
			parent = parent or successHandler.__self__
			self.requestsSucceeded.connect(successHandler)
		if failureHandler is not None:
			parent = parent or failureHandler.__self__
			self.requestFailed.connect(failureHandler)
		if finishedHandler is not None:
			parent = parent or finishedHandler.__self__
			self.finished.connect(finishedHandler)
		assert parent is not None
		self.setParent(parent)
		self.queryCount = 0  # Total amount of subqueries remaining
		self.maxQueryCount = 0  # Total amount of all queries
		self.pendingRequests: List[Any] = list()
		self.runningRequests = 0
		self.hadErrors = False
		self.hasFinished = False

	def addQuery(self, query: RequestWrapper) -> None:
		"""Add an RequestWrapper to the Group
		"""

		query.setParent(self)
		query.downloadProgress.connect(self.onProgress)
		query.requestFailed.connect(self.onError)
		query.finished.connect(self.onFinished)
		self.cancel.connect(query.abort)
		self.queryCount += 1
		self.maxQueryCount += 1
		self.runningRequests += 1

	def addRequest(
			self,
			*args: Any,
			**kwargs: Any) -> None:
		self.pendingRequests.append((args, kwargs))
		self.launchNextRequest()

	def launchNextRequest(self) -> None:
		if not self.pendingRequests:
			return
		if self.runningRequests > 2:
			return
		args, kwargs = self.pendingRequests.pop(0)
		if "parent" in kwargs:
			del kwargs["parent"]
		req = NetworkService.request(*args, parent=self, **kwargs)
		self.addQuery(req)

	def onProgress(
			self,
			myRequest: RequestWrapper,
			bytesReceived: int,
			bytesTotal: int) -> None:
		if bytesReceived == bytesTotal:
			self.progressUpdate.emit(self, self.maxQueryCount - self.queryCount, self.maxQueryCount)

	def onError(self, myRequest: RequestWrapper, error: Any) -> None:
		self.requestFailed.emit(self)
		self.progressUpdate.emit(self, self.maxQueryCount - self.queryCount, self.maxQueryCount)
		self.runningRequests -= 1
		self.launchNextRequest()

	def onFinished(self, queryWrapper: Dict[str, Any]) -> None:
		self.queryCount -= 1
		self.runningRequests -= 1
		self.launchNextRequest()
		if self.queryCount == 0:
			QtCore.QTimer.singleShot(1000, self.recheckFinished)

	def recheckFinished(self) -> None:
		"""Delays emitting of our onFinished signal.

		On the local server the requests could finish even before all requests have been queued.
		"""
		if self.queryCount == 0:
			self.hasFinished = True
			self.finished.emit(self)
			self.deleteLater()

	def isIdle(self) -> bool:
		"""Check whenever no more queries are pending.

		:return: Bool
		"""
		return self.queryCount == 0

	def abort(self) -> None:
		"""Abort all remaining queries.

		If there was at least one running query, the finishedHandler will be called shortly after.
		"""
		self.cancel.emit()


class RemoteFile(QtCore.QObject):
	"""Allows easy access to remote files by their DL-Key.

	Its loads a File from the server if needed and Caches it locally sothat further requests will
	not bother the server again
	"""
	GarbargeTypeName = "RemoteFile"

	maxBlockTime = 30  # Maximum seconds, we are willing to wait for a file to download in "blocking" mode

	def __init__(
			self,
			dlKey: str,
			successHandler: Union[None, Callable] = None,
			failureHandler: Callable = None,
			*args: Any,
			**kwargs: Any):
		super(RemoteFile, self).__init__(*args, **kwargs)
		logger.debug("New RemoteFile: %s for %s", str(self), str(dlKey))
		self.successHandler = None
		self.failureHandler = None
		if successHandler:
			self.successHandlerSelf = weakref.ref(successHandler.__self__)
			self.successHandlerName = successHandler.__name__
		if failureHandler:
			self.failureHandlerSelf = weakref.ref(failureHandler.__self__)
			self.failureHandlerName = failureHandler.__name__
		self.dlKey = dlKey
		fileName = os.path.join(conf.currentPortalConfigDirectory, sha1(dlKey.encode("UTF-8")).hexdigest())
		if os.path.isfile(fileName):
			logger.debug("RemoteFile: file exists %r", fileName)
			# self.logger.debug("We already have that file :)")
			self._delayTimer = QtCore.QTimer(self)
			self._delayTimer.singleShot(250, self.onTimerEvent)
		else:
			logger.debug("RemoteFile: file missing %r", fileName)
			# self.logger.debug("Need to fetch that file")
			self.loadFile()
		NetworkService.currentRequests.append(self)

	def remove(self) -> None:
		"""Unregister this object, so it gets garbage collected
		"""
		# self.logger.debug("Checkpoint: remove")
		self._delayTimer = None
		NetworkService.currentRequests.remove(self)
		self.successHandler = None
		self.failureHandler = None

	def onTimerEvent(self) -> None:
		# self.logger.debug("Checkpoint: onTimerEvent")

		if "successHandlerSelf" in dir(self):
			s = self.successHandlerSelf()
			if s:
				try:
					getattr(s, self.successHandlerName)(self)
				except Exception as err:
					logger.exception(err)
		self._delayTimer = QtCore.QTimer(self)
		self._delayTimer.singleShot(250, self.remove)

	def loadFile(self) -> None:
		dlKey = self.dlKey
		if not dlKey.lower().startswith("http://") and not dlKey.lower().startswith("https://"):
			if dlKey.startswith("/"):
				url = NetworkService.url
				if url.endswith("/admin"):
					url = url[: -len("/admin")]
				dlKey = "%s%s" % (url, dlKey)
			else:
				dlKey = "/file/download/%s" % dlKey
		req = NetworkService.request(
			dlKey,
			successHandler=self.onFileAvailable,
			failSilent=True)

	def onFileAvailable(self, fileRequest: RequestWrapper) -> None:
		fileName = os.path.join(conf.currentPortalConfigDirectory, sha1(self.dlKey.encode("UTF-8")).hexdigest())
		logger.debug("RemoteFile.onFileAvailable: %r", fileName)
		data = fileRequest.readAll()
		open(fileName, "w+b").write(data.data())
		s = self.successHandlerSelf()
		if s:
			try:
				getattr(s, self.successHandlerName)(self)
			except Exception as err:
				pass
		self._delayTimer = QtCore.QTimer(self)
		# Queue our deletion giving our child (networkReply) chance to finish
		self._delayTimer.singleShot(250, self.remove)

	def getFileName(self) -> str:
		"""Returns the local fileName of our file, or none if downloading hasn't succeeded yet
		"""
		fileName = os.path.join(conf.currentPortalConfigDirectory, sha1(self.dlKey.encode("UTF-8")).hexdigest())
		if os.path.isfile(fileName):
			return fileName
		return ""

	def getFileContents(self) -> bytes:
		"""Returns the content of the file as bytes
		"""
		fileName = self.getFileName()
		if not fileName:
			return b""
		return open(fileName, "rb").read()


class NetworkService:
	url = "/admin"
	serverVersion = None
	currentRequests: List[RequestWrapper] = list()  # A list of currently running requests

	@staticmethod
	def genReqStr(value: Dict[str, Any], prefix="", multiPart=None) -> QHttpMultiPart:
		if not multiPart:
			multiPart = QHttpMultiPart(QHttpMultiPart.FormDataType)

		if isinstance(value, (QtCore.QFile, io.BufferedReader)):  # file content must be a QFile object
			# FIXME: This is broken. IoBufferedReader will be read to memory entirely - not streamed!!
			if "name" in dir(value):
				fileName = value.name
			elif "fileName" in dir(value):
				fileName = value.fileName()
			try:
				mimetype, encoding = mimetypes.guess_type(fileName, strict=False)
				mimetype = mimetype or "application/octet-stream"
			except:
				mimetype = "application/octet-stream"
			filePart = QHttpPart()
			filePart.setHeader(QNetworkRequest.ContentTypeHeader, mimetype)
			filePart.setHeader(
				QNetworkRequest.ContentDispositionHeader,
				'form-data; name="{0}"; filename="{1}"'.format(
					prefix,
					os.path.basename(fileName)))
			if isinstance(value, io.BufferedReader):
				filePart.setBody(value.read())
			else:
				filePart.setBodyDevice(value)
				value.setParent(multiPart)
			multiPart.append(filePart)
		elif isinstance(value, list):
			if not value:
				otherPart = QHttpPart()
				otherPart.setHeader(QNetworkRequest.ContentTypeHeader, "application/octet-stream")
				otherPart.setHeader(QNetworkRequest.ContentDispositionHeader, 'form-data; name="{0}"'.format(prefix))
				otherPart.setBody(b"")
				multiPart.append(otherPart)
			elif any([isinstance(x, dict) for x in value]):
				for idx, v in enumerate(value):
					NetworkService.genReqStr(v, (prefix+"." if prefix else "")+str(idx), multiPart)
			else:
				for val in value:
					logger.debug("serializing param item %r of list value %r", val, prefix)
					textPart = QHttpPart()
					textPart.setHeader(
						QNetworkRequest.ContentTypeHeader,
						"application/octet-stream")
					textPart.setHeader(
						QNetworkRequest.ContentDispositionHeader,
						'form-data; name="{0}"'.format(prefix))
					textPart.setBody(str(val).encode("utf-8"))
					multiPart.append(textPart)
		elif isinstance(value, dict):
			if prefix:
				prefix += "."
			for k, v in value.items():
				NetworkService.genReqStr(v, prefix+k, multiPart)
		#elif value is None:
			#return multiPart
		else:
			if value is None:
				value = ""
			otherPart = QHttpPart()
			otherPart.setHeader(QNetworkRequest.ContentTypeHeader, "application/octet-stream")
			otherPart.setHeader(QNetworkRequest.ContentDispositionHeader, 'form-data; name="{0}"'.format(prefix))
			otherPart.setBody(str(value).encode("utf-8"))
			multiPart.append(otherPart)
		return multiPart

	@staticmethod
	def request(
			url: str,
			params: Union[dict, None] = None,
			secure: bool = False,
			extraHeaders: Union[dict, None] = None,
			successHandler: Union[Callable, None] = None,
			failureHandler: Union[Callable, None] = None,
			finishedHandler: Union[Callable, None] = None,
			parent: Union[QtCore.QObject, None] = None,
			failSilent: bool = False) -> RequestWrapper:
		"""

		:param url:
		:param params:
		:param secure:
		:param extraHeaders:
		:param successHandler:
		:param failureHandler:
		:param finishedHandler:
		:param parent:
		:param failSilent:
		:return: RequestWrapper
		"""
		#if secure == True:
		#	SP2.addRequest(partial(NetworkService.request, url=url, params=params, extraHeaders=extraHeaders, successHandler=successHandler, failureHandler=failureHandler, finishedHandler=finishedHandler,parent=parent, failSilent=failSilent))
		global nam, _isSecureSSL
		if _isSecureSSL == False:  # Warn the user of a potential security risk
			msgRes = QtWidgets.QMessageBox.warning(
				None,
				QtCore.QCoreApplication.translate(
					"NetworkService",
					"Insecure connection"),
				QtCore.QCoreApplication.translate(
					"Updater",
					"The cacerts.pem file is missing or invalid. "
					"Your passwords and data will be send unsecured! Continue without encryption? If unsure, choose 'abort'!"),
				QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Abort)
			if msgRes == QtWidgets.QMessageBox.Ok:
				_isSecureSSL = None
			else:
				sys.exit(1)
		return RequestWrapper(url=url, params=params, secure=secure, extraHeaders=extraHeaders,successHandler=successHandler, failureHandler=failureHandler, finishedHandler=finishedHandler, parent=parent, failSilent=failSilent)

	@staticmethod
	def decode(req: RequestWrapper) -> Any:
		# logger.debug("NetworkService.decode: %r", req)
		data = req.readAll().data().decode("utf-8")
		return json.loads(data)

	@staticmethod
	def setup(url: str, *args: Any, **kwargs: Any) -> None:
		logger.debug("NetworkService.setup: %r, %r, %r", url, args, kwargs)
		NetworkService.url = url
		# This is the only request that is intentionally blocking
		try:
			req = request.urlopen(url + "/getVersion")
			rawData = req.read().decode("UTF-8")
			logger.debug("version raw data: %r", rawData)
			NetworkService.serverVersion = tuple(json.loads(rawData))
			assert isinstance(NetworkService.serverVersion, tuple) and len(NetworkService.serverVersion) == 3
		except Exception as err:
			logger.exception(err)
			NetworkService.serverVersion = (1, 0, 0)  # The first version of ViUR didn't support that
		logger.info("Attached to an instance running ViUR %s", NetworkService.serverVersion)
		securityTokenProvider.reset()
