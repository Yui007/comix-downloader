import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    
    // Theme colors
    readonly property color bgCard: "#1C1C24"
    readonly property color bgElevated: "#252530"
    readonly property color accentPrimary: "#E8A54B"
    readonly property color accentGradientEnd: "#D4873A"
    readonly property color textPrimary: "#F5F5F0"
    readonly property color textTertiary: "#5C5C66"
    readonly property color bgDeep: "#0A0A0C"
    
    color: bgCard
    radius: 12
    
    signal fetchRequested(string url)
    
    property bool isLoading: false
    
    RowLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 8
        
        // LINK ICON
        Text {
            text: "🔗"
            font.pixelSize: 18
            opacity: 0.7
        }
        
        // TEXT INPUT
        TextField {
            id: urlField
            Layout.fillWidth: true
            Layout.fillHeight: true
            
            placeholderText: "Paste manga URL here..."
            placeholderTextColor: textTertiary
            color: textPrimary
            font.family: "Segoe UI"
            font.pixelSize: 14
            
            background: Rectangle {
                color: "transparent"
                
                // Animated underline
                Rectangle {
                    anchors.bottom: parent.bottom
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: urlField.activeFocus ? parent.width : 0
                    height: 2
                    color: accentPrimary
                    radius: 1
                    
                    Behavior on width {
                        NumberAnimation { duration: 250; easing.type: Easing.OutCubic }
                    }
                }
                
                // Static dim underline
                Rectangle {
                    anchors.bottom: parent.bottom
                    width: parent.width
                    height: 1
                    color: textTertiary
                    opacity: 0.3
                }
            }
            
            Keys.onReturnPressed: {
                if (text.length > 0 && !root.isLoading) {
                    root.fetchRequested(text)
                }
            }
        }
        
        // FETCH BUTTON
        Rectangle {
            id: fetchButton
            
            Layout.preferredWidth: 100
            Layout.fillHeight: true
            
            radius: 6
            
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: accentPrimary }
                GradientStop { position: 1.0; color: accentGradientEnd }
            }
            
            scale: fetchMouseArea.pressed ? 0.97 : (fetchMouseArea.containsMouse ? 1.02 : 1.0)
            
            Behavior on scale {
                NumberAnimation { duration: 150; easing.type: Easing.OutCubic }
            }
            
            Text {
                anchors.centerIn: parent
                text: root.isLoading ? "..." : "FETCH"
                font.family: "Segoe UI"
                font.pixelSize: 12
                font.weight: Font.Bold
                color: bgDeep
                font.letterSpacing: 1
            }
            
            MouseArea {
                id: fetchMouseArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                enabled: !root.isLoading
                
                onClicked: {
                    if (urlField.text.length > 0) {
                        root.fetchRequested(urlField.text)
                    }
                }
            }
        }
    }
    
    Connections {
        target: MangaBridge
        function onLoadingChanged(loading) {
            root.isLoading = loading
        }
    }
}
