import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "components"
import "views"

ApplicationWindow {
    id: root
    
    readonly property color bgDeep: "#0A0A0C"
    readonly property color bgSurface: "#141419"
    
    width: 1100
    height: 750
    minimumWidth: 900
    minimumHeight: 650
    visible: true
    title: "Comix Downloader"
    color: bgDeep
    
    flags: Qt.FramelessWindowHint | Qt.Window
    
    property point dragStart: Qt.point(0, 0)
    
    RowLayout {
        anchors.fill: parent
        spacing: 0
        
        // SIDEBAR NAVIGATION
        SideBar {
            id: sideBar
            Layout.fillHeight: true
            Layout.preferredWidth: 240
            
            onBrowseClicked: viewStack.currentIndex = 0
            onDownloadsClicked: viewStack.currentIndex = 1
            onSettingsClicked: settingsDrawer.isOpen = true
        }
        
        // MAIN CONTENT AREA
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0
            
            // TITLE BAR (Modified for the new layout)
            TitleBar {
                Layout.fillWidth: true
                Layout.preferredHeight: 40
                
                onMinimizeClicked: root.showMinimized()
                onMaximizeClicked: root.visibility === Window.Maximized ? root.showNormal() : root.showMaximized()
                onCloseClicked: Qt.quit()
                onDragStarted: (pos) => root.dragStart = pos
                onDragMoved: (pos) => { root.x += pos.x - root.dragStart.x; root.y += pos.y - root.dragStart.y }
            }
            
            // VIEW STACK
            StackLayout {
                id: viewStack
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: 0
                
                BrowseView {
                    id: browseView
                }
                
                DownloadsView {
                    id: downloadsView
                }
            }
        }
    }
    
    // SETTINGS DRAWER (Global overlay)
    SettingsDrawer {
        id: settingsDrawer
        anchors.fill: parent
        isOpen: false
    }
    
    // CONNECTIONS TO PYTHON BRIDGES
    Connections {
        target: MangaBridge
        function onMangaLoaded(info) { browseView.getMangaCard().manga = info }
        function onChaptersLoaded(chapters) { browseView.getChapterList().setChapters(chapters) }
        function onErrorOccurred(error) { console.log("Manga Error:", error) }
    }
    
    Connections {
        target: DownloadBridge
        function onDownloadStarted() { 
            // Auto switch to downloads tab
            sideBar.activeTab = 1
            viewStack.currentIndex = 1
            downloadsView.getProgressPanel().reset() 
        }
        function onOverallProgress(current, total) { 
            downloadsView.getProgressPanel().updateProgress(current, total) 
        }
        function onChapterProgress(name, current, total) { 
            downloadsView.getProgressPanel().updateChapterProgress(name, current, total) 
        }
        function onChapterComplete(name, success, message) { 
            downloadsView.getProgressPanel().setChapterStatus(name, success, message) 
        }
        function onDownloadFinished(successful, failed) { 
            downloadsView.getProgressPanel().setFinished(successful, failed) 
        }
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
