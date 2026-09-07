"""One-time cleanup for Python package bytecode left by older builds."""

from __future__ import annotations

import os
import shutil


STAMP_NAME = "fm_python_package_epoch.txt"


def _read_epoch(stamp_path):
    try:
        with open(stamp_path, "r", encoding="utf-8") as stream:
            return stream.read().strip()
    except OSError:
        return None


def ensure_clean_python_package_cache(game_dir, epoch):
    """Remove stale package bytecode once for the requested release epoch."""
    game_dir = os.fspath(game_dir)
    epoch = str(epoch)
    cache_root = os.path.join(game_dir, "cache")
    stamp_path = os.path.join(cache_root, STAMP_NAME)
    if _read_epoch(stamp_path) == epoch:
        return {
            "cleaned": False,
            "removed_files": 0,
            "removed_dirs": 0,
            "errors": (),
        }

    package_root = os.path.join(game_dir, "python-packages")
    removed_files = 0
    removed_dirs = 0
    errors = []

    if os.path.isdir(package_root):
        for current, directories, filenames in os.walk(package_root, topdown=False):
            for filename in filenames:
                if not filename.lower().endswith((".pyc", ".pyo")):
                    continue
                path = os.path.join(current, filename)
                try:
                    os.remove(path)
                    removed_files += 1
                except OSError as exc:
                    errors.append("%s: %s" % (path, exc))

            for dirname in directories:
                if dirname != "__pycache__":
                    continue
                path = os.path.join(current, dirname)
                try:
                    shutil.rmtree(path)
                    removed_dirs += 1
                except OSError as exc:
                    errors.append("%s: %s" % (path, exc))

    if not errors:
        temporary_stamp = stamp_path + ".tmp"
        try:
            os.makedirs(cache_root, exist_ok=True)
            with open(temporary_stamp, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(epoch + "\n")
            os.replace(temporary_stamp, stamp_path)
        except OSError as exc:
            errors.append("%s: %s" % (stamp_path, exc))
            try:
                os.remove(temporary_stamp)
            except OSError:
                pass

    return {
        "cleaned": True,
        "removed_files": removed_files,
        "removed_dirs": removed_dirs,
        "errors": tuple(errors),
    }
