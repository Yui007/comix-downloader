import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    
    ListModel { id: chapterModel }
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
        chapterModel.clear()
        
        for (var i = 0; i < allChapters.length; i++) {
            var ch = allChapters[i]
            if (filter === "Any" || !filter || ch.group_name === filter) {
                chapterModel.append(ch)
            }
        }
    }
    
    function getSelectedChapters() {
        var selected = []
        for (var i = 0; i < allChapters.length; i++) {
            if (allChapters[i].selected) selected.push(allChapters[i])
        }
        return selected
    }
    
    function getScanlators() {
        var scanlators = new Set()
        for (var i = 0; i < allChapters.length; i++) {
            if (allChapters[i].group_name) {
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
            model: chapterModel
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
                chapter: ({
                    "chapter_id": model.chapter_id,
                    "number": model.number,
                    "title": model.title,
                    "group_name": model.group_name,
                    "selected": model.selected
                })
                onToggled: {
                    var isSelected = !model.selected
                    chapterModel.setProperty(index, "selected", isSelected)
                    
                    // Also update in allChapters reference
                    for (var j = 0; j < root.allChapters.length; j++) {
                        if (root.allChapters[j].chapter_id === model.chapter_id) {
                            root.allChapters[j].selected = isSelected
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
                visible: chapterModel.count === 0
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
                        for (var i = 0; i < chapterModel.count; i++) {
                            chapterModel.setProperty(i, "selected", true)
                        }
                        for (var j = 0; j < allChapters.length; j++) {
                            allChapters[j].selected = true
                        }
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
                        for (var i = 0; i < chapterModel.count; i++) {
                            chapterModel.setProperty(i, "selected", false)
                        }
                        for (var j = 0; j < allChapters.length; j++) {
                            allChapters[j].selected = false
                        }
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
