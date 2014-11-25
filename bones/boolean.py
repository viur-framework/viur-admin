#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
from event import event
from bones.base import BaseViewBoneDelegate
from priorityqueue import editBoneSelector, viewDelegateSelector, protocolWrapperInstanceSelector


class BooleanViewBoneDelegate(BaseViewBoneDelegate):
    def displayText(self, value, locale):
        if value:
            return ( QtCore.QCoreApplication.translate("BooleanEditBone", "Yes") )
        else:
            return ( QtCore.QCoreApplication.translate("BooleanEditBone", "No") )


class BooleanEditBone(QtWidgets.QWidget):
    def __init__(self, modulName, boneName, readOnly, *args, **kwargs):
        super(BooleanEditBone, self).__init__(*args, **kwargs)
        self.modulName = modulName
        self.boneName = boneName
        self.readOnly = readOnly
        self.layout = QtWidgets.QVBoxLayout(self)
        self.comboBox = QtWidgets.QComboBox(self)
        self.layout.addWidget(self.comboBox)
        self.comboBox.addItems([QtCore.QCoreApplication.translate("BooleanEditBone", "No"),
                                QtCore.QCoreApplication.translate("BooleanEditBone", "Yes")])

    @classmethod
    def fromSkelStructure(cls, modulName, boneName, skelStructure):
        readOnly = "readonly" in skelStructure[boneName].keys() and skelStructure[boneName]["readonly"]
        return ( cls(modulName, boneName, readOnly) )

    def unserialize(self, data):
        protoWrap = protocolWrapperInstanceSelector.select(self.modulName)
        assert protoWrap is not None
        if self.boneName in data.keys() and data[self.boneName]:
            self.comboBox.setCurrentIndex(1)  # Yes is 2nd element
        elif self.boneName in data.keys() and not data[self.boneName]:
            self.comboBox.setCurrentIndex(0)
        else:
            self.comboBox.setCurrentIndex(-1)

    def serializeForPost(self):
        if self.comboBox.currentIndex() != -1:
            return ( {self.boneName: str(self.comboBox.currentIndex())} )
        return ( {self.boneName: None} )

    def serializeForDocument(self):
        return ( self.serialize() )


def CheckForBooleanBone(modulName, boneName, skelStucture):
    return ( skelStucture[boneName]["type"] == "bool" )

# Register this Bone in the global queue
editBoneSelector.insert(2, CheckForBooleanBone, BooleanEditBone)
viewDelegateSelector.insert(2, CheckForBooleanBone, BooleanViewBoneDelegate)



