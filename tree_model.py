
from tree_item import TreeItem
from PyQt5.QtCore import QObject, pyqtSignal, QAbstractItemModel, QModelIndex, Qt, pyqtProperty
from PyQt5.QtQml import QQmlListProperty

class TreeModel(QAbstractItemModel):
    treeChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.rootItem = TreeItem("Root")

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            print("index not valid, return none")
            return None

        if role != Qt.DisplayRole:
            print("role not display role")
            return None

        item = index.internalPointer()
        print("item", item)

        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    @pyqtProperty(QQmlListProperty, notify=treeChanged)
    def root_node(self):
        return QQmlListProperty(TreeItem, self, self.rootItem._childs)
