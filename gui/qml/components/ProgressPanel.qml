import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    
    property string currentChapter: ""
    property int completedChapters: 0
    property int totalChapters: 0
    property bool isFinished: false
    property int successCount: 0
    property int failCount: 0
    
    // Theme colors
    readonly property color bgCard: "#1C1C24"
    readonly property color bgElevated: "#252530"
    readonly property color accentPrimary: "#E8A54B"
    readonly property color accentHighlight: "#FFD93D"
    readonly property color textPrimary: "#F5F5F0"
    readonly property color textSecondary: "#8B8B99"
    readonly property color success: "#7CB342"
    
    color: bgCard
    radius: 12
    
    function reset() {
        currentChapter = ""; completedChapters = 0; totalChapters = 0
        isFinished = false; successCount = 0; failCount = 0
    }
    
    function updateProgress(completed, total) {
        completedChapters = completed; totalChapters = total
    }
    
    function setChapterStatus(name, s, message) {
        currentChapter = name
        if (s) successCount++; else failCount++
    }
    
    function setFinished(successful, failed) {
        isFinished = true; successCount = successful; failCount = failed
    }
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 8
        
        // HEADER
        RowLayout {
            Layout.fillWidth: true
            Text {
                text: isFinished ? "DOWNLOAD COMPLETE" : "DOWNLOADING"
                font.family: "Segoe UI"; font.pixelSize: 18; font.weight: Font.DemiBold
                color: isFinished ? success : textPrimary
            }
            Item { Layout.fillWidth: true }
            Text {
                text: isFinished 
                    ? "✓ " + successCount + " succeeded" + (failCount > 0 ? ", " + failCount + " failed" : "")
                    : completedChapters + "/" + totalChapters + " chapters"
                font.pixelSize: 12
                color: isFinished ? success : textSecondary
            }
        }
        
        // CURRENT CHAPTER
        Text {
            text: currentChapter
            font.pixelSize: 14
            color: textSecondary
            elide: Text.ElideRight
            Layout.fillWidth: true
            visible: !isFinished
        }
        
        // PROGRESS BAR
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 12
            color: bgElevated
            radius: 6
            
            Rectangle {
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: totalChapters > 0 ? parent.width * (completedChapters / totalChapters) : 0
                radius: 6
                
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: isFinished ? success : accentPrimary }
                    GradientStop { position: 1.0; color: isFinished ? "#8BC34A" : accentHighlight }
                }
                
                Behavior on width { NumberAnimation { duration: 250; easing.type: Easing.OutCubic } }
            }
        }
        
        // COMPLETION MESSAGE
        Text {
            text: "🎉 All chapters downloaded successfully!"
            font.pixelSize: 14
            color: success
            visible: isFinished && failCount === 0
            opacity: isFinished ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: 400 } }
        }
    }
}
