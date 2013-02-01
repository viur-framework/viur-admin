from PyQt4 import QtCore, QtGui
import math
from ui.taskUI import Ui_Task
import os, os.path
from network import NetworkService
from utils import Overlay


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
		self.request = NetworkService.request( "/_tasks/list" )
		self.connect( self.request, QtCore.SIGNAL("finished()"), self.onTaskList )
		self.setWindowTitle( QtCore.QCoreApplication.translate("Tasks", "Tasks") )
		self.setWindowIcon( QtGui.QIcon( QtGui.QPixmap( "icons/menu/tasks.png" ) ) )
		self.show()
		
	def onTaskList(self):
		self.tasks = NetworkService.decode( self.request )
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
		from widgets.edit import EditWidget
		self.ui.verticalLayout.addWidget( EditWidget( "_tasks", EditWidget.appSingleton,  taskID ) )

