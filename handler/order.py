from PyQt4 import QtCore, QtGui
from network import NetworkService
from event import event
from config import conf

def askYesNo( question ):
	return( QtGui.QMessageBox.question(	None,
									QtCore.QCoreApplication.translate("OrderHandler", "Please confirm"),
									question,
									QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
									QtGui.QMessageBox.No 
								)==QtGui.QMessageBox.Yes )

class ShopMarkPayedAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		parent = parent
		self.request = None
		super( ShopMarkPayedAction, self ).__init__( QtGui.QIcon("icons/status/payed.png"), QtCore.QCoreApplication.translate("OrderHandler", "Payment recived"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
	
	def onTriggered( self, e ):
		itemIndexes = []
		for row in [ x.row() for x in self.parentWidget().selectionModel.selection().indexes() ]:
			if not row in itemIndexes:
				itemIndexes.append( row )
		items = [ self.parentWidget().model.getData()[ x ] for x in itemIndexes ]
		if QtGui.QMessageBox.question(self.parentWidget(), QtCore.QCoreApplication.translate("OrderHandler", "Mark as payed"), QtCore.QCoreApplication.translate("OrderHandler", "Mark %s orders as payed?" )% len( items ), QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)==QtGui.QMessageBox.No:
			return
		self.parent().overlay.inform( self.parent().overlay.BUSY )
		self.request = QueryAggregator()
		changedOne = False
		for item in items:
			if "state_payed" in item.keys() and str( item["state_payed"])=="1":
				if not askYesNo( 
						QtCore.QCoreApplication.translate(	"OrderHandler",
														"The order %s %s from %s is allready marked as payed. Resend its bill?" % (	item["bill_firstname"],
																															item["bill_lastname"],
																															item["creationdate"] ) ) ):
					continue
			changedOne = True
			self.request.addQuery( NetworkService.request( "/%s/markPayed" % self.parent().modul, {"id":  item["id"] }, secure=True ) )
		if changedOne:
			self.connect( self.request, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.onFinished ) 
		else:
			self.onFinished( None )
	
	def onFinished(self, req ):
		if self.request.isIdle():
			self.request.deleteLater()
			self.request = None
		self.parent().reloadData()
	
		
class ShopMarkSendAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		parent = parent
		self.request = None
		super( ShopMarkSendAction, self ).__init__( QtGui.QIcon("icons/status/send.png"), QtCore.QCoreApplication.translate("OrderHandler","Order Shipped"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
	
	def onTriggered( self, e ):
		itemIndexes = []
		for row in [ x.row() for x in self.parentWidget().selectionModel.selection().indexes() ]:
			if not row in itemIndexes:
				itemIndexes.append( row )
		items = [ self.parentWidget().model.getData()[ x ] for x in itemIndexes ]
		if QtGui.QMessageBox.question(self.parentWidget(), QtCore.QCoreApplication.translate("OrderHandler", 'Mark shipped'), QtCore.QCoreApplication.translate("OrderHandler", "Mark %s orders as shipped?" ) % len( items ), QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)==QtGui.QMessageBox.No:
			return
		self.parent().overlay.inform( self.parent().overlay.BUSY )
		self.request = QueryAggregator()
		changedOne = False
		for item in items:
			if "state_send" in item.keys() and str( item["state_send"])=="1":
				if not askYesNo( 
						QtCore.QCoreApplication.translate(	"OrderHandler",
														"The order %s %s from %s is allready marked as shipped. Repeat the command?" % (	item["bill_firstname"],
																																item["bill_lastname"],
																																item["creationdate"] ) ) ):
					continue
			changedOne = True
			self.request.addQuery( NetworkService.request( "/%s/markSend" % self.parent().modul, {"id":  item["id"] }, secure=True ) )
		if changedOne:
			self.connect( self.request, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.onFinished ) 
		else:
			self.onFinished( None )

	def onFinished(self, req ):
		if self.request.isIdle():
			self.request.deleteLater()
			self.request = None
		self.parent().reloadData()
		
class ShopMarkCanceledAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		parent = parent
		self.request = None
		super( ShopMarkCanceledAction, self ).__init__( QtGui.QIcon("icons/actions/cancel_small.png"), QtCore.QCoreApplication.translate("OrderHandler","Order canceled"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
	
	def onTriggered( self, e ):
		itemIndexes = []
		for row in [ x.row() for x in self.parentWidget().selectionModel.selection().indexes() ]:
			if not row in itemIndexes:
				itemIndexes.append( row )
		items = [ self.parentWidget().model.getData()[ x ] for x in itemIndexes ]
		if QtGui.QMessageBox.question(self.parentWidget(), QtCore.QCoreApplication.translate("OrderHandler", 'Mark shipped'), QtCore.QCoreApplication.translate("OrderHandler", "Cancel %s orders?" ) % len( items ), QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)==QtGui.QMessageBox.No:
			return
		self.parent().overlay.inform( self.parent().overlay.BUSY )
		self.request = QueryAggregator()
		changedOne = False
		for item in items:
			if "state_canceled" in item.keys() and str( item["state_canceled"])=="1":
				if not askYesNo( 
						QtCore.QCoreApplication.translate(	"OrderHandler",
														"The order %s %s from %s is allready marked as canceled. Repeat the command?" % (	item["bill_firstname"],
																																item["bill_lastname"],
																																item["creationdate"] ) ) ):
					continue
			changedOne = True
			self.request.addQuery( NetworkService.request( "/%s/markCanceled" % self.parent().modul, {"id":  item["id"] }, secure=True ) )
		if changedOne:
			self.connect( self.request, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.onFinished ) 
		else:
			self.onFinished( None )

	def onFinished(self, req ):
		if self.request.isIdle():
			self.request.deleteLater()
			self.request = None
		self.parent().reloadData()

	
class OrderHandler( QtCore.QObject ):
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('requestModulListActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)') ,  self.requestModulListActions )

	def requestModulListActions(self, queue, modul, config, parent ):
		try:
			config = conf.serverConfig["modules"][ modul ]
			if( not config["handler"].startswith("list.order") ):
				return
		except: 
			return
		queue.registerHandler( 10, ShopMarkSendAction )
		queue.registerHandler( 10, ShopMarkPayedAction )
		queue.registerHandler( 10, ShopMarkCanceledAction )

_orderHandler = OrderHandler()
