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

## Tools

- **Whoremaster importer** — batch-imports `.girlsx` / `.rgirlsx` character
  packs. Skills and traits are mapped to FM equivalents, unknown traits get a
  per-trait resolution step (map to an existing trait, create a stub, or
  skip — remembered for future imports), duplicates against your installed
  game are flagged, and image folders are copied into
  `game/images/workers/<folder>/` with WM→FM renaming (Portrait→profile…).
- **GIF → WebM** — converts GIF animations (Ren'Py can't animate GIFs) right
  in the browser via ffmpeg.wasm. Downloads the converter from a CDN on first
  use (~31 MB, cached); works on the hosted page and the local server.

With a game folder selected (Chrome/Edge/Brave), files save directly into
`game/data/` using the same merge rules the game applies at load time.
Without a folder, the finished JSON downloads as a ready-to-drop file.

## Run it (easiest): the hosted page

<https://horologist1.github.io/fantasy-manager/devkit/> — nothing to
download, always up to date. Republished automatically on every push that
touches the devkit or the game data. The GIF→WebM tool works best here.

## Run it (recommended): double-click the HTML

Open `dist/FantasyManagerDevkit.html` by double-clicking it. It is a single
self-contained HTML file — no server, no console window, no `.cmd`, nothing
for an antivirus to complain about. Use Chrome, Edge, or Brave so the
"Select game folder" button can save directly into your game.

Rebuild it after changing the app or re-baking catalogs:

    npm run build:offline

Note: the single-file build uses the catalogs baked into it. Select your
game folder to switch to live data from your install.

## Run it (developers): local server

`start.cmd` (Windows) / `./start.sh` (Linux/macOS) starts a tiny local
server on `http://localhost:8765` and opens the browser. Requires Node 18+
on PATH. Use this while developing the devkit itself — source edits are
picked up on refresh without rebuilding.

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

ES module imports and `fetch()` of the catalog files do not work over
`file://`, so opening `src/index.html` directly shows a broken page. The
offline build (`dist/FantasyManagerDevkit.html`) solves this by bundling
every module and catalog into one inline script — that file works from
`file://`, including the folder picker (the File System Access API is
available to local files in Chromium browsers).

Heads-up for future tools: anything that needs to download extra binaries
at runtime (e.g. ffmpeg.wasm for GIF→WebM) will need the served or hosted
version, since `fetch()` stays unavailable over `file://`.

See `docs/superpowers/specs/2026-06-10-modding-devkit-web-design.md`
for the full design.
