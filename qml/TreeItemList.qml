import QtQuick 2.0

Column{
    Repeater{
        model: modelData.children
        delegate: TreeItemView{}
    }
}
