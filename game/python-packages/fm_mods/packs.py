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
    content_roots = set()
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
        elif "/data/" in "/" + name:
            prefix, relative = ("/" + name).rsplit("/data/", 1)
            if content_kind("data/" + relative):
                content_roots.add(prefix.lstrip("/"))
    if not found and not content_roots:
        raise PackError("No workers.json, data/workers/*.json or supported data/ content found in this pack.")
    roots = {root for root, _ in found} | content_roots
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


# Additive content a character pack may carry besides workers. The game loads
# every JSON file in these folders, so each kind is installed as one namespaced
# file (<folder><pack id>.json) and never replaces a shipped file.
CONTENT_FOLDERS = {"traits": "data/traits/", "events": "data/events/",
                   "recruit": "data/events/recruit/",
                   "stories": "data/buildings/daily_story_extensions/"}
CONTENT_LABELS = {"traits": "traits", "events": "events", "recruit": "recruitment scenes",
                  "stories": "daily stories"}
CONTENT_SINGULAR = {"traits": "trait", "events": "event", "recruit": "recruitment scene",
                    "stories": "daily story"}
DOC_FILE = re.compile(r"(readme|license|licence|changelog|credits)[^/]*\.(txt|md)\Z", re.IGNORECASE)
CONDITION_PREFIXES = ("has_flag", "flag_value", "after_days_from_flag", "exact_date", "has_worker",
                      "not_has_worker", "has_folder_worker", "not_has_folder_worker", "after_date",
                      "before_days", "after_days")
SIMPLE_COMPARISON = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*\s*(?:==|!=|>=|<=|>|<)\s*"
                               r"(?:-?\d+(?:\.\d+)?|True|False|None|'[^'\\]*'|\"[^\"\\]*\")\Z")
STORY_MERGE_MODE = "append"
# The only evaluated flag value shipped data uses: "today" as a day number, read
# back by after_days_from_flag. Any other "[...]" value would run as code.
SAFE_FLAG_EXPRESSIONS = {"[calculate_total_days()]"}


def content_kind(relative):
    """Map a game-relative path to an additive content kind, or None."""
    if not relative.lower().endswith(".json"):
        return None
    for kind in ("recruit", "stories", "events", "traits"):
        folder = CONTENT_FOLDERS[kind]
        if relative.startswith(folder) and "/" not in relative[len(folder):]:
            return kind
    return None


def content_count(kind, rows):
    """Daily stories count stories, not the profession blocks holding them."""
    return sum(len(row.get("daily_stories", [])) for row in rows) if kind == "stories" else len(rows)


def _walk(value):
    """Yield every dict nested anywhere inside a JSON value."""
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            yield item
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)


def _check_condition(text, where):
    """The game eval()s comparisons it does not recognise; allow only data."""
    if not isinstance(text, str):
        raise PackError(where + ": conditions must be text.")
    for atom in re.split(r" AND | OR ", text.strip()):
        atom = atom.strip()
        if atom in ("True", "False"):
            continue
        prefix = atom.split(":", 1)[0]
        if ":" in atom and prefix in CONDITION_PREFIXES:
            continue
        if "__" not in atom and SIMPLE_COMPARISON.fullmatch(atom):
            continue
        raise PackError(where + ": unsupported condition '" + atom[:80] + "'. Use has_flag:, has_worker:, after_days: and similar prefixes.")


SFW_SKILLS = ("Combat", "Clever", "Charm", "Service", "Agility", "Craft")
NSFW_SKILLS = ("Sex", "Anal", "BDSM", "Hand", "Oral", "Homo", "Special", "Group", "Extreme", "Striptease")
KNOWN_SKILLS = SFW_SKILLS + NSFW_SKILLS + tuple("Specialty %d" % i for i in range(4, 13))


def _check_skill_requirements(event, kind):
    """Choice-level skill_requirements need a worker, real skill names and an
    NSFW rating when they test NSFW skills."""
    where = "Event " + str(event.get("id"))
    for choice in event.get("choices", []) if isinstance(event.get("choices"), list) else []:
        if not isinstance(choice, dict) or "skill_requirements" not in choice:
            continue
        requirements = choice["skill_requirements"]
        if kind == "recruit":
            raise PackError(where + ": skill_requirements is not supported in recruitment scenes.")
        if event.get("worker_selection") == "none" or choice.get("condition") == "building_skill":
            raise PackError(where + ": skill_requirements needs a worker; it can't be used with worker_selection \"none\" or building_skill.")
        if not isinstance(requirements, dict) or not requirements or len(requirements) > 6:
            raise PackError(where + ": skill_requirements must map 1 to 6 skills to minimum levels.")
        for skill, minimum in requirements.items():
            if skill not in KNOWN_SKILLS:
                raise PackError(where + ": unknown skill '" + str(skill)[:40] + "' in skill_requirements.")
            if isinstance(minimum, bool) or not isinstance(minimum, (int, float)) or not 0 <= minimum <= 300:
                raise PackError(where + ": skill_requirements minimums must be numbers from 0 to 300.")
            if skill in NSFW_SKILLS and not (event.get("nsfw") or choice.get("nsfw")):
                raise PackError(where + ": requires the NSFW skill " + skill + "; mark the event or the choice \"nsfw\": true.")
        condition = choice.get("condition")
        if condition and condition not in KNOWN_SKILLS:
            raise PackError(where + ": condition '" + str(condition)[:40] + "' is not a skill.")


def _check_scripted_values(value, where):
    """Reject the two JSON shapes the game evaluates as Python code."""
    for node in _walk(value):
        for key in ("start_when", "stop_when"):
            if node.get(key) is not None:  # Authoring tools write null for "no condition".
                _check_condition(node[key], where)
        flags = node.get("event_flags")
        if isinstance(flags, dict):
            for flag, flag_value in flags.items():
                if (isinstance(flag_value, str) and flag_value.startswith("[") and flag_value.endswith("]")
                        and flag_value not in SAFE_FLAG_EXPRESSIONS):
                    raise PackError(where + ": event flag '" + str(flag)[:60] + "' uses a [code] value, which packs cannot run.")


def _rows(value, key, where):
    if isinstance(value, dict):
        value = value.get(key, [value]) if key else [value]
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise PackError(where + ": expected a list of JSON objects.")
    return value


def _identifier(row, key, where):
    value = row.get(key)
    if not isinstance(value, str) or not value.strip() or len(value) > 200:
        raise PackError(where + ": every entry needs a text '" + key + "'.")
    return value


def content_entries(kind, value, where):
    """Normalise one content file to a list of entries for its kind."""
    if kind == "traits":
        return _rows(value, "traits", where)
    if kind in ("events", "recruit"):
        return _rows(value, None, where)
    if isinstance(value, dict) and "daily_story_extensions" in value:
        value = value["daily_story_extensions"]
    return _rows(value, None, where)


def _validate_content(content, catalog):
    """Check identities, references and evaluated strings. Returns per-kind ids."""
    catalog = catalog or {}
    ids = {"traits": [], "events": [], "stories": []}
    for kind, rows in content.items():
        label = CONTENT_LABELS[kind]
        for row in rows:
            if kind == "traits":
                ids["traits"].append(_identifier(row, "name", label))
            elif kind in ("events", "recruit"):
                event_id = _identifier(row, "id", label)
                if kind == "events" and event_id.startswith("event_recruit_"):
                    raise PackError("Event " + event_id + ": ids starting with event_recruit_ belong in data/events/recruit/.")
                ids["events"].append(event_id)
                _check_skill_requirements(row, kind)
            else:
                building, profession = row.get("building_id"), row.get("profession_id")
                if not isinstance(building, str) or not isinstance(profession, str):
                    raise PackError("Daily stories need building_id and profession_id.")
                professions = catalog.get("professions")
                if professions is not None and profession not in professions.get(building, ()):
                    raise PackError("Daily stories target an unknown profession: " + building + "/" + profession)
                if row.get("merge_mode", STORY_MERGE_MODE) != STORY_MERGE_MODE:
                    raise PackError("Daily stories in character packs must use merge_mode \"append\"; they cannot replace the game's stories.")
                stories = row.get("daily_stories")
                if not isinstance(stories, list) or not stories or any(not isinstance(s, dict) for s in stories):
                    raise PackError("Daily story extension for " + building + "/" + profession + " has no stories.")
                ids["stories"].extend(_identifier(s, "id", "daily stories") for s in stories)
            _check_scripted_values(row, label)
    for kind, values in ids.items():
        seen, taken = set(), set(catalog.get(kind, ()))
        for value in values:
            if value in seen:
                raise PackError("Duplicate " + kind[:-1] + " in pack: " + value)
            if value in taken:
                raise PackError("This " + kind[:-1] + " already exists in the game or another pack: " + value)
            seen.add(value)
    return ids


def game_catalog(files, read):
    """Identifiers already used by game data. read(name) returns bytes.

    Best effort: unreadable files are skipped, as the game's loaders do.
    """
    catalog = {"traits": set(), "events": set(), "stories": set(), "professions": {}}
    def load(name):
        try:
            return json.loads(read(name).decode("utf-8-sig"))
        except (OSError, ValueError, UnicodeError):
            return None
    for name in sorted(files):
        if not name.endswith(".json") or not name.startswith("data/"):
            continue
        kind = content_kind(name)
        value = load(name) if kind or name.startswith("data/buildings/") or name == "data/traits.json" else None
        if value is None:
            continue
        try:
            if kind is None and name.startswith("data/buildings/"):
                for building in value.get("building_types", []):
                    professions = catalog["professions"].setdefault(building.get("id"), set())
                    for profession in building.get("professions", []):
                        professions.add(profession.get("id"))
                        catalog["stories"].update(s.get("id") for s in profession.get("daily_stories", []) if hasattr(s, "get"))
            elif kind == "traits" or name == "data/traits.json":
                catalog["traits"].update(t.get("name") for t in content_entries("traits", value, name) if t.get("name"))
            elif kind in ("events", "recruit"):
                catalog["events"].update(e.get("id") for e in value if hasattr(e, "get") and e.get("id"))
            elif kind == "stories":
                for entry in content_entries("stories", value, name):
                    catalog["stories"].update(s.get("id") for s in entry.get("daily_stories", []) if hasattr(s, "get"))
        except (AttributeError, TypeError, PackError):
            continue
    for kind in ("traits", "events", "stories"):
        catalog[kind].discard(None)
    return catalog


def _taken_by_packs(root, exclude_id=None):
    taken = {"traits": set(), "events": set(), "stories": set()}
    for pack in installed_packs(root):
        if pack["id"] != exclude_id:
            for kind, values in (pack.get("content_ids") or {}).items():
                if kind in taken and isinstance(values, list):
                    taken[kind].update(v for v in values if isinstance(v, str))
    return taken


def check_pack_content(plan, root):
    """Reject content ids another installed pack already uses."""
    taken = _taken_by_packs(root, plan["id"])
    for kind, values in plan.get("content_ids", {}).items():
        clash = sorted(set(values) & taken.get(kind, set()))
        if clash:
            raise PackError("Another installed pack already uses these " + kind + ": " + ", ".join(clash[:5]))


def _merge_catalog(catalog, taken):
    merged = {key: set(value) if isinstance(value, (set, list)) else value for key, value in (catalog or {}).items()}
    for kind, values in taken.items():
        merged[kind] = set(merged.get(kind, ())) | values
    return merged


def _rewrite_references(value, names, folders):
    """Keep pack content pointing at the pack's workers after install renames."""
    def identity(raw, mapping):
        if isinstance(raw, str):
            return mapping.get(raw.strip(), raw)
        if isinstance(raw, list):
            return [identity(item, mapping) for item in raw]
        return raw
    def condition(text):
        if not isinstance(text, str):
            return text
        parts = re.split(r"( AND | OR )", text)
        for index, part in enumerate(parts):
            prefix, sep, target = part.strip().partition(":")
            mapping = names if prefix in ("has_worker", "not_has_worker") else folders if prefix in ("has_folder_worker", "not_has_folder_worker") else None
            if sep and mapping and target.strip() in mapping:
                parts[index] = part.replace(target, mapping[target.strip()], 1)
        return "".join(parts)
    for node in _walk(value):
        if "worker_name" in node:
            node["worker_name"] = identity(node["worker_name"], names)
        if "specific_worker_images" in node:
            node["specific_worker_images"] = identity(node["specific_worker_images"], folders)
        for key in ("start_when", "stop_when"):
            if key in node:
                node[key] = condition(node[key])
    return value


def inspect_pack(path, catalog=None):
    """catalog: identifiers from game_catalog(); None skips game-collision checks."""
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
        root_prefix = prefix + "/" if prefix else ""
        content = {}
        content_files = []
        for name in sorted(source.entries):
            if not name.startswith(root_prefix):
                continue
            kind = content_kind(name[len(root_prefix):])
            if not kind:
                continue
            # Same structural checks as overrides: syntax, duplicate keys, ids.
            value = _validate_override_json(name[len(root_prefix):], source.read(name, MAX_JSON))
            content.setdefault(kind, []).extend(content_entries(kind, value, name))
            content_files.append(name)
        content = {kind: rows for kind, rows in content.items() if rows}
        content_ids = _validate_content(content, catalog)
        if len(workers) > MAX_WORKERS or not (workers or content):
            raise PackError("A pack must contain up to 1,000 workers, or at least one event, trait or daily story.")
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
        docs = [name for name in source.entries if DOC_FILE.fullmatch(PurePosixPath(name).name)]
        ignored = len(source.entries) - len(json_files) - len(images) - len(content_files) - len(docs)
        if ignored:
            warnings.append("%d extra file(s) excluded: scripts, buildings, items and other files are not imported by character packs." % ignored)
        identity = {"workers": workers, "images": [(i["relative"], i["sha256"]) for i in images]}
        if content:
            # Worker-only packs keep the identity they had before content support.
            identity["content"] = content
        canonical = json.dumps(identity, sort_keys=True, ensure_ascii=False).encode("utf-8")
        pack_id = "mod_" + hashlib.sha256(canonical).hexdigest()[:20]
        content_bytes = len(json.dumps(content, ensure_ascii=False).encode("utf-8")) if content else 0
        return {"id": pack_id, "source": str(source.path), "title": source.path.stem,
                "workers": workers, "images": images, "warnings": sorted(set(warnings)),
                "content": content, "content_ids": content_ids,
                "bytes": sum(i["size"] for i in images) + content_bytes}


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
            content = manifest.get("content", [])
            if (not isinstance(manifest.get("title"), str) or
                    not isinstance(names, list) or not len(names) <= MAX_WORKERS or
                    any(not isinstance(name, str) or not name for name in names) or
                    manifest.get("workers") != len(names) or not _valid_content_manifest(content) or
                    not (names or content)):
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


def _content_path(kind, pack_id):
    return CONTENT_FOLDERS[kind] + pack_id + ".json"


def _valid_content_manifest(content):
    if not isinstance(content, list) or len(content) > len(CONTENT_FOLDERS):
        return False
    seen = set()
    for entry in content:
        if not isinstance(entry, dict) or entry.get("kind") not in CONTENT_FOLDERS or entry["kind"] in seen:
            return False
        if not isinstance(entry.get("sha256"), str) or not re.fullmatch("[0-9a-f]{64}", entry["sha256"]):
            return False
        seen.add(entry["kind"])
    return True


def install_pack(plan, root, reserved_names=(), rename_conflicts=False, catalog=None):
    """Stage completely, then publish a new directory atomically. Never overwrite."""
    root = disk_path(root)
    root.mkdir(parents=True, exist_ok=True)
    fresh = inspect_pack(plan["source"], _merge_catalog(catalog, _taken_by_packs(root, plan["id"])))
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
        content.mkdir()
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
        if workers:
            worker_dir = content / "data/workers"
            worker_dir.mkdir(parents=True)
            (worker_dir / (fresh["id"] + ".json")).write_text(json.dumps(workers, ensure_ascii=False, indent=2), encoding="utf-8")
        names = {entry["original"]: entry["imported"] for entry in renamed}
        folders = {original["folder"]: worker["folder"] for original, worker in zip(fresh["workers"], workers)}
        content_manifest = []
        for kind, rows in sorted(fresh["content"].items()):
            rows = _rewrite_references(json.loads(json.dumps(rows)), names, folders)
            if kind == "stories":
                rows = {"daily_story_extensions": [dict(row, merge_mode=STORY_MERGE_MODE) for row in rows]}
            data = json.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8")
            destination = content / _content_path(kind, fresh["id"])
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            content_manifest.append({"kind": kind, "sha256": hashlib.sha256(data).hexdigest(),
                                     "count": content_count(kind, fresh["content"][kind])})
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
                    "images": len(fresh["images"]), "bytes": fresh["bytes"], "warnings": fresh["warnings"], "renamed": renamed,
                    "content": content_manifest, "content_ids": fresh["content_ids"]}
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
                expected = {_content_path(entry["kind"], pack["id"]): entry for entry in pack.get("content", [])}
                if (allowed_json in source.entries) != bool(pack["workers"]):
                    continue
                if any(name != allowed_json and name not in expected and not (
                        name.startswith("images/workers/" + pack["id"] + "__") and
                        PurePosixPath(name).suffix.lower() in IMAGE_EXTENSIONS)
                        for name in source.entries):
                    continue
                if not set(expected) <= set(source.entries):
                    continue
                for name, entry in expected.items():
                    data = source.read(name, MAX_JSON)
                    if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                        raise PackError("Installed pack content changed: " + name)
                    value = _validate_override_json(name, data)
                    _validate_content({entry["kind"]: content_entries(entry["kind"], value, name)}, None)
                rows = json.loads(source.read(allowed_json, MAX_JSON).decode("utf-8")) if pack["workers"] else []
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
        raise PackError("Invalid JSON (syntax error or a key written twice): " + path) from exc
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
        raise PackError("Unexpected JSON structure: " + path)
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
        docs = [name for name in source.entries if DOC_FILE.fullmatch(PurePosixPath(name).name)]
        ignored = len(source.entries) - len(files) - len(docs)
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
