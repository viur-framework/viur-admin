import QtQuick 2.1
import QtQuick.Controls 1.0

ScrollView {
    id: view

    property var model
    property int rowHeight: 19
    property int columnIndent: 22
    property var currentNode
    property var currentItem

    property Component delegate: Label {
        id: label
        text: model.text ? model.text : 0
        color: currentNode === model ? "white" : "black"
    }

    frameVisible: true
    implicitWidth: 200
    implicitHeight: 160

    contentItem: Loader {
        id: content

        onLoaded: item.isRoot = true
        sourceComponent: treeBranch
        property var elements: model

        Column {
            anchors.fill: parent
            Repeater {
                model: 1 + Math.max(view.contentItem.height, view.height) / rowHeight
                Rectangle {
                    objectName: "Faen"
                    color: index % 2 ? "#eee" : "white"
                    width: view.width ; height: rowHeight
                }
            }
        }
        Component {
            id: treeBranch
            Item {
                id: root
                property bool isRoot: false
                implicitHeight: column.implicitHeight
                implicitWidth: column.implicitWidth
                Column {
                    id: column
                    x: 2
                    Item { height: isRoot ? 0 : rowHeight; width: 1}
                    Repeater {
                        model: elements
                        Item {
                            id: filler
                            width: Math.max(loader.width + columnIndent, row.width)
                            height: Math.max(row.height, loader.height)
                            property var _model: model
                            Rectangle {
                                id: rowfill
                                x: view.mapToItem(rowfill, 0, 0).x
                                width: view.width
                                height: rowHeight
                                visible: currentNode === model
                                color: "#37f"
                            }
                            MouseArea {
                                anchors.fill: rowfill
                                onPressed: {
                                    currentNode = model
                                    currentItem = loader
                                    forceActiveFocus()
                                }
                            }
                            Row {
                                id: row
                                Item {
                                    width: rowHeight
                                    height: rowHeight
                                    opacity: !!model.elements ? 1 : 0
                                    Image {
                                        id: expander
                                        source: "expander.png"
                                        opacity: mouse.containsMouse ? 1 : 0.7
                                        anchors.centerIn: parent
                                        rotation: loader.expanded ? 90 : 0
                                        Behavior on rotation {NumberAnimation { duration: 120}}
                                    }
                                    MouseArea {
                                        id: mouse
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: loader.expanded = !loader.expanded
                                    }
                                }
                                Loader {
                                    property var model: _model
                                    sourceComponent: delegate
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                            }
                            Loader {
                                id: loader
                                x: columnIndent
                                height: expanded ? implicitHeight : 0
                                property var node: model
                                property bool expanded: false
                                property var elements: model.elements
                                property var text: model.text
                                sourceComponent: (expanded && !!model.elements) ? treeBranch : undefined
                            }
                        }
                    }
                }
            }
        }
    }
}
