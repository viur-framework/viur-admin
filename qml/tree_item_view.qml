import QtQuick 2.0

Row{
    id: itemView
    Text{
        width: 10
        height: 10
        text: modelData.has_child ? modelData.is_open ? "-" : "+" : ""
        MouseArea{
            anchors.fill: parent
            onClicked: modelData.is_open = !modelData.is_open;
        }
    }
    Column{
        Text{ text: modelData.content }
        Loader{
            source: modelData.is_open ? "tree_item_list.qml" : "empty.qml"
        }
    }
}
