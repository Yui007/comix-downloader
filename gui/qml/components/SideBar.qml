import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

Rectangle {
    id: root
    
    signal browseClicked()
    signal downloadsClicked()
    signal settingsClicked()
    
    property int activeTab: 0 // 0: Browse, 1: Downloads
    
    // Theme colors (mirroring Theme.qml for consistency)
    readonly property color bgDeep: "#0A0A0C"
    readonly property color bgSurface: "#141419"
    readonly property color accentPrimary: "#E8A54B"
    readonly property color textPrimary: "#F5F5F0"
    readonly property color textSecondary: "#8B8B99"
    
    width: 240
    color: bgDeep
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 32
        
        // LOGO / TITLE
        ColumnLayout {
            spacing: -4
            Text {
                text: "COMIX"
                font.family: "Segoe UI"
                font.pixelSize: 28
                font.weight: Font.Black
                color: accentPrimary
                font.letterSpacing: 2
            }
            Text {
                text: "DOWNLOADER"
                font.family: "Segoe UI"
                font.pixelSize: 10
                font.weight: Font.Bold
                color: textSecondary
                font.letterSpacing: 4
            }
        }
        
        // NAVIGATION ITEMS
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8
            
            NavButton {
                icon: "🔍"
                label: "Browse Manga"
                isActive: root.activeTab === 0
                onClicked: { root.activeTab = 0; root.browseClicked() }
            }
            
            NavButton {
                icon: "📥"
                label: "Downloads"
                isActive: root.activeTab === 1
                onClicked: { root.activeTab = 1; root.downloadsClicked() }
            }
        }
        
        Item { Layout.fillHeight: true }
        
        // SETTINGS BUTTON AT BOTTOM
        NavButton {
            icon: "⚙️"
            label: "Settings"
            onClicked: root.settingsClicked()
        }
    }
    
    // ═══════════════════════════════════════════════════════════════
    // NAVIGATION BUTTON COMPONENT
    // ═══════════════════════════════════════════════════════════════
    component NavButton: Rectangle {
        id: btn
        property string icon: ""
        property string label: ""
        property bool isActive: false
        signal clicked()
        
        Layout.fillWidth: true
        Layout.preferredHeight: 48
        radius: 8
        color: isActive ? "#1C1C24" : (mouseArea.containsMouse ? "#141419" : "transparent")
        
        Behavior on color { ColorAnimation { duration: 150 } }
        
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            spacing: 12
            
            Text {
                text: btn.icon
                font.pixelSize: 18
                opacity: btn.isActive ? 1.0 : 0.7
            }
            
            Text {
                text: btn.label
                font.family: "Segoe UI"
                font.pixelSize: 14
                font.weight: btn.isActive ? Font.DemiBold : Font.Normal
                color: btn.isActive ? textPrimary : textSecondary
            }
        }
        
        // Indicator for active tab
        Rectangle {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            width: 4; height: 24
            radius: 2
            color: accentPrimary
            visible: btn.isActive
        }
        
        MouseArea {
            id: mouseArea
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: btn.clicked()
        }
    }
}
