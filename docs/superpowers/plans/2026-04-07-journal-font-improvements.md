# Journal & UI Font Size Improvements

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Increase font sizes in the Journal panel and other under-sized UI elements for better readability, without breaking layout or UX.

**Architecture:** Incremental font size bumps across 3 areas: Journal panel content, secondary UI screens (skip tutorial confirm, file dialog, dialogue history), and global styles (nav/roster). The Journal frame and viewport get a proportional size increase to accommodate larger text. All changes use existing `font_size()` function where already in use.

**Tech Stack:** Ren'Py (Python-based visual novel engine), `.rpy` screen language

---

## Summary of Changes

### Journal Panel (tutorial_system.rpy)
| Element | Current | New | Rationale |
|---------|---------|-----|-----------|
| Frame size | 720x720 | 780x740 | Accommodate larger text |
| Viewport | 590x480 | 650x500 | More readable area |
| Text xsize | 520 | 580 | Match wider viewport |
| Flavor text | 20 | 22 | Slightly more readable |
| Objective title | 32 | 34 | Modest bump for hierarchy |
| Objective description | 24 | 26 | Core readability improvement |
| Progress text | 22 | 24 | Match description hierarchy |
| Tutorial header | 24 | 26 | Match description level |
| Tutorial links | 22 | 24 | Easier to click/read |
| Tips | 18-20 | 20-22 | Floor raised to 20 minimum |
| Completion text | 20 | 22 | Consistent with flavor text |
| Mark complete buttons | 24 | 26 | Match new description size |
| Skip tutorial | 22 | 24 | Consistent |
| Victory text | 28 | 30 | Proportional bump |

### Other UI Elements (Priority 2)
| Element | File | Current | New |
|---------|------|---------|-----|
| Skip tutorial body | tutorial_system.rpy:1589 | 16 | 20 |
| Skip tutorial title | tutorial_system.rpy:1584 | 28 | 30 |
| File dialog metadata | file_save_system.rpy:327 | 16 | 18 |
| Dialogue history offset | screens.rpy:678 | 14 | 16 |

### Global Styles (Priority 3 - script.rpy)
| Style | Current | New | Notes |
|-------|---------|-----|-------|
| nav_button_text | 14 | 16 | Navigation buttons |
| roster_button_text | 14 | 16 | Worker roster names |
| roster_stats | 14 | 16 | Worker stats |
| roster_button | 14 | 16 | Roster button container |

---

### Task 1: Journal Panel — Frame & Viewport Resize

**Files:**
- Modify: `game/scripts/tutorial_system.rpy:1085-1107`

- [ ] **Step 1: Increase frame dimensions**

Change lines 1090-1091 from:
```renpy
        xsize 720  # Increased width
        ysize 720  # Increased height for more verticality
```
to:
```renpy
        xsize 780
        ysize 740
```

- [ ] **Step 2: Increase viewport dimensions**

Change lines 1102-1104 from:
```renpy
                ysize 480
                xsize 590
                xoffset 40
```
to:
```renpy
                ysize 500
                xsize 650
                xoffset 25
```

Note: xoffset reduced from 40 to 25 to keep content centered within wider frame (780 - 2*40 padding = 700 usable; 650 viewport + 25 offset = 675, leaving 25px for scrollbar).

- [ ] **Step 3: Verify in-game**

Launch the game, open the Journal panel, scroll through content. Confirm:
- Parchment background scales or tiles correctly
- Scrollbar is visible and not cut off
- Content doesn't overflow the frame
- Close button still positioned correctly at top-right

---

### Task 2: Journal Panel — Update All Text xsize Values

**Files:**
- Modify: `game/scripts/tutorial_system.rpy:1112-1548`

All `xsize 520` values within the journal viewport must become `xsize 580` to match the wider viewport. There are approximately 30+ occurrences.

- [ ] **Step 1: Replace all xsize 520 within journal_panel**

Use find-and-replace within the `screen journal_panel()` function (lines 1076-1565) to change every `xsize 520` to `xsize 580`.

Affected lines: 1112, 1119, 1124, 1144, 1150, 1161, 1172, 1183, 1195, 1201, 1213, 1219, 1231, 1246, 1261, 1270, 1284, 1292, 1305, 1314, 1327, 1336, 1349, 1358, 1371, 1380, 1408, 1423, 1442, 1460, 1472, 1488, 1500, 1514, 1526, 1542.

- [ ] **Step 2: Update victory text xsize**

Line 1549 — change `xsize 580` (already 580) to `xsize 620` since it uses a larger font and is outside the viewport's scrollable area... Actually, checking: this text IS inside the viewport. Keep at `xsize 580` for consistency.

No change needed here. Skip.

---

### Task 3: Journal Panel — Bump Font Sizes

**Files:**
- Modify: `game/scripts/tutorial_system.rpy:1076-1565`

- [ ] **Step 1: Flavor text 20 → 22**

Line 1113: change `size font_size(20)` to `size font_size(22)`

- [ ] **Step 2: Objective title 32 → 34**

Line 1121: change `size font_size(32)` to `size font_size(34)`

- [ ] **Step 3: Objective description 24 → 26**

Line 1126: change `size font_size(24)` to `size font_size(26)`

- [ ] **Step 4: Progress text 22 → 24**

Line 1134: change `size font_size(22)` to `size font_size(24)`

- [ ] **Step 5: All "Tutorial:" headers 24 → 26**

Lines 1142, 1159, 1170, 1181, 1193, 1211, 1229: change `size font_size(24)` to `size font_size(26)`

- [ ] **Step 6: All tutorial link buttons 22 → 24**

Lines 1146, 1152, 1163, 1174, 1185, 1197, 1203, 1215, 1221, 1233: change `text_size font_size(22)` to `text_size font_size(24)`

- [ ] **Step 7: Tips — raise floor to 20 minimum**

Line 1189: `font_size(18)` → `font_size(20)`
Line 1242: `font_size(18)` → `font_size(20)`
Line 1438: `font_size(18)` → `font_size(20)`
Lines 1207, 1225, 1237: already at `font_size(20)` → change to `font_size(22)`

- [ ] **Step 8: Completion instruction text 20 → 22**

Lines 1263, 1285, 1307, 1329, 1351, 1373, 1395: change `size font_size(20)` to `size font_size(22)`

- [ ] **Step 9: Mark complete buttons 24 → 26**

Lines 1248, 1272, 1294, 1316, 1338, 1360, 1382, 1410, 1425, 1444, 1462, 1474, 1490, 1502, 1516, 1528: change `text_size font_size(24)` to `text_size font_size(26)`

- [ ] **Step 10: Choice headers 24 → 26**

Line 1400 (`"Choose Your Gambit:"`): `size font_size(24)` → `size font_size(26)`
Line 1455 (`"Choose Your Path of Vengeance:"`): `size font_size(24)` → `size font_size(26)`

- [ ] **Step 11: Skip tutorial button 22 → 24**

Line 1543: `text_size font_size(22)` → `text_size font_size(24)`

- [ ] **Step 12: Victory text 28 → 30**

Line 1551: `size font_size(28)` → `size font_size(30)`

- [ ] **Step 13: Verify in-game**

Open Journal at various objectives (1-8, 9, 10-15, 16, post-tutorial). Confirm:
- Text is noticeably more readable
- No text overflows or overlaps
- Scrolling still works for longer objectives
- Font hierarchy preserved (title > description > progress > tips)

---

### Task 4: Skip Tutorial Confirm Dialog

**Files:**
- Modify: `game/scripts/tutorial_system.rpy:1566-1610`

- [ ] **Step 1: Bump skip tutorial dialog fonts**

Line 1584: change `size 28` to `size 30`
Line 1589: change `size 16` to `size 20`

- [ ] **Step 2: Increase dialog height to fit larger text**

Line 1575: change `ysize 300` to `ysize 320`

- [ ] **Step 3: Verify in-game**

Open Journal → click "Skip Tutorial" → confirm dialog appears readable and centered.

---

### Task 5: File Dialog & Dialogue History

**Files:**
- Modify: `game/scripts/file_save_system.rpy:327`
- Modify: `game/scripts/core/screens.rpy:678`

- [ ] **Step 1: File dialog metadata text**

Line 327 of `file_save_system.rpy`: change `size 16` to `size 18`

- [ ] **Step 2: Dialogue history offset indicator**

Line 678 of `screens.rpy`: change `size 14` to `size 16`

- [ ] **Step 3: Verify in-game**

- Save/load game → check file metadata text is readable
- Scroll through dialogue history → check offset indicator is visible but not intrusive

---

### Task 6: Global Navigation & Roster Styles

**Files:**
- Modify: `game/scripts/script.rpy:7275-7317`

- [ ] **Step 1: Bump nav_button_text**

Line 7278: change `size 14` to `size 16`

- [ ] **Step 2: Bump roster_button_text**

Line 7294: change `size 14` to `size 16`

- [ ] **Step 3: Bump roster_stats**

Line 7305: change `size 14` to `size 16`

- [ ] **Step 4: Bump roster_button**

Line 7316: change `size 14` to `size 16`

- [ ] **Step 5: Verify in-game**

Open Workers screen. Confirm:
- Navigation buttons still fit without wrapping
- Roster names and stats are more readable
- Layout doesn't break with the 2px increase
- Hover effects still work properly

---

### Task 7: Final Integration Test

- [ ] **Step 1: Full walkthrough**

Test the following screens in order:
1. Main menu → Workers screen (nav buttons, roster text)
2. Journal panel (all objective states if possible)
3. Skip Tutorial dialog
4. Save/Load dialog (file metadata)
5. Dialogue history navigation

- [ ] **Step 2: Test with large_font_mode enabled**

Enable `persistent.large_font_mode` and repeat the Journal check. With the new base sizes and 1.4x multiplier:
- Objective title: 34 * 1.4 = 47.6px — should still fit in 580px width
- Description: 26 * 1.4 = 36.4px — verify scrolling accommodates

- [ ] **Step 3: Commit**

```bash
git add game/scripts/tutorial_system.rpy game/scripts/file_save_system.rpy game/scripts/core/screens.rpy game/scripts/script.rpy
git commit -m "feat: improve font sizes in Journal panel and other UI elements

Bump Journal text by +2px across all tiers, widen frame to 780x740
and viewport to 650x500 to accommodate larger text.
Also increase nav/roster styles from 14→16, skip tutorial dialog
body 16→20, file dialog metadata 16→18, dialogue history 14→16."
```
