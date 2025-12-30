import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    
    property bool isOpen: false
    
    // Theme colors
    readonly property color bgDeep: "#0A0A0C"
    readonly property color bgSurface: "#141419"
    readonly property color bgCard: "#1C1C24"
    readonly property color bgElevated: "#252530"
    readonly property color accentPrimary: "#E8A54B"
    readonly property color textPrimary: "#F5F5F0"
    readonly property color textSecondary: "#8B8B99"
    readonly property color textTertiary: "#5C5C66"
    readonly property color error: "#E57373"
    readonly property color success: "#7CB342"
    
    visible: isOpen
    color: Qt.rgba(0, 0, 0, 0.7)
    
    // Click outside to close
    MouseArea {
        anchors.fill: parent
        onClicked: root.isOpen = false
    }
    
    // Settings Panel
    Rectangle {
        id: panel
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 380
        color: bgSurface
        
        x: root.isOpen ? 0 : width
        Behavior on x { NumberAnimation { duration: 300; easing.type: Easing.OutCubic } }
        
        MouseArea { anchors.fill: parent } // Prevent click-through
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 24
            spacing: 20
            
            // Header
            RowLayout {
                Layout.fillWidth: true
                
                Text {
                    text: "⚙️ SETTINGS"
                    font.family: "Segoe UI"
                    font.pixelSize: 22
                    font.weight: Font.Bold
                    color: textPrimary
                }
                
                Item { Layout.fillWidth: true }
                
                Rectangle {
                    width: 32; height: 32; radius: 6
                    color: closeArea.containsMouse ? bgElevated : "transparent"
                    Text { anchors.centerIn: parent; text: "×"; font.pixelSize: 18; font.weight: Font.Bold; color: textSecondary }
                    MouseArea { id: closeArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.isOpen = false }
                }
            }
            
            // Settings Items
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                
                ColumnLayout {
                    width: parent.width
                    spacing: 16
                    
                    // Output Format
                    SettingItem {
                        label: "Output Format"
                        RowLayout {
                            spacing: 8
                            Repeater {
                                model: ["images", "pdf", "cbz"]
                                Rectangle {
                                    width: 70; height: 32; radius: 6
                                    color: SettingsBridge.outputFormat === modelData ? accentPrimary : bgElevated
                                    border.color: textTertiary; border.width: SettingsBridge.outputFormat === modelData ? 0 : 1
                                    Text { anchors.centerIn: parent; text: modelData.toUpperCase(); font.pixelSize: 12; font.weight: Font.Bold
                                           color: SettingsBridge.outputFormat === modelData ? bgDeep : textSecondary }
                                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                        onClicked: SettingsBridge.setValue("output_format", modelData) }
                                }
                            }
                        }
                    }
                    
                    // Keep Images
                    SettingItem {
                        label: "Keep Images After Conversion"
                        ToggleSwitch {
                            checked: SettingsBridge.keepImages
                            onToggled: SettingsBridge.setValue("keep_images", checked)
                        }
                    }
                    
                    // Enable Logs
                    SettingItem {
                        label: "Enable Debug Logs"
                        ToggleSwitch {
                            checked: SettingsBridge.getValue("enable_logs") || false
                            onToggled: SettingsBridge.setValue("enable_logs", checked)
                        }
                    }
                    
                    // Download Path
                    SettingItem {
                        label: "Download Path"
                        Rectangle {
                            width: 200; height: 36; radius: 6
                            color: bgElevated; border.color: textTertiary; border.width: 1
                            TextInput {
                                anchors.fill: parent; anchors.margins: 8
                                text: SettingsBridge.downloadPath
                                color: textPrimary; font.pixelSize: 14
                                clip: true
                                onTextChanged: if (text !== SettingsBridge.downloadPath) SettingsBridge.setValue("download_path", text)
                            }
                        }
                    }
                    
                    // Max Chapter Workers
                    SettingItem {
                        label: "Max Chapter Workers (1-10)"
                        SpinBox {
                            id: chapterWorkers
                            from: 1; to: 10
                            value: SettingsBridge.maxChapterWorkers
                            onValueModified: SettingsBridge.setValue("max_chapter_workers", value)
                            
                            background: Rectangle { color: bgElevated; radius: 6; border.color: textTertiary; border.width: 1 }
                            contentItem: Text { text: chapterWorkers.value; font.pixelSize: 14; color: textPrimary; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        }
                    }
                    
                    // Max Image Workers
                    SettingItem {
                        label: "Max Image Workers (1-20)"
                        SpinBox {
                            id: imageWorkers
                            from: 1; to: 20
                            value: SettingsBridge.maxImageWorkers
                            onValueModified: SettingsBridge.setValue("max_image_workers", value)
                            
                            background: Rectangle { color: bgElevated; radius: 6; border.color: textTertiary; border.width: 1 }
                            contentItem: Text { text: imageWorkers.value; font.pixelSize: 14; color: textPrimary; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        }
                    }
                    
                    // Chapters Display Limit
                    SettingItem {
                        label: "Chapters Display Limit (0=all)"
                        SpinBox {
                            id: displayLimit
                            from: 0; to: 500
                            value: SettingsBridge.getValue("chapters_display_limit") || 20
                            onValueModified: SettingsBridge.setValue("chapters_display_limit", value)
                            
                            background: Rectangle { color: bgElevated; radius: 6; border.color: textTertiary; border.width: 1 }
                            contentItem: Text { text: displayLimit.value; font.pixelSize: 14; color: textPrimary; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        }
                    }
                    
                    Item { height: 20 }
                    
                    // Reset Button
                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        width: 160; height: 40; radius: 8
                        color: resetArea.containsMouse ? error : bgElevated
                        border.color: error; border.width: 1
                        
                        Text { anchors.centerIn: parent; text: "Reset to Defaults"; font.pixelSize: 13; font.weight: Font.DemiBold
                               color: resetArea.containsMouse ? textPrimary : error }
                        
                        MouseArea {
                            id: resetArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: SettingsBridge.resetToDefaults()
                        }
                    }
                }
            }
        }
    }
    
    // Setting Item Component
    component SettingItem: ColumnLayout {
        property string label: ""
        default property alias content: contentArea.children
        
        Layout.fillWidth: true
        spacing: 6
        
        Text { text: label; font.pixelSize: 13; color: textSecondary }
        Row { id: contentArea; spacing: 8 }
    }
    
    // Toggle Switch Component
    component ToggleSwitch: Rectangle {
        property bool checked: false
        signal toggled()
        
        width: 50; height: 26; radius: 13
        color: checked ? accentPrimary : bgElevated
        border.color: checked ? accentPrimary : textTertiary; border.width: 1
        
        Behavior on color { ColorAnimation { duration: 150 } }
        
        Rectangle {
            width: 20; height: 20; radius: 10
            anchors.verticalCenter: parent.verticalCenter
            x: parent.checked ? parent.width - width - 3 : 3
            color: textPrimary
            
            Behavior on x { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
        }
        
        MouseArea {
            anchors.fill: parent; cursorShape: Qt.PointingHandCursor
            onClicked: { parent.checked = !parent.checked; parent.toggled() }
        }
    }
}
