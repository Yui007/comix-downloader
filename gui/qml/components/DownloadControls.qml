import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    
    property var scanlators: ["Any"]
    property string scanlator: "Any"
    
    signal downloadClicked()
    signal settingsClicked()
    
    // Theme colors
    readonly property color bgCard: "#1C1C24"
    readonly property color bgElevated: "#252530"
    readonly property color accentPrimary: "#E8A54B"
    readonly property color accentGradientEnd: "#D4873A"
    readonly property color textPrimary: "#F5F5F0"
    readonly property color textSecondary: "#8B8B99"
    readonly property color textTertiary: "#5C5C66"
    readonly property color bgDeep: "#0A0A0C"
    
    color: bgCard
    radius: 12
    
    RowLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 24
        
        // SETTINGS BUTTON
        Rectangle {
            Layout.preferredWidth: 120
            Layout.preferredHeight: 44
            radius: 8
            color: settingsArea.containsMouse ? bgElevated : "transparent"
            border.color: textTertiary; border.width: 1
            
            Behavior on color { ColorAnimation { duration: 150 } }
            
            RowLayout {
                anchors.centerIn: parent
                spacing: 8
                Text { text: "⚙️"; font.pixelSize: 16 }
                Text { text: "Settings"; font.family: "Segoe UI"; font.pixelSize: 14; color: textSecondary }
            }
            
            MouseArea {
                id: settingsArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.settingsClicked()
            }
        }
        
        // SCANLATOR SELECTOR
        ColumnLayout {
            spacing: 4
            Text { text: "Scanlator Preference"; font.pixelSize: 12; color: textTertiary }
            ComboBox {
                id: scanlatorCombo
                model: root.scanlators
                implicitWidth: 180; implicitHeight: 36
                onCurrentTextChanged: root.scanlator = currentText
                
                background: Rectangle { color: bgElevated; radius: 6; border.color: textTertiary; border.width: 1 }
                contentItem: Text { text: scanlatorCombo.currentText; font.pixelSize: 14; color: textPrimary; verticalAlignment: Text.AlignVCenter; leftPadding: 8; elide: Text.ElideRight }
            }
        }
        
        Item { Layout.fillWidth: true }
        
        // DOWNLOAD BUTTON
        Rectangle {
            Layout.preferredWidth: 220
            Layout.preferredHeight: 48
            radius: 12
            
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: accentPrimary }
                GradientStop { position: 1.0; color: accentGradientEnd }
            }
            
            scale: downloadArea.pressed ? 0.97 : (downloadArea.containsMouse ? 1.02 : 1.0)
            Behavior on scale { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
            
            RowLayout {
                anchors.centerIn: parent
                spacing: 8
                Text { text: "▶"; font.pixelSize: 14; color: bgDeep }
                Text { text: "DOWNLOAD CHAPTERS"; font.family: "Segoe UI"; font.pixelSize: 12; font.weight: Font.Bold; color: bgDeep; font.letterSpacing: 1 }
            }
            
            MouseArea {
                id: downloadArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.downloadClicked()
            }
        }
    }
}
