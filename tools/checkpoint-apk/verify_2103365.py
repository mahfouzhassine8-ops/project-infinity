#!/usr/bin/env python3
"""Exact green 2103365 preservation; enumerated system-stability delta only."""
import argparse
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'repairs/mobile-regressions-2103304'))
from packaging_checks import DEX, SIGNATURE, dex_contract, require

BASELINE_SHA = '251851c1a97eac0430632aa7f74cde45d306bbbda1094629dfb26820412baa72'
ASSETS = {'assets/infinity/checkpoint-controller.zip', 'assets/infinity/checkpoint-controller-20.zip'}
REVIEWED = ('InfinityCheckpointAddonInstaller', 'InfinityCheckpointController20Installer', 'InfinityHealthExport')
ADDED = {'Lcom/projectinfinity/kodi/InfinityInstalledCodeEvidence;'}

def compare(a, b):
    for archive in (a, b):
        require(archive.testzip() is None and len(archive.namelist()) == len(set(archive.namelist())), 'Corrupt or duplicate APK payload')
    left = {n for n in a.namelist() if not SIGNATURE.fullmatch(n)}
    right = {n for n in b.namelist() if not SIGNATURE.fullmatch(n)}
    require(left == right, 'APK entry inventory drift from green 2103365')
    allowed = {'AndroidManifest.xml', 'lib/arm64-v8a/libkodi.so'} | ASSETS
    protected = sorted(n for n in left if n not in allowed and not DEX.fullmatch(n))
    for name in protected:
        require(a.read(name) == b.read(name), 'Protected green payload changed: ' + name)
    old_jni, old_classes = dex_contract(a)
    new_jni, new_classes = dex_contract(b)
    require(old_jni == new_jni, 'Protected JNI declaration drift')
    prefixes = tuple('Lcom/projectinfinity/kodi/' + n + '$' for n in REVIEWED)
    require(all(n.startswith(prefixes) for n in old_classes - new_classes), 'Unreviewed Java class removal')
    require(all(n in ADDED or n.startswith(prefixes) for n in new_classes - old_classes), 'Unreviewed Java class addition')
    for name in ASSETS:
        with zipfile.ZipFile(io.BytesIO(a.read(name))) as old, zipfile.ZipFile(io.BytesIO(b.read(name))) as new:
            require(old.testzip() is None and new.testzip() is None, 'Corrupt script asset')
            require(set(old.namelist()) == set(new.namelist()), 'Script asset inventory drift')
            prior = json.loads(old.read('manifest.json'))
            current = json.loads(new.read('manifest.json'))
            for key in ('schema', 'addon_id', 'addon_version', 'addon_xml_sha256'):
                require(prior[key] == current[key], 'Script identity drift: ' + key)
            pins = {row['path']: row for row in prior['files']}
            require(set(pins) == {row['path'] for row in current['files']}, 'Script manifest inventory drift')
            for row in current['files']:
                p = row['path']
                require(row['before'] == pins[p]['before'] and row['previous'] == pins[p]['previous'] and row['baseline'] == pins[p]['after'], 'Unreviewed script preimage: ' + p)
                raw = new.read('payload/' + p)
                require(hashlib.sha256(raw).hexdigest() == row['after'], 'Bad script postimage: ' + p)
                if p not in ('service.py', 'plugin.py', 'resume_hub.py'):
                    require(raw == old.read('payload/' + p), 'Unrelated script mutation: ' + p)
    return dict(baseline_version=2103365, baseline_sha256=BASELINE_SHA,
                protected_entries_byte_identical=len(protected), jni_unchanged=True,
                reviewed_android_owners=list(REVIEWED), added_java_classes=sorted(new_classes-old_classes),
                changed_script_files=['service.py', 'plugin.py', 'resume_hub.py'], physical_fold_verified=False)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('baseline', 'candidate', 'report'): p.add_argument('--' + name, required=True, type=Path)
    args = p.parse_args()
    require(hashlib.sha256(args.baseline.read_bytes()).hexdigest() == BASELINE_SHA, 'Wrong green 2103365 APK')
    with zipfile.ZipFile(args.baseline) as a, zipfile.ZipFile(args.candidate) as b: result = compare(a, b)
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS exact green 2103365 payload, script identities/preimages and reviewed Java/JNI delta')
