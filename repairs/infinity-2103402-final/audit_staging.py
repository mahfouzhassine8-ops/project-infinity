"""Fail-closed staging inventory; does not claim APK or Android acceptance."""
import hashlib
import json
import os
from pathlib import Path
from zipfile import ZipFile

import clock_reflow_scope
import health_partial_scope
import home_reflow_scope
import information_spacing_scope
import visual_scope

ROOT = Path(__file__).parent
EXTRA = {
    'skin.infinity.diggz/unified/Home.xml': clock_reflow_scope.transform,
    'script.infinity.commandcenter/service.py': home_reflow_scope.transform,
    'script.infinity.commandcenter/information.py': information_spacing_scope.transform,
    health_partial_scope.PATH: health_partial_scope.transform,
}


def audit(apk, overlay=ROOT / 'overlay'):
    ledger = json.loads((ROOT / 'FILE-AUTHORIZATION-LEDGER.json').read_text())
    visual = {row['path'] for row in ledger['files']
              if row['path'].endswith('/VideoOSD.xml') or row['path'].endswith('/InfinityInformation.xml')}
    expected = visual | EXTRA.keys()
    actual = {p.relative_to(overlay).as_posix() for p in overlay.rglob('*') if p.is_file()}
    if actual != expected or any(p.is_symlink() for p in overlay.rglob('*')):
        raise ValueError('Unexplained or missing staged source member')
    rows = {}
    with ZipFile(apk) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())):
            raise ValueError('Duplicate APK members')
        for name in sorted(expected):
            original = archive.read('assets/addons/' + name)
            after = (overlay / name).read_bytes()
            permitted = EXTRA[name](original) if name in EXTRA else visual_scope.transform(name, original)
            if after != permitted:
                raise ValueError('Staged file does not match exact authorized transform: ' + name)
            rows[name] = {'baseline_sha256': hashlib.sha256(original).hexdigest(),
                          'staged_sha256': hashlib.sha256(after).hexdigest()}
    return {'status': 'PASS', 'scope': 'Exact staged addon sources only', 'members': rows,
            'production_apk_audit': 'NOT RUN', 'android17': 'NOT RUN', 'physical_fold': 'NOT RUN'}


if __name__ == '__main__':
    print(json.dumps(audit(os.environ['INFINITY_BASELINE_APK']), indent=2))
