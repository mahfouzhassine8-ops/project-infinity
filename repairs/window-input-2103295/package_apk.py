#!/usr/bin/env python3
"""Preserve every 2103294 APK payload except libkodi.so and integer versionCode."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile

PARENT_SHA256 = '34c7bf61235316b2c5730056cf3136c281c1e886f2d991bb46fef9d708df73c3'
PARENT_NATIVE_SHA256 = '91400d51655c0e85b5e069a4108eda0fcc6a40bb0edb9f2014e1a901dac9cab2'
VERSION = 2103295
parent_module = Path(__file__).resolve().parents[1] / 'fold-unification-2103293/package_apk.py'
spec = importlib.util.spec_from_file_location('parent_package', parent_module)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
H = lambda b: hashlib.sha256(b).hexdigest()

def check(source, candidate, engine_proof):
    proof = json.loads(engine_proof.read_text())
    assert proof['candidate'] == VERSION
    assert proof['source_parent_apk_sha256'] == PARENT_SHA256
    assert proof['text_reflow_v1'] is True
    assert proof['window_input_v1'] is True
    with zipfile.ZipFile(source) as old, zipfile.ZipFile(candidate) as new:
        assert old.testzip() is None and new.testzip() is None
        names = lambda z: {n for n in z.namelist() if not n.endswith('/') and not parent.SIGNING.fullmatch(n)}
        old_names, new_names = names(old), names(new)
        assert old_names == new_names, (old_names-new_names, new_names-old_names)
        changed = [n for n in sorted(old_names) if old.read(n) != new.read(n)]
        assert changed == ['AndroidManifest.xml', 'lib/arm64-v8a/libkodi.so'], changed
        manifest = new.read('AndroidManifest.xml')
        assert parent.version_code(manifest)[1] == VERSION
        assert parent.version_code(manifest, 2103294)[0] == old.read('AndroidManifest.xml')
        native_digest = H(new.read('lib/arm64-v8a/libkodi.so'))
        assert native_digest == proof['native_engine_sha256']
        assert native_digest != PARENT_NATIVE_SHA256
        return dict(candidate=VERSION, parent_apk_sha256=H(source.read_bytes()),
                    apk_sha256=H(candidate.read_bytes()), native_sha256=native_digest,
                    changed_payloads=changed, unchanged_payload_count=len(old_names)-2,
                    dex_and_assets_byte_preserved=True, unexpected_payload_changes=0,
                    manifest_changes_only_integer_version_code=True,
                    physical_verified=False, locked=False)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('build','verify'))
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--native', type=Path)
    parser.add_argument('--engine-proof', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--proof', type=Path, required=True)
    args = parser.parse_args()
    assert H(args.parent.read_bytes()) == PARENT_SHA256
    if args.command == 'build':
        native = args.native.read_bytes()
        assert native[:4] == b'\x7fELF' and native[4] == 2
        assert int.from_bytes(native[18:20], 'little') == 183 # AArch64
        assert H(native) != PARENT_NATIVE_SHA256
        with zipfile.ZipFile(args.parent) as old, zipfile.ZipFile(args.out, 'w') as new:
            assert H(old.read('lib/arm64-v8a/libkodi.so')) == PARENT_NATIVE_SHA256
            for info in old.infolist():
                if parent.SIGNING.fullmatch(info.filename):
                    continue
                data = old.read(info.filename)
                if info.filename == 'lib/arm64-v8a/libkodi.so':
                    data = native
                elif info.filename == 'AndroidManifest.xml':
                    data, old_version = parent.version_code(data, VERSION)
                    assert old_version == 2103294
                new.writestr(info, data)
    result = check(args.parent, args.out, args.engine_proof)
    args.proof.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))

if __name__ == '__main__':
    main()
