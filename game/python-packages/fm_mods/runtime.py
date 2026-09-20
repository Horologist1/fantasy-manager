"""Device-local mod UI state. Never included in Ren'Py store/save/rollback."""
import json
import os
from pathlib import Path
from . import android_picker

from .packs import (Source, PackError, inspect_pack, install_pack, installed_packs,
                    mount_paths, schedule_uninstall, finish_uninstalls,
                    inspect_override_pack, install_override_pack)

_root = None
_reserved_names = []
_known_files = set()
_mounted_ids = set()
_startup_ids = set()
_plan = None
_state = {"busy": False, "message": "", "preview": None, "installed": [], "override_mode": False}
_files = {}
_previous_open = None
_previous_loadable = None
_android_pending = False
_android_source = False


def discard_preview():
    global _plan, _android_source
    _plan = None
    _state["preview"] = None
    if _android_source:
        android_picker.discard()
        _android_source = False


def start_android_picker(renpy):
    global _android_pending
    if _state["busy"]:
        return
    discard_preview()
    try:
        android_picker.start()
        _android_pending = True
        _state.update(busy=True, message="Choose a mod ZIP in Android's file picker.")
    except Exception as exc:
        _state.update(busy=False, message="Could not open Android's file picker. This APK needs the mod import bridge: " + str(exc))


def poll_android_picker(renpy):
    global _android_pending, _android_source
    if not _android_pending:
        return
    try:
        result = android_picker.poll()
        status = result["status"]
        if status == "ready":
            _android_pending = False
            _android_source = True
            _state["message"] = "Checking pack..."
            renpy.invoke_in_thread(_preview_job, result["path"])
        elif status in ("cancelled", "error", "idle"):
            _android_pending = False
            android_picker.discard()
            _state.update(busy=False, message=result.get("message") or "Selection cancelled.")
        elif status == "copying":
            _state["message"] = "Copying ZIP: {:.1f} MB...".format(result.get("bytes", 0) / 1048576)
    except Exception as exc:
        _android_pending = False
        android_picker.discard()
        _state.update(busy=False, message="Could not read the selected ZIP: " + str(exc))


def _open_file(name):
    path = _files.get(name)
    if path is not None:
        return open(path, "rb")
    return _previous_open(name) if _previous_open is not None else None


def _loadable(name):
    if name in _files:
        return True
    return bool(_previous_loadable(name)) if _previous_loadable is not None else False


def _scan_files(add, seen):
    import renpy
    for name in _files:
        add(None, name, renpy.loader.game_files, seen)


def bootstrap(renpy):
    global _root, _reserved_names, _known_files, _mounted_ids, _startup_ids, _plan, _state, _files, _previous_open, _previous_loadable
    _root = str(Path(renpy.config.savedir) / "character_mods")
    _reserved_names = []
    _plan = None
    _state = {"busy": False, "message": "", "preview": None, "installed": [], "override_mode": False}
    removal_errors = finish_uninstalls(_root)
    if removal_errors:
        _state["message"] = "Some pack files could not be removed. Restart to retry cleanup."
        for error in removal_errors:
            renpy.log("CHARACTER_MODS: " + error)
    # Read raw catalog names; loading worker instances here would roll traits
    # and depend on store functions that have not been defined yet.
    _known_files = set(renpy.list_files())
    for filename in _known_files:
        if filename == "data/workers.json" or (filename.startswith("data/workers/") and filename.endswith(".json")):
            try:
                with renpy.file(filename) as handle:
                    rows = json.loads(handle.read().decode("utf-8-sig"))
                if hasattr(rows, "get"):
                    rows = rows.get("workers", [rows])
                _reserved_names.extend(w["name"] for w in rows if hasattr(w, "get") and isinstance(w.get("name"), str))
            except (OSError, ValueError, TypeError):
                continue
    paths = mount_paths(_root)
    installed = installed_packs(_root)
    _startup_ids = {pack["id"] for pack in installed if not pack["pending_uninstall"]}
    override_ids = {pack["id"] for pack in installed if pack.get("mode") == "override"}
    _files = {}
    _mounted_ids = set()
    for path in paths:
        try:
            with Source(path) as source:
                indexed = {name: str(disk_file) for name, (disk_file, _size) in source.entries.items()}
            # Overrides only target files shipped by this version. An update
            # which removed a target must not silently turn it into new content.
            if Path(path).parent.name in override_ids and not set(indexed).issubset(_known_files):
                renpy.log("MODS: Override skipped; a target no longer exists: " + Path(path).parent.name)
                continue
            _files.update(indexed)
            _mounted_ids.add(Path(path).parent.name)
        except (OSError, PackError):
            continue
    if _files:
        # A virtual file index avoids Ren'Py 8.3's Windows long-path walker.
        # Hooks serve additive JSON/images and opted-in JSON overrides; other files retain the
        # original callbacks and normal engine lookup. No script search path
        # is added. This is installed once at init, never during prediction.
        if renpy.config.file_open_callback is not _open_file:
            _previous_open = renpy.config.file_open_callback
        if renpy.config.loadable_callback is not _loadable:
            _previous_loadable = renpy.config.loadable_callback
        renpy.config.file_open_callback = _open_file
        renpy.config.loadable_callback = _loadable
        if _scan_files not in renpy.loader.scandirfiles_callbacks:
            renpy.loader.scandirfiles_callbacks.append(_scan_files)
        renpy.loader.cleardirfiles()
    refresh()


def state():
    return _state


def refresh():
    packs = installed_packs(_root) if _root else []
    _state["installed"] = [dict(pack, active=pack["id"] in _mounted_ids,
                                restart_required=pack["id"] not in _startup_ids) for pack in packs]


def default_folder():
    downloads = Path.home() / "Downloads"
    return str(downloads if downloads.is_dir() else Path.home())


def browse(path):
    path = Path(path).expanduser().resolve()
    rows = []
    error = ""
    try:
        for child in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.casefold())):
            if child.name.startswith("."):
                continue
            if child.is_dir() or child.suffix.lower() == ".zip":
                rows.append({"path": str(child), "name": child.name, "directory": child.is_dir()})
    except OSError as exc:
        error = "Cannot open this folder: " + str(exc)
    return {"path": str(path), "parent": str(path.parent), "rows": rows, "error": error}


def set_message(text):
    _state["message"] = text


def set_override_mode(enabled):
    global _plan
    if _state["busy"]:
        return
    discard_preview()
    _state.update(override_mode=bool(enabled), preview=None, message="")


def start_preview(renpy, source):
    if _state["busy"]:
        return
    discard_preview()
    _state.update(busy=True, message="Checking pack...", preview=None)
    renpy.invoke_in_thread(_preview_job, source)


def _preview_job(source):
    global _plan
    import renpy
    try:
        if _state["override_mode"]:
            _plan = inspect_override_pack(source, _known_files)
            replacing = []
            targets = {f["path"] for f in _plan["files"]}
            for pack in installed_packs(_root):
                if pack.get("mode") == "override" and pack["id"] != _plan["id"] and not pack["pending_uninstall"]:
                    replacing.extend(f["path"] for f in pack["files"] if f["path"] in targets)
            warnings = list(_plan["warnings"])
            if replacing:
                warnings.append("Overrides earlier installed packs for: " + ", ".join(sorted(set(replacing))))
            _state["preview"] = {"title": _plan["title"], "mode": "override", "files": sorted(targets),
                                 "mb": round(_plan["bytes"] / 1048576, 1), "warnings": warnings, "conflicts": []}
            _state["message"] = "Review the full-file replacements below. The last installed override wins for matching paths."
            return
        _plan = inspect_pack(source)
        conflicts = set(n.casefold() for n in _reserved_names)
        for pack in installed_packs(_root):
            if pack["id"] != _plan["id"]:
                conflicts.update(n.casefold() for n in pack["worker_names"])
        collisions = [w["name"] for w in _plan["workers"] if w["name"].casefold() in conflicts]
        _state["preview"] = {"title": _plan["title"], "workers": len(_plan["workers"]),
                             "images": len(_plan["images"]), "mb": round(_plan["bytes"] / 1048576, 1),
                             "names": ", ".join(w["name"] for w in _plan["workers"]),
                             "warnings": _plan["warnings"], "conflicts": collisions}
        _state["message"] = ("Overlapping names: " + ", ".join(collisions) + ". The import button will keep both by adding a Mod suffix to these imported names.") if collisions else "Pack checked. Review it before installing."
    except Exception as exc:
        discard_preview()
        _state["message"] = "Could not read this pack: " + str(exc)
    finally:
        _state["busy"] = False
        renpy.invoke_in_main_thread(renpy.restart_interaction)


def start_install(renpy, rename_conflicts=False):
    if _state["busy"] or _plan is None:
        return
    _state.update(busy=True, message="Installing character pack...")
    renpy.invoke_in_thread(_install_job, rename_conflicts)


def _install_job(rename_conflicts=False):
    import renpy
    try:
        override = _plan.get("mode") == "override"
        if override:
            result = install_override_pack(_plan, _root, _known_files)
        else:
            result = install_pack(_plan, _root, _reserved_names, rename_conflicts=rename_conflicts)
        _state["message"] = ("This pack is already installed." if result == "already_installed" else
                             "Installed. Close and reopen the game, then start a new game for these overrides." if override else
                             "Installed. Close and reopen the game to activate the pack, then load your save.")
        discard_preview()
        _state["override_mode"] = False
        refresh()
    except Exception as exc:
        _state["message"] = "Nothing was installed: " + str(exc)
    finally:
        _state["busy"] = False
        renpy.invoke_in_main_thread(renpy.restart_interaction)


def start_uninstall(renpy, pack_id, cancel=False):
    if _state["busy"]:
        return
    _state.update(busy=True, message="Updating pack...")
    renpy.invoke_in_thread(_uninstall_job, pack_id, cancel)


def _uninstall_job(pack_id, cancel=False):
    import renpy
    try:
        override = any(p["id"] == pack_id and p.get("mode") == "override" for p in installed_packs(_root))
        schedule_uninstall(_root, pack_id, cancel=cancel)
        _state["message"] = ("Uninstall cancelled. The pack is kept." if cancel else
                             "Uninstall scheduled. Restart and start a new game to use the remaining JSON definitions." if override else
                             "Uninstall scheduled. Close and reopen the game to remove the pack. Saved characters are kept; their pack images will be unavailable.")
        discard_preview()
        refresh()
    except Exception as exc:
        _state["message"] = "Could not update this pack: " + str(exc)
    finally:
        _state["busy"] = False
        renpy.invoke_in_main_thread(renpy.restart_interaction)
