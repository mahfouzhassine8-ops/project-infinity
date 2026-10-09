#!/usr/bin/env python3
"""Use the inherited signer/asset gates and verify the new diagnostic engine."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VERSION = 2103338
RELEASE = '1.0.9-Join-Target-Diagnostic-RC1'
TAG = 'infinity-shutdown-2103338-diagnostic-v1'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def load_parent():
    spec = importlib.util.spec_from_file_location('join_diagnostic_parent_package', ROOT / 'tools/checkpoint-apk/package.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.VERSION = VERSION
    module.RELEASE = RELEASE
    return module

def associated_native(parent, args):
    proof = json.loads((args.engine / 'ENGINE-PROOF.json').read_text())
    manifest_path = args.engine / 'SOURCE-MANIFEST.json'
    manifest = json.loads(manifest_path.read_text())
    expected_changes = sorted(['xbmc/interfaces/generic/LanguageInvokerThread.cpp',
                               'xbmc/interfaces/generic/LanguageInvokerThread.h',
                               'xbmc/interfaces/generic/InfinityInvokerTarget.h',
                               'xbmc/platform/android/activity/InfinityShutdownTrace.h'])
    parent.require(proof['source_commit'] == os.environ['GITHUB_SHA'], 'Wrong native source revision')
    parent.require(proof['diagnostic_only'] is True and proof['shutdown_behavior_changed'] is False,
                   'Unexpected diagnostic behavior contract')
    parent.require(proof['engine_tag'] == TAG and proof['diagnostic_changes'] == expected_changes,
                   'Unexpected engine diagnostic scope')
    parent.require(proof['protected_parent_inputs_preserved'] is True, 'Source protection missing')
    parent.require(sha(manifest_path.read_bytes()) == proof['diagnostic_source_manifest_sha256'],
                   'Diagnostic source receipt mismatch')
    original = parent.RUNTIME / 'runtime/native/manifest.json'
    parent.require(sha(original.read_bytes()) == proof['source_manifest_sha256'], 'Parent overlay changed')
    parent.require(manifest['before'] == json.loads(original.read_text())['after'], 'Wrong native parent map')
    parent.require(manifest['changed'] == expected_changes and manifest['deleted'] == [], 'Wrong native delta')
    before, after = manifest['before'], manifest['after']
    parent.require(set(after) == set(before) | {'xbmc/interfaces/generic/InfinityInvokerTarget.h'}, 'Source-map coverage changed')
    parent.require(all(after[name] == digest for name, digest in before.items() if name not in expected_changes),
                   'Protected native source changed')
    native = args.engine / 'libkodi.so'
    data = native.read_bytes()
    parent.require(sha(data) == proof['native_sha256'], 'Native binary/source proof mismatch')
    for token in (TAG.encode(), b'scripts.target_before_join', b'os_tid.%u.stage.%s'):
        parent.require(token in data, 'Diagnostic implementation absent')
    parent.android_ci.factory.elf_identity(native, args.out / 'native-elf.txt')
    target = args.out / 'libkodi.so'
    shutil.copyfile(native, target)
    strip = Path(os.environ['ANDROID_HOME']) / 'ndk' / os.environ['NDK_VER'] / 'toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip'
    parent.run(strip, '--strip-unneeded', target)
    parent.android_ci.factory.elf_identity(target, args.out / 'packaged-elf.txt')
    for name in ('ENGINE-PROOF.json', 'SOURCE-MANIFEST.json', 'elf-identity.txt'):
        shutil.copyfile(args.engine / name, args.out / ('native-' + name))
    return target, proof

def finish(parent, args):
    receipt_path = args.previous_receipt
    if receipt_path.is_dir():
        receipts = list(receipt_path.rglob('DELIVERY.json'))
        parent.require(len(receipts) == 1, 'Previous delivery receipt is ambiguous')
        receipt_path = receipts[0]
    previous_receipt = json.loads(receipt_path.read_text())
    parent.require(previous_receipt['candidate'] == 2103337, 'Wrong previous diagnostic candidate')
    parent.require(previous_receipt['source_commit'] == '83bb461c1523f7e648ea4b32148e9e9eb7998598', 'Wrong 3337 package source')
    parent.require(sha(args.previous_apk.read_bytes()) == previous_receipt['sha256'], 'Previous APK/receipt mismatch')
    parent.associated_native = lambda a: associated_native(parent, a)
    parent.finish(args)
    original = args.out / f'Infinity-{VERSION}-Checkpoint-Installed-Fix-RC1.apk'
    final = args.out / f'Infinity-{VERSION}-Join-Target-Diagnostic-RC1.apk'
    original.rename(final)
    with zipfile.ZipFile(args.previous_apk) as old, zipfile.ZipFile(final) as new:
        ignored = lambda n: n == 'AndroidManifest.xml' or n == parent.ENGINE or parent.DEX.fullmatch(n) or parent.SIGNATURE.fullmatch(n)
        protected = {n for n in old.namelist() if not ignored(n)}
        parent.require(protected == {n for n in new.namelist() if not ignored(n)}, 'Previous APK payload coverage changed')
        for name in protected:
            parent.require(old.read(name) == new.read(name), 'Previous protected APK entry changed: ' + name)
        parent.require(parent.dex_contract(old) == parent.dex_contract(new), 'Previous APK class/JNI coverage changed')
    path = args.out / 'DELIVERY.json'
    result = json.loads(path.read_text())
    result.update(file=final.name, purpose='join-target diagnostic capture; shutdown root cause remains unproven',
                  previous_candidate=2103337, previous_apk_sha256=previous_receipt['sha256'],
                  previous_protected_entries=len(protected), engine_tag=TAG,
                  diagnostic_only=True, shutdown_behavior_changed=False, device_accepted=False, locked=False)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('stage', 'package'))
    for name in ('source', 'base', 'build', 'out', 'engine'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--previous-apk', type=Path)
    parser.add_argument('--previous-receipt', type=Path)
    args = parser.parse_args()
    for name in ('source', 'base', 'build', 'out', 'engine'):
        setattr(args, name, getattr(args, name).resolve())
    args.out.mkdir(parents=True, exist_ok=True)
    parent = load_parent()
    if args.mode == 'stage':
        parent.stage(args)
    else:
        if args.previous_apk is None or args.previous_receipt is None:
            parser.error('Packaging requires the previous candidate APK and receipt')
        finish(parent, args)

if __name__ == '__main__':
    main()
