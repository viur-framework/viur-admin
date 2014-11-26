import sys

from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject, QCoreApplication, QUrl
from PyQt5.QtQml import qmlRegisterType, QQmlComponent, QQmlEngine
from PyQt5.QtGui import QApplication


class TreeItem(QObject):
    content_changed = pyqtSignal()
    children_changed = pyqtSignal()
    is_open_changed = pyqtSignal()
    has_child_changed = pyqtSignal()

    def __init__(self, content, parent=None, **kwargs):
        super().__init__(parent)
        self._content = content
        self._childs = list()
        self._is_open = False

        @pyqtProperty("QString")
        def content(self):
            return self._content

        @content.setter
        def set_content(self, content):
            self._content = content
            self.content_changed.emit()

        @pyqtProperty("QList<QObject*>")
        def children(self):
            return self._childs

        @children.setter
        def set_children(self, children):
            self._childs = children

        def add_child(self, child):
            self._childs.append(child)
            self.children_changed.emit()

        @pyqtProperty("bool")
        def is_open(self):
            return self._is_open

        @is_open.setter
        def set_is_open(self, value):
            self._is_open = value
            self.is_open_changed.emit()

        @pyqtProperty("bool")
        def has_child(self):
            return self._childs


# Create the application instance.
app = QApplication(sys.argv)

# Register the Python type.  Its URI is 'People', it's v1.0 and the type
# will be called 'Person' in QML.
qmlRegisterType(TreeItem, 'TreeItem', 1, 0, 'Person')

# Create a QML engine.
engine = QQmlEngine()

# Create a component factory and load the QML script.
component = QQmlComponent(engine)
component.loadUrl(QUrl('example.qml'))

# Create an instance of the component.
person = component.create()

if person is not None:
    # Print the value of the properties.
    print("The person's name is %s." % person.name)
    print("They wear a size %d shoe." % person.shoeSize)
else:
    # Print all errors that occurred.
    for error in component.errors():
        print(error.toString())
