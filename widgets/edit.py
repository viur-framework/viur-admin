# -*- coding: utf-8 -*-
from collections import OrderedDict

from PyQt5 import QtCore, QtGui, QtWidgets
from viur_admin.network import NetworkService
from viur_admin.event import event
from viur_admin.utils import RegisterQueue, Overlay, formatString
from viur_admin.config import conf
from viur_admin.ui.editUI import Ui_Edit
from viur_admin.ui.editpreviewUI import Ui_BasePreview
from viur_admin.priorityqueue import editBoneSelector
from viur_admin.priorityqueue import protocolWrapperInstanceSelector


class Preview(QtWidgets.QWidget):
    """Livepreview for unsaved changes"""

    def __init__(self, modul, data, *args, **kwargs):
        super(Preview, self).__init__(*args, **kwargs)
        self.ui = Ui_BasePreview()
        self.ui.setupUi(self)
        self.modul = modul
        self.data = data
        self.ui.cbUrls.hide()
        self.ui.btnReload.hide()
        if "name" in data.keys():
            self.setWindowTitle("Vorschau: %s" % data["name"])
        self.loadURL()
        self.show()

    def loadURL(self):
        NetworkService.request("%s/%s/preview" % (NetworkService.url.replace("/admin", ""), self.modul ), self.data,
                               secure=True, successHandler=self.setHTML)

    def setHTML(self, req):
        try:
            res = req.readAll().data().decode("UTF-8")
        except:
            res = QtCore.QCoreApplication.translate("Preview", "Preview not possible")
        self.ui.webView.setHtml(res,
                                QtCore.QUrl("%s/%s/preview" % (NetworkService.url.replace("/admin", ""), self.modul )))

    def onBtnReloadReleased(self, *args, **kwargs):
        self.loadURL()


class EditWidget(QtWidgets.QWidget):
    appList = "list"
    appHierarchy = "hierarchy"
    appTree = "tree"
    appSingleton = "singleton"

    def __init__(self, modul, applicationType, key=0, node=None, skelType=None, clone=False, *args, **kwargs):
        """
            Initialize a new Edit or Add-Widget for the given modul.
            @param modul: Name of the modul
            @type modul: String
            @param applicationType: Defines for what application this Add / Edit should be created. This hides
            additional complexity introduced by the hierarchy / tree-application
            @type applicationType: Any of EditWidget.appList, EditWidget.appHierarchy, EditWidget.appTree or
            EditWidget.appSingleton
            @param id: ID of the entry. If none, it will add a new Entry.
            @type id: Number
            @param rootNode: If applicationType==EditWidget.appHierarchy, the new entry will be added under this
            node, if applicationType==EditWidget,appTree the final node is derived from this and the path-parameter.
            Has no effect if applicationType is not appHierarchy or appTree or if an id have been set.
            @type rootNode: String
            @param path: Specifies the path from the rootNode for new entries in a treeApplication
            @type path: String
            @param clone: If true, it will load the values from the given id, but will save a new entry (i.e. allows
            "cloning" an existing entry)
            @type clone: Bool
        """
        super(EditWidget, self).__init__(*args, **kwargs)
        self.ui = Ui_Edit()
        self.ui.setupUi(self)
        protoWrap = protocolWrapperInstanceSelector.select(modul)
        assert protoWrap is not None
        self.modul = modul
        # A Bunch of santy-checks, as there is a great chance to mess around with this widget
        assert applicationType in [EditWidget.appList, EditWidget.appHierarchy, EditWidget.appTree,
                                   EditWidget.appSingleton]  # Invalid Application-Type?
        if applicationType == EditWidget.appHierarchy or applicationType == EditWidget.appTree:
            assert id or node  # Need either an id or an node
        if clone:
            assert id  # Need an id if we should clone an entry
            assert not applicationType == EditWidget.appSingleton  # We cant clone a singleton
            if applicationType == EditWidget.appHierarchy or applicationType == EditWidget.appTree:
                assert rootNode  # We still need a rootNode for cloning
            if applicationType == EditWidget.appTree:
                assert path  # We still need a path for cloning
        # End santy-checks
        self.applicationType = applicationType
        self.key = key
        self.node = node
        self.skelType = skelType
        self.clone = clone
        self.bones = {}
        self.overlay = Overlay(self)
        self.overlay.inform(self.overlay.BUSY)
        self.closeOnSuccess = False
        self._lastData = {}  # Dict of structure and values recived
        self.editTaskID = None
        self.reloadData()
        # Hide Previewbuttons if no PreviewURLs are set
        if modul in conf.serverConfig["modules"].keys():
            if not "previewurls" in conf.serverConfig["modules"][self.modul].keys() \
                    or not conf.serverConfig["modules"][self.modul]["previewurls"]:
                self.ui.btnPreview.hide()
        if modul == "_tasks":
            self.ui.btnPreview.hide()
            self.ui.btnSaveClose.setText(QtCore.QCoreApplication.translate("EditWidget", "Execute"))
            self.ui.btnSaveContinue.hide()
            self.ui.btnReset.hide()
        self.ui.btnReset.released.connect(self.onBtnResetReleased)
        self.ui.btnSaveContinue.released.connect(self.onBtnSaveContinueReleased)
        self.ui.btnSaveClose.released.connect(self.onBtnSaveCloseReleased)
        self.ui.btnPreview.released.connect(self.onBtnPreviewReleased)
        self.ui.btnClose.released.connect(self.onBtnCloseReleased)
        if not self.key and not self.clone:
            self.ui.btnSaveClose.setText(QtCore.QCoreApplication.translate("EditWidget", "Save and Close"))
            self.ui.btnSaveContinue.setText(QtCore.QCoreApplication.translate("EditWidget", "Save and New"))
        else:
            self.ui.btnSaveClose.setText(QtCore.QCoreApplication.translate("EditWidget", "Save and Close"))
            self.ui.btnSaveContinue.setText(QtCore.QCoreApplication.translate("EditWidget", "Save and Continue"))
        protoWrap.busyStateChanged.connect(self.onBusyStateChanged)
        protoWrap.updatingSucceeded.connect(self.onSaveSuccess)
        protoWrap.updatingFailedError.connect(self.onSaveError)
        protoWrap.updatingDataAvaiable.connect(self.onDataAvaiable)
        self.overlay.inform(self.overlay.BUSY)

    def onBusyStateChanged(self, busy):
        if busy:
            self.overlay.inform(self.overlay.BUSY)
        else:
            self.overlay.clear()

    def getBreadCrumb(self):
        if self._lastData:
            config = conf.serverConfig["modules"][self.modul]
            if "format" in config.keys():
                format = config["format"]
            else:
                format = "$(name)"
            itemName = formatString(format, self._lastData["structure"], self._lastData["values"])
        else:
            itemName = ""
        if self.clone:
            if itemName:
                descr = QtCore.QCoreApplication.translate("EditWidget", "Clone: %s") % itemName
            else:
                descr = QtCore.QCoreApplication.translate("EditWidget", "Clone entry")
            icon = QtGui.QIcon(":icons/actions/clone.png")
        elif self.key or self.applicationType == EditWidget.appSingleton:  # Were editing
            if itemName:
                descr = QtCore.QCoreApplication.translate("EditWidget", "Edit: %s") % itemName
            else:
                descr = QtCore.QCoreApplication.translate("EditWidget", "Edit entry")
            icon = QtGui.QIcon(":icons/actions/edit.svg")
        else:  # Were adding
            descr = QtCore.QCoreApplication.translate("EditWidget",
                                                      "Add entry")  #We know that we cant know the name yet
            icon = QtGui.QIcon(":icons/actions/add.svg")
        return ( descr, icon )


    def onBtnCloseReleased(self, *args, **kwargs):
        event.emit("popWidget", self)

    def reloadData(self):
        print("--RELOADING--")
        self.save({})
        return

    def save(self, data):
        protoWrap = protocolWrapperInstanceSelector.select(self.modul)
        assert protoWrap is not None
        if self.modul == "_tasks":
            self.editTaskID = protoWrap.edit(self.key, **data)
        # request = NetworkService.request("/%s/execute/%s" % ( self.modul, self.id ), data, secure=True,
        # successHandler=self.onSaveResult )
        elif self.applicationType == EditWidget.appList:  ## Application: List
            if self.key and (not self.clone or not data):
                self.editTaskID = protoWrap.edit(self.key, **data)
            else:
                self.editTaskID = protoWrap.add(**data)
        elif self.applicationType == EditWidget.appHierarchy:  ## Application: Hierarchy
            if self.key and not self.clone:
                self.editTaskID = protoWrap.edit(self.key, **data)
            else:
                self.editTaskID = protoWrap.add(self.node, **data)
        elif self.applicationType == EditWidget.appTree:  ## Application: Tree
            if self.key and not self.clone:
                self.editTaskID = protoWrap.edit(self.key, self.skelType, **data)
            else:
                self.editTaskID = protoWrap.add(self.node, self.skelType, **data)
        elif self.applicationType == EditWidget.appSingleton:  ## Application: Singleton
            self.editTaskID = protoWrap.edit(**data)
        else:
            raise NotImplementedError()  # Should never reach this

    def onBtnResetReleased(self, *args, **kwargs):
        res = QtGui.QMessageBox.question(self,
                                         QtCore.QCoreApplication.translate("EditWidget", "Confirm reset"),
                                         QtCore.QCoreApplication.translate("EditWidget",
                                                                           "Discard all unsaved changes?"),
                                         QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No
        )
        if res == QtGui.QMessageBox.Yes:
            self.setData(data=self.dataCache)

    def parseHelpText(self, txt):
        """Parses the HTML-Text txt and returns it with remote Images replaced with their local copys

        @type txt: String
        @param txt: HTML-Text
        @return: String
        """
        res = ""
        while txt:
            idx = txt.find("<img src=")
            if idx == -1:
                res += txt
                return ( res )
            startpos = txt.find("\"", idx + 8) + 1
            endpos = txt.find("\"", idx + 13)
            url = txt[startpos:endpos]
            res += txt[: startpos]
            res += getFileName(url)  # FIXME: BROKEN
            txt = txt[endpos:]

        fileName = os.path.join(conf.currentPortalConfigDirectory, sha1(dlkey.encode("UTF-8")).hexdigest())
        if not os.path.isfile(fileName):
            try:
                data = NetworkService.request(dlkey)
            except:
                return ( None )
            open(fileName, "w+b").write(data)
        return ( fileName )

    def setData(self, request=None, data=None, ignoreMissing=False):
        """
        Rebuilds the UI according to the skeleton recived from server

        @type data: dict
        @param data: The data recived
        """
        assert (request or data)
        if request:
            data = NetworkService.decode(request)
        # Clear the UI
        while ( self.ui.tabWidget.count() ):
            item = self.ui.tabWidget.widget(0)
            if item and item.widget():
                if "remove" in dir(item.widget()):
                    item.widget().remove()
            self.ui.tabWidget.removeTab(0)
        self.bones = OrderedDict()
        self.dataCache = data
        tmpDict = {}
        tabs = {}
        tmpTabs = []  #Sort tabs by their description
        for key, bone in data["structure"]:
            tmpDict[key] = bone
        for key, bone in data["structure"]:
            if bone["visible"] == False:
                continue
            if "params" in bone.keys() and bone["params"] and "category" in bone["params"].keys():
                tabName = bone["params"]["category"]
            else:
                tabName = QtCore.QCoreApplication.translate("EditWidget", "General")
            if not tabName in tabs.keys():
                scrollArea = QtWidgets.QScrollArea()
                containerWidget = QtWidgets.QWidget(scrollArea)
                scrollArea.setWidget(containerWidget)
                tabs[tabName] = QtWidgets.QFormLayout(containerWidget)
                containerWidget.setLayout(tabs[tabName])
                containerWidget.setSizePolicy(
                    QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred))
                tmpTabs.append((scrollArea, tabName))
                scrollArea.setWidgetResizable(True)
        tmpTabs.sort(key=lambda x: x[1])
        for scrollArea, tabName in tmpTabs:
            self.ui.tabWidget.addTab(scrollArea, tabName)
        for key, bone in data["structure"]:
            if bone["visible"] == False:
                continue
            if "params" in bone.keys() and bone["params"] and "category" in bone["params"].keys():
                tabName = bone["params"]["category"]
            else:
                tabName = QtCore.QCoreApplication.translate("EditWidget", "General")
            #queue = RegisterQueue()
            #event.emit( QtCore.SIGNAL('requestBoneEditWidget(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject,
            # PyQt_PyObject)'),queue, self.modul, key, tmpDict )
            #widget = queue.getBest()
            wdgGen = editBoneSelector.select(self.modul, key, tmpDict)
            widget = wdgGen.fromSkelStructure(self.modul, key, tmpDict)
            if bone["error"] and not ignoreMissing:
                dataWidget = QtWidgets.QWidget()
                layout = QtWidgets.QHBoxLayout(dataWidget)
                dataWidget.setLayout(layout)
                layout.addWidget(widget, stretch=1)
                iconLbl = QtWidgets.QLabel(dataWidget)
                if bone["required"]:
                    iconLbl.setPixmap(QtGui.QPixmap(":icons/status/error.png"))
                else:
                    iconLbl.setPixmap(QtGui.QPixmap(":icons/status/incomplete.png"))
                layout.addWidget(iconLbl, stretch=0)
                iconLbl.setToolTip(str(bone["error"]))
            else:
                dataWidget = widget
            ## Temporary MacOS Fix
            import sys

            if sys.platform.startswith("darwin"):
                dataWidget.setMaximumWidth(500)
                dataWidget.setMinimumWidth(500)
            ## Temporary MacOS Fix
            lblWidget = QtWidgets.QWidget(self)
            layout = QtWidgets.QHBoxLayout(lblWidget)
            if "params" in bone.keys() and isinstance(bone["params"], dict) and "tooltip" in bone["params"].keys():
                lblWidget.setToolTip(self.parseHelpText(bone["params"]["tooltip"]))
            descrLbl = QtWidgets.QLabel(bone["descr"], lblWidget)
            descrLbl.setWordWrap(True)
            if bone["required"]:
                font = descrLbl.font()
                font.setBold(True)
                font.setUnderline(True)
                descrLbl.setFont(font)
            layout.addWidget(descrLbl)
            tabs[tabName].addRow(lblWidget, dataWidget)
            dataWidget.show()
            self.bones[key] = widget
        self.unserialize(data["values"])
        self._lastData = data
        event.emit("rebuildBreadCrumbs()")

    # if self.overlay.status==self.overlay.BUSY:
    #	self.overlay.clear()

    def unserialize(self, data):
        try:
            for bone in self.bones.values():
                bone.unserialize(data)
        except AssertionError as err:
            # self.parent().parent().logger.error(err)
            self.overlay.inform(self.overlay.ERROR, str(err))
            self.ui.btnSaveClose.setDisabled(True)
            self.ui.btnSaveContinue.setDisabled(True)

    def onBtnSaveContinueReleased(self, *args, **kwargs):
        self.closeOnSuccess = False
        #self.overlay.inform( self.overlay.BUSY )
        res = {}
        for key, bone in self.bones.items():
            res.update(bone.serializeForPost())
        self.save(res)

    def onBtnSaveCloseReleased(self, *args, **kwargs):
        self.closeOnSuccess = True
        #self.overlay.inform( self.overlay.BUSY )
        res = {}
        for key, bone in self.bones.items():
            res.update(bone.serializeForPost())
        self.save(res)

    def onBtnPreviewReleased(self, *args, **kwargs):
        res = {}
        for key, bone in self.bones.items():
            res.update(bone.serializeForPost())
        self.preview = Preview(self.modul, res)

    def onSaveSuccess(self, editTaskID):
        """
            Adding/editing an entry just succeeded
        """
        if editTaskID != self.editTaskID:  #Not our task
            return
        self.overlay.inform(self.overlay.SUCCESS, QtCore.QCoreApplication.translate("EditWidget", "Entry saved"))
        if self.closeOnSuccess:
            event.emit('popWidget', self)
        else:
            self.reloadData()

    def onDataAvaiable(self, editTaskID, data, wasInitial):
        """
            Adding/editing failed, cause some required fields are missing/invalid
        """
        if editTaskID != self.editTaskID:  #Not our task
            return
        self.setData(data=data, ignoreMissing=wasInitial)
        if not wasInitial:
            self.overlay.inform(self.overlay.MISSING, QtCore.QCoreApplication.translate("EditWidget", "Missing data"))


    def onSaveError(self, error):
        """
            Unspecified error on saving/editing
        """
        self.overlay.inform(self.overlay.ERROR,
                            QtCore.QCoreApplication.translate("EditWidget", "There was an error saving your changes"))
        return


    def taskAdded(self):
        QtGui.QMessageBox.information(self,
                                      QtCore.QCoreApplication.translate("EditWidget", "Task created"),
                                      QtCore.QCoreApplication.translate("EditWidget",
                                                                        "The task was sucessfully created."),
                                      QtCore.QCoreApplication.translate("EditWidget", "Okay"))
        self.parent().deleteLater()
