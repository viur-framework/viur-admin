# -*- coding: utf-8 -*-
from PyQt5 import QtGui, QtWidgets


class BoneEditInterface(QtWidgets.QWidget):
	def __init__(self, moduleName, boneName, readOnly, editWidget=None, *args, **kwargs):
		super(BoneEditInterface, self).__init__(*args, **kwargs)
		self.moduleName = moduleName
		self.boneName = boneName
		self.readOnly = readOnly
		self.editWidget = editWidget

	@staticmethod
	def fromSkelStructure(moduleName, boneName, skelStructure, **kwargs):
		raise NotImplementedError()

	def showDialog(self):
		raise NotImplementedError()

	def unserialize(self, data):
		raise NotImplementedError()

	def serializeForPost(self):
		raise NotImplementedError()

	def serializeForDocument(self):
		pass
