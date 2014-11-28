import QtQuick 2.3
import QtQuick.Window 2.0
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1


ApplicationWindow {
    id: mainWindow
    title: "Viur Admin"
    width: 640
    height: 480
    visible: true

    menuBar: MenuBar {
        id: menuBar
        Menu {
            title: "File"
            MenuItem {
                 text: "Quit"
                 shortcut: "Ctrl+Q"
                 onTriggered: Qt.quit()
            }
        }
        Menu {
            title: "Advanced"
            MenuItem {
                text: "Tasks"
                shortcut: "Ctrl+T"
            }
        }
        Menu {
            title: "Help"
            MenuItem {
                 text: "Viur-Admin Help"
                 shortcut: "Ctrl+H"
            }
            MenuItem {
                 text: "About"
                 shortcut: "F1"
            }
        }
    }
    SplitView {
        id: layout
        anchors.fill: parent
        orientation: Qt.Horizontal

        Rectangle {
            border.color: '#888888'
            // minimumWidth: tree_view.implicitWidth
            //Layout.fillWidth: true
            //Layout.fillHeight: true
            Layout.minimumWidth: tree_view.implicitWidth

            TreeView {
                id: tree_view
                anchors.fill: parent
                model: tree_model.root_node
            }

        }

        Rectangle {
            Text {
                anchors.centerIn: parent
                text: parent.width + 'x' + parent.height
            }
        }
    }
}
