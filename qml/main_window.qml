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
    RowLayout {
        id: layout
        anchors.fill: parent
        spacing: 6

        Rectangle {
            border.color: '#888888'
            Layout.fillWidth: true
            Layout.fillHeight: true

            TreeView {
                anchors.fill: parent
                model: tree_model.root_node
            }

        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Text {
                anchors.centerIn: parent
                text: parent.width + 'x' + parent.height
            }
        }
    }
}
