#!/usr/bin/env python3
"""Exact protected 2103365 APK payload and reviewed 2103367 integration assets."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

import verify_2103365 as baseline
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'repairs/android-checkpoint-shutdown'))
import participant_asset
import android_ci
from packaging_checks import DEX, SIGNATURE, dex_contract, require

ASSETS = baseline.ASSETS
REVIEWED = baseline.REVIEWED + ('InfinityCheckpointEvidence', 'InfinityInstalledCodeEvidence', 'InfinityInstalledCheckpointInstaller')
ADDED = baseline.ADDED | {'Lcom/projectinfinity/kodi/InfinityCheckpointEvidence;'}


def asset_bytes():
    return {'assets/infinity/checkpoint-controller.zip': participant_asset.build(),
            'assets/infinity/checkpoint-controller-20.zip': android_ci.installed_build.build('script.infinity.commandcenter')}


def compare(a, b):
    for archive in (a, b):
        require(archive.testzip() is None and len(archive.namelist()) == len(set(archive.namelist())), 'Corrupt or duplicate APK')
    left = {n for n in a.namelist() if not SIGNATURE.fullmatch(n)}
    right = {n for n in b.namelist() if not SIGNATURE.fullmatch(n)}
    require(left == right, 'Protected APK inventory changed')
    allowed = {'AndroidManifest.xml', 'lib/arm64-v8a/libkodi.so'} | ASSETS
    protected = sorted(n for n in left if n not in allowed and not DEX.fullmatch(n))
    for name in protected:
        require(a.read(name) == b.read(name), 'Protected payload changed: ' + name)
    old_jni, old_classes = dex_contract(a)
    new_jni, new_classes = dex_contract(b)
    require(old_jni == new_jni, 'Protected JNI declaration drift')
    prefixes = tuple('Lcom/projectinfinity/kodi/' + n + '$' for n in REVIEWED)
    require(all(n.startswith(prefixes) for n in old_classes-new_classes), 'Protected Java class removed')
    require(all(n in ADDED or n.startswith(prefixes) for n in new_classes-old_classes), 'Unexpected Java class added')
    expected = asset_bytes()
    for name in ASSETS:
        require(b.read(name) == expected[name], 'APK does not contain exact reviewed code asset: ' + name)
        with zipfile.ZipFile(io.BytesIO(a.read(name))) as old, zipfile.ZipFile(io.BytesIO(b.read(name))) as new:
            prior, current = (json.loads(z.read('manifest.json')) for z in (old, new))
            for key in ('schema', 'addon_id', 'addon_version', 'addon_xml_sha256'):
                require(prior[key] == current[key], 'Add-on identity changed: ' + key)
            pins = {row['path']: row for row in prior['files']}
            require(set(new.namelist()) == set(old.namelist()) | {'payload/context.py', 'payload/addon.xml'}, 'Unexpected script asset member')
            require(set(pins) | {'context.py', 'addon.xml'} == {row['path'] for row in current['files']}, 'Unexpected script manifest path')
            for row in current['files']:
                path = row['path']
                if path in pins:
                    require(row['before'] == pins[path]['before'] and row['previous'] == pins[path]['previous'] and row['baseline'] == pins[path]['after'], 'Unreviewed script preimage: ' + path)
                elif path == 'addon.xml':
                    require(row['before'] == prior['addon_xml_sha256'] and row['baseline'] == prior['addon_xml_sha256'], 'Unverified original context marker')
                else:
                    require(row['before'] is None and row['baseline'] is None and row['previous'] is None and row['rejected'] is None, 'New context code has a false preimage')
                require(hashlib.sha256(new.read('payload/' + path)).hexdigest() == row['after'], 'Script postimage mismatch')
    return dict(candidate_version=2103367, baseline_version=2103365, baseline_sha256=baseline.BASELINE_SHA,
                protected_entries_byte_identical=len(protected), jni_unchanged=True,
                skin_payload_unchanged=True, health_center_payload_unchanged=True,
                reviewed_android_owners=list(REVIEWED), added_java_classes=sorted(new_classes-old_classes),
                code_asset_sha256={n: hashlib.sha256(v).hexdigest() for n, v in expected.items()},
                physical_fold_verified=False, locked=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('baseline', 'candidate', 'report'): p.add_argument('--' + name, required=True, type=Path)
    args = p.parse_args()
    require(hashlib.sha256(args.baseline.read_bytes()).hexdigest() == baseline.BASELINE_SHA, 'Wrong protected APK')
    with zipfile.ZipFile(args.baseline) as a, zipfile.ZipFile(args.candidate) as b: result = compare(a, b)
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS exact protected 2103365 APK, JNI and unrelated payloads; reviewed 2103367 assets')
