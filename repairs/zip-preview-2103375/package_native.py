#!/usr/bin/env python3
"""Native-only test APK: exact locked DEX/assets/resources plus reviewed libkodi and version."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

from manifest_patch import patch, CODE, NAME

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'repairs/mobile-regressions-2103304'))
from packaging_checks import manifest_tree, resource_ids, run
from package_candidate import elf_identity

PARENT = '160adfccc775f83c640354778e54f6f33164084413401f9c348ebe9ea41fb3e4'
ENGINE = 'lib/arm64-v8a/libkodi.so'
SIGNER = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
SIGNATURE = re.compile(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:RSA|DSA|EC|SF))')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def unique(directory, name):
    files = list(directory.rglob(name))
    assert len(files) == 1, (name, files)
    return files[0]


def package(args):
    assert sha(args.parent.read_bytes()) == PARENT, 'Incorrect locked APK 2103374'
    args.out.mkdir(parents=True, exist_ok=True)
    engine = unique(args.engine, 'libkodi.so')
    proof = json.loads(unique(args.proof, 'ENGINE-PROOF.json').read_text())
    source = json.loads(unique(args.proof, 'FILE-PREVIEW-NATIVE-PRESERVATION.json').read_text())
    current_delta = json.loads((HERE / 'native-delta.json').read_text())['files']
    assert proof['native_sha256'] == sha(engine.read_bytes())
    assert proof['preview_delta'] == current_delta, 'Native artifact from a superseded source delta'
    assert source['changed'] == sorted(entry['file'] for entry in current_delta)
    assert all(source['before'].get(entry['file']) == entry['before'] and source['after'][entry['file']] == entry['after']
               for entry in current_delta)
    assert all(source['after'][name] == digest for name, digest in source['before'].items() if name not in source['changed'])
    tests = json.loads(unique(args.tests, 'RUNTIME-RESULTS.json').read_text())
    assert tests['totals'] == {'tests': 207, 'failures': 0, 'errors': 0, 'skipped': 0}
    inherited = json.loads(unique(args.tests, 'SAVED-TEST-PRESERVATION.json').read_text())
    assert inherited['original_test_names_preserved'] == 206 and inherited['inherited_sources_unchanged']
    for name in ('INFINITY_KEYSTORE_B64', 'INFINITY_STORE_PASSWORD', 'INFINITY_KEY_PASSWORD', 'INFINITY_KEY_ALIAS'):
        assert os.environ.get(name), 'Missing mandatory permanent signing setting: ' + name
    bt = Path(os.environ['ANDROID_HOME']) / 'build-tools/34.0.0'
    # Use the existing release packaging strip recipe. Full compile evidence
    # retains the unstripped engine; it must not inflate the installable APK.
    unstripped = engine
    identity = elf_identity(unstripped, args.out / 'unstripped-elf-identity.txt')
    engine = args.out / 'libkodi.so'
    shutil.copyfile(unstripped, engine)
    strip = Path(os.environ['ANDROID_HOME']) / 'ndk' / os.environ.get('NDK_VER', '21.4.7075529') / 'toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip'
    run(strip, '--strip-unneeded', engine)
    stripped_identity = elf_identity(engine, args.out / 'packaged-elf-identity.txt')
    assert identity[0] == stripped_identity[0]
    assert identity[0] != 'build-id' or identity == stripped_identity
    for token in (b'Infinity.FilePreview.AcceptNonce', b'special://skin/resources/lib/infinity_file_preview.py',
                  b'/InfinityAndroidKeyboard', b'_infinityHeartbeat'):
        assert token in engine.read_bytes(), 'Required compiled native identity lost during strip'
    with zipfile.ZipFile(args.parent) as parent:
        assert parent.testzip() is None and len(parent.namelist()) == len(set(parent.namelist()))
        before_manifest = parent.read('AndroidManifest.xml')
        manifest, edits = patch(before_manifest)
        before_native = parent.read(ENGINE)
        assert sha(before_native) == proof['immediate_parent_native_sha256']
        protected = {name for name in parent.namelist() if name not in (ENGINE, 'AndroidManifest.xml') and not SIGNATURE.fullmatch(name)}
        signature_files = [name for name in parent.namelist() if SIGNATURE.fullmatch(name)]
    unsigned = args.out / 'preview-unsigned.apk'
    shutil.copyfile(args.parent, unsigned)
    subprocess.run(['zip', '-q', '-d', str(unsigned.resolve()), *signature_files], check=True)
    with tempfile.TemporaryDirectory(prefix='infinity-native-preview-package-') as directory:
        directory = Path(directory)
        for name, data in [(ENGINE, engine.read_bytes()), ('AndroidManifest.xml', manifest)]:
            file = directory / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(data)
            file.chmod(0o644)
            os.utime(file, (1791763200, 1791763200))
        subprocess.run(['zip', '-q', '-X', '-0', str(unsigned.resolve()), ENGINE], cwd=directory, check=True)
        subprocess.run(['zip', '-q', '-X', '-9', str(unsigned.resolve()), 'AndroidManifest.xml'], cwd=directory, check=True)
        parent_library = directory / 'parent-libkodi.so'
        parent_library.write_bytes(before_native)
        old_dynamic = run('readelf', '-d', '-W', parent_library, output=args.out / 'parent-elf-dynamic.txt')
        new_dynamic = run('readelf', '-d', '-W', engine, output=args.out / 'candidate-elf-dynamic.txt')
        needed = lambda text: sorted(re.findall(r'\(NEEDED\).*?\[(.*?)\]', text))
        assert needed(old_dynamic) == needed(new_dynamic), 'Native ELF dependency list changed'
        old_symbols = run('readelf', '--dyn-syms', '-W', parent_library, output=args.out / 'parent-elf-symbols.txt')
        new_symbols = run('readelf', '--dyn-syms', '-W', engine, output=args.out / 'candidate-elf-symbols.txt')
        def exports(text):
            return {parts[-1].split('@', 1)[0] for line in text.splitlines()
                    if len(parts := line.split()) >= 8 and parts[4] == 'GLOBAL' and parts[5] == 'DEFAULT' and parts[6] != 'UND'}
        missing = exports(old_symbols) - exports(new_symbols)
        assert not missing, 'Required exported native symbols removed: ' + repr(sorted(missing))
    final = args.out / 'Cobra-2103375-File-Preview-Native-RC1.apk'
    run('bash', ROOT / 'scripts/sign-infinity71.sh', unsigned, final)
    for label, file in [('parent', args.parent), ('candidate', final)]:
        signature = run(bt / 'apksigner', 'verify', '--verbose', '--print-certs', file, output=args.out / (label + '-signature.txt'))
        assert SIGNER in signature.lower(), 'Permanent signing identity changed'
        assert 'Verified using v2 scheme (APK Signature Scheme v2): true' in signature
        assert 'Verified using v3 scheme (APK Signature Scheme v3): true' in signature
    manifests = []
    for label, file in [('parent', args.parent), ('candidate', final)]:
        tree = manifest_tree(run(bt / 'aapt', 'dump', 'xmltree', file, 'AndroidManifest.xml', output=args.out / (label + '-manifest.txt')))
        for name in ('android:versionCode', 'android:versionName'):
            tree['attrs'].pop(name, None)
        manifests.append(tree)
    assert manifests[0] == manifests[1], 'Manifest changed outside version identity'
    assert resource_ids(bt / 'aapt2', args.parent, args.out / 'parent-resources.txt') == resource_ids(bt / 'aapt2', final, args.out / 'candidate-resources.txt')
    badging = run(bt / 'aapt', 'dump', 'badging', final, output=args.out / 'badging.txt')
    assert f"package: name='com.projectinfinity.kodi' versionCode='{CODE}' versionName='{NAME}'" in badging
    assert 'application-debuggable' not in badging
    run(bt / 'zipalign', '-c', '-p', '4', final, output=args.out / 'alignment.txt')
    with zipfile.ZipFile(args.parent) as parent, zipfile.ZipFile(final) as candidate:
        assert candidate.testzip() is None and len(candidate.namelist()) == len(set(candidate.namelist()))
        assert {name for name in parent.namelist() if not SIGNATURE.fullmatch(name)} == {name for name in candidate.namelist() if not SIGNATURE.fullmatch(name)}
        for name in protected:
            assert parent.read(name) == candidate.read(name), 'Protected payload changed: ' + name
        assert candidate.read(ENGINE) == engine.read_bytes()
        assert candidate.read('AndroidManifest.xml') == manifest
        native = {name: sha(candidate.read(name)) for name in candidate.namelist() if name.startswith('lib/') and name.endswith('.so')}
        dex = {name: sha(candidate.read(name)) for name in candidate.namelist() if re.fullmatch(r'classes\d*\.dex', name)}
    receipt = {'file': final.name, 'bytes': final.stat().st_size, 'sha256': sha(final.read_bytes()),
               'parent_version': 2103374, 'parent_sha256': PARENT, 'parent_bytes': args.parent.stat().st_size,
               'version_code': CODE, 'version_name': NAME, 'package': 'com.projectinfinity.kodi',
               'source_commit': os.environ['GITHUB_SHA'], 'native_source_commit': proof['source_commit'],
               'native_binary': {'unstripped_sha256': proof['native_sha256'], 'unstripped_bytes': unstripped.stat().st_size,
                                 'packaged_sha256': sha(engine.read_bytes()), 'packaged_bytes': engine.stat().st_size,
                                 'strip_recipe': 'NDK 21.4.7075529 llvm-strip --strip-unneeded (unchanged release recipe)'},
               'run_id': int(os.environ['GITHUB_RUN_ID']), 'permanent_signer_sha256': SIGNER,
               'tests': tests['totals'], 'all_dex_byte_identical': dex, 'protected_payload_entries': len(protected),
               'all_46_other_native_libraries_byte_identical': True, 'native_libraries': native,
               'native_source_delta': current_delta, 'native_exports_preserved': True,
               'native_elf_dependencies_unchanged': True, 'manifest_edits': edits,
               'manifest_preserved_except_version': True, 'resources_and_assets_byte_identical': True,
               'bytes_saved': args.parent.stat().st_size - final.stat().st_size,
               'physical_device_verified': False, 'locked': False, 'production_promoted': False}
    write(args.out / 'DELIVERY.json', receipt)
    unsigned.unlink()
    print(json.dumps({key: receipt[key] for key in ('file', 'bytes', 'sha256', 'version_code', 'bytes_saved')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('parent', 'engine', 'proof', 'tests', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    package(parser.parse_args())
