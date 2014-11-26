"""
class OrderHandler( QtCore.QObject ):
	def __init__(self, *args, **kwargs ):
		QtCore.QObject.__init__( self, *args, **kwargs )
		self.connect( event, QtCore.SIGNAL('requestModulListActions(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,
		PyQt_PyObject)') ,  self.requestModulListActions )

	def requestModulListActions(self, queue, modul, config, parent ):
		try:
			config = conf.serverConfig["modules"][ modul ]
			print( config["handler"] )
			if( not config["handler"].startswith("list.order") ):
				return
		except: 
			return
		queue.registerHandler( 10, ShopMarkSendAction )
		queue.registerHandler( 10, ShopMarkPayedAction )
		queue.registerHandler( 10, ShopMarkCanceledAction )
		queue.registerHandler( 10, ShopDownloadBillAction )
		queue.registerHandler( 10, ShopDownloadDeliveryNoteAction )
		

_orderHandler = OrderHandler()
"""

from viur_admin.widgets.tree import TreeWidget
from viur_admin.widgets.file import FileListView

class FileWidget(TreeWidget):
    """
        Extension for TreeWidget to handle the specialities of files like Up&Downloading.
    """

    treeWidget = FileListView

    def __init__(self, *args, **kwargs):
        super(FileWidget, self).__init__(
            actions=["dirup", "mkdir", "upload", "download", "edit", "rename", "delete", "switchview"], *args, **kwargs)
