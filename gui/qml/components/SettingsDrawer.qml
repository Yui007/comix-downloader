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
            spacing: 24
            
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
            
            // Settings Content (no ScrollView to avoid scrollbar issues)
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 20
                
                // Output Format
                SettingItem {
                    label: "Output Format"
                    RowLayout {
                        spacing: 8
                        Repeater {
                            model: ["images", "pdf", "cbz"]
                            Rectangle {
                                width: 75; height: 36; radius: 8
                                color: SettingsBridge.outputFormat === modelData ? accentPrimary : bgElevated
                                border.color: SettingsBridge.outputFormat === modelData ? accentPrimary : textTertiary
                                border.width: 1
                                
                                Text { 
                                    anchors.centerIn: parent
                                    text: modelData.toUpperCase()
                                    font.pixelSize: 12
                                    font.weight: Font.Bold
                                    color: SettingsBridge.outputFormat === modelData ? bgDeep : textSecondary 
                                }
                                MouseArea { 
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: SettingsBridge.setValue("output_format", modelData) 
                                }
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
                        width: 220; height: 40; radius: 8
                        color: bgElevated
                        border.color: textTertiary; border.width: 1
                        
                        TextInput {
                            anchors.fill: parent
                            anchors.leftMargin: 12; anchors.rightMargin: 12
                            verticalAlignment: Text.AlignVCenter
                            text: SettingsBridge.downloadPath
                            color: textPrimary
                            font.pixelSize: 14
                            clip: true
                            selectByMouse: true
                            onEditingFinished: SettingsBridge.setValue("download_path", text)
                        }
                    }
                }
                
                // Max Chapter Workers
                SettingItem {
                    label: "Max Chapter Workers (1-10)"
                    NumberInput {
                        value: SettingsBridge.maxChapterWorkers
                        minValue: 1; maxValue: 10
                        onValueChanged: SettingsBridge.setValue("max_chapter_workers", value)
                    }
                }
                
                // Max Image Workers
                SettingItem {
                    label: "Max Image Workers (1-20)"
                    NumberInput {
                        value: SettingsBridge.maxImageWorkers
                        minValue: 1; maxValue: 20
                        onValueChanged: SettingsBridge.setValue("max_image_workers", value)
                    }
                }
                
                Item { Layout.fillHeight: true }
                
                // Reset Button
                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 180; height: 44; radius: 8
                    color: resetArea.containsMouse ? error : "transparent"
                    border.color: error; border.width: 2
                    
                    Text { 
                        anchors.centerIn: parent
                        text: "Reset to Defaults"
                        font.pixelSize: 14
                        font.weight: Font.DemiBold
                        color: resetArea.containsMouse ? textPrimary : error 
                    }
                    
                    MouseArea {
                        id: resetArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: SettingsBridge.resetToDefaults()
                    }
                }
            }
        }
    }
    
    // ═══════════════════════════════════════════════════════════════
    // SETTING ITEM COMPONENT
    // ═══════════════════════════════════════════════════════════════
    component SettingItem: ColumnLayout {
        property string label: ""
        default property alias content: contentArea.children
        
        Layout.fillWidth: true
        spacing: 8
        
        Text { 
            text: label
            font.pixelSize: 13
            font.weight: Font.Medium
            color: textSecondary 
        }
        Row { id: contentArea; spacing: 8 }
    }
    
    // ═══════════════════════════════════════════════════════════════
    // TOGGLE SWITCH COMPONENT
    // ═══════════════════════════════════════════════════════════════
    component ToggleSwitch: Rectangle {
        property bool checked: false
        signal toggled()
        
        width: 52; height: 28; radius: 14
        color: checked ? accentPrimary : bgElevated
        border.color: checked ? accentPrimary : textTertiary; border.width: 1
        
        Behavior on color { ColorAnimation { duration: 150 } }
        
        Rectangle {
            width: 22; height: 22; radius: 11
            anchors.verticalCenter: parent.verticalCenter
            x: parent.checked ? parent.width - width - 3 : 3
            color: textPrimary
            
            Behavior on x { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
        }
        
        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: { parent.checked = !parent.checked; parent.toggled() }
        }
    }
    
    // ═══════════════════════════════════════════════════════════════
    // NUMBER INPUT COMPONENT (custom spinbox replacement)
    // ═══════════════════════════════════════════════════════════════
    component NumberInput: Rectangle {
        property int value: 0
        property int minValue: 0
        property int maxValue: 100
        
        width: 120; height: 40; radius: 8
        color: bgElevated
        border.color: textTertiary; border.width: 1
        
        RowLayout {
            anchors.fill: parent
            anchors.margins: 4
            spacing: 0
            
            // Minus button
            Rectangle {
                Layout.preferredWidth: 32; Layout.fillHeight: true
                radius: 6
                color: minusArea.containsMouse ? bgCard : "transparent"
                
                Text {
                    anchors.centerIn: parent
                    text: "−"
                    font.pixelSize: 18
                    font.weight: Font.Bold
                    color: value > minValue ? accentPrimary : textTertiary
                }
                
                MouseArea {
                    id: minusArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: if (value > minValue) value--
                }
            }
            
            // Value display
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                
                Text {
                    anchors.centerIn: parent
                    text: value
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                    color: textPrimary
                }
            }
            
            // Plus button
            Rectangle {
                Layout.preferredWidth: 32; Layout.fillHeight: true
                radius: 6
                color: plusArea.containsMouse ? bgCard : "transparent"
                
                Text {
                    anchors.centerIn: parent
                    text: "+"
                    font.pixelSize: 18
                    font.weight: Font.Bold
                    color: value < maxValue ? accentPrimary : textTertiary
                }
                
                MouseArea {
                    id: plusArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: if (value < maxValue) value++
                }
            }
        }
    }
}
