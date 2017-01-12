# -*- coding: utf-8 -*-
__author__ = 'Stefan Kögl <sk@mausbrand.de>'

import sys

import html2text
from PyQt5 import QtWebKitWidgets, QtCore, QtGui, QtWidgets
from markdown2 import Markdown

from viur_admin.config import conf
from viur_admin.event import event


class MkEditor(QtWidgets.QWidget):
	onDataChanged = QtCore.pyqtSignal((str,))

	def __init__(self, html, parent=None):
		super(MkEditor, self).__init__(parent)
		self.webView = QtWebKitWidgets.QWebView()
		self.editor = QtWidgets.QTextEdit()
		document = self.editor.document()
		option = document.defaultTextOption()
		option.setFlags(option.flags() | QtGui.QTextOption.ShowTabsAndSpaces)
		document.setDefaultTextOption(option)
		self.htmlPlainTextView = QtWidgets.QPlainTextEdit()
		self.htmlPlainTextView.setReadOnly(True)
		self.helpPlainTextView = QtWidgets.QPlainTextEdit()
		self.helpPlainTextView.setReadOnly(True)
		self.helpPlainTextView.document().setDefaultTextOption(option)
		exampleText = QtCore.QFile(":icons/mdedit_docs_de.md")
		exampleText.open(QtCore.QFile.ReadOnly)
		exampleText = str(exampleText.readAll(), encoding='utf-8')
		self.helpPlainTextView.setPlainText(exampleText)
		self.toolBar = QtWidgets.QToolBar(self)
		self.splitter = QtWidgets.QSplitter()

		self.saveButton = self.toolBar.addAction(QtGui.QIcon(":icons/actions/accept.svg"), "&Save")
		self.cancelButton = self.toolBar.addAction(QtGui.QIcon(":icons/actions/cancel.svg"), "&Cancel")

		font = QtGui.QFont("Monospace")
		font.setStyleHint(QtGui.QFont.TypeWriter)
		font.setPointSize(20)
		self.editor.setFont(font)
		self.helpPlainTextView.setFont(font)
		self.htmlPlainTextView.setFont(font)
		self.tabview = QtWidgets.QTabWidget(self)
		self.tabview.addTab(self.webView, "HTML Preview")
		self.tabview.addTab(self.htmlPlainTextView, "Source View")
		self.tabview.addTab(self.helpPlainTextView, "Help")
		self.splitter.addWidget(self.editor)
		self.splitter.addWidget(self.tabview)
		self.splitter.setOpaqueResize(True)
		self.splitter.setStretchFactor(0, 1)
		self.splitter.setStretchFactor(1, 1)
		sizes = conf.adminConfig.get("mdtext_edit_splitter_sizes")
		if sizes:
			self.splitter.setSizes(sizes)

		mainVLayout = QtWidgets.QVBoxLayout(self)
		mainVLayout.addWidget(self.toolBar)
		mainVLayout.addWidget(self.splitter)
		self.html = html
		self.markdowner = Markdown()
		self.html2md_converter = html2text.HTML2Text()
		self.html2md_converter.escape_snob = True
		self.html2md_converter.unicode_snob = True
		self.markdownText = None
		tplTemp = QtCore.QFile(":icons/mdedit.html")
		tplTemp.open(QtCore.QFile.ReadOnly)
		self.tpl = str(tplTemp.readAll(), encoding="ascii")
		self.html2md()
		self.md2html()
		self.editor.textChanged.connect(self.md2html)
		self.saveButton.triggered.connect(self.save)
		self.splitter.splitterMoved.connect(self.onSplitterMoved)
		self.cancelButton.triggered.connect(self.onClose)

	def md2html(self):
		self.markdownText = self.editor.toPlainText()
		self.html = self.markdowner.convert(self.markdownText)
		self.htmlPlainTextView.setPlainText(self.html)
		resultText = self.tpl.format(output=self.html)
		self.webView.setHtml(resultText)

	def html2md(self):
		self.markdownText = self.html2md_converter.handle(self.html)
		self.editor.setText(self.markdownText)

	def save(self):
		self.onDataChanged.emit(self.html)
		event.emit("popWidget", self)

	def onClose(self):
		event.emit("popWidget", self)

	def onSplitterMoved(self, pos, index):
		sizes = self.splitter.sizes()
		conf.adminConfig["mdtext_edit_splitter_sizes"] = sizes


if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	editor = MkEditor("")
	editor.show()
	app.exec_()
