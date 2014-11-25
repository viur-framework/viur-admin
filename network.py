#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from queue import Queue
import urllib.request
import urllib.error
import urllib.parse
from urllib.parse import quote_plus
import sys
import os
import os.path
import time
import json
import mimetypes
import ssl
import random
from threading import local, Lock
import http.cookiejar
import base64
from queue import Queue, Empty as QEmpty, Full as QFull
from hashlib import sha1
import traceback
import logging
import weakref

import urllib

from config import conf
import string
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QUrl, QObject
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QSslConfiguration, QSslCertificate, QNetworkReply

##Setup the SSL-Configuration. We accept only the two known Certificates from google; reject all other
try:
    certs = open("cacert.pem", "r").read()
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
        def onSSLError(self, networkReply, sslErros):
            networkReply.ignoreSslErrors()

    _SSLFIX = SSLFIX()
    nam.sslErrors.connect(_SSLFIX.onSSLError)
    _isSecureSSL = False

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
#Match keys of that array with the numeric values suppied by QT
for k, v in NetworkErrorDescrs.copy().items():
    try:
        NetworkErrorDescrs[getattr(QNetworkReply, k)] = v
    except:
        pass  #Some errors don't seem to exist on all Platforms (eg. TemporaryNetworkFailureError seems missing on
        # MacOs)
    del NetworkErrorDescrs[k]


class SecurityTokenProvider(QObject):
    """
        Provides an pool of valid securitykeys.
        As they dont have to be requested before the original request can be send,
        the whole process speeds up
    """
    errorCount = 0

    def __init__(self, *args, **kwargs):
        super(SecurityTokenProvider, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger("RequestWrapper")
        self.queue = Queue(5)  #Queue of valid tokens
        self.isRequesting = False

    def reset(self):
        """
            Flushes the cache and tries to rebuild it
        """
        self.logger.debug("Reset")
        while not self.queue.empty():
            self.queue.get(False)
        self.isRequesting = False

    def fetchNext(self):
        """
            Requests a new SKey if theres currently no request pending
        """
        if not self.isRequesting:
            if SecurityTokenProvider.errorCount > 5:  #We got 5 Errors in a row
                raise RuntimeError("Error-limit exceeded on fetching skey")
            self.logger.debug("Fetching new skey")
            self.isRequesting = True
            NetworkService.request("/skey", successHandler=self.onSkeyAvailable, failureHandler=self.onError)

    def onError(self, request, error):
        self.logger.warning("Error fetching skey: %r", error)
        SecurityTokenProvider.errorCount += 1
        self.isRequesting = False
        raise ValueError("onError")

    def onSkeyAvailable(self, request=None):
        """
            New SKey got avaiable
        """
        self.isRequesting = False
        try:
            skey = NetworkService.decode(request)
        except Exception as err:
            self.logger.error("cannot decode get skey response")
            logging.exception(err)
            SecurityTokenProvider.errorCount += 1
            self.isRequesting = False
            return
        if SecurityTokenProvider.errorCount > 0:
            SecurityTokenProvider.errorCount = 0
        self.isRequesting = False
        if not skey:
            return
        try:
            self.queue.put((skey, time.time()), False)
        except QFull:
            print("Err: Queue FULL")

    def getKey(self):
        """
            Returns a fresh, valid SKey from the pool.
            Blocks and requests a new one if the Pool is currently empty.
        """
        self.logger.debug("Consuming a new skey")
        skey = None
        while not skey:
            self.fetchNext()
            try:
                skey, creationTime = self.queue.get(False)
                if creationTime < time.time() - 600:  #Its older than 10 minutes - dont use
                    self.logger.debug("Discarding old skey")
                    skey = None
                    raise QEmpty()
            except QEmpty:
                self.logger.debug("Empty cache! Please wait...")
                QtCore.QCoreApplication.processEvents()
        self.logger.debug("Using skey: %s", skey)
        return ( skey )


securityTokenProvider = SecurityTokenProvider()


class RequestWrapper(QtCore.QObject):
    GarbargeTypeName = "RequestWrapper"
    requestSucceeded = QtCore.pyqtSignal((QtCore.QObject,))
    requestFailed = QtCore.pyqtSignal((QtCore.QObject, QNetworkReply.NetworkError))
    finished = QtCore.pyqtSignal((QtCore.QObject,))
    uploadProgress = QtCore.pyqtSignal((QtCore.QObject, int, int))
    downloadProgress = QtCore.pyqtSignal((QtCore.QObject, int, int))

    def __init__(self, request, successHandler=None, failureHandler=None, finishedHandler=None, parent=None, url=None,
                 failSilent=False):
        super().__init__()
        self.logger = logging.getLogger("RequestWrapper")
        self.logger.debug("New network request: %s", str(self))
        self.request = request
        self.url = url
        self.failSilent = failSilent
        request.setParent(self)
        self.hasFinished = False
        if successHandler and "__self__" in dir(successHandler) and isinstance(successHandler.__self__, QtCore.QObject):
            parent = parent or successHandler.__self__
            self.requestSucceeded.connect(successHandler)
        if failureHandler and "__self__" in dir(failureHandler) and isinstance(failureHandler.__self__, QtCore.QObject):
            parent = parent or failureHandler.__self__
            self.requestFailed.connect(failureHandler)
        if finishedHandler and "__self__" in dir(finishedHandler) and isinstance(finishedHandler.__self__,
                                                                                 QtCore.QObject):
            parent = parent or finishedHandler.__self__
            self.finished.connect(finishedHandler)
        assert parent is not None
        self.setParent(parent)
        request.downloadProgress.connect(self.onDownloadProgress)
        request.uploadProgress.connect(self.onUploadProgress)
        request.finished.connect(self.onFinished)

    def onDownloadProgress(self, bytesReceived, bytesTotal):
        if bytesReceived == bytesTotal:
            self.requestStatus = True
        self.downloadProgress.emit(self, bytesReceived, bytesTotal)


    def onUploadProgress(self, bytesSend, bytesTotal):
        if bytesSend == bytesTotal:
            self.requestStatus = True
        self.uploadProgress.emit(self, bytesSend, bytesTotal)

    def onFinished(self):
        self.hasFinished = True
        if self.request.error() == self.request.NoError:
            self.requestSucceeded.emit(self)
        else:
            try:
                errorDescr = NetworkErrorDescrs[self.request.error()]
            except:  #Unknown error
                errorDescr = None
            if errorDescr:
                if not self.failSilent:
                    QtGui.QMessageBox.warning(None, "Networkrequest Failed",
                                              "The request to \"%s\" failed with: %s" % (self.url, errorDescr))
            self.requestFailed.emit(self, self.request.error())
        self.finished.emit(self)
        self.logger.debug("Request finished: %r", self)
        self.logger.debug("Remaining requests: %d", len(NetworkService.currentRequests))
        self.request = None
        self.successHandler = None
        self.failureHandler = None
        self.finishedHandler = None
        self.deleteLater()

    def readAll(self):
        return ( self.request.readAll() )

    def abort(self):
        self.request.abort()


class RequestGroup(QtCore.QObject):
    """
        Aggregates multiple RequestWrapper into one place.
        Informs the creator whenever an Query finishes processing and allows
        easy checking if there are more queries pending.
    """
    GarbargeTypeName = "RequestGroup"
    requestsSucceeded = QtCore.pyqtSignal((QtCore.QObject,))
    requestFailed = QtCore.pyqtSignal((QtCore.QObject,))  #FIXME.....What makes sense here?
    finished = QtCore.pyqtSignal((QtCore.QObject,))
    progessUpdate = QtCore.pyqtSignal((QtCore.QObject, int, int))
    cancel = QtCore.pyqtSignal()

    def __init__(self, successHandler=None, failureHandler=None, finishedHandler=None, parent=None, *args, **kwargs):
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
        self.hadErrors = False
        self.hasFinished = False

    def addQuery(self, query):
        """
            Add an RequestWrapper to the Group
        """
        query.setParent(self)
        query.downloadProgress.connect(self.onProgress)
        query.requestFailed.connect(self.onError)
        query.finished.connect(self.onFinished)
        self.cancel.connect(query.abort)
        self.queryCount += 1
        self.maxQueryCount += 1


    def onProgress(self, request, bytesReceived, bytesTotal):
        if bytesReceived == bytesTotal:
            self.progessUpdate.emit(self, self.maxQueryCount - self.queryCount, self.maxQueryCount)
        #self.emit( QtCore.SIGNAL("progessUpdate(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)"), self,
        # self.maxQueryCount-len( self.querys ), self.maxQueryCount )

    def onError(self, request, error):
        self.requestFailed.emit(self)
        self.progessUpdate.emit(self, self.maxQueryCount - self.queryCount, self.maxQueryCount)

    def onFinished(self, queryWrapper):
        self.queryCount -= 1
        if self.queryCount == 0:
            QtCore.QTimer.singleShot(25, self.recheckFinished)

    def recheckFinished(self):
        """
            Delay the emiting of our onFinished signal, as on the local
            server the requests could finish even before all requests have
            been queued.
        """
        if self.queryCount == 0:
            self.hasFinished = True
            self.finished.emit(self)
            self.deleteLater()


    def isIdle(self):
        """
            Check whenever no more querys are pending.
            @returns: Bool
        """
        return ( self.queryCount == 0 )

    def abort(self):
        """
            Abort all remaining queries.
            If there was at least one running query, the finishedHandler will be called shortly after.
        """
        self.cancel.emit()


class RemoteFile(QtCore.QObject):
    """
        Allows easy access to remote files by their DL-Key.
        Its loads a File from the server if needed and Caches it locally sothat further requests will
        not bother the server again
    """
    GarbargeTypeName = "RemoteFile"

    maxBlockTime = 30  #Maximum seconds, we are willing to wait for a file to download in "blocking" mode

    def __init__(self, dlKey, successHandler=None, failureHandler=None, *args, **kwargs):
        super(RemoteFile, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger("RemoteFile")
        self.logger.debug("New RemoteFile: %s for %s", str(self), str(dlKey))
        if successHandler:
            self.successHandlerSelf = weakref.ref(successHandler.__self__)
            self.successHandlerName = successHandler.__name__
        if failureHandler:
            self.failureHandlerSelf = weakref.ref(failureHandler.__self__)
            self.failureHandlerName = failureHandler.__name__
        self.dlKey = dlKey
        fileName = os.path.join(conf.currentPortalConfigDirectory, sha1(dlKey.encode("UTF-8")).hexdigest())
        if os.path.isfile(fileName):
            self.logger.debug("We already have that file :)")
            self._delayTimer = QtCore.QTimer(self)
            self._delayTimer.singleShot(250, self.onTimerEvent)
        else:
            self.logger.debug("Need to fetch that file")
            self.loadFile()
        NetworkService.currentRequests.append(self)

    def remove(self):
        """
            Unregister this object, so it gets garbarge collected
        """
        self.logger.debug("Checkpoint: remove")
        self._delayTimer = None
        NetworkService.currentRequests.remove(self)
        self.successHandler = None
        self.failureHandler = None


    def onTimerEvent(self):
        self.logger.debug("Checkpoint: onTimerEvent")
        if "successHandlerSelf" in dir(self):
            s = self.successHandlerSelf()
            if s:
                try:
                    getattr(s, self.successHandlerName)(self)
                except e:
                    self.logger.exception(e)
        self._delayTimer = QtCore.QTimer(self)
        self._delayTimer.singleShot(250, self.remove)


    def loadFile(self):
        dlKey = self.dlKey
        if not dlKey.lower().startswith("http://") and not dlKey.lower().startswith("https://"):
            if dlKey.startswith("/"):
                url = NetworkService.url
                if url.endswith("/admin"):
                    url = url[: -len("/admin")]
                dlKey = "%s%s" % (url, dlKey)
            else:
                dlKey = "/file/download/%s" % dlKey
        req = NetworkService.request(dlKey, successHandler=self.onFileAvaiable, failSilent=True)

    def onFileAvaiable(self, request):
        self.logger.debug("Checkpoint: onFileAvaiable")
        fileName = os.path.join(conf.currentPortalConfigDirectory, sha1(self.dlKey.encode("UTF-8")).hexdigest())
        data = request.readAll()
        open(fileName, "w+b").write(data.data())
        s = self.successHandlerSelf()
        if s:
            try:
                getattr(s, self.successHandlerName)(self)
            except e:
                self.logger.exception(e)
        self._delayTimer = QtCore.QTimer(
            self)  # Queue our deletion, sothat our child (networkReply) has a chance to finnish
        self._delayTimer.singleShot(250, self.remove)

    def getFileName(self):
        """
            Returns the local fileName of our file, or none if downloading hasnt succeded yet
        """
        fileName = os.path.join(conf.currentPortalConfigDirectory, sha1(self.dlKey.encode("UTF-8")).hexdigest())
        if os.path.isfile(fileName):
            return ( fileName )
        return ( "" )

    def getFileContents(self):
        """
            Returns the content of the file as bytes
        """
        fileName = self.getFileName()
        if not fileName:
            return ( b"" )
        return ( open(fileName, "rb").read() )


class NetworkService():
    url = None
    currentRequests = []  #A list of currently running requests
    logger = logging.getLogger("NetworkService")

    @staticmethod
    def genReqStr(params):
        boundary_str = "---" + ''.join(
            [random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for x in range(13)])
        boundary = boundary_str.encode("UTF-8")
        res = b'Content-Type: multipart/mixed; boundary="' + boundary + b'"\r\nMIME-Version: 1.0\r\n'
        res += b'\r\n--' + boundary
        for (key, value) in list(params.items()):
            if all([x in dir(value) for x in ["name", "read"]]):  #File
                try:
                    (type, encoding) = mimetypes.guess_type(value.name.decode(sys.getfilesystemencoding()),
                                                            strict=False)
                    type = type or "application/octet-stream"
                except:
                    type = "application/octet-stream"
                res += b'\r\nContent-Type: ' + type.encode(
                    "UTF-8") + b'\r\nMIME-Version: 1.0\r\nContent-Disposition: form-data; name="' + key.encode(
                    "UTF-8") + b'"; filename="' + os.path.basename(value.name).decode(
                    sys.getfilesystemencoding()).encode("UTF-8") + b'"\r\n\r\n'
                res += value.read()
                res += b'\r\n--' + boundary
            elif isinstance(value, list):
                for val in value:
                    res += b'\r\nContent-Type: application/octet-stream\r\nMIME-Version: 1.0\r\nContent-Disposition: ' \
                           b'form-data; name="' + key.encode(
                        "UTF-8") + b'"\r\n\r\n'
                    res += str(val).encode("UTF-8")
                    res += b'\r\n--' + boundary
            else:
                res += b'\r\nContent-Type: application/octet-stream\r\nMIME-Version: 1.0\r\nContent-Disposition: form-data; name="' + key.encode(
                    "UTF-8") + b'"\r\n\r\n'
                res += str(value).encode("UTF-8")
                res += b'\r\n--' + boundary
        res += b'--\r\n'
        return ( res, boundary )

    @staticmethod
    def request(url, params=None, secure=False, extraHeaders=None, successHandler=None, failureHandler=None,
                finishedHandler=None, parent=None, failSilent=False):
        global nam, _isSecureSSL
        if _isSecureSSL == False:  #Warn the user of a potential security risk
            msgRes = QtGui.QMessageBox.warning(None, QtCore.QCoreApplication.translate("NetworkService",
                                                                                       "Insecure connection"),
                                               QtCore.QCoreApplication.translate("Updater",
                                                                                 "The cacerts.pem file is missing or invalid. Your passwords and data will be send unsecured! Continue without encryption? If unsure, choose \"abort\"!"),
                                               QtCore.QCoreApplication.translate("NetworkService",
                                                                                 "Continue in unsecure mode"),
                                               QtCore.QCoreApplication.translate("NetworkService", "Abort"))
            if msgRes == 0:
                _isSecureSSL = None
            else:
                sys.exit(1)
        if secure:
            key = securityTokenProvider.getKey()
            if not params:
                params = {}
            params["skey"] = key
        if url.lower().startswith("http"):
            reqURL = QUrl(url)
        else:
            reqURL = QUrl(NetworkService.url + url)
        req = QNetworkRequest(reqURL)
        if extraHeaders:
            for k, v in extraHeaders.items():
                req.setRawHeader(k, v)
        if params:
            if isinstance(params, dict):
                multipart, boundary = NetworkService.genReqStr(params)
                req.setRawHeader("Content-Type", b'multipart/form-data; boundary=' + boundary + b'; charset=utf-8')
            elif isinstance(params, bytes):
                req.setRawHeader("Content-Type", b'application/x-www-form-urlencoded')
                multipart = params
            else:
                print(params)
                print(type(params))
            return (
            RequestWrapper(nam.post(req, multipart), successHandler, failureHandler, finishedHandler, parent, url=url,
                           failSilent=failSilent) )
        else:
            return (RequestWrapper(nam.get(req), successHandler, failureHandler, finishedHandler, parent, url=url,
                                   failSilent=failSilent) )

    @staticmethod
    def decode(req):
        data = req.readAll().data().decode("utf-8")
        # print("data %r", type(data))
        NetworkService.logger.debug("decoding request data %r", data)
        return json.loads(data)

    @staticmethod
    def setup(url, *args, **kwargs):
        NetworkService.url = url
        securityTokenProvider.reset()

