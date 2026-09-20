"""Additive character packs and opt-in JSON overrides outside the shipped game.

The original files are never changed. No extractall or script installation.
Override destinations must match validated, existing game-relative JSON paths.
This module needs only stdlib.
"""
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import zipfile

MAX_FILES = 10000
MAX_TOTAL = 1024 * 1024 * 1024
MAX_FILE = 32 * 1024 * 1024
MAX_JSON = 4 * 1024 * 1024
MAX_WORKERS = 1000
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
PACK_ID = re.compile(r"mod_[0-9a-f]{20}\Z")
REMOVE_MARKER = ".remove-on-restart"
REMOVE_PREFIX = ".uninstall-"
FOLDER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}\Z")
BOOL_FIELDS = ("nsfw", "unique", "encounter_only", "monster", "procedural")
WORKER_FIELDS = {"name", "folder", "cost", "skills", "names_list", "traits",
                 "description", "gender", "comfort_desired", *BOOL_FIELDS}


class PackError(ValueError):
    pass


def disk_path(path):
    """Ren'Py's Windows executable may lack the longPathAware manifest flag."""
    path = os.path.abspath(os.path.expanduser(str(path)))
    if os.name == "nt" and not path.startswith("\\\\?\\"):
        path = "\\\\?\\UNC\\" + path[2:] if path.startswith("\\\\") else "\\\\?\\" + path
    return Path(path)


def safe_path(name):
    """Reject traversal, drive/ADS paths and platform-ambiguous names."""
    name = name.replace("\\", "/")
    parts = name.rstrip("/").split("/")
    if (not name or name.startswith("/") or any(
            p in ("", ".", "..") or p.endswith((".", " ")) or
            any(ord(c) < 32 or c in ':<>"|?*' for c in p) or
            p.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *("COM%d" % i for i in range(10)), *("LPT%d" % i for i in range(10))}
            for p in parts)):
        raise PackError("Unsafe path in pack: " + name[:180])
    return "/".join(parts)


def _is_link(path):
    info = path.lstat()
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & 0x400)


class Source:
    """Bounded read-only view of a ZIP or selected folder."""
    def __init__(self, source):
        self.path = disk_path(source)
        self.archive = None
        self.entries = {}
        self._seen = set()
        try:
            if self.path.is_dir():
                for parent, directories, filenames in os.walk(self.path, followlinks=False):
                    for name in directories + filenames:
                        path = Path(parent) / name
                        if _is_link(path):
                            raise PackError("Links are not supported inside character packs.")
                    for name in filenames:
                        path = Path(parent) / name
                        self._add(path.relative_to(self.path).as_posix(), path, path.stat().st_size)
            elif self.path.is_file() and zipfile.is_zipfile(self.path):
                self.archive = zipfile.ZipFile(self.path)
                if len(self.archive.infolist()) > MAX_FILES:
                    raise PackError("This pack contains too many files (limit: 10,000).")
                for entry in self.archive.infolist():
                    safe_path(entry.filename)
                    if stat.S_ISLNK(entry.external_attr >> 16):
                        raise PackError("Links are not supported inside character packs.")
                    if entry.flag_bits & 1:
                        raise PackError("Encrypted ZIP files are not supported.")
                    if not entry.is_dir():
                        self._add(entry.filename, entry, entry.file_size)
            else:
                raise PackError("Select a ZIP file or an unpacked character-pack folder.")
            if sum(size for _, size in self.entries.values()) > MAX_TOTAL:
                raise PackError("The unpacked pack exceeds the 1 GB limit.")
        except Exception:
            self.close()
            raise

    def _add(self, name, entry, size):
        name = safe_path(name)
        if name.casefold() in self._seen:
            raise PackError("Duplicate file path in pack: " + name)
        if size > MAX_FILE or len(self.entries) >= MAX_FILES:
            raise PackError("Pack exceeds the file-size or file-count limit.")
        self.entries[name] = (entry, size)
        self._seen.add(name.casefold())

    def read(self, name, limit=MAX_FILE):
        entry, size = self.entries[name]
        if size > limit:
            raise PackError("File is too large: " + name)
        with self.archive.open(entry) if self.archive else open(entry, "rb") as handle:
            data = handle.read(limit + 1)
        if len(data) != size or len(data) > limit:
            raise PackError("File changed or exceeds the size limit: " + name)
        return data

    def close(self):
        if self.archive:
            self.archive.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _worker_files(source):
    found = []
    for name in sorted(source.entries):
        if not name.lower().endswith(".json"):
            continue
        if "/data/workers/" in "/" + name:
            prefix = ("/" + name).split("/data/workers/", 1)[0].lstrip("/")
            found.append((prefix, name))
        elif name.endswith("data/workers.json"):
            found.append((name[:-len("data/workers.json")].rstrip("/"), name))
        elif PurePosixPath(name).name == "workers.json":
            found.append((name.rsplit("/", 1)[0] if "/" in name else "", name))
    if not found:
        raise PackError("No workers.json or data/workers/*.json found in this pack.")
    roots = {root for root, _ in found}
    if len(roots) != 1:
        raise PackError("Several game roots found. Select one character pack at a time.")
    return roots.pop(), [name for _, name in found]


def _number(value, key, maximum):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= maximum:
        raise PackError("Invalid " + key + " in worker data.")
    return value


def _worker(entry):
    if not hasattr(entry, "get"):
        raise PackError("Every worker must be a JSON object.")
    name, folder = entry.get("name"), entry.get("folder")
    if not isinstance(name, str) or not name.strip() or len(name) > 100 or any(c in name for c in "{}[]\r\n\x00"):
        raise PackError("Each worker needs a plain-text name (1-100 characters).")
    if not isinstance(folder, str) or not FOLDER.fullmatch(folder):
        raise PackError("Invalid image folder for " + name)
    if entry.get("procedural") or entry.get("monster") or entry.get("procedural_template") or entry.get("event_recruit_only"):
        raise PackError(name + ": this importer supports regular characters, not procedural or event-only templates.")
    for field in BOOL_FIELDS:
        if field in entry and not isinstance(entry[field], bool):
            raise PackError(name + ": " + field + " must be true or false.")
    gender = entry.get("gender")
    if gender not in ("male", "female"):
        raise PackError(name + ": gender must be male or female.")
    skills = entry.get("skills", {})
    if not hasattr(skills, "items") or any(not isinstance(k, str) for k in skills):
        raise PackError(name + ": skills must be a JSON object.")
    for key, value in skills.items():
        _number(value, "skill " + key, 100)
    traits = entry.get("traits", [])
    if not isinstance(traits, list) or any(not isinstance(t, str) or len(t) > 100 for t in traits):
        raise PackError(name + ": traits must be a list of names.")
    result = {key: value for key, value in entry.items() if key in WORKER_FIELDS}
    result["name"] = name.strip()
    result["cost"] = _number(entry.get("cost", 0), "cost", 10000000)
    result["comfort_desired"] = _number(entry.get("comfort_desired", 1), "comfort_desired", 100)
    for key in ("description", "names_list"):
        if result.get(key) is not None and (not isinstance(result[key], str) or len(result[key]) > 10000):
            raise PackError(name + ": invalid " + key)
    # Treat packs without an explicit rating conservatively; the normal game
    # content filter remains authoritative after importing.
    result.setdefault("nsfw", True)
    return result


def _image_signature(data, extension):
    return ((extension == ".png" and data.startswith(b"\x89PNG\r\n\x1a\n")) or
            (extension in (".jpg", ".jpeg") and data.startswith(b"\xff\xd8\xff")) or
            (extension == ".webp" and data.startswith(b"RIFF") and data[8:12] == b"WEBP"))


def inspect_pack(path):
    with Source(path) as source:
        prefix, json_files = _worker_files(source)
        workers, warnings = [], []
        for filename in json_files:
            try:
                rows = json.loads(source.read(filename, MAX_JSON).decode("utf-8-sig"))
            except (ValueError, UnicodeError) as exc:
                raise PackError("Invalid worker JSON: " + filename) from exc
            if hasattr(rows, "get"):
                rows = rows.get("workers", [rows])
            if not isinstance(rows, list):
                raise PackError("Worker JSON must contain a list of workers.")
            for row in rows:
                workers.append(_worker(row))
                dropped = set(row) - WORKER_FIELDS
                if dropped:
                    warnings.append("Unrecognised worker fields omitted: " + ", ".join(sorted(dropped)))
        if not workers or len(workers) > MAX_WORKERS:
            raise PackError("A pack must contain between 1 and 1,000 workers.")
        names = [w["name"].casefold() for w in workers]
        if len(names) != len(set(names)):
            raise PackError("The pack contains duplicate worker names.")
        folders = {w["folder"] for w in workers}
        image_root = (prefix + "/" if prefix else "") + "images/workers/"
        images = []
        for name in sorted(source.entries):
            if not name.startswith(image_root):
                continue
            relative = name[len(image_root):]
            if "/" not in relative or relative.split("/")[0] not in folders:
                continue
            extension = PurePosixPath(name).suffix.lower()
            if extension not in IMAGE_EXTENSIONS:
                continue
            data = source.read(name)
            if not _image_signature(data, extension):
                raise PackError("Image contents do not match the file extension: " + name)
            images.append({"source": name, "relative": relative, "size": len(data),
                           "sha256": hashlib.sha256(data).hexdigest()})
        for folder in folders:
            profiles = [i for i in images if i["relative"].startswith(folder + "/")
                        and re.fullmatch(r"profile(?:[ _-]?\d+| \(\d+\))?", PurePosixPath(i["relative"]).stem.lower())]
            if not profiles:
                raise PackError("Missing profile.png/jpg/webp in images/workers/" + folder)
        ignored = len(source.entries) - len(json_files) - len(images)
        if ignored:
            warnings.append("%d extra file(s) excluded. Custom events, scripts and other content are not imported." % ignored)
        canonical = json.dumps({"workers": workers, "images": [(i["relative"], i["sha256"]) for i in images]},
                               sort_keys=True, ensure_ascii=False).encode("utf-8")
        pack_id = "mod_" + hashlib.sha256(canonical).hexdigest()[:20]
        return {"id": pack_id, "source": str(source.path), "title": source.path.stem,
                "workers": workers, "images": images, "warnings": sorted(set(warnings)),
                "bytes": sum(i["size"] for i in images)}


def installed_packs(root):
    result = []
    root = disk_path(root)
    try:
        if not root.is_dir():
            return result
        directories = sorted(root.iterdir())
    except OSError:
        return result
    for directory in directories:
        try:
            if not PACK_ID.fullmatch(directory.name) or not directory.is_dir() or _is_link(directory):
                continue
            manifest_file = directory / "manifest.json"
            if _is_link(manifest_file) or manifest_file.stat().st_size > MAX_JSON:
                continue
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict):
                continue
            if manifest.get("id") != directory.name:
                continue
            if manifest.get("format") == 2:
                if not _valid_override_manifest(manifest):
                    continue
                marker = directory / REMOVE_MARKER
                pending = marker.exists() and not _is_link(marker) and marker.is_file()
                result.append(dict(manifest, pending_uninstall=pending))
                continue
            if manifest.get("format") != 1:
                continue
            names = manifest.get("worker_names")
            if (not isinstance(manifest.get("title"), str) or
                    not isinstance(names, list) or not 1 <= len(names) <= MAX_WORKERS or
                    any(not isinstance(name, str) or not name for name in names) or
                    manifest.get("workers") != len(names)):
                continue
            marker = directory / REMOVE_MARKER
            pending = marker.exists() and not _is_link(marker) and marker.is_file()
            result.append(dict(manifest, pending_uninstall=pending))
        except (OSError, ValueError):
            continue
    # Additive packs retain their existing order. Overrides run afterwards,
    # in installation order, so the latest installed file wins explicitly.
    return sorted(result, key=lambda p: (p.get("mode") == "override", p.get("load_order", 0), p["id"]))


def _owned_directory(root, name):
    """Resolve and check the exact managed child before any move or deletion."""
    root = disk_path(root)
    if _is_link(root):
        raise PackError("The character-mod directory must not be a link.")
    root = disk_path(root.resolve())
    target = root / name
    if _is_link(target) or not target.is_dir() or disk_path(target.resolve()).parent != root:
        raise PackError("Unsafe character-pack directory; no files were removed.")
    return target


def schedule_uninstall(root, pack_id, cancel=False):
    """Keep mounted files intact until the next process starts."""
    if not isinstance(pack_id, str) or not PACK_ID.fullmatch(pack_id):
        raise PackError("Invalid character-pack identifier.")
    target = _owned_directory(root, pack_id)
    if not any(pack["id"] == pack_id for pack in installed_packs(root)):
        raise PackError("This pack is no longer installed. Reopen the pack list.")
    marker = target / REMOVE_MARKER
    if marker.exists() or marker.is_symlink():
        if _is_link(marker) or not marker.is_file():
            raise PackError("Unsafe removal marker; no files were changed.")
        if cancel:
            marker.unlink()
    elif not cancel:
        # Exclusive creation cannot overwrite a file or follow a link.
        with marker.open("xb"):
            pass


def finish_uninstalls(root):
    """Startup only: retire complete packs, then retry safe physical cleanup.

    A failed deletion stays outside discovery, so a half-deleted pack can
    never mount. Sources and saves are outside these exact managed children.
    """
    root = disk_path(root)
    errors = []
    def fail_walk(error):
        raise error
    try:
        if not root.exists():
            return errors
        if _is_link(root):
            raise PackError("The character-mod directory must not be a link.")
        candidates = sorted(root.iterdir())
    except (OSError, PackError) as exc:
        return [str(exc)]
    for candidate in candidates:
        name = candidate.name
        retired = name.startswith(REMOVE_PREFIX) and PACK_ID.fullmatch(name[len(REMOVE_PREFIX):])
        if not retired and not PACK_ID.fullmatch(name):
            continue
        try:
            if not retired and not (candidate / REMOVE_MARKER).exists():
                continue
            target = _owned_directory(root, name)
            # Reject reparse points anywhere in the tree before recursive
            # deletion; do not traverse a link/junction to external content.
            for parent, directories, filenames in os.walk(target, followlinks=False, onerror=fail_walk):
                for child in directories + filenames:
                    if _is_link(Path(parent) / child):
                        raise PackError("A pack contains a link; automatic removal was stopped.")
            if not retired:
                destination = target.parent / (REMOVE_PREFIX + name)
                if destination.exists() or destination.is_symlink():
                    raise PackError("Previous removal cleanup is still pending. Restart again to retry.")
                if disk_path(destination.resolve()).parent != disk_path(root.resolve()):
                    raise PackError("Unsafe removal destination.")
                target = target.rename(destination)
            # Recheck the resolved target immediately before recursive delete.
            target = _owned_directory(root, target.name)
            shutil.rmtree(target)
        except (OSError, PackError) as exc:
            errors.append(name + ": " + str(exc))
    return errors


def install_pack(plan, root, reserved_names=(), rename_conflicts=False):
    """Stage completely, then publish a new directory atomically. Never overwrite."""
    root = disk_path(root)
    root.mkdir(parents=True, exist_ok=True)
    fresh = inspect_pack(plan["source"])
    if fresh["id"] != plan["id"]:
        raise PackError("The source changed after preview. Please inspect it again.")
    target = root / fresh["id"]
    if target.exists():
        if (target / REMOVE_MARKER).exists():
            raise PackError("This pack is scheduled for removal. Cancel its uninstall first.")
        if any(p["id"] == fresh["id"] for p in installed_packs(root)):
            return "already_installed"
        raise PackError("An incomplete installation exists for this pack. No files were overwritten.")
    taken = {n.casefold() for n in reserved_names}
    for pack in installed_packs(root):
        taken.update(n.casefold() for n in pack.get("worker_names", []))
    conflicts = [w["name"] for w in fresh["workers"] if w["name"].casefold() in taken]
    if conflicts and not rename_conflicts:
        raise PackError("Worker names already in the game: " + ", ".join(conflicts) + ". Rename them in the source pack first.")
    if shutil.disk_usage(root).free < fresh["bytes"] + 32 * 1024 * 1024:
        raise PackError("Not enough free space to install this pack.")
    stage = Path(tempfile.mkdtemp(prefix=".install-", dir=str(root)))
    try:
        content = stage / "content"
        worker_dir = content / "data/workers"
        worker_dir.mkdir(parents=True)
        workers = []
        renamed = []
        for worker in fresh["workers"]:
            worker = dict(worker)
            original_name = worker["name"]
            if original_name.casefold() in taken:
                base = original_name[:75] + " (Mod " + fresh["id"][-6:] + ")"
                candidate = base
                counter = 2
                while candidate.casefold() in taken:
                    candidate = base + " " + str(counter)
                    counter += 1
                worker["name"] = candidate
                renamed.append({"original": original_name, "imported": candidate})
            taken.add(worker["name"].casefold())
            worker["folder"] = fresh["id"] + "__" + worker["folder"]
            workers.append(worker)
        (worker_dir / (fresh["id"] + ".json")).write_text(json.dumps(workers, ensure_ascii=False, indent=2), encoding="utf-8")
        with Source(fresh["source"]) as source:
            for entry in fresh["images"]:
                data = source.read(entry["source"])
                if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                    raise PackError("An image changed while importing. Nothing was installed.")
                destination = content / "images/workers" / (fresh["id"] + "__" + entry["relative"])
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
        manifest = {"format": 1, "id": fresh["id"], "title": fresh["title"],
                    "worker_names": [w["name"] for w in workers], "workers": len(workers),
                    "images": len(fresh["images"]), "bytes": fresh["bytes"], "warnings": fresh["warnings"], "renamed": renamed}
        (stage / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        # The directory is only visible to startup discovery once complete.
        stage.rename(target)
        return "installed"
    finally:
        if stage.exists():
            assert disk_path(stage.resolve()).parent == disk_path(root.resolve()) and stage.name.startswith(".install-")
            shutil.rmtree(stage)


def mount_paths(root):
    """Mount only generated content, without executable or unrelated files."""
    root = disk_path(root)
    paths = []
    for pack in installed_packs(root):
        if pack["pending_uninstall"]:
            continue
        content = Path(root) / pack["id"] / "content"
        try:
            if not content.is_dir() or _is_link(content):
                continue
            if pack.get("mode") == "override":
                with Source(content) as source:
                    expected = {entry["path"]: entry for entry in pack["files"]}
                    if set(source.entries) != set(expected):
                        continue
                    for name, entry in expected.items():
                        data = source.read(name, MAX_JSON)
                        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                            raise PackError("An installed override changed: " + name)
                        _validate_override_json(name, data)
                paths.append(str(disk_path(content.resolve())))
                continue
            with Source(content) as source:
                allowed_json = "data/workers/" + pack["id"] + ".json"
                if allowed_json not in source.entries:
                    continue
                if any(name != allowed_json and not (
                        name.startswith("images/workers/" + pack["id"] + "__") and
                        PurePosixPath(name).suffix.lower() in IMAGE_EXTENSIONS)
                        for name in source.entries):
                    continue
                rows = json.loads(source.read(allowed_json, MAX_JSON).decode("utf-8"))
                if not isinstance(rows, list) or len(rows) != pack["workers"]:
                    continue
                folders = set()
                for row in rows:
                    if not isinstance(row, dict) or not isinstance(row.get("folder"), str):
                        raise PackError("Invalid installed worker.")
                    folder = row["folder"]
                    prefix = pack["id"] + "__"
                    if not folder.startswith(prefix):
                        raise PackError("Installed worker has a foreign image folder.")
                    _worker(dict(row, folder=folder[len(prefix):]))
                    folders.add(folder)
                if [row["name"] for row in rows] != pack["worker_names"]:
                    continue
                if any(name.startswith("images/workers/") and name.split("/")[2] not in folders
                       for name in source.entries):
                    continue
            paths.append(str(disk_path(content.resolve())))
        except (OSError, PackError, ValueError):
            continue
    return paths


def override_category(path):
    """Only authored JSON catalogs; never scripts, settings or save files."""
    if path == "data/monthly_conditions/cards.json":
        return "Monthly conditions"
    if path == "data/workers.json":
        return "Workers"
    parts = path.split("/")
    if len(parts) < 3 or parts[0] != "data" or not path.endswith(".json"):
        return None
    if len(parts) == 3 and parts[1] in ("workers", "items", "traits", "buildings", "events"):
        return parts[1].title()
    if len(parts) == 4 and parts[1:3] == ["buildings", "daily_story_extensions"]:
        return "Daily stories"
    if len(parts) == 4 and parts[1:3] == ["events", "recruit"]:
        return "Events"
    return None


def _validate_override_json(path, data):
    """Check JSON structure, not the gameplay semantics of an author's mod."""
    def reject_constant(value):
        raise ValueError("Non-finite number: " + value)
    def finite_float(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("Non-finite number: " + value)
        return result
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result
    try:
        value = json.loads(data.decode("utf-8-sig"), parse_constant=reject_constant, parse_float=finite_float, object_pairs_hook=unique_keys)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise PackError("Invalid override JSON: " + path) from exc
    category = override_category(path)
    if category == "Monthly conditions":
        from fm_monthly.conditions import validate_catalog
        _cards, errors = validate_catalog(value)
        if errors:
            raise PackError("Invalid monthly conditions: " + "; ".join(errors))
    if category in ("Items", "Buildings"):
        key = "items" if category == "Items" else "building_types"
        rows = value.get(key) if isinstance(value, dict) else None
    elif category == "Workers":
        rows = [value] if isinstance(value, dict) else value
    elif category == "Traits":
        rows = value.get("traits") if isinstance(value, dict) else value
    elif category == "Daily stories":
        rows = value.get("daily_story_extensions", [value]) if isinstance(value, dict) else value
        if isinstance(rows, dict):
            rows = [rows]
    else:
        rows = value
    if not category or not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise PackError("Unexpected catalog structure: " + path)
    if category != "Daily stories":
        key = "name" if category in ("Workers", "Traits") else "id"
        # Shipped procedural monster templates intentionally have no name.
        # Keep their identity separate from named workers, as the game does.
        identities = []
        for row in rows:
            identity_key = "template_id" if category == "Workers" and row.get("procedural_template") is True else key
            identity_value = row.get(identity_key)
            if not isinstance(identity_value, str) or not identity_value.strip():
                raise PackError("Missing or duplicate catalog identifiers: " + path)
            identity = (identity_key, identity_value)
            # Kar/Kara ship one named entry for each content rating. Editing
            # one variant must preserve the other, without permitting duplicate
            # names within the same rating. Additive packs still require unique
            # names across the entire pack in inspect_pack().
            if category == "Workers" and identity_key == "name":
                rating = row.get("nsfw", False)
                if not isinstance(rating, bool):
                    raise PackError("Invalid worker content rating: " + path)
                identity += (rating,)
            identities.append(identity)
        if len(identities) != len(set(identities)):
            raise PackError("Missing or duplicate catalog identifiers: " + path)
    return value


def inspect_override_pack(path, known_files):
    """Replace whole existing files by exact game-relative path, with opt-in UI."""
    known_files = set(known_files)
    with Source(path) as source:
        found = []
        for name in sorted(source.entries):
            parts = name.split("/")
            for index, part in enumerate(parts):
                relative = "/".join(parts[index:])
                if part == "data" and override_category(relative):
                    found.append(("/".join(parts[:index]), name, relative))
                    break
        if not found:
            raise PackError("No supported JSON files found. Keep the original data/... paths inside the ZIP or folder.")
        if len({prefix for prefix, _, _ in found}) != 1:
            raise PackError("Several game roots found. Select one override pack at a time.")
        files = []
        for _, name, relative in found:
            if relative not in known_files:
                raise PackError("Override target does not exist in this game version: " + relative)
            data = source.read(name, MAX_JSON)
            _validate_override_json(relative, data)
            files.append({"source": name, "path": relative, "size": len(data),
                          "sha256": hashlib.sha256(data).hexdigest(), "category": override_category(relative)})
        canonical = json.dumps([(f["path"], f["sha256"]) for f in files], ensure_ascii=False).encode("utf-8")
        warnings = ["Whole JSON files are replaced; missing entries are not inherited from the original file.",
                    "Use a new game. Keep the same packs installed for that playthrough. Gameplay compatibility is the mod author's responsibility."]
        ignored = len(source.entries) - len(files)
        if ignored:
            warnings.append("%d other file(s) excluded. This mode imports JSON only, not images or scripts." % ignored)
        return {"id": "mod_" + hashlib.sha256(b"override-v1\0" + canonical).hexdigest()[:20],
                "mode": "override", "source": str(source.path), "title": source.path.stem,
                "files": files, "bytes": sum(f["size"] for f in files), "workers": [], "images": [], "warnings": warnings}


def _valid_override_manifest(manifest):
    files = manifest.get("files")
    order = manifest.get("load_order")
    if (manifest.get("mode") != "override" or not isinstance(manifest.get("title"), str)
            or not isinstance(order, int) or isinstance(order, bool) or order < 1
            or manifest.get("workers") != 0 or manifest.get("worker_names") != []
            or not isinstance(files, list) or not 1 <= len(files) <= MAX_FILES):
        return False
    seen = set()
    for entry in files:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            return False
        path = safe_path(entry["path"])
        if not override_category(path) or path != entry["path"] or path in seen:
            return False
        if not isinstance(entry.get("sha256"), str) or not re.fullmatch("[0-9a-f]{64}", entry["sha256"]):
            return False
        seen.add(path)
    return True


def install_override_pack(plan, root, known_files):
    """Reuse the managed pack lifecycle without modifying any shipped file."""
    fresh = inspect_override_pack(plan["source"], known_files)
    if fresh["id"] != plan["id"]:
        raise PackError("The source changed after preview. Please inspect it again.")
    root = disk_path(root)
    root.mkdir(parents=True, exist_ok=True)
    target = root / fresh["id"]
    installed = installed_packs(root)
    if target.exists():
        if (target / REMOVE_MARKER).exists():
            raise PackError("This pack is scheduled for removal. Cancel its uninstall first.")
        if any(p["id"] == fresh["id"] for p in installed):
            return "already_installed"
        raise PackError("An incomplete installation exists. No files were overwritten.")
    if shutil.disk_usage(root).free < fresh["bytes"] + 32 * 1024 * 1024:
        raise PackError("Not enough free space to install this pack.")
    stage = Path(tempfile.mkdtemp(prefix=".install-", dir=str(root)))
    try:
        with Source(fresh["source"]) as source:
            for entry in fresh["files"]:
                data = source.read(entry["source"], MAX_JSON)
                if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                    raise PackError("The source changed while importing. Nothing was installed.")
                destination = stage / "content" / entry["path"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
        manifest = {"format": 2, "mode": "override", "id": fresh["id"], "title": fresh["title"],
                    "workers": 0, "worker_names": [], "images": 0, "bytes": fresh["bytes"],
                    "warnings": fresh["warnings"],
                    "load_order": 1 + max((p.get("load_order", 0) for p in installed), default=0),
                    "files": [{k: v for k, v in entry.items() if k != "source"} for entry in fresh["files"]]}
        (stage / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        stage.rename(target)
        return "installed"
    finally:
        if stage.exists():
            assert disk_path(stage.resolve()).parent == disk_path(root.resolve()) and stage.name.startswith(".install-")
            shutil.rmtree(stage)
