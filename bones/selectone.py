#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
from event import event
from bones.base import BaseViewBoneDelegate
from priorityqueue import editBoneSelector, viewDelegateSelector, protocolWrapperInstanceSelector
from utils import wheelEventFilter


class SelectOneViewBoneDelegate(BaseViewBoneDelegate):
    def displayText(self, value, locale):
        items = dict([(str(k), str(v)) for k, v in self.skelStructure[self.boneName]["values"].items()])
        if str(value) in items.keys():
            return ( items[str(value)])
        else:
            return ( value )


class FixedComboBox(QtWidgets.QComboBox):
    """
        Subclass of QComboBox which doesn't accept QWheelEvents if it doesnt have focus
    """

    def __init__(self, *args, **kwargs):
        super(FixedComboBox, self).__init__(*args, **kwargs)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.installEventFilter(wheelEventFilter)

    def focusInEvent(self, e):
        self.setFocusPolicy(QtCore.Qt.WheelFocus)
        super(FixedComboBox, self).focusInEvent(e)

    def focusOutEvent(self, e):
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        super(FixedComboBox, self).focusOutEvent(e)


class SelectOneEditBone(QtWidgets.QWidget):
    def __init__(self, modulName, boneName, readOnly, values, sortBy="keys", *args, **kwargs):
        super(SelectOneEditBone, self).__init__(*args, **kwargs)
        self.modulName = modulName
        self.boneName = boneName
        self.readOnly = readOnly
        self.values = values
        self.layout = QtGui.QVBoxLayout(self)
        self.comboBox = FixedComboBox(self)
        self.layout.addWidget(self.comboBox)
        tmpList = values
        if sortBy == "keys":
            tmpList.sort(key=lambda x: x[0])  # Sort by keys
        else:
            tmpList.sort(key=lambda x: x[1])  # Values
        self.comboBox.addItems([x[1] for x in tmpList])

    @classmethod
    def fromSkelStructure(cls, modulName, boneName, skelStructure):
        readOnly = "readonly" in skelStructure[boneName].keys() and skelStructure[boneName]["readonly"]
        if "sortBy" in skelStructure[boneName].keys():
            sortBy = skelStructure[boneName]["sortBy"]
        else:
            sortBy = "keys"
        values = list(skelStructure[boneName]["values"].items())
        return ( cls(modulName, boneName, readOnly, values=values, sortBy=sortBy) )

    def unserialize(self, data):
        protoWrap = protocolWrapperInstanceSelector.select(self.modulName)
        assert protoWrap is not None
        if 1:  # There might be junk comming from the server
            items = dict([(str(k), str(v)) for k, v in self.values])
            if str(data[self.boneName]) in items.keys():
                self.comboBox.setCurrentIndex(self.comboBox.findText(items[str(data[self.boneName])]))
            else:
                self.comboBox.setCurrentIndex(-1)
        else:  # except:
            self.comboBox.setCurrentIndex(-1)

    def serializeForPost(self):
        for key, value in self.values:
            if str(value) == str(self.comboBox.currentText()):
                return ( {self.boneName: str(key)} )
        return ( {self.boneName: None} )

    def serializeForDocument(self):
        return ( self.serialize() )


def CheckForSelectOneBone(modulName, boneName, skelStucture):
    return ( skelStucture[boneName]["type"] == "selectone" )

# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForSelectOneBone, SelectOneEditBone)
viewDelegateSelector.insert(2, CheckForSelectOneBone, SelectOneViewBoneDelegate)



