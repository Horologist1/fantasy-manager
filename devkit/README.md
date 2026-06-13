# ⚠️ Deprecated — use the web devkit instead

This folder holds the **old Python/Tkinter editor** (`fantasy_manager_editor_v6.py`
and the bundled `.exe`). It is **no longer maintained** and is kept only as a
temporary fallback for one or two releases.

## Use this instead

**Web devkit** — `../devkit_web/`:

- Hosted (nothing to install, always up to date):
  <https://horologist1.github.io/fantasy-manager/devkit/>
- Offline single file (double-click):
  `../devkit_web/dist/FantasyManagerDevkit.html`

The web devkit:

- has **no `.exe`**, so no antivirus false positives;
- covers **every moddable content type** (workers, traits, items,
  interactions, events, recruitment, daily stories, buildings) with guided
  recipes plus a full editor;
- includes the **Whoremaster importer** and the **GIF→WebM** tool;
- saves directly into your `game/data/` folder using the same merge rules the
  game applies at load time.

## Why this one is going away

The PyInstaller `.exe` triggers antivirus false positives and the Tkinter UI is
harder to maintain. No new features land here — only critical bugfixes, if any.
See `../docs/superpowers/specs/2026-06-10-modding-devkit-web-design.md`.
