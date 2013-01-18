from ui.editUI import Ui_Edit
from PyQt4 import QtCore, QtGui
from network import NetworkService
from event import event
from collections import OrderedDict
from utils import RegisterQueue, Overlay
from mainwindow import EntryHandler
from ui.editpreviewUI import Ui_EditPreview
from config import conf


class Preview( QtGui.QWidget ):
	"""Livepreview for unsaved changes"""
	def __init__( self, modul, data, *args, **kwargs ):
		super( Preview, self).__init__( *args, **kwargs )
		self.ui = Ui_EditPreview()
		self.ui.setupUi( self )
		self.modul = modul
		self.data = data
		self.ui.cbUrls.hide()
		self.ui.btnReload.hide()
		if "name" in data.keys():
			self.setWindowTitle("Vorschau: %s" % data["name"])
		self.loadURL()
		self.show()
	
	def loadURL( self ):
		try:
			res = NetworkService.request( "%s/%s/preview" % (NetworkService.url.replace("/admin",""), self.modul ), self.data, secure=True )
			res = res.decode("UTF-8")
		except:
			res = QtCore.QCoreApplication.translate("Preview", "Preview not possible")
		self.setHTML( res )
	
	def setHTML( self, html ):
		self.ui.webView.setHtml( html, QtCore.QUrl( "%s/%s/preview" % (NetworkService.url.replace("/admin",""), self.modul ) ) )
		
	def on_btnReload_released(self, *args, **kwargs):
		self.loadURL()

class EditHandler( EntryHandler ):
	def __init__( self, modul, widget, *args, **kwargs ):
		super( EditHandler, self ).__init__( modul, *args, **kwargs )
		self.addWidget( widget )
		if widget.id:
			self.setText( 0, QtCore.QCoreApplication.translate("EditHandler", "Edit entry") )
			self.setIcon( 0, QtGui.QIcon("icons/actions/edit_small.png") )
		else:
			self.setText( 0, QtCore.QCoreApplication.translate("EditHandler", "Add entry") )
			self.setIcon( 0, QtGui.QIcon("icons/actions/add_small.png") )
		self.focus()
		widget.connect( widget, QtCore.SIGNAL("descriptionChanged(PyQt_PyObject)"), self.on_widget_descriptionChanged )
		
	def on_widget_descriptionChanged( self, descr ):
		self.setText( 0, descr )
		self.focus()

	def clicked( self ):
		if self.widgets:
			self.focus()
	
	def close( self ):
		super( EditHandler, self).close()
		if not self.widgets:
			self.remove()

class Edit( QtGui.QWidget ):
	def __init__(self, modul, id=0, *args, **kwargs ):
		super( Edit, self ).__init__( *args, **kwargs )
		if not "ui" in dir( self ):
			self.ui = Ui_Edit()
			self.ui.setupUi( self )
		self.modul = modul
		self.id = id
		self.bones = {}
		self.overlay = Overlay( self )
		self.overlay.inform( self.overlay.BUSY )
		self.reloadData( )
		self.closeOnSuccess = False
		#Hide Previewbuttons if no PreviewURLs are set
		if modul in conf.serverConfig["modules"].keys():
			if not "previewurls" in conf.serverConfig["modules"][ self.modul  ].keys() \
				or not conf.serverConfig["modules"][ self.modul  ][ "previewurls"  ]:
				self.ui.btnPreview.hide()
		if modul == "_tasks":
			self.ui.btnPreview.hide()
			self.ui.btnSaveClose.setText( QtCore.QCoreApplication.translate("EditHandler", "Execute") )
			self.ui.btnSaveContinue.hide()
			self.ui.btnReset.hide()

	def getBreadCrumb( self ):
		return( QtCore.QCoreApplication.translate("EditHandler", "List: %s") % self.modul, QtGui.QPixmap( "icons/action/edit.png" ) )
		
	
	def on_btnClose_released(self, *args, **kwargs):
		event.emit( QtCore.SIGNAL('popWidget(PyQt_PyObject)'), self )

	def reloadData(self):
		if self.modul == "_tasks":
			request = NetworkService.request("/%s/execute/%s" % ( self.modul, self.id ), successHandler=self.setData )
		elif self.id: #We are in Edit-Mode
			request = NetworkService.request("/%s/edit/%s" % ( self.modul, self.id ), successHandler=self.setData )
		else:
			request = NetworkService.request("/%s/add/" % ( self.modul ), successHandler=self.setData )
		
	def on_btnReset_released( self, *args, **kwargs ):
		res = QtGui.QMessageBox.question(	self,
						QtCore.QCoreApplication.translate("EditHandler", "Confirm reset"),
						QtCore.QCoreApplication.translate("EditHandler", "Discard all unsaved changes?"),
						QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No
						)
		if res == QtGui.QMessageBox.Yes:
			self.setData( data=self.dataCache )

	def parseHelpText( self, txt ):
		"""Parses the HTML-Text txt and returns it with remote Images replaced with their local copys
		
		@type txt: String
		@param txt: HTML-Text
		@return: String
		"""
		res = ""
		while txt:
			idx = txt.find("<img src=")
			if idx==-1:
				res += txt
				return( res )
			startpos = txt.find( "\"", idx+8)+1
			endpos = txt.find( "\"", idx+13)
			url = txt[ startpos:endpos ]
			res += txt[ : startpos ]
			res += getFileName( url ) #FIXME: BROKEN
			txt = txt[ endpos : ]
		
		fileName = os.path.join( conf.currentPortalConfigDirectory, sha1(dlkey.encode("UTF-8")).hexdigest() )
		if not os.path.isfile( fileName ):
			try:
				data = NetworkService.request( dlkey )
			except:
				return( None )
			open( fileName, "w+b" ).write( data )	
		return( fileName )


	def setData( self, request=None, data=None ):
		"""
		Rebuilds the UI according to the skeleton recived from server
		
		@type data: dict
		@param data: The data recived
		"""
		assert (request or data)
		if request:
			data = NetworkService.decode( request )
		#Clear the UI
		while( self.ui.tabWidget.count() ):
			item = self.ui.tabWidget.widget(0)
			if item and item.widget():
				item.widget().deleteLater()
				if "remove" in dir( item.widget() ):
					item.widget().remove()
			self.ui.tabWidget.removeTab( 0 )
		self.bones = OrderedDict()
		self.dataCache = data
		tmpDict = {}
		tabs = {}
		for key, bone in data["structure"]:
			tmpDict[ key ] = bone
		for key, bone in data["structure"]:
			if key=="id" or bone["visible"]==False:
				continue
			if "params" in bone.keys() and bone["params"] and "category" in bone["params"].keys():
				tabName = bone["params"]["category"]
			else:
				tabName = QtCore.QCoreApplication.translate("EditHandler", "General")
			if not tabName in tabs.keys():
				scrollArea = QtGui.QScrollArea()
				containerWidget = QtGui.QWidget( scrollArea )
				scrollArea.setWidget( containerWidget )
				tabs[tabName] = QtGui.QFormLayout( containerWidget )
				containerWidget.setLayout( tabs[tabName] )
				containerWidget.setSizePolicy( QtGui.QSizePolicy( QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred) )
				self.ui.tabWidget.addTab( scrollArea,  tabName )
				scrollArea.setWidgetResizable(True)
			queue = RegisterQueue()
			event.emit( QtCore.SIGNAL('requestBoneEditWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),queue, self.modul, key, tmpDict )
			widget = queue.getBest()
			if bone["error"]:
				dataWidget = QtGui.QWidget()
				layout = QtGui.QHBoxLayout(dataWidget)
				dataWidget.setLayout( layout )
				layout.addWidget( widget, stretch=1 )
				iconLbl = QtGui.QLabel( dataWidget )
				if bone["required"]:
					iconLbl.setPixmap( QtGui.QPixmap( "icons/status/error.png" ) )
				else:
					iconLbl.setPixmap( QtGui.QPixmap( "icons/status/incomplete.png" ) )
				layout.addWidget( iconLbl, stretch=0 )
				iconLbl.setToolTip( str(bone["error"]) )
			else:
				dataWidget =  widget
			lblWidget = QtGui.QWidget( self )
			layout = QtGui.QHBoxLayout(lblWidget)
			if "params" in bone.keys() and isinstance( bone["params"], dict ) and "tooltip" in bone["params"].keys():
				lblWidget.setToolTip( self.parseHelpText( bone["params"]["tooltip"] ) )
			descrLbl = QtGui.QLabel( bone["descr"], lblWidget )
			descrLbl.setWordWrap(True)
			layout.addWidget( descrLbl )
			tabs[tabName].addRow( lblWidget , dataWidget )
			dataWidget.show()
			self.bones[ key ] = widget
		self.unserialize( data["values"] )
		if self.id and "name" in data["values"].keys(): #Update name in Menu
			self.emit( QtCore.SIGNAL("descriptionChanged(PyQt_PyObject)"), QtCore.QCoreApplication.translate("EditHandler", "Edit: %s") % str( data["values"]["name"] ) )
		if self.overlay.status==self.overlay.BUSY:
			self.overlay.clear()

	def unserialize(self, data):
		for bone in self.bones.values():
			bone.unserialize( data )
	
	def on_btnSaveContinue_released(self, *args, **kwargs ):
		self.closeOnSuccess = False
		self.overlay.inform( self.overlay.BUSY )
		res = {}
		for key, bone in self.bones.items():
			value = bone.serialize()
			if value!=None:
				res[ key ] = value
		self.save( res )
		
	def on_btnSaveClose_released( self, *args, **kwargs ):
		self.closeOnSuccess = True
		self.overlay.inform( self.overlay.BUSY )
		res = {}
		for key, bone in self.bones.items():
			value = bone.serialize()
			if value!=None:
				res[ key ] = value
		self.save( res )

	def on_btnPreview_released( self, *args, **kwargs ):
		res = {}
		for key, bone in self.bones.items():
			value = bone.serialize()
			if value!=None:
				res[ key ] = value
		self.preview = Preview( self.modul, res )
	
	def save(self, data ):
		if self.modul=="_tasks":
			request = NetworkService.request("/%s/execute/%s" % ( self.modul, self.id ), data, secure=True, successHandler=self.onSaveResult )
		elif self.id:
			request = NetworkService.request("/%s/edit/%s" % ( self.modul, self.id ), data, secure=True, successHandler=self.onSaveResult )
		else:
			request = NetworkService.request("/%s/add/" % ( self.modul ), data, secure=True, successHandler=self.onSaveResult )

	
	def onSaveResult(self, request):
		try:
			data = NetworkService.decode( request )
		except:
			self.overlay.inform( self.overlay.ERROR, QtCore.QCoreApplication.translate("EditHandler", "There was an error saving your changes") )
			return
		if data=="OKAY":
			if self.modul=="_tasks":
				self.taskAdded()
				return
			else:
				self.overlay.inform( self.overlay.SUCCESS, QtCore.QCoreApplication.translate("EditHandler", "Entry saved")  )
				if self.closeOnSuccess:
					event.emit( QtCore.SIGNAL('popWidget(PyQt_PyObject)'), self )
				else:
					self.reloadData()
		else:
			self.overlay.inform( self.overlay.MISSING, QtCore.QCoreApplication.translate("EditHandler", "Missing data") )
			self.setData( data=data )
		self.emitEntryChanged( self.modul )

	def taskAdded(self):
		QtGui.QMessageBox.information(	self,
									QtCore.QCoreApplication.translate("EditHandler", "Task created"), 
									QtCore.QCoreApplication.translate("EditHandler", "The task was sucessfully created."), 
									QtCore.QCoreApplication.translate("EditHandler", "Okay") )
		self.parent().close()

	def emitEntryChanged( self, modul ):
		event.emit( QtCore.SIGNAL('dataChanged(PyQt_PyObject,PyQt_PyObject)'), modul, self )
