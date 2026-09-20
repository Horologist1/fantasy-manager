# Fantasy Manager Devkit 0.2

A static browser editor for mod projects, with editable drafts and validated ZIP
exports. The game and devkit now live in the same checkout so the published
reference can be generated and tested against the actual importer.

## For mod authors

Open `dist/FantasyManagerDevkit.html` or the hosted devkit, then choose a mode:

- **Character pack:** named regular workers plus PNG/JPG/WebP images; install the
  exported ZIP through Mods on PC or Android.
- **JSON override (experimental):** copies complete existing catalogs into the
  project, edits entries there, and exports their original `data/...` paths.
- **Manual JSON files (PC only):** advanced authoring outside the managed importer.

Read [USER_GUIDE.md](USER_GUIDE.md), also available through **User guide** inside
the web and offline application. It includes a first character pack, an Ironroot
price override, Android installation, draft backups, and troubleshooting.

The devkit does not write into the game installation. Optional PC folder access
is read-only. The separate GIF conversion tool writes its explicitly selected
output files, as described in the guide.

## Architecture

- `src/lib/content_types.js`: content registry, schemas, assistant/editor bindings.
- `src/lib/project.js`: isolated project state, identity-aware edits, drafts,
  validation and export. No game directory handles or save-state dependencies.
- `src/lib/contract.js`: bounded paths, JSON, identities and additive-pack rules.
- `src/lib/reference.js`: complete catalog reference and project-aware lookups.
- `src/lib/zip.js`: offline ZIP writer; no network/CDN needed for pack export.
- `src/recipes`, `src/editors`, `src/schemas`, `src/converters`: reusable authoring
  modules retained from the previous devkit.
- `src/project_app.js`: user workflow; `src/app.js` is the shared entry point.
- `src/user_guide.js`: source for the in-app and generated Markdown user guides.

The generated `_meta.json` records the game version, content fingerprint and
per-file hashes. `base_files.json` contains the full original JSON catalogs used
for editing and offline override creation. Do not copy snapshots from another
branch or ship an offline HTML built before baking current catalogs.

## Development and checks

Use Node 20.11+ and Python 3.9+ available on PATH. From `devkit_web`:

    npm ci
    npm run check

`check` bakes current game catalogs, generates guides, runs tests and builds the
single-file offline app. Tests include the UI flows, malformed reads, draft
round-trips and real Python pack inspection/installation in temporary storage.
Set `FM_GAME_ROOT` to test against another complete checkout deliberately.
Set `PYTHON` if the Python executable has another name.

Serve `src` with `start.cmd` / `start.sh` for development, or double-click the
built offline HTML. Source ES modules do not run directly from `file://`.

The GitHub Pages workflow publishes from **main** after baking and verification.
The old `feature/devkit-web` checkout is retained as a backup/reference, not the
source for these changes. Local edits or building an HTML do not update the
hosted page: deployment requires publishing the verified main revision.

## Limits and compatibility

Projects allow 128 MB of unpacked content, 10,000 files, and up to 1,000 regular
workers. The importer limits still apply: 32 MB per image and 4 MB per JSON file.
JSON overrides cannot add new file paths, include images/scripts, or import
Interactions. They replace whole files, not matching fields across mods.

The game-side identity adjustment in this update allows existing nameless
monster templates and named SFW/NSFW variants (Kar/Kara) in overrides. Older
APKs can reject those catalogs. The character-pack format and game save format
are unchanged. Installing/removing overrides during an existing playthrough is
outside the supported scope; use a new game and a stable set of mods.

Validation does not prove that every event is playable. Test authored events,
including failure branches, with the matching game before distributing a mod.
