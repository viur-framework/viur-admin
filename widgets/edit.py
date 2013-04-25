# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from network import NetworkService
from event import event
from collections import OrderedDict
from utils import RegisterQueue, Overlay, formatString
from config import conf
from ui.editUI import Ui_Edit
from ui.editpreviewUI import Ui_EditPreview


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



class EditWidget( QtGui.QWidget ):
	appList = "list"
	appHierarchy = "hierarchy"
	appTree = "tree"
	appSingleton = "singleton"

	def __init__(self, modul, applicationType, id=0, rootNode=None, path=None, clone=False, *args, **kwargs ):
		"""
			Initialize a new Edit or Add-Widget for the given modul.
			@param modul: Name of the modul
			@type modul: String
			@param applicationType: Defines for what application this Add / Edit should be created. This hides additional complexity introduced by the hierarchy / tree-application
			@type applicationType: Any of EditWidget.appList, EditWidget.appHierarchy, EditWidget.appTree or EditWidget.appSingleton
			@param id: ID of the entry. If none, it will add a new Entry.
			@type id: Number
			@param rootNode: If applicationType==EditWidget.appHierarchy, the new entry will be added under this node, if applicationType==EditWidget,appTree the final node is derived from this and the path-parameter. 
							Has no effect if applicationType is not appHierarchy or appTree or if an id have been set.
			@type rootNode: String
			@param path: Specifies the path from the rootNode for new entries in a treeApplication
			@type path: String
			@param clone: If true, it will load the values from the given id, but will save a new entry (i.e. allows "cloning" an existing entry)
			@type clone: Bool
		"""
		super( EditWidget, self ).__init__( *args, **kwargs )
		if not "ui" in dir( self ):
			self.ui = Ui_Edit()
			self.ui.setupUi( self )
		self.modul = modul
		# A Bunch of santy-checks, as there is a great chance to mess around with this widget
		assert applicationType in [ EditWidget.appList, EditWidget.appHierarchy, EditWidget.appTree, EditWidget.appSingleton ] #Invalid Application-Type?
		if applicationType==EditWidget.appHierarchy or applicationType==EditWidget.appTree:
			assert id or rootNode #Need either an id or an rootNode
		if applicationType==EditWidget.appTree:
			assert id or path #Need either an id or an path
		if clone:
			assert id #Need an id if we should clone an entry
			assert not applicationType==EditWidget.appSingleton # We cant clone a singleton
			if applicationType==EditWidget.appHierarchy or applicationType==EditWidget.appTree:
				assert rootNode #We still need a rootNode for cloning
			if applicationType==EditWidget.appTree:
				assert path #We still need a path for cloning
		# End santy-checks
		self.applicationType = applicationType
		self.id = id
		self.rootNode = rootNode
		self.path = path
		self.clone = clone
		self.bones = {}
		self.overlay = Overlay( self )
		self.overlay.inform( self.overlay.BUSY )
		self.reloadData( )
		self.closeOnSuccess = False
		self._lastData = {} #Dict of structure and values recived
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
		if self._lastData:
			config = conf.serverConfig["modules"][ self.modul ]
			if "format" in config.keys():
				format = config["format"]
			else:
				format = "$(name)"
			itemName = formatString( format, self._lastData["structure"], self._lastData["values"] )
		else:
			itemName = ""
		if self.clone:
			if itemName:
				descr = QtCore.QCoreApplication.translate("EditHandler", "Clone: %s") % itemName
			else:
				descr = QtCore.QCoreApplication.translate("EditHandler", "Clone entry")
			icon = QtGui.QIcon( "icons/actions/clone.png" )
		elif self.id or self.applicationType == EditWidget.appSingleton: #Were editing
			if itemName:
				descr = QtCore.QCoreApplication.translate("EditHandler", "Edit: %s") % itemName
			else:
				descr = QtCore.QCoreApplication.translate("EditHandler", "Edit entry")
			icon = QtGui.QIcon( "icons/actions/edit.png" )
		else: #Were adding 
			descr = QtCore.QCoreApplication.translate("EditHandler", "Add entry") #We know that we cant know the name yet
			icon = QtGui.QIcon( "icons/actions/add.png" )
		return( descr, icon )
		
	
	def on_btnClose_released(self, *args, **kwargs):
		event.emit( QtCore.SIGNAL('popWidget(PyQt_PyObject)'), self )

	def reloadData(self):
		if self.modul == "_tasks":
			request = NetworkService.request("/%s/execute/%s" % ( self.modul, self.id ), successHandler=self.setData )
		elif self.applicationType == EditWidget.appList: ## Application: List
			if self.id: #We are in Edit-Mode
				request = NetworkService.request("/%s/edit/%s" % ( self.modul, self.id ), successHandler=self.setData )
			else:
				request = NetworkService.request("/%s/add/" % ( self.modul ), successHandler=self.setData )
		elif self.applicationType == EditWidget.appHierarchy: ## Application: Hierarchy
			if self.id: #We are in Edit-Mode
				self.request = NetworkService.request("/%s/edit/%s" % ( self.modul, self.id ), {"rootNode": self.rootNode }, successHandler=self.setData )
			else:
				self.request = NetworkService.request("/%s/add/" % ( self.modul ), {"parent": self.rootNode }, successHandler=self.setData )
		elif self.applicationType == EditWidget.appTree: ## Application: Tree
			if self.id: #We are in Edit-Mode
				self.request = NetworkService.request("/%s/edit/%s" % ( self.modul, self.id ), {"rootNode": self.rootNode, "path": self.path }, successHandler=self.setData )
			else:
				self.request = NetworkService.request("/%s/add/" % ( self.modul ), {"rootNode": self.rootNode, "path": self.path }, successHandler=self.setData )
		elif self.applicationType == EditWidget.appSingleton: ## Application: Singleton
			request = NetworkService.request("/%s/edit" % ( self.modul ), successHandler=self.setData )
		else:
			raise NotImplementedError() #Should never reach this

	def save(self, data ):
		if self.modul=="_tasks":
			request = NetworkService.request("/%s/execute/%s" % ( self.modul, self.id ), data, secure=True, successHandler=self.onSaveResult )
		elif self.applicationType == EditWidget.appList: ## Application: List
			if self.id and not self.clone:
				request = NetworkService.request("/%s/edit/%s" % ( self.modul, self.id ), data, secure=True, successHandler=self.onSaveResult )
			else:
				request = NetworkService.request("/%s/add/" % ( self.modul ), data, secure=True, successHandler=self.onSaveResult )
		elif self.applicationType == EditWidget.appHierarchy: ## Application: Hierarchy
			self.overlay.inform( self.overlay.BUSY )
			data.update( {"parent": self.rootNode } )
			if self.id and not self.clone:
				self.request = NetworkService.request("/%s/edit/%s" % ( self.modul, self.id ), data, secure=True, successHandler=self.onSaveResult )
			else:
				self.request = NetworkService.request("/%s/add/" % ( self.modul ), data, secure=True, successHandler=self.onSaveResult )
		elif self.applicationType == EditWidget.appTree: ## Application: Tree
			data.update( {"rootNode": self.rootNode, "path": self.path } )
			if self.id and not self.clone:
				self.request = NetworkService.request("/%s/edit/%s" % ( self.modul, self.id ), data, secure=True, successHandler=self.onSaveResult )
			else:
				self.request = NetworkService.request("/%s/add/" % ( self.modul ), data, secure=True, successHandler=self.onSaveResult )
		elif self.applicationType == EditWidget.appSingleton: ## Application: Singleton
			self.request = NetworkService.request("/%s/edit" % ( self.modul ), data, secure=True, successHandler=self.onSaveResult )
		else:
			raise NotImplementedError() #Should never reach this

	def emitEntryChanged( self, modul ):
		if self.applicationType == EditWidget.appList: ## Application: List
			event.emit( QtCore.SIGNAL('listChanged(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self, self.modul, self.id )
		elif self.applicationType == EditWidget.appHierarchy: ## Application: Hierarchy
			event.emit( QtCore.SIGNAL('hierarchyChanged(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self, modul, self.rootNode, self.id )
		elif self.applicationType == EditWidget.appTree: ## Application: Tree
			event.emit( QtCore.SIGNAL('treeChanged(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self, self.modul, self.rootNode, self.id )
		elif self.applicationType == EditWidget.appSingleton: ## Application: Tree
			event.emit( QtCore.SIGNAL('singletonChanged(PyQt_PyObject,PyQt_PyObject)'), self, self.modul )
		else:
			raise NotImplementedError() #Should never reach this

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
			if bone["visible"]==False:
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
			## Temporary MacOS Fix
			import sys
			if sys.platform.startswith("darwin"):
				dataWidget.setMaximumWidth(500)
				dataWidget.setMinimumWidth(500)
			## Temporary MacOS Fix
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
		self._lastData = data
		event.emit( QtCore.SIGNAL("rebuildBreadCrumbs()") )
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
			res.update( bone.serializeForPost( ) )
		self.save( res )
		
	def on_btnSaveClose_released( self, *args, **kwargs ):
		self.closeOnSuccess = True
		self.overlay.inform( self.overlay.BUSY )
		res = {}
		for key, bone in self.bones.items():
			res.update( bone.serializeForPost( ) )
		self.save( res )

	def on_btnPreview_released( self, *args, **kwargs ):
		res = {}
		for key, bone in self.bones.items():
			value = bone.serialize()
			if value!=None:
				res[ key ] = value
		self.preview = Preview( self.modul, res )
	
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
		self.parent().deleteLater()
