"""Lazy JNI access, exclusively outside Ren'Py's save/rollback store."""
import json

_bridge = None


def _native():
    global _bridge
    if _bridge is None:
        from jnius import autoclass
        _bridge = autoclass("org.fantasymanager.mods.ModImportActivity")
    return _bridge


def start():
    from jnius import autoclass
    activity = autoclass("org.renpy.android.PythonSDLActivity").mActivity
    if not _native().open(activity):
        raise RuntimeError("A file selection is already in progress.")


def poll():
    return json.loads(_native().poll())


def discard():
    if _bridge is not None:
        _bridge.discard()
