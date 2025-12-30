import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    
    property var manga: null
    
    // Theme colors
    readonly property color bgCard: "#1C1C24"
    readonly property color bgElevated: "#252530"
    readonly property color accentPrimary: "#E8A54B"
    readonly property color textPrimary: "#F5F5F0"
    readonly property color textSecondary: "#8B8B99"
    readonly property color textTertiary: "#5C5C66"
    readonly property color success: "#7CB342"
    
    color: bgCard
    radius: 12
    
    // Fade-in animation
    opacity: manga ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 16
        
        // COVER IMAGE
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 200
            color: bgElevated
            radius: 12
            clip: true
            
            Image {
                id: coverImage
                anchors.fill: parent
                source: manga ? manga.poster_url : ""
                fillMode: Image.PreserveAspectCrop
                
                opacity: status === Image.Ready ? 1 : 0
                scale: status === Image.Ready ? 1 : 0.95
                
                Behavior on opacity { NumberAnimation { duration: 400 } }
                Behavior on scale { NumberAnimation { duration: 400; easing.type: Easing.OutBack } }
            }
            
            Text {
                anchors.centerIn: parent
                text: "📖"
                font.pixelSize: 48
                opacity: coverImage.status !== Image.Ready ? 0.3 : 0
            }
        }
        
        // TITLE
        Text {
            Layout.fillWidth: true
            text: manga ? manga.title : ""
            font.family: "Segoe UI"
            font.pixelSize: 16
            font.weight: Font.DemiBold
            color: textPrimary
            wrapMode: Text.WordWrap
            maximumLineCount: 2
            elide: Text.ElideRight
        }
        
        // METADATA
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            
            // Type
            RowLayout {
                Text { text: "Type"; font.pixelSize: 12; color: textTertiary }
                Text { text: manga ? manga.manga_type : ""; font.pixelSize: 12; color: textSecondary; Layout.fillWidth: true }
            }
            
            // Status
            RowLayout {
                Text { text: "Status"; font.pixelSize: 12; color: textTertiary }
                Text { 
                    text: manga ? manga.status : ""
                    font.pixelSize: 12
                    color: manga && manga.status === "releasing" ? success : textSecondary
                    Layout.fillWidth: true
                }
            }
            
            // Rating
            RowLayout {
                spacing: 8
                Text { text: "Rating"; font.pixelSize: 12; color: textTertiary }
                Row {
                    spacing: 2
                    Repeater {
                        model: 5
                        Text {
                            text: "★"
                            font.pixelSize: 14
                            color: index < Math.round(manga ? manga.rated_avg : 0) ? accentPrimary : textTertiary
                        }
                    }
                }
                Text { text: manga ? manga.rated_avg.toFixed(1) : "0.0"; font.pixelSize: 12; color: textSecondary }
            }
            
            // Followers
            RowLayout {
                Text { text: "Followers"; font.pixelSize: 12; color: textTertiary }
                Text { text: manga ? (manga.follows_total ? manga.follows_total.toLocaleString() : "0") : "0"; font.pixelSize: 12; color: textSecondary }
            }
        }
        
        Item { Layout.fillHeight: true }
    }
}
