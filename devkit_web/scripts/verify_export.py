"""Verify a devkit ZIP with the game's real importer in temporary storage."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import zipfile

sys.dont_write_bytecode = True
parser = argparse.ArgumentParser()
parser.add_argument('pack', type=Path)
parser.add_argument('--mode', choices=('characters', 'override'), required=True)
parser.add_argument('--game-root', type=Path, default=Path(__file__).resolve().parents[2])
args = parser.parse_args()
root = args.game_root.resolve()
sys.path.insert(0, str(root / 'game/python-packages'))
from fm_mods import packs

known = [p.relative_to(root / 'game').as_posix() for p in (root / 'game/data').rglob('*.json')]
inspect = (lambda: packs.inspect_override_pack(args.pack, known)) if args.mode == 'override' else (lambda: packs.inspect_pack(args.pack))
plan = inspect()
with zipfile.ZipFile(args.pack) as archive:
    assert archive.testzip() is None, 'ZIP integrity check failed'
    with tempfile.TemporaryDirectory(prefix='fm-devkit-verify-', dir=args.pack.resolve().parent) as temporary:
        install_root = Path(temporary) / 'installed'
        if args.mode == 'override':
            result = packs.install_override_pack(plan, install_root, known)
        else:
            result = packs.install_pack(plan, install_root)
        assert result == 'installed', result
        mounted = packs.mount_paths(install_root)
        assert len(mounted) == 1, mounted
        if args.mode == 'override':
            for entry in plan['files']:
                assert (Path(mounted[0]) / entry['path']).read_bytes() == archive.read(entry['source'])
        else:
            for entry in plan['images']:
                relative = 'images/workers/' + plan['id'] + '__' + entry['relative']
                assert (Path(mounted[0]) / relative).read_bytes() == archive.read(entry['source'])
print(json.dumps({'accepted': True, 'installed': result, 'mode': args.mode, 'files': len(plan.get('files', [])), 'workers': len(plan['workers']), 'images': len(plan['images']), 'warnings': plan['warnings']}))
