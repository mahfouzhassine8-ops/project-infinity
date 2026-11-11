#!/usr/bin/env python3
"""Authenticated artifact verification only; no signing or application launch."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
BASE = '9cbb4c5f89a214924b6890463aa5842f85b18ff445d04d855e441fa61f4578c2'
ENGINE82 = '503f91109332ef050a604cf15ad604b16e156b55459bafd47c453c3f72de0437'


def digest(f):
    h = hashlib.sha256()
    for chunk in iter(lambda: f.read(1024*1024), b''):
        h.update(chunk)
    return h.hexdigest()


def file_hash(p):
    with p.open('rb') as f:
        return digest(f)


def members(p):
    result = {}
    with zipfile.ZipFile(p) as z:
        for name in z.namelist():
            assert name not in result, 'duplicate zip member'
            if name.endswith('/') or name.startswith('META-INF/'):
                continue
            with z.open(name) as f:
                result[name] = digest(f)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--base', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    base, candidate = list(a.base.rglob('*.apk')), list(a.candidate.rglob('*.apk'))
    assert len(base) == len(candidate) == 1, 'ambiguous APK'
    base, candidate = base[0], candidate[0]
    assert file_hash(base) == BASE
    sdk = Path(os.environ['ANDROID_HOME'])/'build-tools/35.0.0'
    sig = subprocess.check_output([str(sdk/'apksigner'), 'verify', '--verbose', '--print-certs', str(candidate)], text=True)
    (a.out/'SIGNATURE.txt').write_text(sig)
    assert CERT in sig.lower(), 'unexpected certificate'
    for v in (1, 2, 3):
        assert re.search(r'Verified using v'+str(v)+r' scheme[^\n]*: true', sig), 'signature scheme failed'
    badging = subprocess.check_output([str(sdk/'aapt'), 'dump', 'badging', str(candidate)], text=True)
    package = next(line for line in badging.splitlines() if line.startswith('package:'))
    assert "name='com.projectinfinity.kodi'" in package and "versionCode='2103482'" in package
    old, new = members(base), members(candidate)
    assert old.keys() == new.keys(), 'member set changed'
    changed = sorted(name for name in old if old[name] != new[name])
    assert changed == sorted(['AndroidManifest.xml', 'lib/arm64-v8a/libkodi.so', 'assets/experience-component-updates.properties']), changed
    assert new['lib/arm64-v8a/libkodi.so'] == ENGINE82
    report = dict(status='PASS_AUTHENTICATED_SIGNED82_ARTIFACT_AND_PRESERVATION',
                  source_run=42979187229, source_artifact=13836509327,
                  verification_run=os.environ.get('GITHUB_RUN_ID'),
                  source_commit=os.environ.get('GITHUB_SHA'),
                  package='com.projectinfinity.kodi', versionCode=2103482,
                  apk_sha256=file_hash(candidate), certificate_sha256=CERT,
                  signature_schemes=[1, 2, 3], baseline80_sha256=BASE,
                  engine_sha256=ENGINE82, changed_members=changed,
                  unchanged_members=len(new)-len(changed),
                  dex_and_addons_unchanged=True, cobra_unchanged=True,
                  application_execution='NOT_RUN', new_apk_created=False,
                  new_key_access=False)
    (a.out/'SIGNED82-VERIFICATION.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
            f.write('```json\n'+json.dumps(report, indent=2)+'\n```\n')


if __name__ == '__main__':
    main()
