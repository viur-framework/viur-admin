import QtQuick 2.0
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2

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
    ToolButton {
        tooltip: "Button"
        iconSource: "cancel.svg"
        height: rowHeight
        width: rowHeight
    }
}
