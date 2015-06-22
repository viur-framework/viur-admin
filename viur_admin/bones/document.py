from PyQt5 import QtCore, QtGui, QtWebKit, QtWidgets

from viur_admin.bones.docedit import DocEdit
from viur_admin.bones.text import TextViewBoneDelegate


class DocumentViewBoneDelegate(TextViewBoneDelegate):
	pass


class DocumentEditBone(QtWidgets.QWidget):
	def __init__(self, modulName, boneName, skelStructure, *args, **kwargs):
		super(DocumentEditBone, self).__init__(*args, **kwargs)
		self.skelStructure = skelStructure
		self.boneName = boneName
		self.layout = QtWidgets.QVBoxLayout(self)
		self.btn = QtWidgets.QPushButton(QtCore.QCoreApplication.translate("DocumentEditBone", "Open editor"), self)
		iconbtn = QtGui.QIcon()
		iconbtn.addPixmap(QtGui.QPixmap(":icons/actions/document-edit_small.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.btn.setIcon(iconbtn)
		self.btn.connect(self.btn, QtCore.SIGNAL("released()"), self.openEditor)
		self.webView = QtWebKit.QWebView(self)
		self.webView.mousePressEvent = self.openEditor
		self.layout.addWidget(self.webView)
		self.layout.addWidget(self.btn)
		self.setSizePolicy(
			QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred))
		self.html = ""
		self.editor = None

	def sizeHint(self):
		return (QtCore.QSize(150, 150))

	def openEditor(self, *args, **kwargs):
		ext = []
		if "extensions" in self.skelStructure[self.boneName].keys():
			ext = self.skelStructure[self.boneName]["extensions"]
		editor = DocEdit(self.onSave, ext)
		editor.unserialize(self.html)

	def onSave(self, text):
		self.html = str(text)
		self.webView.setHtml(text)

	def unserialize(self, data):
		self.html = data[self.boneName]
		self.webView.setHtml(self.html)

	def serializeForPost(self):
		return ({self.boneName: self.html})

	def serializeForDocument(self):
		return (self.serialize())


class DocumentHandler(QtCore.QObject):
	def __init__(self, *args, **kwargs):
		QtCore.QObject.__init__(self, *args, **kwargs)
		# self.connect(event,
		#              QtCore.SIGNAL('requestBoneViewDelegate(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),
		#              self.onRequestBoneViewDelegate)  # RegisterObj, ModulName, BoneName, SkelStructure
		# self.connect(event,
		#              QtCore.SIGNAL('requestBoneEditWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)'),
		#              self.onRequestBoneEditWidget)

	def onRequestBoneViewDelegate(self, registerObject, modulName, boneName, skelStucture):
		if skelStucture[boneName]["type"] == "document":
			registerObject.registerHandler(10, lambda: DocumentViewBoneDelegate(registerObject, modulName, boneName,
			                                                                    skelStucture))

	def onRequestBoneEditWidget(self, registerObject, modulName, boneName, skelStucture):
		if skelStucture[boneName]["type"] == "document":
			registerObject.registerHandler(10, DocumentEditBone(modulName, boneName, skelStucture))


_documentHandler = DocumentHandler()
