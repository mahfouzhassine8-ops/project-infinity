#!/usr/bin/env python3
"""Build-only delivery adapter for the coordinated 2103392 test candidate.

No runtime repair is invented here. Reuse the reviewed source stage, exact
startup DEX, immutable 2103391 native producer and permanent signing script.
A package can be published only after the full native build and strict delta
checks. Real install-over, whole-process Close and Fold acceptance stay open.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PRODUCER = '7bd9b1085d598789e9e803b4b76ee1429e1df7e3'
PARENT_SHA = '47609f2ada1d6bbc7cdbddb791d11815bdbf1100a083bd8205d60ac21c882151'
DEX_SHA = '2b54ba6ede1461cfcd0e1788de8c35a7cf63df582d9c8e03bb3c583890b8de54'
DEX2_SHA = 'd4df6604044e7cb66584229562186bf2ed8f0031d2d3efba03bba8ebe38934ca'
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
CODE = 2103392
OLD_NAME = '1.0.9-All-In-One-Bugfix-TEST0001'
NAME = '1.0.9-All-In-One-Bugfix-TEST0002'
FILENAME = 'Infinity-2103392-Coherent-Integration-EXPERIMENTAL.apk'
ENGINE = 'lib/arm64-v8a/libkodi.so'
RECORDER = 'lib/arm64-v8a/libinfinitycrash.so'
SIGNATURE = re.compile(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))', re.I)
KEYS = ('INFINITY_KEYSTORE_B64', 'INFINITY_STORE_PASSWORD', 'INFINITY_KEY_PASSWORD', 'INFINITY_KEY_ALIAS')


def require(value, reason):
    if not value:
        raise RuntimeError('2103392 DELIVERY REFUSED: ' + reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest() if hasattr(hashlib, 'file_digest') else stream_digest(f)


def stream_digest(f):
    h = hashlib.sha256()
    for b in iter(lambda: f.read(1024 * 1024), b''):
        h.update(b)
    return h.hexdigest()


def save(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def load_json(path):
    return json.loads(Path(path).read_text())


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    require(spec is not None and spec.loader is not None, 'Cannot load reviewed build adapter')
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


def adapters():
    sys.path.insert(0, str(HERE))
    import release
    import integration
    sys.path.insert(0, str(HERE.parent))
    import sign_all_in_one
    return release, integration, sign_all_in_one


def command(args):
    return subprocess.check_output([str(x) for x in args], text=True, stderr=subprocess.STDOUT)


def exact_file(root, filename, expected=None):
    matches = [p for p in Path(root).rglob(filename) if p.is_file() and not p.is_symlink()]
    if expected:
        matches = [p for p in matches if digest(p) == expected]
    require(len(matches) == 1, 'Expected one verified input: ' + filename)
    return matches[0].resolve()


def replace_recorder_field(recorder, old_hash, new_hash, sections):
    require(re.fullmatch('[0-9a-f]{64}', old_hash) and re.fullmatch('[0-9a-f]{64}', new_hash), 'Invalid engine identity')
    require(old_hash != new_hash, 'Old native engine cannot be shipped as corrected')
    before = b'native_engine_sha256=' + old_hash.encode() + b'\n'
    after = b'native_engine_sha256=' + new_hash.encode() + b'\n'
    require(recorder.count(before) == 1, 'Recorder does not identify the exact parent engine once')
    offset = recorder.index(before)
    start, size = sections.get('.rodata', (0, 0))
    require(start <= offset and offset + len(before) <= start + size <= len(recorder), 'Recorder identity lies outside bounded rodata')
    result = recorder[:offset] + after + recorder[offset + len(before):]
    require(len(result) == len(recorder) and result[:offset] == recorder[:offset] and result[offset + len(before):] == recorder[offset + len(before):], 'Recorder instructions or layout changed')
    return result


def verify_source_binding(binding, expected_native, source_commit):
    require(re.fullmatch('[0-9a-f]{40}', source_commit), 'Full release commit required')
    require(binding.get('source_commit') == source_commit and binding.get('base_source_commit') == PRODUCER, 'Native source provenance mismatch')
    require(binding.get('original_source_count') == 9404 and binding.get('final_source_count') == 9404, 'Incomplete native inventory')
    require(binding.get('protected_source_count') == 9402 and binding.get('all_other_sources_byte_identical') is True, 'Protected native source changed')
    require(binding.get('after') == expected_native and set(binding.get('before', {})) == set(expected_native), 'Wrong native correction set')
    require(len(binding.get('old_group7_native_paths', [])) == 8, 'Prior native group corrections missing')
    require(binding.get('physical_fold_verified') is False and binding.get('final_lock') is False, 'Invented device qualification')


def bind(args):
    r, integration, _ = adapters()
    producer = args.producer.resolve()
    require(command(['git', '-C', producer, 'rev-parse', 'HEAD']).strip() == PRODUCER, 'Original producer checkout changed')
    require(not command(['git', '-C', producer, 'diff', '--name-only']).strip(), 'Original producer tracked files modified')
    parent = exact_file(args.parent_dir, 'Infinity-2103391-All-In-One-Bugfix-EXPERIMENTAL.apk', PARENT_SHA)
    integration.prepare(parent, args.stage.resolve())
    driver = module('delivery92_original_native_driver', producer / 'repairs/four-repair-20261018/native_ci.py')
    ordering = driver.parent.parent.parent.parent.parent.parent.parent
    manifest = Path(ordering.native_manifest(ordering.stable())).resolve()
    report = integration.bind_native(parent, args.stage.resolve() / 'source', producer / 'kodi', producer / 'checkpoint-build', manifest, args.source_commit)
    verify_source_binding(report, integration.FINAL_NATIVE, args.source_commit)
    print(json.dumps(report, indent=2, sort_keys=True))


def verify_signature(apk, build_tools):
    text = command([build_tools / 'apksigner', 'verify', '--verbose', '--print-certs', apk])
    found = re.findall(r'Signer #\d+ certificate SHA-256 digest:\s*([0-9a-f:]+)', text, re.I)
    require(len(found) == 1 and found[0].lower().replace(':', '') == CERT, 'Permanent signing identity mismatch')
    for version in (1, 2, 3):
        require(re.search(r'Verified using v' + str(version) + r' scheme[^\n]*:\s*true', text, re.I), 'APK signature scheme failed')
    subprocess.run([str(build_tools / 'zipalign'), '-c', '-p', '4', str(apk)], check=True)
    return text


def assemble(args):
    # Reject absent/partial credentials before invoking the inherited signer,
    # whose separate test-only mode must never be reachable from this adapter.
    require(all(os.environ.get(k) for k in KEYS), 'All four permanent signing secrets required; no debug fallback')
    r, integration, signer = adapters()
    producer = args.producer.resolve()
    require(command(['git', '-C', producer, 'rev-parse', 'HEAD']).strip() == PRODUCER, 'Wrong immutable native producer')
    require(not command(['git', '-C', producer, 'diff', '--name-only']).strip(), 'Original producer modified')
    parent = exact_file(args.parent_dir, 'Infinity-2103391-All-In-One-Bugfix-EXPERIMENTAL.apk', PARENT_SHA)
    stage = args.stage.resolve() / 'source'
    _, staged = integration.verified_stage(parent, stage)
    checkpoint = producer / 'checkpoint-build'
    binding = load_json(checkpoint / 'COHERENT92-NATIVE-BINDING.json')
    verify_source_binding(binding, integration.FINAL_NATIVE, args.source_commit)
    expected = load_json(checkpoint / 'COHERENT92-NATIVE-SOURCE-MAP.json')
    require(len(expected) == 9404 and all(digest(producer / 'kodi' / n) == h for n, h in expected.items()), 'Reviewed native source changed during compilation')
    proof = load_json(checkpoint / 'ENGINE-PROOF.json')
    engine_path = checkpoint / 'libkodi.so'
    engine_hash = digest(engine_path)
    require(proof.get('source_commit') == args.source_commit and proof.get('complete_native_engine_compiled') is True, 'Complete native build provenance missing')
    require(proof.get('native_sha256') == engine_hash and proof.get('shutdown_policy') == 'essential_first_process_exit_v1', 'Native engine/hash/shutdown policy mismatch')
    require(proof.get('physical_fold_verified') is False and proof.get('crash_fixed') is False, 'Unproved native crash or device success claimed')
    native = engine_path.read_bytes()
    require(len(native) > 90_000_000, 'Full native engine missing')
    identity = signer.nativeidentity
    identity.elf_sections(native)
    for word in (b'RunScript(script.infinity.uirepair,option-b,', b'Skin.HasSetting(Infinity.SilentMode)', b'Hide from this browser (not Disable)', b'0.3.5.22'):
        require(word in native, 'Required compiled behavior missing: ' + repr(word))
    pins = json.loads(staged['addons/' + r.UI + '/CONTROLLER-PREIMAGES.json'])
    require(len(pins) == 13 and all(h.encode() in native for h in pins.values()), 'Compiled native controller contract incomplete')
    dex = exact_file(args.dex_dir, '*.dex', DEX_SHA).read_bytes()
    build_tools = Path(os.environ['ANDROID_HOME']) / 'build-tools/34.0.0'
    parent_signing = verify_signature(parent, build_tools)
    out = args.out.resolve()
    require(not out.exists(), 'Refusing to overwrite an existing delivery directory')
    require(not parent.is_relative_to(out) and not producer.is_relative_to(out), 'Unsafe delivery directory')
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.infinity2103392-', dir=out.parent) as temp:
        temp = Path(temp)
        unsigned = temp / ('unsigned-' + FILENAME)
        signed = temp / FILENAME
        with zipfile.ZipFile(parent) as old:
            require(digest(parent) == PARENT_SHA and old.testzip() is None, 'Parent APK changed')
            old_names = old.namelist()
            require(len(old_names) == len(set(old_names)), 'Duplicate parent members')
            require(sha(old.read('classes2.dex')) == DEX2_SHA, 'Protected second DEX shard changed')
            previous_engine = old.read(ENGINE)
            require(sha(previous_engine) != engine_hash, 'Old engine relabeled as 2103392')
            abi = signer.native_export_compatibility(previous_engine, native)
            recorder = old.read(RECORDER)
            recorder_new = replace_recorder_field(recorder, sha(previous_engine), engine_hash, identity.elf_sections(recorder))
            manifest = signer.load_module('delivery92_manifest', ROOT / 'repairs/critical-preview-2103376/manifest_patch.py')
            manifest.PARENT_CODE = 2103391
            manifest.CODE = CODE
            manifest.PARENT_NAME = OLD_NAME
            manifest.NAME = NAME
            require(len(NAME) == len(OLD_NAME), 'Binary manifest name size changed')
            manifest_new, edits = manifest.patch(old.read('AndroidManifest.xml'))
            require(len(edits) == 2 and {e['field'] for e in edits} == {'versionCode', 'versionName'}, 'Unapproved Android manifest delta')
            targets = {'assets/addons/' + n: staged['addons/' + n] for n in r.CHANGED_ADDON_MEMBERS}
            targets.update({ENGINE: native, RECORDER: recorder_new, 'classes.dex': dex, 'AndroidManifest.xml': manifest_new})
            require(len(targets) == 12 and set(targets).issubset(old_names), 'Wrong APK delta scope')
            require(not any('cobra' in n.lower() for n in targets), 'Protected Cobra resource targeted')
            with zipfile.ZipFile(unsigned, 'w', allowZip64=True) as new:
                for info in old.infolist():
                    if not SIGNATURE.fullmatch(info.filename):
                        new.writestr(copy.copy(info), targets[info.filename] if info.filename in targets else old.read(info))
        integration.verify_addon_delta(parent, unsigned, stage)
        subprocess.run(['bash', str(ROOT / 'scripts/sign-infinity71.sh'), str(unsigned), str(signed)], check=True)
        signing = verify_signature(signed, build_tools)
        badge = command([build_tools / 'aapt', 'dump', 'badging', signed])
        require("package: name='com.projectinfinity.kodi' versionCode='2103392'" in badge and "versionName='" + NAME + "'" in badge, 'Final package/version mismatch')
        require('application-debuggable' not in badge, 'Debuggable APK not authorized')
        scope = integration.verify_addon_delta(parent, signed, stage)
        require(scope['dex_shard'] == 'classes.dex' and len(scope['changed_members']) == 12, 'Final signed APK delta differs')
        with zipfile.ZipFile(signed) as final:
            require(sha(final.read('classes.dex')) == DEX_SHA and sha(final.read('classes2.dex')) == DEX2_SHA, 'Final DEX bytes changed')
            require(sha(final.read(ENGINE)) == engine_hash, 'Final packaged native engine changed')
            for name, value in targets.items():
                require(final.read(name) == value, 'Signed target drift: ' + name)
            for addon, _, version in r.PACKAGES:
                prefix = 'assets/addons/' + addon + '/'
                entries = [n for n in final.namelist() if n.startswith(prefix) and not n.endswith('/')]
                require(entries, 'Missing matching component ' + addon)
                filename = addon + '-' + version + '.zip'
                with zipfile.ZipFile(temp / filename, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as component:
                    for n in sorted(entries):
                        component.writestr(n[len('assets/addons/'):], final.read(n))
                with zipfile.ZipFile(temp / filename) as component:
                    require(component.testzip() is None and len(component.namelist()) == len(entries), 'Component ZIP corrupt')
                    for n in component.namelist():
                        require(component.read(n) == final.read('assets/addons/' + n), 'Component differs from signed APK')
        (temp / 'PARENT-SIGNATURE.txt').write_text(parent_signing)
        (temp / 'FINAL-SIGNATURE.txt').write_text(signing)
        (temp / 'APK-BADGING.txt').write_text(badge)
        for filename in ('ENGINE-PROOF.json', 'COHERENT92-NATIVE-BINDING.json'):
            (temp / filename).write_bytes((checkpoint / filename).read_bytes())
        receipt = dict(schema=1, version_code=CODE, source_commit=args.source_commit, native_producer_commit=PRODUCER,
            parent_apk_sha256=PARENT_SHA, apk_sha256=digest(signed), native_sha256=engine_hash,
            startup_dex_sha256=DEX_SHA, startup_dex_producer_run=39376264712, startup_dex_android_test_run=39380859431,
            permanent_certificate_sha256=CERT, signed_permanently=True, complete_native_engine_compiled=True,
            native_source_files_verified=9404, native_source_changes=sorted(integration.FINAL_NATIVE),
            protected_native_source_files=9402, apk_changed_members=scope['changed_members'], native_abi=abi,
            matching_component_versions={a:v for a,_,v in r.PACKAGES}, matching_zips_identical_to_apk=True,
            runtime_repairs_added_by_this_adapter=False, cobra_resources_and_prior_protected_dex_preserved=True,
            shutdown_policy='essential_first_process_exit_v1', shutdown_guards_weakened=False,
            install_over_package_and_signing_compatible=True, actual_install_over_tested=False,
            whole_process_close_reopen_tested=False, physical_fold_verified=False,
            original_sigsegv_fixed=False, task19_deferred_unfixed=True, final_lock=False, experimental_only=True)
        save(temp / 'INFINITY-2103392-DELIVERY.json', receipt)
        unsigned.unlink()
        signed.with_suffix('.sha256').write_text(digest(signed) + '  ' + signed.name + '\n')
        (temp / 'INSTALLATION.txt').write_text(
            'INFINITY 2103392 - UNLOCKED TEST CANDIDATE\n'
            'Preserve/export important state before updating. Never uninstall or clear data.\n'
            '1. Install the signed 2103392 APK over the existing Infinity app.\n'
            '2. In Kodi Install from ZIP, install Command Center 0.3.5.22.\n'
            '3. Install Watched Bridge 1.0.3, then UI Repair 0.1.4.\n'
            '4. Skin 1.0.5.229 and Rails 0.2.7 are supplied unchanged; only install them if your versions differ.\n'
            '5. After component updates finish, test normal Close and reopen.\n'
            'Do not install these component ZIPs with the old native engine.\n'
            'Actual install-over, installed startup, Close/reopen and physical Fold behavior are not yet accepted.\n'
            'If Close fails, retain the failure and export diagnostics; do not clear data or assume success.\n'
            'The original SIGSEGV cause remains unresolved; task 19 remains deferred. No final LOCK.\n')
        # Publish only a complete validated set, never an unsigned intermediate.
        hashes = {p.name:digest(p) for p in temp.iterdir() if p.is_file()}
        (temp / 'SHA256SUMS').write_text(''.join(h + '  ' + n + '\n' for n,h in sorted(hashes.items())))
        os.rename(temp, out)
    print(json.dumps(receipt, indent=2, sort_keys=True))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['bind', 'assemble'])
    p.add_argument('--producer', type=Path, required=True)
    p.add_argument('--parent-dir', type=Path, required=True)
    p.add_argument('--stage', type=Path, required=True)
    p.add_argument('--source-commit', required=True)
    p.add_argument('--dex-dir', type=Path)
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    if args.mode == 'assemble':
        require(args.dex_dir is not None and args.out is not None, 'Assembly arguments incomplete')
        assemble(args)
    else:
        bind(args)


if __name__ == '__main__':
    main()
