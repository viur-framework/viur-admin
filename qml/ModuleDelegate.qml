Item {
    property Component mdelegate: module_delegate
    property var model

    Component {
        id: module_delegate

        Row {
            spacing: 15
            Image {
                id: expander
                visible : model.icon ? 1 : 0
                source: model.icon ? model.icon : "list.svg"
                height: rowHeight
                width: model.icon ? height : 0
            }
            Label {
                id: label
                font.pixelSize: rowHeight
                text: model.content ? model.content : 0
                color: "black"
            }
        }
}
