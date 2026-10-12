#!/usr/bin/env python3
"""Immediate-parent preservation for the isolated cancelled-script candidate."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'repairs/mobile-regressions-2103304'))
from packaging_checks import DEX, SIGNATURE, dex_contract, require, manifest_tree

BASELINE_SHA = 'a6b22a0b761ddc9eba108e1f235001c961592dd911edff8c48a0abc6fb3592c8'
OLD_TAG = 'infinity-checkpoint-installer-close-2103368-v1'
NEW_TAG = 'infinity-checkpoint-cancelled-script-2103369-v1'


def compare(old, new):
    for archive in (old, new):
        require(archive.testzip() is None and len(archive.namelist()) == len(set(archive.namelist())), 'Corrupt or duplicate APK')
    left = {n for n in old.namelist() if not SIGNATURE.fullmatch(n)}
    right = {n for n in new.namelist() if not SIGNATURE.fullmatch(n)}
    require(left == right, '2103368 payload inventory changed')
    allowed = {'AndroidManifest.xml', 'lib/arm64-v8a/libkodi.so'}
    protected = sorted(n for n in left if n not in allowed and not DEX.fullmatch(n))
    for name in protected:
        require(old.read(name) == new.read(name), '2103368 protected payload changed: ' + name)
    require(dex_contract(old) == dex_contract(new), '2103368 JNI or Java class inventory changed')
    require(old.read('lib/arm64-v8a/libkodi.so') != new.read('lib/arm64-v8a/libkodi.so'), 'Repaired engine was not packaged')
    require(NEW_TAG.encode() in new.read('lib/arm64-v8a/libkodi.so'), 'Wrong repaired engine identity')
    return dict(candidate_version=2103369, baseline_version=2103368, baseline_sha256=BASELINE_SHA,
                protected_entries_byte_identical=len(protected), all_assets_byte_identical=True,
                resources_byte_identical=True, other_native_libraries_byte_identical=True,
                jni_and_java_class_inventory_unchanged=True, physical_fold_verified=False, locked=False)


def normalized_smali(name, text):
    if name == 'com/projectinfinity/kodi/InfinityHealthExport.smali':
        return text.replace(NEW_TAG, OLD_TAG)
    if name == 'com/projectinfinity/kodi/BuildConfig.smali':
        return text.replace('1.0.9-Cancelled-Script-Receipt-RC1', '1.0.9-Installer-Close-RC1').replace('0x201849', '0x201848')
    return text


def compare_smali(old, new):
    require(set(old) == set(new), 'Android class inventory drift')
    changed = []
    for name in sorted(old):
        require(normalized_smali(name, old[name]) == normalized_smali(name, new[name]),
                'Android instructions changed outside exact candidate constants: ' + name)
        if old[name] != new[name]:
            changed.append(name)
    require('com/projectinfinity/kodi/InfinityHealthExport.smali' in changed, 'Exporter candidate tag was not compiled')
    return dict(android_classes_checked=len(old), changed_classes=changed,
                only_exporter_tag_and_build_version_constants_changed=True)


def verify_dex(base, donor, classpath):
    with tempfile.TemporaryDirectory(prefix='receipt-dex-proof-') as work:
        maps = []
        for label, apk in (('base', base), ('donor', donor)):
            root = Path(work) / label
            root.mkdir()
            smali = root / 'smali'
            with zipfile.ZipFile(apk) as z:
                for name in z.namelist():
                    if DEX.fullmatch(name):
                        dex = root / name
                        dex.write_bytes(z.read(name))
                        subprocess.run(['java', '-cp', classpath, 'org.jf.baksmali.Main', 'disassemble', str(dex), '-o', str(smali)], check=True)
            maps.append({p.relative_to(smali).as_posix(): p.read_text() for p in smali.rglob('*.smali')})
        return compare_smali(*maps)


def main():
    p = argparse.ArgumentParser()
    for name in ('baseline', 'candidate', 'report'):
        p.add_argument('--' + name, required=True, type=Path)
    p.add_argument('--android-donor', action='store_true')
    p.add_argument('--classpath', type=Path)
    p.add_argument('--aapt', type=Path)
    args = p.parse_args()
    require(hashlib.sha256(args.baseline.read_bytes()).hexdigest() == BASELINE_SHA, 'Wrong immediate parent 2103368 APK')
    if args.android_donor:
        require(args.classpath is not None, 'DEX preservation classpath is required')
        result = verify_dex(args.baseline, args.candidate, args.classpath.read_text().strip())
    else:
        with zipfile.ZipFile(args.baseline) as old, zipfile.ZipFile(args.candidate) as new:
            result = compare(old, new)
        require(args.aapt is not None, 'Manifest verification tool is required')
        trees = []
        for apk in (args.baseline, args.candidate):
            t = manifest_tree(subprocess.check_output([str(args.aapt), 'dump', 'xmltree', str(apk), 'AndroidManifest.xml'], text=True))
            for key in ('android:versionCode', 'android:versionName'):
                t['attrs'].pop(key, None)
            trees.append(t)
        require(trees[0] == trees[1], '2103368 manifest changed outside candidate identity')
        result['manifest_unchanged_except_version'] = True
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS exact 2103368 immediate-parent preservation')


if __name__ == '__main__':
    main()
