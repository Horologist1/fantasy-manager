# Fantasy Manager Devkit (Web)

Static HTML/JS modding tool for Fantasy Manager. Replaces the legacy
`devkit/fantasy_manager_editor_v6.py`. No `.exe`, no antivirus friction.

## Running locally

Open `src/index.html` in Chrome, Edge, or Brave (recommended — File System
Access API). Firefox/Safari fall back to drag-and-drop + ZIP download.

## Tests

    cd devkit_web
    npm install
    npm test

## Refresh bundled catalog snapshots

    npm run bake

Reads `../game/data/` and writes `src/catalogs/*.json`.

See `docs/superpowers/specs/2026-06-10-modding-devkit-web-design.md`
for the full design.
