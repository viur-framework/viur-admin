from PyQt4 import QtCore, QtGui
from network import NetworkService
from event import event
from config import conf
from utils import QueryAggregator

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
		for item in items:
			#order = service.call( "/order/view", {"id":  item["id"] }, secure=True ) #Fixme: We need a solution for this...
			#if "is_payed" in  order["values"].keys() and str( order["values"]["is_payed"])=="1":
			#	if not askYesNo( "Bestellung von %s %s vom %s bereits als Bezahlt markiert. Rechnung erneut zusenden?" % (order["values"]["bill_firstname"], order["values"]["bill_lastname"], order["values"]["creationdate"] ) ):
			#		continue
			self.request.addQuery( NetworkService.request( "/%s/markPayed" % self.parent().modul, {"id":  item["id"] }, secure=True ) )
		self.connect( self.request, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.onFinished ) 
	
	def onFinished(self, req ):
		if self.request.isIdle():
			self.request.deleteLater()
			self.request = None
		self.parent().overlay.inform( self.parent().overlay.SUCCESS )
	
		
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
		for item in items:
			#order = service.call( "/order/view", {"id":  item["id"] }, secure=True ) #Fixme: We need a solution for this...
			#if "is_payed" in  order["values"].keys() and str( order["values"]["is_payed"])=="1":
			#	if not askYesNo( "Bestellung von %s %s vom %s bereits als Bezahlt markiert. Rechnung erneut zusenden?" % (order["values"]["bill_firstname"], order["values"]["bill_lastname"], order["values"]["creationdate"] ) ):
			#		continue
			self.request.addQuery( NetworkService.request( "/%s/markSend" % self.parent().modul, {"id":  item["id"] }, secure=True ) )
		self.connect( self.request, QtCore.SIGNAL("finished(PyQt_PyObject)"), self.onFinished ) 

	def onFinished(self, req ):
		if self.request.isIdle():
			self.request.deleteLater()
			self.request = None
		self.parent().overlay.inform( self.parent().overlay.SUCCESS )

	
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

_orderHandler = OrderHandler()
