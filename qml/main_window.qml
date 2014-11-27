import QtQuick 2.1
import QtQuick.Window 2.0
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Controls.Styles 1.2
import QtMultimedia 5.0

// import com.mausbrand.ModuleModel 1.0
// import com.mausbrand.Module 1.0



import TreeView
import programModel.tree


ApplicationWindow {
    id: window
    title: "Viur Admin"
    visible: true
    width: 960
    height: 600
    color: "#aeaeae"

    ListView{
        anchors.fill: parent
        model: programModel.tree
        delegate: ItemView{}
    }
}
