from PyQt5.QtCore import QObject, pyqtSignal


class Model(QObject):
    treeChanged = pyqtSignal()

    def __init__(self, parent=None):
        self._tree = list()

