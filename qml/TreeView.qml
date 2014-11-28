import QtQuick 2.1
import QtQuick.Controls 1.0

ScrollView {
    id: view

    property var model
    property int rowHeight: 30
    property int columnIndent: 10
    property var currentNode
    property var currentItem

    property Component delegate: ModuleDelegate {}

    frameVisible: true
    implicitWidth: content.implicitWidth + 40
    implicitHeight: 160

    contentItem: Loader {
        id: content

        onLoaded: item.isRoot = true
        sourceComponent: treeBranch
        property var elements: model

        Component {
            id: treeBranch
            Item {
                id: root
                property bool isRoot: false
                implicitHeight: column.implicitHeight
                implicitWidth: column.implicitWidth

                Column {
                    id: column
                    x: 0
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
                                gradient: Gradient {
                                    GradientStop { position: 0.0; color: "red" }
                                    GradientStop { position: 0.55; color: "#ff5555" }
                                    GradientStop { position: 1.0; color: "gray" }
                                }
                            }

                            Rectangle {
                                id: colfill
                                x: view.mapToItem(colfill, 0, 0).x
                                width: view.width
                                height: loader.expanded ? loader.implicitHeight : 0
                                border.color: "#000000"
                                border.width: 1
                                color: '#00000000'
                            }
                            MouseArea {
                                anchors.fill: rowfill
                                onPressed: {
                                    currentNode = model
                                    currentItem = loader
                                    forceActiveFocus()
                                    loader.expanded = true
                                }
                            }
                            Row {
                                id: row

                                Item {
                                    width: 15
                                    height: rowHeight
                                    opacity: model.children.length > 0 ? 1 : 0
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
                                x: model.children.length > 0 ? columnIndent : 0
                                height: expanded ? implicitHeight : 0
                                property var node: model
                                property bool expanded: false
                                property var elements: model.children
                                property var text: model.text
                                sourceComponent: (expanded && model.children.length > 0) ? treeBranch : undefined
                            }

                        }
                    }
                }
            }
        }
    }
}
