import sys, time, random

from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject, QUrl, QModelIndex
from PyQt5.QtQml import qmlRegisterType, QQmlComponent, QQmlEngine
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQuick import QQuickView
from tree_item import TreeItem
from tree_model import TreeModel
# Create the application instance.
app = QApplication(sys.argv)

# Register the Python type.  Its URI is 'People', it's v1.0 and the type
# will be called 'Person' in QML.
qmlRegisterType(TreeItem, 'TreeItem', 1, 0, 'TreeItem')
qmlRegisterType(TreeModel, 'TreeModel', 1, 0, 'TreeModel')

tree_model = TreeModel()

rootItem = tree_model.rootItem

count = 0

icons = ["list.svg", "hierarchy.svg", "singleton.svg", "my_files.svg", "news.svg", None]

def populate(node, level=0):
    for i in range(random.randint(1, 7)):
        item = TreeItem("T: %s" % random.randint(0, 10000), icon=random.sample(icons, 1)[0])
        node.add_child(item)
        if level < 3:
            populate(item, level + 1)


populate(rootItem, 0)

# view = QQuickView()
# view.setResizeMode(QQuickView.SizeRootObjectToView)
engine = QQmlEngine()
engine.quit.connect(app.quit)
cxt = engine.rootContext()
cxt.setContextProperty("tree_model", tree_model)

print(1)
component = QQmlComponent(engine, QUrl.fromLocalFile('qml/main_window.qml'))

while not component.isReady():
    time.sleep(1)

main_window = component.create()
main_window.setIcon(QIcon("old_foo/icons/viur_logo.png"));
print(1)
# view.show()
sys.exit(app.exec_())
