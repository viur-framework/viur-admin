from PyQt4 import QtCore, QtGui
from network import NetworkService
from event import event
from ui.calenderlistUI import Ui_List
from handler.list import ListCoreHandler, List
from utils import RegisterQueue, Overlay, formatString, QueryAggregator
from config import conf

class CalenderList( List ):
	def __init__(self, modul, fields=None, filter=None, *args, **kwargs ):
		QtGui.QWidget.__init__( self, *args, **kwargs )
		self.ui = Ui_List()
		self.ui.setupUi( self )
		self.overlay = Overlay( self )
		self.toolBar = QtGui.QToolBar( self )
		self.toolBar.setIconSize( QtCore.QSize( 32, 32 ) )
		self.ui.tableView.verticalHeader().hide()
		super( CalenderList, self ).__init__( modul, fields, filter, *args, **kwargs )
		self.filterTypes = {	"none": QtCore.QCoreApplication.translate("CalenderList", "unfiltered"),
						"year": QtCore.QCoreApplication.translate("CalenderList", "Year"), 
						"month": QtCore.QCoreApplication.translate("CalenderList", "Month"), 
						"day": QtCore.QCoreApplication.translate("CalenderList", "Day") }
		self.currentFilterMode = None
		for k, v in self.filterTypes.items():
			self.ui.cbFilterType.addItem( v, k )

	def on_cbFilterType_currentIndexChanged(self, txt):
		if isinstance( txt, int ):
			return
		for k, v in self.filterTypes.items():
			if v == txt :
				self.currentFilterMode = k
		if self.currentFilterMode == "none":
			self.ui.deFilter.setDisplayFormat( "---" )
			self.ui.deFilter.setEnabled( False )
		elif self.currentFilterMode == "year":
			self.ui.deFilter.setDisplayFormat( QtCore.QCoreApplication.translate("CalenderList", "yyyy") )
			self.ui.deFilter.setEnabled( True )
		elif self.currentFilterMode == "month":
			self.ui.deFilter.setDisplayFormat( QtCore.QCoreApplication.translate("CalenderList", "MM.yyyy") )
			self.ui.deFilter.setEnabled( True )
		elif self.currentFilterMode == "day":
			self.ui.deFilter.setDisplayFormat( QtCore.QCoreApplication.translate("CalenderList", "dd.MM.yyyy") )
			self.ui.deFilter.setEnabled( True )
		self.updateDateFilter()
	
	def on_deFilter_dateChanged(self, date):
		self.updateDateFilter()
	
	def updateDateFilter(self):
		filter = self.model.getFilter()
		if self.currentFilterMode=="none":
			if filter and "startdate$gt" in filter.keys():
				del filter["startdate$gt"]
			if filter and "startdate$lt" in filter.keys():
				del filter["startdate$lt"]
		elif self.currentFilterMode=="year":
			filter["startdate$gt"] = self.ui.deFilter.date().toString("01.01.yyyy")
			filter["startdate$lt"] = "01.01.%0.4i" % (self.ui.deFilter.date().year()+1)
		elif self.currentFilterMode=="month":
			filter["startdate$gt"] = self.ui.deFilter.date().toString("01.MM.yyyy")
			#Calculate enddate: set Day of Month to 01; add 33 Days, read Year+Month
			filter["startdate$lt"] = QtCore.QDate( self.ui.deFilter.date().year(), self.ui.deFilter.date().month(), 1).addDays(33).toString("01.MM.yyyy")
		elif self.currentFilterMode=="day":
			filter["startdate$gt"] = self.ui.deFilter.date().toString("dd.MM.yyyy")
			filter["startdate$lt"] = self.ui.deFilter.date().addDays(1).toString("dd.MM.yyyy")
		self.model.setFilter( filter )
			


class CalenderCoreHandler( ListCoreHandler ):
	"""Class for holding the main (module) Entry within the modules-list"""
	
	def clicked( self ):
		if not self.widgets:
			config = conf.serverConfig["modules"][ self.modul ]
			if "columns" in config.keys():
				if "filter" in config.keys():
					self.addWidget( CalenderList( self.modul, config["columns"], config["filter"]  ) )
				else:
					self.addWidget( CalenderList( self.modul, config["columns"] ) )
			else:
				self.addWidget( CalenderList( self.modul ) )
		else:
			self.focus()

	
class CalenderHandler( QtCore.QObject ):
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('requestModulHandler(PyQt_PyObject,PyQt_PyObject)'), self.requestModulHandler )

	def requestModulHandler(self, queue, modulName ):
		config = conf.serverConfig["modules"][ modulName ]
		if config and "handler" in config.keys() and config["handler"].startswith("list.calender"):
			f = lambda: CalenderCoreHandler( modulName )
			queue.registerHandler( 5, f )


_calenderHandler = CalenderHandler()
