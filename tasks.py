from PyQt4 import QtCore, QtGui
from ui.taskUI import Ui_Task
from network import NetworkService
from utils import Overlay, WidgetHandler, loadIcon
from event import event


class TaskEntryHandler( WidgetHandler ):
	def __init__( self, widgetFactory,  *args, **kwargs ):
		name = QtCore.QCoreApplication.translate("tasks", "Tasks")
		super( TaskEntryHandler, self ).__init__( widgetFactory, icon=loadIcon("icons/modules/tasks.png"), vanishOnClose=True , *args, **kwargs )
		self.setText(0,name)

	def getBreadCrumb(self):
		"""
			Dont use the description of our edit widget here
		"""
		if len( self.widgets )==2: #We adding exactly one task
			try:
				tasks = self.widgets[0].tasks
			except:
				tasks = None
			if tasks:
				taskDict = {}
				for t in tasks["skellist"]:
					taskDict[ t["id"] ] = t
				try:
					taskID = self.widgets[1].key
				except:
					taskID = None
				if taskID and taskID in taskDict.keys():
					return( taskDict[ taskID ]["name"], self.icon(0) )
		return( self.text(0), self.icon(0) )



class TaskItem(QtGui.QListWidgetItem):
	def __init__(self, task, *args, **kwargs ):
		super(TaskItem,self).__init__(  task["name"], *args, **kwargs )
		self.task = task


class TaskViewer( QtGui.QWidget ):
	def __init__(self, parent=None, *args, **kwargs ):
		super( TaskViewer, self ).__init__( parent, *args,  **kwargs )
		self.ui = Ui_Task()
		self.ui.setupUi( self )
		self.overlay = Overlay( self )
		self.overlay.inform( self.overlay.BUSY )
		self.tasks = None
		NetworkService.request( "/_tasks/list", secure=True, successHandler=self.onTaskList )
		self.show()
		
	def onTaskList(self, req):
		self.tasks = NetworkService.decode( req )
		for task in self.tasks["skellist"]:
			item = TaskItem( task )
			self.ui.listWidget.addItem( item )
		self.overlay.clear()
	
	def on_listWidget_itemClicked( self, item ):
		self.ui.lblName.setText( item.task["name"] )
		self.ui.lblDescr.setText( item.task["descr"] )

	def on_btnExecute_released( self, *args, **kwargs ):
		item = self.ui.listWidget.currentItem()
		if not item:
			return
		taskID = item.task["id"]
		"""
		for i in range(self.ui.horizontalLayout.count()):
			if self.ui.horizontalLayout.itemAt(i).widget():
				self.ui.horizontalLayout.itemAt(i).widget().close()
		for i in range(self.ui.verticalLayout.count()):
			if self.ui.verticalLayout.itemAt(i).widget():
				self.ui.verticalLayout.itemAt(i).widget().close()
		task = None
		for t in self.tasks["skellist"]:
			if t["id"] == taskID:
				task = t
				break
		if not task:
			return
		nameLbl = QtGui.QLabel( task["name"], self )
		self.ui.verticalLayout.addWidget( nameLbl )
		descrLbl = QtGui.QLabel( task["descr"], self )
		self.ui.verticalLayout.addWidget( descrLbl )
		"""
		from widgets.edit import EditWidget
		event.emit("stackWidget", EditWidget( "_tasks", EditWidget.appSingleton,  taskID ) )

