import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "components"

ApplicationWindow {
    id: root
    
    // Theme colors
    readonly property color bgDeep: "#0A0A0C"
    readonly property color bgSurface: "#141419"
    
    width: 1000
    height: 700
    minimumWidth: 800
    minimumHeight: 600
    visible: true
    title: "Comix Downloader"
    color: bgDeep
    
    flags: Qt.FramelessWindowHint | Qt.Window
    
    property point dragStart: Qt.point(0, 0)
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        
        // TITLE BAR
        TitleBar {
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            
            onMinimizeClicked: root.showMinimized()
            onMaximizeClicked: root.visibility === Window.Maximized ? root.showNormal() : root.showMaximized()
            onCloseClicked: Qt.quit()
            onDragStarted: (pos) => root.dragStart = pos
            onDragMoved: (pos) => { root.x += pos.x - root.dragStart.x; root.y += pos.y - root.dragStart.y }
        }
        
        // MAIN CONTENT
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: bgSurface
            
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 16
                
                // URL INPUT
                UrlInput {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    onFetchRequested: (url) => MangaBridge.fetchManga(url)
                }
                
                // CONTENT AREA
                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 16
                    
                    // MANGA CARD
                    MangaCard {
                        id: mangaCard
                        Layout.preferredWidth: 280
                        Layout.fillHeight: true
                        visible: manga !== null
                        manga: null
                    }
                    
                    // CHAPTER LIST
                    ChapterList {
                        id: chapterList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        chapters: []
                    }
                }
                
                // DOWNLOAD CONTROLS
                DownloadControls {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 100
                    scanlators: chapterList.getScanlators()
                    onSettingsClicked: settingsDrawer.isOpen = true
                    onDownloadClicked: {
                        var selected = chapterList.getSelectedChapters()
                        DownloadBridge.startDownload(mangaCard.manga, selected, SettingsBridge.outputFormat, scanlator)
                    }
                }
                
                // PROGRESS PANEL
                ProgressPanel {
                    id: progressPanel
                    Layout.fillWidth: true
                    Layout.preferredHeight: visible ? 120 : 0
                    visible: false
                }
            }
        }
    }
    
    // SETTINGS DRAWER (overlay)
    SettingsDrawer {
        id: settingsDrawer
        anchors.fill: parent
        isOpen: false
    }
    
    // CONNECTIONS TO PYTHON
    Connections {
        target: MangaBridge
        function onMangaLoaded(info) { mangaCard.manga = info; mangaCard.visible = true }
        function onChaptersLoaded(chapters) { chapterList.chapters = chapters }
        function onErrorOccurred(error) { console.log("Error:", error) }
    }
    
    Connections {
        target: DownloadBridge
        function onDownloadStarted() { progressPanel.visible = true; progressPanel.reset() }
        function onOverallProgress(current, total) { progressPanel.updateProgress(current, total) }
        function onChapterComplete(name, success, message) { progressPanel.setChapterStatus(name, success, message) }
        function onDownloadFinished(successful, failed) { progressPanel.setFinished(successful, failed) }
    }
    
    // STARTUP ANIMATION
    Component.onCompleted: { opacity = 0; startupAnimation.start() }
    
    PropertyAnimation {
        id: startupAnimation
        target: root
        property: "opacity"
        from: 0; to: 1
        duration: 300
        easing.type: Easing.OutCubic
    }
}
