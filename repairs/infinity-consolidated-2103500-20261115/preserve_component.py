"""Use original pinned DEX inventory to check every compiled Cast class.

No installer is assembled. The entire signed500 APK is an immutable input.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import tempfile
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = '224d5f808587ce4004a96a003331abe7c71cbe7bd08ec6b1d3ec288c6c75cf40'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('apk', type=Path)
    parser.add_argument('dex', type=Path)
    parser.add_argument('jars', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    with args.apk.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == BASE
    path = ROOT / 'repairs/dual-experience-isolation-2103420/inventory.py'
    spec = importlib.util.spec_from_file_location('original_dex_inventory', path)
    inventory = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inventory)
    with tempfile.TemporaryDirectory(prefix='infinity500-classes-', dir='/dev/shm') as temp:
        temp = Path(temp)
        with ZipFile(args.apk) as apk:
            original = apk.read('classes6.dex')
        classes = []
        for name, data in [('baseline', original), ('candidate', args.dex.read_bytes())]:
            archive = temp / (name + '.zip')
            with ZipFile(archive, 'w') as z:
                z.writestr('classes.dex', data)
            folder = temp / name
            inventory.disassemble(archive, args.jars, folder)
            rows, _, _ = inventory.parse_dex(folder)
            classes.append(rows)
        old, new = classes
        assert set(old) == set(new) and len(old) == 1037, 'Class additions/removals refused'
        changed = sorted(name for name in old if old[name]['sha256'] != new[name]['sha256'])
        roots = ('Lcom/projectinfinity/kodi/InfinityCastSession', 'Lcom/projectinfinity/kodi/InfinityCastDialog')
        unexpected = [name for name in changed if not any(name == root + ';' or name.startswith(root + '$') for root in roots)]
        result = dict(status='FAIL_UNAPPROVED_CLASS_CHANGE' if unexpected else 'PASS_TWO_CAST_CLASS_ROOTS_ONLY',
                      baseline_APK_sha256=BASE, baseline_DEX_sha256=hashlib.sha256(original).hexdigest(),
                      candidate_DEX_sha256=hashlib.sha256(args.dex.read_bytes()).hexdigest(),
                      changed=changed, unexpected=unexpected, unchanged=len(old)-len(changed), total=len(old),
                      actual_owner_APK_assembled=False)
        args.out.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))
        assert not unexpected, unexpected


if __name__ == '__main__':
    main()
