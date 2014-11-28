from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject, QVariant
from PyQt5.QtQml import QQmlListProperty


class TreeItem(QObject):
    content_changed = pyqtSignal()
    children_changed = pyqtSignal()
    has_child_changed = pyqtSignal()
    icon_changed = pyqtSignal()

    def __init__(self, content, icon=None, parent=None, **kwargs):
        super().__init__(parent)
        self._icon = icon
        self._content = content
        self._childs = list()
        self._is_open = False

    @pyqtProperty(QVariant, notify=content_changed)
    def content(self):
        print("get content", self._content)
        return self._content

    @content.setter
    def content(self, content):
        self._content = content
        self.content_changed.emit()

    @pyqtProperty(QVariant, notify=icon_changed)
    def icon(self):
        print("icon", self._icon)
        return self._icon

    @icon.setter
    def icon(self, icon):
        self._icon = icon
        self.icon_changed.emit()

    @pyqtProperty(QQmlListProperty, notify=children_changed)
    def children(self):
        return QQmlListProperty(TreeItem, self, self._childs)

    @children.setter
    def children(self, children):
        self._childs = children

    def add_child(self, child):
        self._childs.append(child)
        self.children_changed.emit()

    isOpenChanged = pyqtSignal()

    @pyqtProperty(bool, notify=isOpenChanged)
    def isOpen(self):
        return self._is_open

    @isOpen.setter
    def isOpen(self, value):
        self._is_open = value
        self.isOpenChanged.emit()

    @pyqtProperty(bool, notify=has_child_changed)
    def has_child(self):
        return len(self._childs) > 0

    def data(self, index):
        if index == 0:
            return self.content
        return None

    def columnCount(self):
        return 1

    def childCount(self):
        return len(self._childs)

    def child(self, ix):
        print("child", ix, self._childs)
        return self._childs[ix]
