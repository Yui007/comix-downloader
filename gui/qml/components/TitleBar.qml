import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    
    // Theme colors (inline)
    readonly property color bgDeep: "#0A0A0C"
    readonly property color bgSurface: "#141419"
    readonly property color bgCard: "#1C1C24"
    readonly property color bgElevated: "#252530"
    readonly property color accentPrimary: "#E8A54B"
    readonly property color textPrimary: "#F5F5F0"
    readonly property color textSecondary: "#8B8B99"
    readonly property color textTertiary: "#5C5C66"
    readonly property color error: "#E57373"
    
    color: bgDeep
    
    signal minimizeClicked()
    signal maximizeClicked()
    signal closeClicked()
    signal dragStarted(point pos)
    signal dragMoved(point pos)
    
    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: 8
        spacing: 16
        
        // LOGO / TITLE
        Text {
            text: "COMIX DOWNLOADER"
            font.family: "Segoe UI"
            font.pixelSize: 22
            font.weight: Font.Bold
            color: textPrimary
            
            // Amber underline accent
            Rectangle {
                anchors.bottom: parent.bottom
                anchors.bottomMargin: -2
                anchors.left: parent.left
                width: parent.width * 0.4
                height: 2
                color: accentPrimary
                radius: 1
            }
        }
        
        // DRAG AREA
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            
            MouseArea {
                anchors.fill: parent
                onPressed: (mouse) => root.dragStarted(Qt.point(mouse.x, mouse.y))
                onPositionChanged: (mouse) => root.dragMoved(Qt.point(mouse.x, mouse.y))
            }
        }
        
        // WINDOW CONTROLS
        RowLayout {
            spacing: 2
            
            // Minimize
            Rectangle {
                width: 36; height: 28; radius: 6
                color: minArea.containsMouse ? bgElevated : "transparent"
                Text { anchors.centerIn: parent; text: "─"; font.pixelSize: 14; font.weight: Font.Bold; color: textSecondary }
                MouseArea { id: minArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.minimizeClicked() }
            }
            
            // Maximize
            Rectangle {
                width: 36; height: 28; radius: 6
                color: maxArea.containsMouse ? bgElevated : "transparent"
                Text { anchors.centerIn: parent; text: "□"; font.pixelSize: 14; font.weight: Font.Bold; color: textSecondary }
                MouseArea { id: maxArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.maximizeClicked() }
            }
            
            // Close
            Rectangle {
                width: 36; height: 28; radius: 6
                color: closeArea.containsMouse ? error : "transparent"
                Text { anchors.centerIn: parent; text: "×"; font.pixelSize: 14; font.weight: Font.Bold; color: closeArea.containsMouse ? textPrimary : textSecondary }
                MouseArea { id: closeArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.closeClicked() }
            }
        }
    }
}
