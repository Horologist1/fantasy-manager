# Fantasy Manager Devkit (Web)

Static HTML/JS modding tool for Fantasy Manager. Replaces the legacy
`devkit/fantasy_manager_editor_v6.py`. No `.exe`, no antivirus friction.

## What you can create

Every moddable content type has guided wizards (recipes) plus a full
section editor for existing JSON:

| Type | Recipes |
|---|---|
| Workers | Unique Worker, Procedural Worker Template, Monster Worker |
| Traits | Permanent Trait, Temporary Trait |
| Items | Consumable, Equipment, Quest Item |
| Interactions | Simple, Trait-Granting, Worker-Specific |
| Events | Worker-Specific, Event Chain (2 steps), Building Skill Check |
| Recruitment | Recruitment Event |
| Daily Stories | Basic, With Trait Roll (saved as daily_story_extensions) |
| Buildings | New Building Type, Add Job to Existing Building |

With a game folder selected (Chrome/Edge/Brave), files save directly into
`game/data/` using the same merge rules the game applies at load time.
Without a folder, the finished JSON downloads as a ready-to-drop file.

## Run it (Windows)

Double-click `start.cmd`. A console window opens, a local server starts,
and your default browser opens automatically. Use Chrome, Edge, or Brave
(File System Access API). Close the console window when you are done.

## Run it (Linux/macOS)

    ./start.sh

Same behaviour: starts a local server and opens the default browser.

## Requirements

Node 18+ on PATH (`node --version`). That is it. No build step.

## Tests

    cd devkit_web
    npm install
    npm test

## Refresh bundled catalog snapshots

    npm run bake

Reads `../game/data/` and `../game/images/workers/`, writes
`src/catalogs/*.json`. Run this after the game adds new traits, items,
buildings, or worker image folders so the offline catalogs stay current.

## Why not just open `src/index.html`?

The File System Access API and ES module imports both require an
`http://` origin. Opening the HTML file with `file://` will not work
(modules fail to load, folder picker is unavailable). The launcher
serves the same files over `http://localhost:8765` and works around
this in one click.

See `docs/superpowers/specs/2026-06-10-modding-devkit-web-design.md`
for the full design.
