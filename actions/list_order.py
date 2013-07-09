from PyQt4 import QtCore, QtGui
from network import NetworkService, RequestGroup
from event import event
from config import conf
import os, os.path
from priorityqueue import protocolWrapperInstanceSelector, actionDelegateSelector

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
		super( ShopMarkPayedAction, self ).__init__( QtGui.QIcon("icons/status/payed.png"), QtCore.QCoreApplication.translate("OrderHandler", "Payment recived"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
	
	def onTriggered( self, e ):
		protoWrap = protocolWrapperInstanceSelector.select( self.parent().getModul() )
		assert protoWrap is not None
		itemIndexes = []
		for row in [ x.row() for x in self.parentWidget().list.selectionModel().selection().indexes() ]:
			if not row in itemIndexes:
				itemIndexes.append( row )
		items = [ self.parentWidget().list.model().getData()[ x ] for x in itemIndexes ]
		if QtGui.QMessageBox.question(self.parentWidget(), QtCore.QCoreApplication.translate("OrderHandler", "Mark as payed"), QtCore.QCoreApplication.translate("OrderHandler", "Mark %s orders as payed?" )% len( items ), QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)==QtGui.QMessageBox.No:
			return
		for item in items:
			protoWrap.execNetworkAction( "/%s/markPayed" % self.parent().modul, {"id":  item["id"] }, secure=True )
	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( modul.startswith("list.order") and actionName=="markpayed" )

actionDelegateSelector.insert( 1, ShopMarkPayedAction.isSuitableFor, ShopMarkPayedAction )

		
class ShopMarkSendAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		parent = parent
		self.request = None
		super( ShopMarkSendAction, self ).__init__( QtGui.QIcon("icons/status/send.png"), QtCore.QCoreApplication.translate("OrderHandler","Order Shipped"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
	
	def onTriggered( self, e ):
		protoWrap = protocolWrapperInstanceSelector.select( self.parent().getModul() )
		itemIndexes = []
		for row in [ x.row() for x in self.parentWidget().list.selectionModel().selection().indexes() ]:
			if not row in itemIndexes:
				itemIndexes.append( row )
		items = [ self.parentWidget().list.model().getData()[ x ] for x in itemIndexes ]
		if QtGui.QMessageBox.question(self.parentWidget(), QtCore.QCoreApplication.translate("OrderHandler", 'Mark shipped'), QtCore.QCoreApplication.translate("OrderHandler", "Mark %s orders as shipped?" ) % len( items ), QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)==QtGui.QMessageBox.No:
			return
		for item in items:
			if "state_send" in item.keys() and str( item["state_send"])=="1":
				if not askYesNo( 
						QtCore.QCoreApplication.translate(	"OrderHandler",
														"The order %s %s from %s is allready marked as shipped. Repeat the command?" % (	item["bill_firstname"],
																																item["bill_lastname"],
																																item["creationdate"] ) ) ):
					continue
			protoWrap.execNetworkAction( "/%s/markSend" % self.parent().modul, {"id":  item["id"] }, secure=True )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( modul.startswith("list.order") and actionName=="marksend" )

actionDelegateSelector.insert( 1, ShopMarkSendAction.isSuitableFor, ShopMarkSendAction )

		
class ShopMarkCanceledAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		parent = parent
		self.request = None
		super( ShopMarkCanceledAction, self ).__init__( QtGui.QIcon("icons/actions/cancel_small.png"), QtCore.QCoreApplication.translate("OrderHandler","Order canceled"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
	
	def onTriggered( self, e ):
		protoWrap = protocolWrapperInstanceSelector.select( self.parent().getModul() )
		itemIndexes = []
		for row in [ x.row() for x in self.parentWidget().list.selectionModel().selection().indexes() ]:
			if not row in itemIndexes:
				itemIndexes.append( row )
		items = [ self.parentWidget().list.model().getData()[ x ] for x in itemIndexes ]
		if QtGui.QMessageBox.question(self.parentWidget(), QtCore.QCoreApplication.translate("OrderHandler", 'Mark shipped'), QtCore.QCoreApplication.translate("OrderHandler", "Cancel %s orders?" ) % len( items ), QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)==QtGui.QMessageBox.No:
			return
		for item in items:
			if "state_canceled" in item.keys() and str( item["state_canceled"])=="1":
				if not askYesNo( 
						QtCore.QCoreApplication.translate(	"OrderHandler",
											"The order %s %s from %s is allready marked as canceled. Repeat the command?" % (	item["bill_firstname"],
																						item["bill_lastname"],
																						item["creationdate"] ) ) ):
					continue
			protoWrap.execNetworkAction( "/%s/markCanceled" % self.parent().modul, {"id":  item["id"] }, secure=True )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( modul.startswith("list.order") and actionName=="markcanceled" )

actionDelegateSelector.insert( 1, ShopMarkCanceledAction.isSuitableFor, ShopMarkCanceledAction )


class ShopDownloadBillAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		parent = parent
		self.request = None
		super( ShopDownloadBillAction, self ).__init__( QtGui.QIcon("icons/actions/download_small.png"), QtCore.QCoreApplication.translate("OrderHandler","Download Bill"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
	
	def onTriggered( self, e ):
		protoWrap = protocolWrapperInstanceSelector.select( self.parent().getModul() )
		itemIndexes = []
		for row in [ x.row() for x in self.parentWidget().list.selectionModel().selection().indexes() ]:
			if not row in itemIndexes:
				itemIndexes.append( row )
		items = [ self.parentWidget().list.model().getData()[ x ] for x in itemIndexes ]
		destDir = QtGui.QFileDialog.getExistingDirectory( self.parent() )
		if not destDir:
			return
		for item in items:
			req = protoWrap.execNetworkAction( "/%s/getBill" % self.parent().modul, {"id":  item["id"] }, secure=True, successHandler=self.saveBill )
			req.destDir = destDir
			assert not any( [ x in str(item["idx"]) for x in "/\\\".:"] )
			req.billIdx = str(item["idx"])

	def saveBill( self, req ):
		fname = "%s-%s.pdf" % ( QtCore.QCoreApplication.translate("OrderHandler", 'Bill'), req.billIdx )
		f = open( os.path.join( req.destDir, fname ), "w+b" )
		f.write( req.readAll() )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( modul.startswith("list.order") and actionName=="downloadbill" )

actionDelegateSelector.insert( 1, ShopDownloadBillAction.isSuitableFor, ShopDownloadBillAction )


class ShopDownloadDeliveryNoteAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		parent = parent
		self.request = None
		super( ShopDownloadDeliveryNoteAction, self ).__init__( QtGui.QIcon("icons/actions/download_small.png"), QtCore.QCoreApplication.translate("OrderHandler","Download delivery note"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
	

	def onTriggered( self, e ):
		protoWrap = protocolWrapperInstanceSelector.select( self.parent().getModul() )
		itemIndexes = []
		for row in [ x.row() for x in self.parentWidget().list.selectionModel().selection().indexes() ]:
			if not row in itemIndexes:
				itemIndexes.append( row )
		items = [ self.parentWidget().list.model().getData()[ x ] for x in itemIndexes ]
		destDir = QtGui.QFileDialog.getExistingDirectory( self.parent() )
		if not destDir:
			return
		for item in items:
			req = protoWrap.execNetworkAction( "/%s/getDeliveryNote" % self.parent().modul, {"id":  item["id"] }, secure=True, successHandler=self.saveBill )
			req.destDir = destDir
			assert not any( [ x in str(item["idx"]) for x in "/\\\".:"] )
			req.billIdx = str(item["idx"])

	def saveBill( self, req ):
		fname = "%s-%s.pdf" % ( QtCore.QCoreApplication.translate("OrderHandler", 'Delivery Note'), req.billIdx )
		f = open( os.path.join( req.destDir, fname ), "w+b" )
		f.write( req.readAll() )

	@staticmethod
	def isSuitableFor( modul, actionName ):
		return( modul.startswith("list.order") and actionName=="downloaddeliverynote" )

actionDelegateSelector.insert( 1, ShopDownloadDeliveryNoteAction.isSuitableFor, ShopDownloadDeliveryNoteAction )
