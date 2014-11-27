import sys, time

from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject, QUrl, QModelIndex
from PyQt5.QtQml import qmlRegisterType, QQmlComponent, QQmlEngine
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQuick import QQuickView
from qmltreeitem import TreeItem
from tree_model import TreeModel
# Create the application instance.
app = QApplication(sys.argv)

# Register the Python type.  Its URI is 'People', it's v1.0 and the type
# will be called 'Person' in QML.
qmlRegisterType(TreeItem, 'TreeItem', 1, 0, 'TreeItem')
qmlRegisterType(TreeModel, 'TreeModel', 1, 0, 'TreeModel')

tree_model = TreeModel()

rootItem = tree_model.rootItem

t1 = TreeItem("t1")
t1.set_is_open = True


t3 = TreeItem("t3")
t4 = TreeItem("t4")
t5 = TreeItem("t5")

t1.add_child(t3)
t3.add_child(t4)
t1.add_child(t5)

t2 = TreeItem("t2")
t5 = TreeItem("t5")
t6 = TreeItem("t6")
t7 = TreeItem("t7")
t8 = TreeItem("t8")

t2.add_child(t5)
t5.add_child(t6)
t6.add_child(t7)
t7.add_child(t8)
rootItem.add_child(t1)
rootItem.add_child(t2)


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
print(1)
# view.show()
sys.exit(app.exec_())
