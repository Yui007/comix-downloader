import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    
    property var chapters: []
    property var allChapters: []  // Store original list for filtering
    property string currentFilter: "Any"
    
    // Theme colors
    readonly property color bgCard: "#1C1C24"
    readonly property color bgElevated: "#252530"
    readonly property color accentPrimary: "#E8A54B"
    readonly property color textPrimary: "#F5F5F0"
    readonly property color textSecondary: "#8B8B99"
    readonly property color textTertiary: "#5C5C66"
    
    color: bgCard
    radius: 12
    
    function setChapters(chapterList) {
        allChapters = chapterList
        applyFilter(currentFilter)
    }
    
    function applyFilter(filter) {
        currentFilter = filter
        if (filter === "Any" || !filter) {
            chapters = allChapters.slice()
        } else {
            var filtered = []
            for (var i = 0; i < allChapters.length; i++) {
                if (allChapters[i].group_name === filter) {
                    filtered.push(allChapters[i])
                }
            }
            chapters = filtered
        }
    }
    
    function getSelectedChapters() {
        var selected = []
        for (var i = 0; i < chapters.length; i++) {
            if (chapters[i].selected) selected.push(chapters[i])
        }
        return selected
    }
    
    function getScanlators() {
        var scanlators = new Set()
        for (var i = 0; i < allChapters.length; i++) {
            if (allChapters[i].group_name && allChapters[i].group_name !== "Unknown") {
                scanlators.add(allChapters[i].group_name)
            }
        }
        var result = ["Any"]
        scanlators.forEach(function(s) { result.push(s) })
        return result
    }
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 8
        
        // HEADER
        RowLayout {
            Layout.fillWidth: true
            
            Text {
                text: "CHAPTERS"
                font.family: "Segoe UI"
                font.pixelSize: 18
                font.weight: Font.DemiBold
                color: textPrimary
                
                Rectangle {
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: -2
                    width: parent.width
                    height: 2
                    color: accentPrimary
                    opacity: 0.5
                    radius: 1
                }
            }
            
            Item { Layout.fillWidth: true }
            
            // Show filtered / total count
            Text {
                text: {
                    if (currentFilter !== "Any") {
                        return chapters.length + " shown (of " + allChapters.length + ")"
                    }
                    return allChapters.length + " available"
                }
                font.pixelSize: 12
                color: currentFilter !== "Any" ? accentPrimary : textTertiary
            }
        }
        
        // CHAPTER LIST
        ListView {
            id: listView
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: root.chapters
            clip: true
            spacing: 4
            
            ScrollBar.vertical: ScrollBar { 
                policy: ScrollBar.AsNeeded
                
                background: Rectangle {
                    implicitWidth: 8
                    color: bgElevated
                    radius: 4
                }
                
                contentItem: Rectangle {
                    implicitWidth: 8
                    radius: 4
                    color: parent.pressed ? accentPrimary : (parent.hovered ? Qt.lighter(accentPrimary, 1.3) : textTertiary)
                    
                    Behavior on color { ColorAnimation { duration: 150 } }
                }
            }
            
            delegate: ChapterDelegate {
                id: chapterDelegate
                width: listView.width - 10
                chapter: modelData
                onToggled: {
                    var updated = chapterList.chapters.slice()
                    updated[index].selected = !updated[index].selected
                    chapterList.chapters = updated
                    
                    // Also update in allChapters
                    for (var j = 0; j < chapterList.allChapters.length; j++) {
                        if (chapterList.allChapters[j].chapter_id === modelData.chapter_id) {
                            chapterList.allChapters[j].selected = updated[index].selected
                            break
                        }
                    }
                }
                
                // Reference the parent ChapterList
                property var chapterList: root
            }
            
            Text {
                anchors.centerIn: parent
                text: currentFilter !== "Any" ? "No chapters from this scanlator" : "Enter a manga URL to see chapters"
                font.pixelSize: 14
                color: textTertiary
                visible: root.chapters.length === 0
            }
        }
        
        // SELECTION CONTROLS
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            
            Rectangle {
                implicitWidth: allText.width + 16
                implicitHeight: 28
                color: allArea.containsMouse ? bgElevated : "transparent"
                border.color: textTertiary; border.width: 1; radius: 6
                Text { id: allText; anchors.centerIn: parent; text: "Select All"; font.pixelSize: 12; color: textSecondary }
                MouseArea { id: allArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        var updated = root.chapters.slice()
                        for (var i = 0; i < updated.length; i++) {
                            updated[i].selected = true
                            // Also update in allChapters
                            for (var j = 0; j < root.allChapters.length; j++) {
                                if (root.allChapters[j].chapter_id === updated[i].chapter_id) {
                                    root.allChapters[j].selected = true
                                    break
                                }
                            }
                        }
                        root.chapters = updated
                    }
                }
            }
            
            Rectangle {
                implicitWidth: noneText.width + 16
                implicitHeight: 28
                color: noneArea.containsMouse ? bgElevated : "transparent"
                border.color: textTertiary; border.width: 1; radius: 6
                Text { id: noneText; anchors.centerIn: parent; text: "None"; font.pixelSize: 12; color: textSecondary }
                MouseArea { id: noneArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        var updated = root.chapters.slice()
                        for (var i = 0; i < updated.length; i++) {
                            updated[i].selected = false
                            // Also update in allChapters
                            for (var j = 0; j < root.allChapters.length; j++) {
                                if (root.allChapters[j].chapter_id === updated[i].chapter_id) {
                                    root.allChapters[j].selected = false
                                    break
                                }
                            }
                        }
                        root.chapters = updated
                    }
                }
            }
            
            Item { Layout.fillWidth: true }
            
            Text {
                text: getSelectedChapters().length + " selected"
                font.pixelSize: 12
                color: accentPrimary
            }
        }
    }
}
