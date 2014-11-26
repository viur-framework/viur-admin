# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWebKit, QtWidgets, QtWebKitWidgets
# from PySide.Qsci import QsciScintilla, QsciLexerHTML
import sys
from viur_admin.event import event
from viur_admin.utils import RegisterQueue
from viur_admin.ui.texteditUI import Ui_textEditWindow
from viur_admin.ui.rawtexteditUI import Ui_rawTextEditWindow
import html.parser
from viur_admin.ui.docEditlinkEditUI import Ui_LinkEdit
from html.entities import entitydefs
from viur_admin.priorityqueue import editBoneSelector, viewDelegateSelector
from viur_admin.bones.file import FileBoneSelector
from viur_admin.bones.string import chooseLang
from viur_admin.network import RemoteFile
from PyQt5.Qsci import QsciScintilla, QsciLexerHTML, QsciStyle

rsrcPath = "icons/actions/text"


class HtmlStripper(html.parser.HTMLParser):
    def __init__(self):
        super(HtmlStripper, self).__init__()
        self.cleanData = []

    def handle_data(self, data):
        self.cleanData.append(data)

    def getData(self):
        return ''.join(self.cleanData)

    @staticmethod
    def strip(txt):
        s = HtmlStripper()
        s.feed(txt)
        return ( s.getData() )


class TextViewBoneDelegate(QtWidgets.QStyledItemDelegate):
    cantSort = True

    def __init__(self, modulName, boneName, skelStructure, *args, **kwargs):
        super(QtWidgets.QStyledItemDelegate, self).__init__()
        self.skelStructure = skelStructure
        self.boneName = boneName
        self.modulName = modulName

    def displayText(self, value, locale):
        if "languages" in self.skelStructure[self.boneName].keys():
            languages = self.skelStructure[self.boneName]["languages"]
        else:
            languages = None
        if languages is not None:
            value = chooseLang(value, languages)
        if value:
            value = HtmlStripper.strip(value)
        return ( super(TextViewBoneDelegate, self).displayText(value, locale) )


class InsertImageDialog(QtWidgets.QDialog):
    onInsertText = QtCore.pyqtSignal((object, ))

    def __init__(self, file):
        super(InsertImageDialog, self).__init__()
        self.setModal(True)
        self.file = file
        self.setLayout(QtWidgets.QVBoxLayout())
        self.cb = QtWidgets.QComboBox(self)
        self.layout().addWidget(self.cb)
        acceptButton = QtWidgets.QPushButton("Accept")
        acceptButton.released.connect(self.accept)
        self.layout().addWidget(acceptButton)
        self.cb.addItem("Normal Link")
        self.cb.addItem("Download Link")
        if "servingurl" in file.keys() and file["servingurl"]:
            self.cb.addItem("Resizable Image Link")

    def accept(self):
        if self.cb.currentIndex() == 0:
            url = "/file/download/%s/%s" % (self.file["dlkey"], self.file["name"])
        elif self.cb.currentIndex() == 1:
            url = "/file/download/%s/%s?download=1" % (self.file["dlkey"], self.file["name"])
        elif "servingurl" in self.file.keys():
            url = self.file["servingurl"]
        self.onInsertText.emit(url)
        super(InsertImageDialog, self).accept()


class TextEditor(QtWidgets.QWidget):
    onDataChanged = QtCore.pyqtSignal((object, ))

    def __init__(self, txt, validHtml, *args, **kwargs):
        super(TextEditor, self).__init__(*args, **kwargs)
        self.validHtml = validHtml
        self.setLayout(QtWidgets.QVBoxLayout())
        btn = QtWidgets.QPushButton("Include file")
        btn.released.connect(self.click)
        self.layout().addWidget(btn)
        self.editor = QsciScintilla()
        self.editor.setLexer(QsciLexerHTML())
        self.layout().addWidget(self.editor)
        self.setMinimumSize(600, 450)
        btn = QtWidgets.QPushButton("Save")
        btn.released.connect(self.save)
        self.layout().addWidget(btn)
        self.setText(txt)

    def click(self, *args, **kwargs):
        d = FileBoneSelector("-", "file", False, "file", None)
        d.selectionChanged.connect(self.onFileSelected)

    def onFileSelected(self, selection):
        print("File", selection)
        if selection:
            selection = selection[0]
        imgdlg = InsertImageDialog(selection)
        imgdlg.onInsertText.connect(self.insertText)
        imgdlg.exec_()

    #self.editor.insert("/file/download/%s/%s" % (selection["dlkey"],selection["name"]))

    def insertText(self, txt):
        self.editor.insert(txt)

    def setText(self, txt):
        self.editor.clear()
        self.editor.append(txt)

    def save(self, *args, **kwargs):
        self.onDataChanged.emit(self.editor.text())
        event.emit('popWidget', self)


class ClickableWebView(QtWebKitWidgets.QWebView):
    clicked = QtCore.pyqtSignal()

    def mousePressEvent(self, ev):
        super(ClickableWebView, self).mousePressEvent(ev)
        self.clicked.emit()


class TextEditBone(QtWidgets.QWidget):
    def __init__(self, modulName, boneName, readOnly, languages=None, plaintext=False, validHtml=None, *args, **kwargs):
        super(TextEditBone, self).__init__(*args, **kwargs)
        self.modulName = modulName
        self.boneName = boneName
        self.readOnly = readOnly
        self.setLayout(QtWidgets.QVBoxLayout(self))
        self.languages = languages
        self.plaintext = plaintext
        self.validHtml = validHtml
        if self.languages:
            self.languageContainer = {}
            self.html = {}
            self.tabWidget = QtGui.QTabWidget(self)
            self.tabWidget.blockSignals(True)
            self.tabWidget.currentChanged.connect(self.onTabCurrentChanged)
            event.connectWithPriority("tabLanguageChanged", self.onTabLanguageChanged, event.lowPriority)
            self.layout().addWidget(self.tabWidget)
            for lang in self.languages:
                self.html[lang] = ""
                container = QtWidgets.QWidget()
                container.setLayout(QtWidgets.QVBoxLayout(container))
                self.languageContainer[lang] = container
                btn = QtWidgets.QPushButton(QtCore.QCoreApplication.translate("TextEditBone", "Open editor"), self)
                iconbtn = QtGui.QIcon()
                iconbtn.addPixmap(QtGui.QPixmap("icons/actions/text-edit.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
                btn.setIcon(iconbtn)
                btn.released.connect(self.openEditor)
                btn.lang = lang
                webView = ClickableWebView(self)
                webView.clicked.connect(self.openEditor)
                container.webView = webView
                container.layout().addWidget(webView)
                container.layout().addWidget(btn)
                self.tabWidget.addTab(container, lang)
            self.tabWidget.blockSignals(False)
            self.tabWidget.show()
        else:
            btn = QtWidgets.QPushButton(QtCore.QCoreApplication.translate("TextEditBone", "Open editor"), self)
            iconbtn = QtGui.QIcon()
            iconbtn.addPixmap(QtGui.QPixmap("icons/actions/text-edit.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            btn.setIcon(iconbtn)
            btn.lang = None
            btn.released.connect(self.openEditor)
            self.webView = ClickableWebView(self)
            self.webView.clicked.connect(self.openEditor)
            self.layout().addWidget(self.webView)
            self.layout().addWidget(btn)
            self.html = ""
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred))

    @staticmethod
    def fromSkelStructure(modulName, boneName, skelStructure):
        readOnly = "readonly" in skelStructure[boneName].keys() and skelStructure[boneName]["readonly"]
        if boneName in skelStructure.keys():
            if "languages" in skelStructure[boneName].keys():
                languages = skelStructure[boneName]["languages"]
            else:
                languages = None
            if "plaintext" in skelStructure[boneName].keys() and skelStructure[boneName]["plaintext"]:
                plaintext = True
            else:
                plaintext = False
            if "validHtml" in skelStructure[boneName].keys():
                validHtml = skelStructure[boneName]["validHtml"]
            else:
                validHtml = None
        return (
        TextEditBone(modulName, boneName, readOnly, languages=languages, plaintext=plaintext, validHtml=validHtml) )

    def onTabLanguageChanged(self, lang):
        if lang in self.languageContainer.keys():
            self.tabWidget.blockSignals(True)
            self.tabWidget.setCurrentWidget(self.languageContainer[lang])
            self.tabWidget.blockSignals(False)

    def onTabCurrentChanged(self, idx):
        wdg = self.tabWidget.widget(idx)
        for k, v in self.languageContainer.items():
            if v == wdg:
                event.emit("tabLanguageChanged", k)
                wdg.setFocus()
                return

    def sizeHint(self):
        return ( QtCore.QSize(150, 150) )

    def openEditor(self, *args, **kwargs):
        if self.languages:
            lang = self.languages[self.tabWidget.currentIndex()]
            if self.plaintext:
                editor = TextEditor(self.html[lang])
            else:
                if self.validHtml:
                    editor = TextEditor(self.html[lang], self.validHtml)
                else:
                    editor = TextEditor(self.html[lang])
        else:
            if self.plaintext:
                editor = TextEditor(self.html)
            else:
                if self.validHtml:
                    editor = TextEditor(self.html, self.validHtml)
                else:
                    editor = TextEditor(self.html)
        editor.onDataChanged.connect(self.onSave)
        event.emit("stackWidget", editor)

    def onSave(self, text):
        if self.languages:
            lang = self.languages[self.tabWidget.currentIndex()]
            self.html[lang] = str(text)
            self.languageContainer[lang].webView.setHtml(text)
        else:
            self.html = str(text)
            self.webView.setHtml(text)

    def unserialize(self, data):
        if not self.boneName in data.keys():
            return
        if self.languages and isinstance(data[self.boneName], dict):
            for lang in self.languages:
                if lang in data[self.boneName].keys() and data[self.boneName][lang] is not None:
                    self.html[lang] = data[self.boneName][lang].replace("target=\"_blank\" href=\"", "href=\"!")
                else:
                    self.html[lang] = ""
                self.languageContainer[lang].webView.setHtml(self.html[lang])
        elif not self.languages:
            self.html = str(data[self.boneName]).replace("target=\"_blank\" href=\"", "href=\"!") if (
            data and data.get(self.boneName) ) else ""
            self.webView.setHtml(self.html)

    def serializeForPost(self):
        if self.languages:
            res = {}
            for lang in self.languages:
                res["%s.%s" % (self.boneName, lang)] = self.html[lang]
            return ( res )
        else:
            return ( {self.boneName: self.html.replace("href=\"!", "target=\"_blank\" href=\"")} )

    def serializeForDocument(self):
        return ( self.serialize() )

    def remove(self):
        pass


def CheckForTextBone(modulName, boneName, skelStucture):
    return ( skelStucture[boneName]["type"] == "text" )

#Register this Bone in the global queue
editBoneSelector.insert(2, CheckForTextBone, TextEditBone)
viewDelegateSelector.insert(2, CheckForTextBone, TextViewBoneDelegate)

