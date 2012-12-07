from ui.hierarchyUI import Ui_Hierarchy
from PyQt4 import QtCore, QtGui
from network import NetworkService
from event import event
from config import conf
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse
from time import sleep, time
import sys, os, os.path
from handler.edit import Edit, EditHandler
from utils import RegisterQueue, Overlay,  formatString
from mainwindow import EntryHandler

class HierarchyItem(QtGui.QTreeWidgetItem):
	def __init__( self, data ):
		if "name" in data.keys():
			name = data["name"]
		else:
			name = "---"
		super( HierarchyItem, self ).__init__( [str( name )] )
		self.loaded = False
		self.data = data
		self.setChildIndicatorPolicy( QtGui.QTreeWidgetItem.ShowIndicator )

	def __gt__( self, other ):
		if isinstance( other, HierarchyItem ) and "sortindex" in self.data.keys() and "sortindex" in other.data.keys():
			return( self.data["sortindex"] > other.data["sortindex"] )
		else:
			return( super( HierarchyItem, self ).__gt__( other ) )

	def __lt__( self, other ):
		if isinstance( other, HierarchyItem ) and "sortindex" in self.data.keys() and "sortindex" in other.data.keys():
			return( self.data["sortindex"] < other.data["sortindex"] )
		else:
			return( super( HierarchyItem, self ).__lt__( other ) )


class HierarchyList( QtGui.QWidget ):
	
	def __init__(self, modul, repoID=None, *args, **kwargs ):
		self.modul = modul
		self.page = 0
		self.rootNodes = {}
		config = conf.serverConfig["modules"][ modul ]
		self.currentRootNode = None
		self.isSorting=False
		self.path = []
		self.request = None
		if not "ui" in dir( self ):
			QtGui.QWidget.__init__( self, *args, **kwargs )
			self.ui = Ui_Hierarchy()
			self.ui.setupUi( self )
			self.toolBar = QtGui.QToolBar( self )
			self.toolBar.setIconSize( QtCore.QSize( 32, 32 ) )
			queue = RegisterQueue()
			event.emit( QtCore.SIGNAL('requestHierarchyListActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), queue, self.modul, self )
			for item in queue.getAll():
				i = item( self )
				if isinstance( i, QtGui.QAction ):
					self.toolBar.addAction( i )
				else:
					self.toolBar.addWidget( i )
			self.ui.boxActions.addWidget( self.toolBar )
		self.overlay = Overlay( self )
		#event.emit( QtCore.SIGNAL('addHandlerWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self, config["name"], None )
		if not repoID:
			self.loadRootNodes()
		else:
			self.setRootNode( repoID )
		self.setAcceptDrops( True )
		self.clipboard = None  #(str repo,str path, bool doMove, list files, list dirs )
		self.lastUploadTime = 0
		self.connect( event, QtCore.SIGNAL('dataChanged(PyQt_PyObject,PyQt_PyObject)'),self.doReloadData )
		self.ui.webView.hide()
		self.ui.treeWidget.dropEvent = self.dropEvent

	def setRootNode( self, repoID, repoName=None ):
		self.currentRootNode = repoID
		self.ui.treeWidget.clear()
		self.loadData()

	def dropEvent( self, event ):
		try:
			dragedItem =  self.ui.treeWidget.selectedItems()[0]
		except:
			return
		targetItem = self.ui.treeWidget.itemAt( event.pos() )
		QtGui.QTreeWidget.dropEvent( self.ui.treeWidget, event )
		if not targetItem: #Moved to the end of the list
			self.reparent( dragedItem.data["id"], self.currentRootNode )
			if self.ui.treeWidget.topLevelItemCount()>1:
				self.updateSortIndex( dragedItem.data["id"], self.ui.treeWidget.topLevelItem( self.ui.treeWidget.topLevelItemCount()-2 ).data["sortindex"]+1 )
		else:
			if dragedItem.parent() == targetItem: #Moved to subitem
				self.reparent( dragedItem.data["id"], targetItem.data["id"] )
			else: # Moved within its parent list
				while( targetItem ):
					childIndex = 0
					while( childIndex < targetItem.childCount() ):
						currChild = targetItem.child( childIndex )
						if currChild == dragedItem:
							self.reparent( dragedItem.data["id"], targetItem.data["id"] )
							if childIndex==0 and targetItem.childCount()>1: # is now 1st item
								self.updateSortIndex( dragedItem.data["id"], targetItem.child( 1 ).data["sortindex"]-1 )
							elif childIndex==(targetItem.childCount()-1) and childIndex>0: #is now lastitem
								self.updateSortIndex( dragedItem.data["id"], targetItem.child( childIndex-1 ).data["sortindex"]+1 )
							elif childIndex>0 and childIndex<(targetItem.childCount()-1): #in between
								newSortIndex = ( targetItem.child( childIndex-1 ).data["sortindex"]+ targetItem.child( childIndex+1 ).data["sortindex"] ) / 2.0
								self.updateSortIndex( dragedItem.data["id"], newSortIndex )
							else: # We are the only one in this layer
								pass
							return
						childIndex += 1
					targetItem = targetItem.parent()
				childIndex = 0
				currChild = self.ui.treeWidget.topLevelItem( childIndex )
				while( currChild ):
					if currChild == dragedItem:
						self.reparent( dragedItem.data["id"], self.currentRootNode )
						if childIndex==0 and self.ui.treeWidget.topLevelItemCount()>1: # is now 1st item
							self.updateSortIndex( dragedItem.data["id"], self.ui.treeWidget.topLevelItem( 1 ).data["sortindex"]-1 )
						elif childIndex==(self.ui.treeWidget.topLevelItemCount()-1) and childIndex>0: #is now lastitem
							self.updateSortIndex( dragedItem.data["id"], self.ui.treeWidget.topLevelItem( childIndex-1 ).data["sortindex"]+1 )
						elif childIndex>0 and childIndex<(self.ui.treeWidget.topLevelItemCount()-1): #in between
							newSortIndex = ( self.ui.treeWidget.topLevelItem( childIndex-1 ).data["sortindex"]+ self.ui.treeWidget.topLevelItem( childIndex+1 ).data["sortindex"] ) / 2.0
							self.updateSortIndex( dragedItem.data["id"], newSortIndex )
						else: # We are the only one in this layer
							pass
						return
					childIndex+=1
					currChild = self.ui.treeWidget.topLevelItem( childIndex )
					
				

	def on_treeWidget_itemExpanded(self, item, *args, **kwargs):
		if not item.loaded:
			while( item.takeChild(0) ):
				pass
			self.loadData( item.data["id"] )

	
	def loadRootNodes(self):
		self.overlay.inform( self.overlay.BUSY )
		self.request = NetworkService.request("/%s/listRootNodes" % ( self.modul ) )
		self.connect(self.request, QtCore.SIGNAL("finished()"), self.onLoadRepositories )
	
	def onLoadRepositories(self, data=None ):
		if not data:
			data = NetworkService.decode( self.request )
			self.request.deleteLater()
			self.request = None
		self.rootNodes = data
		if not self.currentRootNode:
			try:
				self.currentRootNode = list( self.rootNodes )[0]["key"]
			except:
				
				return
			self.loadData()
	
	def onLoadError(self, error ):
		self.overlay.inform( self.overlay.ERROR, str(error) )
	
	def onRequestSucceeded(self):
		self.request.deleteLater()
		self.request = None
		self.reloadData()
		
	def reloadData(self,page=None, ):
		event.emit( QtCore.SIGNAL('dataChanged(PyQt_PyObject,PyQt_PyObject)'), self.modul, self)
		
	def doReloadData(self, modulName, emitingEntry):
		if (modulName!=self.modul or emitingEntry == self):
			return
		self.loadData()

	def loadData(self, parent=None):
		self.overlay.inform( self.overlay.BUSY )
		self.request = NetworkService.request( "/%s/list/%s" % (self.modul, (parent or self.currentRootNode) ) )
		self.connect(self.request, QtCore.SIGNAL("finished()"), self.setData )

	def reparent(self, itemKey, destParent):
		self.request = NetworkService.request( "/%s/reparent" % self.modul, { "item": itemKey, "dest": destParent }, True )
		self.connect(self.request, QtCore.SIGNAL("finished()"), self.onRequestSucceeded )
		self.connect(self.request, QtCore.SIGNAL("error(QNetworkReply::NetworkError)"), self.onLoadError )


	def updateSortIndex(self, itemKey, newIndex):
		self.request = NetworkService.request( "/%s/setIndex" % self.modul, { "item": itemKey, "index": newIndex }, True )
		self.connect(self.request, QtCore.SIGNAL("finished()"), self.onRequestSucceeded )
		self.connect(self.request, QtCore.SIGNAL("error(QNetworkReply::NetworkError)"), self.onLoadError )

	def setData(self, data=None):
		if not data:
			data = NetworkService.decode( self.request )
			self.request.deleteLater()
			self.request = None
		if len( data["skellist"] ):
			if data["skellist"][0]["parententry"] == self.currentRootNode:
				self.ui.treeWidget.clear()
		for itemData in data["skellist"]:
			tvItem = HierarchyItem( itemData )
			if( itemData["parententry"] == self.currentRootNode ):
				self.ui.treeWidget.addTopLevelItem( tvItem )
			else:
				self.insertItem( tvItem )
			self.ui.treeWidget.addTopLevelItem( tvItem )
		self.ui.treeWidget.sortItems(0, QtCore.Qt.AscendingOrder)
		self.ui.treeWidget.setSortingEnabled( False )
		self.overlay.clear()

	def insertItem( self, newItem, fromChildren=None ):
		if not fromChildren:
			idx = 0
			item = self.ui.treeWidget.topLevelItem( idx )
			while item:
				if item.data["id"] == newItem.data["parententry"]:
					item.addChild( newItem )
					item.loaded=True
					return
				self.insertItem( newItem, item )
				idx += 1
				item = self.ui.treeWidget.topLevelItem( idx )
		else:
			idx = 0
			child = fromChildren.child( idx )
			while child:
				if child.data["id"] == newItem.data["parententry"]:
					child.addChild( newItem )
					child.loaded=True
					return
				self.insertItem( newItem, child )
				idx += 1
				child = fromChildren.child( idx )

	def getPath(self):
		return( "/".join( self.path ) or "/" )
	
	def on_treeWidget_itemDoubleClicked(self, item ):
		widget = HierarchyAdd(self.modul, item.data["id"] )
		handler = EditHandler( self.modul, widget )
		event.emit( QtCore.SIGNAL('addHandler(PyQt_PyObject)'), handler )

	def on_treeWidget_itemClicked( self, item ):
		config = conf.serverConfig["modules"][ self.modul ]
		if "previewURL" in config.keys():
			previewURL = config["previewURL"].replace("{{id}}",item.data["id"])
			if not previewURL.lower().startswith("http"):
				previewURL = NetworkService.url.replace("/admin","")+previewURL
			self.loadPreview( previewURL )
			
	def loadPreview( self, url ):
		self.request = NetworkService.request( url )
		self.connect(self.request, QtCore.SIGNAL("finished()"), self.setHTML )
	
	def setHTML( self ):
		html = bytes( self.request.readAll() )
		self.request.deleteLater()
		self.request= None
		self.ui.webView.setHtml( html.decode("UTF-8"), QtCore.QUrl( NetworkService.url.replace("/admin","") ) )
		self.ui.webView.show()


	def delete( self, id ):
		self.request = NetworkService.request("/%s/delete/%s" % (self.modul, id), secure=True )
		self.connect( self.request, QtCore.SIGNAL("finished()"), self.reloadData )


class HierarchyAdd( Edit ):
	def __init__( self, modul, id=0, rootNode="", path="", *args, **kwargs ):
		self.rootNode = rootNode
		self.path = path
		super( HierarchyAdd, self ).__init__( modul, id, *args, **kwargs )
	
	def reloadData(self):
		if self.id: #We are in Edit-Mode
			self.request = NetworkService.request("/%s/edit/%s" % ( self.modul, self.id ), {"rootNode": self.rootNode, "path": self.path } )
		else:
			self.request = NetworkService.request("/%s/add/" % ( self.modul ), {"parent": self.rootNode } )
		self.connect( self.request, QtCore.SIGNAL("finished()"), self.setData )

	def save(self, data ):
		self.overlay.inform( self.overlay.BUSY )
		data.update( {"parent": self.rootNode } )
		if self.id:
			self.request = NetworkService.request("/%s/edit/%s" % ( self.modul, self.id ), data, secure=True )
		else:
			self.request = NetworkService.request("/%s/add/" % ( self.modul ), data, secure=True )
		self.connect( self.request, QtCore.SIGNAL("finished()"), self.onSaveResult )

	def emitEntryChanged( self, modul ):
		event.emit( QtCore.SIGNAL('dataChanged(PyQt_PyObject,PyQt_PyObject)'), modul, self )

class HierarchyAddAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( HierarchyAddAction, self ).__init__(  QtGui.QIcon("icons/actions/add_small.png"), "Eintrag hinzufügen", parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.New )
	
	def onTriggered( self, e ):
		config = conf.serverConfig["modules"][ self.parent().modul ]
		widget = HierarchyAdd(self.parent().modul, 0, rootNode=self.parent().currentRootNode, path=self.parent().getPath())
		handler = EditHandler( self.parentWidget().modul, widget )
		event.emit( QtCore.SIGNAL('addHandler(PyQt_PyObject)'), handler )
		

class HierarchyDeleteAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( HierarchyDeleteAction, self ).__init__(  QtGui.QIcon("icons/actions/delete_small.png"), "Eintrag Löschen", parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( QtGui.QKeySequence.Delete )
	
	def onTriggered( self, e ):
		parent = self.parent()
		for item in parent.ui.treeWidget.selectedItems():
			config = conf.serverConfig["modules"][ self.parentWidget().modul ]
			if "formatstring" in config.keys():
				question = QtCore.QCoreApplication.translate("HierarchyHandler", "Delete entry %s and everything beneath?") % formatString( config["formatstring"],  item.data )
			else:
				question = QtCore.QCoreApplication.translate("HierarchyHandler", "Delete this entry and everything beneath?")
			res = QtGui.QMessageBox.question(	self.parentWidget(),
											QtCore.QCoreApplication.translate("HierarchyHandler", "Confirm delete"),
											question,
											QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No
										)
			if res == QtGui.QMessageBox.Yes:
				parent.delete( item.data["id"] )
			
class HierarchyEditAction( QtGui.QAction ):
	def __init__(self, parent, *args, **kwargs ):
		super( HierarchyEditAction, self ).__init__(  QtGui.QIcon("icons/actions/edit_small.png"), QtCore.QCoreApplication.translate("HierarchyHandler", "Edit entry"), parent )
		self.connect( self, QtCore.SIGNAL( "triggered(bool)"), self.onTriggered )
		self.setShortcut( "Return" )
	
	def onTriggered( self, e ):
		parent = self.parent()
		for item in parent.ui.treeWidget.selectedItems():
			widget = HierarchyAdd(parent.modul, item.data["id"] )
			handler = EditHandler( parent.modul, widget  )
			event.emit( QtCore.SIGNAL('addHandler(PyQt_PyObject)'), handler )


class HierarchyRepoHandler( EntryHandler ):
	"""Class for holding one Repo-Entry within the modules-list"""
	def __init__( self, modul, repo, *args, **kwargs ):
		super( HierarchyRepoHandler, self ).__init__( modul, *args, **kwargs )	
		self.repo = repo
		self.setText(0, repo["name"] )

	def clicked( self ):
		if not self.widgets:
			self.addWidget( HierarchyList( self.modul, self.repo["key"]  ) )
		else:
			self.focus()


class HierarchyCoreHandler( EntryHandler ):
	"""Class for holding the main (module) Entry within the modules-list"""
	
	def __init__( self, modul,  *args, **kwargs ):
		super( HierarchyCoreHandler, self ).__init__( modul, *args, **kwargs )
		config = conf.serverConfig["modules"][ modul ]
		if config["icon"]:
			lastDot = config["icon"].rfind(".")
			smallIcon = config["icon"][ : lastDot ]+"_small"+config["icon"][ lastDot: ]
			if os.path.isfile( os.path.join( os.getcwd(), smallIcon ) ):
				self.setIcon( 0, QtGui.QIcon( smallIcon ) )
			else:
				self.setIcon( 0, QtGui.QIcon( config["icon"] ) )
		self.setText( 0, config["name"] )
		self.repos = []
		self.tmpObj = QtGui.QWidget()
		self.fetchTask = NetworkService.request("/%s/listRootNodes" % self.modul )
		self.tmpObj.connect(self.fetchTask, QtCore.SIGNAL("finished()"), self.setRepos) 

	def setRepos( self ):
		data = NetworkService.decode( self.fetchTask )
		self.fetchTask.deleteLater()
		self.fetchTask = None
		self.tmpObj.deleteLater()
		self.tmpObj = None
		self.repos = data
		if len( self.repos ) > 1:
			for repo in self.repos:
				d = HierarchyRepoHandler( self.modul, repo )
				self.addChild( d )

	def clicked( self ):
		if not self.widgets:
			self.addWidget( HierarchyList( self.modul ) )
		else:
			self.focus()


class HierarchyHandler( QtCore.QObject ):
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('modulHandlerInitializion(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), self.initWidgetItem )
		self.connect( event, QtCore.SIGNAL('requestHierarchyListActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)') ,  self.requestHierarchyListActions )
		self.connect( event, QtCore.SIGNAL('requestModulHandler(PyQt_PyObject,PyQt_PyObject)'), self.requestModulHandler )

	def requestHierarchyListActions(self, queue, modul, parent ):
		config = conf.serverConfig["modules"][ modul ]
		if config and config["handler"]=="hierarchy":
			queue.registerHandler( 2, HierarchyAddAction )
			queue.registerHandler( 3, HierarchyEditAction )
			queue.registerHandler( 4, HierarchyDeleteAction )

	def requestModulHandler(self, queue, modul ):
		config = conf.serverConfig["modules"][ modul ]
		if( config["handler"]=="hierarchy" ):
			f = lambda: HierarchyCoreHandler( modul )
			queue.registerHandler( 5, f )

	def initWidgetItem(self, queue, modulName, config ):
		if( config["handler"]!="hierarchy"):
			return
		listOpener = lambda *args, **kwargs: self.openList( modulName, config )
		contextHandler = lambda *args, **kwargs: None 
		if not "icon" in config.keys():
			config["icon"]="icons/conesofticons/ihre_idee.png"
		res= {"name":config["name"], "icon":config["icon"], "functions":[
				{"name":"Alle Einträge", "icon":config["icon"],  "handler":listOpener, "contextHandler":contextHandler }
			], "defaulthandler":listOpener }
		queue.registerHandler(15,res)
	
	def openList(self, modulName, config ):
		if "name" in config.keys():
			name = config["name"]
		else:
			name = "Liste"
		if "icon" in config.keys():
			icon = config["icon"]
		else:
			icon = None
		event.emit( QtCore.SIGNAL('addHandlerWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'), HierarchyList( modulName, config ), name, icon )

_hierarchyHandler = HierarchyHandler()


