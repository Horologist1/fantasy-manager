# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

Fantasy Manager is a Ren'Py visual novel / worker-management simulator game. It also includes a Python/Tkinter devkit editor for creating/editing game data.

- **Game engine**: Ren'Py (visual novel engine with its own Python runtime)
- **Game scripts**: `.rpy` files under `game/scripts/`
- **Game data**: JSON files under `game/data/`
- **Devkit editor**: `devkit/linux/fantasy_manager_editor_v4_linux.py` (Python 3 + Tkinter)
- **Development notes**: `docs/RENPY_DEVELOPMENT_NOTES.md` (Ren'Py coding patterns, debugging tips)

### Running the game

The Ren'Py SDK must be installed separately (not bundled in the repo). It is installed at `~/renpy-sdk/renpy-8.3.7-sdk/`.

```bash
export DISPLAY=:99
~/renpy-sdk/renpy-8.3.7-sdk/renpy.sh /workspace
```

A virtual framebuffer (Xvfb) is required in headless environments. Start it with:

```bash
Xvfb :99 -screen 0 1280x720x24 -ac +extension GLX +render -noreset &
export DISPLAY=:99
```

ALSA audio warnings are expected and harmless in headless environments (no sound card).

### Lint

Ren'Py has a built-in lint tool. Run it with:

```bash
~/renpy-sdk/renpy-8.3.7-sdk/renpy.sh /workspace --lint
```

There is no separate Python linter configured for the project.

### Running the devkit editor

```bash
export DISPLAY=:99
cd /workspace/devkit/linux
python3 fantasy_manager_editor_v4_linux.py
```

Requires `python3-tk` and optionally `python3-pil` / `python3-pil.imagetk` (for image previews).

### Key gotchas

- Ren'Py uses `RevertableDict`/`RevertableList` instead of standard Python types. Never use `isinstance()` with `dict`/`list`; use `hasattr()` instead. See `docs/RENPY_DEVELOPMENT_NOTES.md`.
- After editing `.rpy` files, delete corresponding `.rpyc` files and `game/cache/*.rpyb` to force recompilation.
- The `game/images/workers/` directory is git-ignored; worker portrait images must be supplied separately for full visual testing.
- The game uses a custom JSON snapshot save system, not Ren'Py's native save. See `scripts/save_snapshot.rpy`.
