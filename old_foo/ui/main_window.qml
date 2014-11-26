import QtQuick 2.1
import QtQuick.Window 2.0
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Controls.Styles 1.2
import QtMultimedia 5.0

import com.mausbrand.ModuleModel 1.0
import com.mausbrand.Module 1.0

ApplicationWindow {
    id: window
    title: "Viur Admin"
    visible: true
    width: 960
    height: 600
    color: "#aeaeae"
    minimumWidth: toolbarLayout.implicitWidth

    SplitView {
        anchors.fill: parent
        Keys.onSpacePressed: video.playbackState == MediaPlayer.PlayingState ? video.pause() : video.play()
        Keys.onLeftPressed: video.seek(video.position - 5000)
        Keys.onRightPressed: video.seek(video.position + 5000)


        RowLayout {

            id: leftLayout
            width: 200
            spacing: 0


            TableView {
                model:sessionModel
                id: sessionView
                Layout.fillHeight: true
                Layout.fillWidth: true


                TableViewColumn{
                    title: "name"
                    role: "name"
                }
                TableViewColumn{
                    title: "start"
                    role: "start"
                    Layout.fillWidth: true
                }

                TableViewColumn{
                    title: "duration"
                    delegate: Text {
                        text: msToTimeStr(duration)
                    }
                }

                TableViewColumn{
                    title: "path"
                    role: "path"
                    delegate: Rectangle {
                        id:pathDelegateComp
                        anchors.fill: parent
                        Text {
                            id:pathDelegate
                            text: styleData.value
                        }
                        MouseArea {
                            id: longPressArea
                            anchors.fill: parent
                            acceptedButtons: Qt.LeftButton | Qt.RightButton
                            onClicked: Component {
                                id: comp
                                FileDialog {
                                    id: fileDialog
                                    title: "Please choose a file"
                                    onAccepted: {
                                        console.log("You chose: " + fileDialog.fileUrls)
                                        Qt.quit()
                                    }
                                    onRejected: {
                                        console.log("Canceled")
                                        Qt.quit()
                                    }
                                    Component.onCompleted: visible = true
                                }
                            }
                        }
                    }
                }

                onActivated: {
                    video.source = model.getPath(currentRow);
                    driver.sessionCommentModel(currentRow);
                }
            }
            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "gray"
            }

            Video {
                id: video
                autoLoad: true
//                autoPlay: true
                Layout.fillWidth: true
                Layout.preferredHeight: width / 16 * 9
                focus: true
                source: sessionModel.getPath(0)
            }
        }

        SplitView {
            id: rightLayout
            orientation: Qt.Vertical

            TextEdit {
                id:sessionText
                color: "#ffffff"
                Layout.alignment: Qt.AlignLeft
                Layout.fillWidth: true
                Layout.minimumHeight: 100
                text: commentModel.comment(0).text
                selectionColor: "#39a8f9"
                textFormat: Qt.RichText
                clip: false
                horizontalAlignment: Text.AlignLeft
            }

            TableView {
                id: commentView
                model: commentModel
                Layout.fillHeight: true
                Layout.fillWidth: true
                selection.onSelectionChanged: commentView.selection.forEach( function(rowIndex) {
                    var comment = commentModel.comment(rowIndex);
                    sessionText.text = comment.text;
                    video.seek(comment.offset - position);
                })

                TableViewColumn{
                    title: "x"
                    width: 16
                    delegate: Image {
                        id: toogleImage
                        source: "images/media-playback-start.png"
                        width:8
                        height:8
                    }
                }

                TableViewColumn{
                    title: "offset"
                    role: "date"
                    delegate: TextInput {
                        id: offsetInput
                        text: msToTimeStr(styleData.value)
                        onAccepted: model.who = text
                        validator: IntValidator{bottom: 0; top: duration;}
                    }
                }
                TableViewColumn{
                    title: "Who"
                    role: "who"
                    delegate: TextInput {
                        id: whoInput
                        text: styleData.value
                        onAccepted: model.who = text
                    }
                }
            }
        }
    }

    statusBar: StatusBar {
        Label {
            id: status
            text: "QComments loaded..."
        }
    }
}
