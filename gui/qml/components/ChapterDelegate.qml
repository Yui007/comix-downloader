import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    
    property var chapter: null
    signal toggled()
    
    // Theme colors
    readonly property color bgElevated: "#252530"
    readonly property color accentPrimary: "#E8A54B"
    readonly property color textPrimary: "#F5F5F0"
    readonly property color textSecondary: "#8B8B99"
    readonly property color textTertiary: "#5C5C66"
    readonly property color bgDeep: "#0A0A0C"
    
    height: 44
    color: mouseArea.containsMouse ? bgElevated : "transparent"
    radius: 6
    
    Behavior on color { ColorAnimation { duration: 150 } }
    
    transform: Translate {
        x: mouseArea.containsMouse ? 4 : 0
        Behavior on x { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
    }
    
    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 8
        anchors.rightMargin: 8
        spacing: 16
        
        // SELECTION CIRCLE
        Rectangle {
            width: 20; height: 20; radius: 10
            color: chapter && chapter.selected ? accentPrimary : "transparent"
            border.color: chapter && chapter.selected ? accentPrimary : textTertiary
            border.width: 2
            
            Behavior on color { ColorAnimation { duration: 150 } }
            
            Text {
                anchors.centerIn: parent
                text: "✓"
                font.pixelSize: 12
                font.weight: Font.Bold
                color: bgDeep
                visible: chapter && chapter.selected
                scale: chapter && chapter.selected ? 1 : 0
                Behavior on scale { NumberAnimation { duration: 150; easing.type: Easing.OutBack } }
            }
        }
        
        // CHAPTER INFO
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            
            Text {
                text: chapter ? ("Ch. " + chapter.number + (chapter.title ? " — " + chapter.title : "")) : ""
                font.family: "Segoe UI"
                font.pixelSize: 14
                font.weight: chapter && chapter.selected ? Font.DemiBold : Font.Normal
                color: chapter && chapter.selected ? textPrimary : textSecondary
                Layout.fillWidth: true
                elide: Text.ElideRight
            }
            
            Text {
                text: chapter ? chapter.group_name : ""
                font.pixelSize: 10
                color: textTertiary
                visible: chapter && chapter.group_name
            }
        }
    }
    
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.toggled()
    }
}
