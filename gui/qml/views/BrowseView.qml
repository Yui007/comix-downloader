import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

Item {
    id: browseView
    
    // Properties passed from main
    property var mangaCard: null
    property var chapterList: null
    property var downloadControls: null

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
                id: mangaCardComp
                Layout.preferredWidth: 280
                Layout.fillHeight: true
                visible: manga !== null
                manga: null
            }
            
            // CHAPTER LIST
            ChapterList {
                id: chapterListComp
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
        }
        
        // DOWNLOAD CONTROLS
        DownloadControls {
            id: downloadControlsComp
            Layout.fillWidth: true
            Layout.preferredHeight: 100
            scanlators: chapterListComp.getScanlators()
            onSettingsClicked: settingsDrawer.isOpen = true
            onFilterChanged: (filter) => chapterListComp.applyFilter(filter)
            onDownloadClicked: {
                var selected = chapterListComp.getSelectedChapters()
                DownloadBridge.startDownload(mangaCardComp.manga, selected, SettingsBridge.outputFormat, scanlatorPreference)
            }
        }
    }
    
    // Expose internal components to main.qml for connections
    function getMangaCard() { return mangaCardComp }
    function getChapterList() { return chapterListComp }
    function getDownloadControls() { return downloadControlsComp }
}
