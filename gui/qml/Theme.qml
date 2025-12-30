pragma Singleton
import QtQuick

QtObject {
    // ═══════════════════════════════════════════════════════════════
    // COLOR PALETTE: "Warm Midnight"
    // ═══════════════════════════════════════════════════════════════
    
    // Backgrounds
    readonly property color bgDeep: "#0A0A0C"
    readonly property color bgSurface: "#141419"
    readonly property color bgCard: "#1C1C24"
    readonly property color bgElevated: "#252530"
    
    // Accents
    readonly property color accentPrimary: "#E8A54B"      // Warm Amber
    readonly property color accentSecondary: "#4ECDC4"    // Muted Teal
    readonly property color accentHighlight: "#FFD93D"    // Soft Gold
    
    // Text
    readonly property color textPrimary: "#F5F5F0"
    readonly property color textSecondary: "#8B8B99"
    readonly property color textTertiary: "#5C5C66"
    
    // Status
    readonly property color success: "#7CB342"
    readonly property color error: "#E57373"
    readonly property color warning: "#FFB74D"
    readonly property color info: "#64B5F6"
    
    // ═══════════════════════════════════════════════════════════════
    // TYPOGRAPHY
    // ═══════════════════════════════════════════════════════════════
    
    readonly property string fontDisplay: "Playfair Display"
    readonly property string fontHeading: "DM Sans"
    readonly property string fontBody: "Source Sans 3"
    readonly property string fontMono: "JetBrains Mono"
    
    // Font sizes
    readonly property int fontSizeLogo: 28
    readonly property int fontSizeTitle: 22
    readonly property int fontSizeSection: 18
    readonly property int fontSizeCard: 16
    readonly property int fontSizeBody: 14
    readonly property int fontSizeCaption: 12
    readonly property int fontSizeMicro: 10
    
    // ═══════════════════════════════════════════════════════════════
    // SPACING & SIZING
    // ═══════════════════════════════════════════════════════════════
    
    readonly property int spacingXs: 4
    readonly property int spacingSm: 8
    readonly property int spacingMd: 16
    readonly property int spacingLg: 24
    readonly property int spacingXl: 32
    
    readonly property int radiusSm: 6
    readonly property int radiusMd: 12
    readonly property int radiusLg: 16
    
    readonly property int titleBarHeight: 40
    
    // ═══════════════════════════════════════════════════════════════
    // ANIMATION DURATIONS
    // ═══════════════════════════════════════════════════════════════
    
    readonly property int animFast: 150
    readonly property int animNormal: 250
    readonly property int animSlow: 400
}
