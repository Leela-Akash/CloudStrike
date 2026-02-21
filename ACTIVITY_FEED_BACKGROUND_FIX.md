# Recent Activity Panel - White Background Fix

## Problem
On some machines, the Recent Activity panel showed a white background when empty, breaking the dark theme consistency.

## Root Cause
Qt's QScrollArea and QWidget can inherit system default backgrounds on certain Windows configurations, overriding the global stylesheet.

## Solution
Hardcoded dark background colors directly on all nested widgets in the Recent Activity panel hierarchy.

## Files Modified

### 1. **activity_feed.py**
Added inline stylesheet to ActivityFeed widget in `__init__()`:

```python
self.setStyleSheet("""
    QWidget {
        background-color: #0f0a08;
        color: #e8e6e3;
    }
    QScrollArea {
        background-color: #0f0a08;
        border: none;
    }
    QScrollBar:vertical {
        background: #0a0705;
        width: 6px;
    }
    QScrollBar::handle:vertical {
        background: #2a1f1a;
        border-radius: 3px;
    }
""")
```

### 2. **cloudstrike_ui.py**
Added explicit background styling to scroll area and viewport in `create_right_panel()`:

```python
scroll.setStyleSheet("background-color: #0f0a08; border: none;")
scroll.viewport().setStyleSheet("background-color: #0f0a08;")
```

## Widget Hierarchy Fixed
```
QScrollArea (scroll)
├── background-color: #0f0a08 ✓
├── viewport()
│   └── background-color: #0f0a08 ✓
└── ActivityFeed (self.activity_feed)
    └── background-color: #0f0a08 ✓
```

## Testing
- [x] Empty state (no scan data) - dark background
- [x] Populated state (after scan) - dark background
- [x] Scrolling behavior - dark scrollbar
- [x] Windows 10 - consistent dark theme
- [x] Windows 11 - consistent dark theme

## Result
✅ Recent Activity panel now maintains consistent dark background (#0f0a08) across all Windows configurations, even when empty.
