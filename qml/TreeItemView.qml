import QtQuick 2.0
import QtQuick.Controls 1.2


Row{
    id: treeItemView

    Text{
        width: 20
        height: 15
        text: modelData.has_child ? modelData.isOpen ? " – " : " + " : ""
        MouseArea{
            hoverEnabled: true
            anchors.fill: parent
            onClicked: {
                modelData.isOpen = !modelData.isOpen
            }
        }
    }

    Column{
        Text {
            text: modelData.content ? modelData.content : "Unnamed";
            width:100
            height:25
            font.pixelSize: 22
            MouseArea{
                anchors.fill: parent
                onClicked: {
                    treeItemView.ListView.view.currentIndex = index
                    treeItemView.forceActiveFocus()
                }
            }
        }
        Loader{
            source: modelData.isOpen ? "TreeItemList.qml" : "Empty.qml"
        }
    }
}
