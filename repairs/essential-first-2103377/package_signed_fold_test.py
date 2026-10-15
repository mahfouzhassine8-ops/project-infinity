#!/usr/bin/env python3
"""Build a matched Essential-First Android donor and sign a TEST-only APK.

Never edits the locked Rails Handoff RC1 input. The native proof is pinned to
the green ARM64 run; the Android checker is compiled from actual Java source.
A signed TEST APK does not establish essential write coverage or device safety.
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
import shutil
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'repairs/mobile-regressions-2103304'))
import package_candidate as factory
from packaging_checks import configured, dex_contract, require, resource_ids, run, sha, DEX, SIGNATURE

LOCKED_APK_SHA = 'de8ce3f122db7bb8b2b3681e7c6ce9caf67cf38888b17ef1f82ff7759fa8a3db'
PINNED_NATIVE_COMMIT = '56fca5a4423a72e2e68e4f3f12e9ebe6076b17da'
LOCKED_REF_COMMIT = '7d3aca64b34d00520908cf4afd531a4687124525'
SIGNER = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
OLD_NAME = '1.0.9-Rails-Handoff-Correct-RC01'
NEW_NAME = '1.0.9-Essential-First-TEST1-RC01'
PACKAGE = 'com.projectinfinity.kodi'
ENGINE = 'lib/arm64-v8a/libkodi.so'
JAVA_PATCHES = ('InfinityCheckpointProtocol', 'InfinityCloseGuardService')
assert len(OLD_NAME) == len(NEW_NAME) == 32

def load(path):
    return json.loads(Path(path).read_text())

def digest(path):
    return sha(Path(path).read_bytes())

def sha256(obj):
    return hashlib.sha256(obj).hexdigest()

def out(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

def file_path(root, name):
    return Path(root) / 'tools/android/packaging/xbmc/src' / (name + '.java.in')

def prepared_java(args):
    require(digest(args.parent) == LOCKED_APK_SHA, 'Wrong parent; must preserve locked Rails Handoff RC1 APK')
    require(Path(args.source, 'tools/android/packaging/xbmc/src').is_dir(), 'Reconstructed native source required')
    require(not args.gradle_dir.exists(), 'Refusing to reuse stale Gradle donor')
    require(not args.out.exists(), 'Refusing to reuse stale Android donor evidence')
    args.out.mkdir(parents=True)
    factory.VERSION_CODE = 2103377
    factory.RELEASE = NEW_NAME
    factory.BASE_APK_SHA256 = LOCKED_APK_SHA
    factory.JNI_ADDITIONS = set()
    # The historical donor factory expects a 2103302 Gradle version preimage.
    # Normalize only the disposable packaging project's version identifiers;
    # this is NOT a change to native runtime, user settings, or the locked APK.
    gradle_template = args.source / 'tools/android/packaging/xbmc/build.gradle.in'
    gradle_before = gradle_template.read_text()
    code_pattern = r'(?m)^([ \t]*versionCode[ \t]+)[^\r\n]+$'
    name_pattern = r'(?m)^([ \t]*versionName[ \t]+)[^\r\n]+$'
    require(len(re.findall(code_pattern, gradle_before)) == 1 and
            len(re.findall(name_pattern, gradle_before)) == 1,
            'Unrecognized Android Gradle identity; refusing unrelated source normalization')
    gradle_after = re.sub(code_pattern, r'\g<1>2103302', gradle_before)
    gradle_after = re.sub(name_pattern,
                          r'\g<1>"1.0.9-Chooser-Weather-Snapshot-RC1"', gradle_after)
    require(gradle_after != gradle_before, 'Unexpected donor Gradle source identity')
    gradle_template.write_text(gradle_after)
    ids = factory.prepare(args.source.resolve(), args.parent.resolve(),
                          args.gradle_dir.resolve(), args.out.resolve())
    updated = {}
    for name in JAVA_PATCHES:
        template = HERE / 'runtime/android/tools/android/packaging/xbmc/src' / (name + '.java.in')
        require(template.is_file(), 'Missing reviewed Java template ' + name)
        existing = file_path(args.source, name)
        require(existing.is_file(), 'Native source did not contain original Java class ' + name)
        staged = args.gradle_dir / 'xbmc/java' / PACKAGE.replace('.', '/') / (name + '.java')
        require(staged.is_file(), 'The original Android shell did not register ' + name)
        # Scope limited to the two shutdown Java files. All other output comes
        # from the SHA-verified locked native source and resource inventory.
        compiled = configured(template, {'APP_PACKAGE': PACKAGE})
        require('essential_first_process_exit_v1' in compiled or
                name == 'InfinityCloseGuardService', 'Missing essential-first policy in Java source')
        before = digest(staged)
        staged.write_text(compiled)
        updated[name] = {'original_generated_sha256': before,
                         'new_generated_sha256': digest(staged),
                         'source_template_sha256': digest(template)}
    out(args.out / 'ANDROID-DONOR-SOURCE.json', {
        'purpose': 'Essential-first shutdown Java-only donor for physical TEST candidate',
        'source_commit': os.environ.get('GITHUB_SHA', 'local'),
        'pinned_native_commit': PINNED_NATIVE_COMMIT,
        'locked_parent_apk_sha256': LOCKED_APK_SHA,
        'resource_id_count': len(ids),
        'java_changes': updated,
        'java_source_changes_count': 2,
        'other_kodi_sources_unchanged': True,
        'final_apk_signed': False,
        'physical_fold_accepted': False,
    })
    print('PASS: reviewed essential-first Java validators staged; source output limited to two shutdown files', flush=True)

def exported_symbols(file):
    syms = set()
    for line in subprocess.check_output(['readelf', '--dyn-syms', '--wide', str(file)], text=True).splitlines():
        p = line.split()
        if len(p) >= 8 and p[4:6] == ['GLOBAL', 'DEFAULT'] and p[6] != 'UND':
            syms.add(p[-1].split('@')[0])
    return syms

def needed(file):
    text = subprocess.check_output(['readelf', '-d', '-W', str(file)], text=True)
    return sorted(re.findall(r'\(NEEDED\).*?\[(.*?)\]', text))

def signed_package(args):
    require(digest(args.parent) == LOCKED_APK_SHA, 'Locked parent APK digest mismatch')
    evidence = args.native / 'checkpoint-build'
    if not evidence.is_dir(): evidence = args.native
    proof = load(evidence / 'ENGINE-PROOF.json')
    require(proof.get('complete_native_engine_compiled') is True, 'Not a full native engine build')
    require(proof.get('shutdown_policy') == 'essential_first_process_exit_v1', 'Wrong native shutdown policy')
    require(proof.get('diagnostic_owners') == 17 and proof.get('essential_owners') == 16,
            'Wrong protected persistence owner contract')
    require(proof.get('source_commit') == PINNED_NATIVE_COMMIT,
            'Native ABI was not built from pinned green shutdown commit')
    require(not proof.get('android_process_death_verified'), 'No physical exit validation belongs in host proof')
    native = evidence / 'libkodi.so'
    require(native.is_file() and digest(native) == proof.get('native_sha256'),
            'Native artifact does not match full ARM64 build receipt')
    source = load(args.android / 'ANDROID-DONOR-SOURCE.json')
    require(source['pinned_native_commit'] == PINNED_NATIVE_COMMIT and
            source['locked_parent_apk_sha256'] == LOCKED_APK_SHA and
            set(source['java_changes']) == set(JAVA_PATCHES), 'Mismatched Java source proof')
    require(args.donor.is_file(), 'Compiled Android donor APK absent')
    for key in ('INFINITY_KEYSTORE_B64','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS'):
        require(bool(os.environ.get(key)), 'Permanent signing key missing: ' + key)
    bt = Path(os.environ['ANDROID_HOME']) / 'build-tools/34.0.0'
    resource_original = resource_ids(bt / 'aapt2', args.parent, args.out / 'parent-resources.txt')
    resource_donor = resource_ids(bt / 'aapt2', args.donor, args.out / 'donor-resources.txt')
    require(resource_original == resource_donor,
            'Rebuilt Android donor has differing resource IDs; refusing mixed APK')
    args.out.mkdir(parents=True, exist_ok=True)
    original_engine = args.out / 'locked-parent-libkodi.so'
    packaged_engine = args.out / 'libkodi.so'
    with zipfile.ZipFile(args.parent) as old:
        require(not old.testzip() and len(old.namelist())==len(set(old.namelist())),
                'Corrupted or duplicate locked APK entries')
        original_engine.write_bytes(old.read(ENGINE))
    shutil.copyfile(native, packaged_engine)
    ndk = Path(os.environ['ANDROID_HOME']) / 'ndk' / os.environ['NDK_VER'] / 'toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip'
    run(ndk, '--strip-unneeded', packaged_engine)
    require(not exported_symbols(original_engine)-exported_symbols(packaged_engine),
            'Locked native ABI export was removed')
    require(needed(original_engine) == needed(packaged_engine), 'Native shared-library dependencies changed')
    # Convert an existing binary manifest solely by changing the equal-length
    # versionName. The existing Android components/intent filters are preserved.
    mod_path = ROOT / 'repairs/critical-preview-2103376/manifest_patch.py'
    spec = importlib.util.spec_from_file_location('essential_exact_manifest', mod_path)
    manifest_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(manifest_mod)
    manifest_mod.PARENT_CODE = manifest_mod.CODE = 2103377
    manifest_mod.PARENT_NAME = OLD_NAME
    manifest_mod.NAME = NEW_NAME

    unsigned = args.out / 'essential-first-unsigned.apk'
    allowed_mutations = {'AndroidManifest.xml', ENGINE}
    with zipfile.ZipFile(args.parent) as old, zipfile.ZipFile(args.donor) as donor, \
            zipfile.ZipFile(unsigned, 'w') as updated:
        a, b = set(old.namelist()), set(donor.namelist())
        require(len(b) == len(donor.namelist()) and not donor.testzip(), 'Android donor is invalid')
        old_jni, old_classes = dex_contract(old)
        donor_jni, donor_classes = dex_contract(donor)
        require(old_jni == donor_jni, 'Reviewed Java rewrite changed JNI native method contract')
        core = {p for p in old_classes if p.startswith('Lcom/projectinfinity/kodi/') and '$' not in p}
        require(core <= donor_classes, 'Existing core Java class missing from compiled Android donor')
        require('Lcom/projectinfinity/kodi/InfinityCheckpointProtocol;' in donor_classes and
                'Lcom/projectinfinity/kodi/InfinityCloseGuardService;' in donor_classes,
                'Essential-first Java validator/coordinator classes not compiled')
        assert any(DEX.fullmatch(n) for n in b)
        for info in old.infolist():
            name = info.filename
            if SIGNATURE.fullmatch(name) or DEX.fullmatch(name):
                continue
            if name == ENGINE:
                updated.writestr(copy.copy(info), packaged_engine.read_bytes())
            elif name == 'AndroidManifest.xml':
                raw, edits = manifest_mod.patch(old.read(name))
                require({x['field'] for x in edits} == {'versionCode','versionName'},
                        'Unexpected binary manifest patch')
                updated.writestr(copy.copy(info), raw)
            else:
                updated.writestr(copy.copy(info), old.read(name))
        for info in donor.infolist():
            if DEX.fullmatch(info.filename):
                updated.writestr(copy.copy(info), donor.read(info.filename))
                allowed_mutations.add(info.filename)
    final = args.out / 'Infinity-2103377-Essential-First-Signed-Fold-TEST1.apk'
    run('bash', ROOT / 'scripts/sign-infinity71.sh', unsigned, final)
    cert = subprocess.check_output([str(bt/'apksigner'),'verify','--verbose','--print-certs',str(final)],
                                   text=True,stderr=subprocess.STDOUT)
    require(SIGNER in cert.lower(), 'Signer does not match the permanently locked APK')
    for v in (2,3):
        require(re.search(r'Verified using v'+str(v)+r' scheme[^\n]+true', cert),
                'Required APK signing scheme missing: ' + str(v))
    run(bt / 'zipalign', '-c', '-p', '4', final)
    badging = subprocess.check_output([str(bt/'aapt'),'dump','badging',str(final)],text=True)
    require("package: name='com.projectinfinity.kodi' versionCode='2103377'" in badging and
            NEW_NAME in badging, 'Candidate package/version identity changed unexpectedly')
    require("application-label:'Infinity'" in badging and 'application-debuggable' not in badging,
            'UI branding or APK debug mode changed')
    with zipfile.ZipFile(args.parent) as old, zipfile.ZipFile(final) as new:
        a, b = set(old.namelist()), set(new.namelist())
        protected = a - {p for p in a if SIGNATURE.fullmatch(p) or DEX.fullmatch(p)} - {ENGINE,'AndroidManifest.xml'}
        require(protected <= b, 'Protected original APK file disappeared')
        for path in protected:
            require(old.read(path) == new.read(path), 'Protected APK bytes changed: ' + path)
        changed = sorted(p for p in a&b if not SIGNATURE.fullmatch(p) and old.read(p)!=new.read(p))
        require(set(changed) <= allowed_mutations and
                {'AndroidManifest.xml', ENGINE} <= set(changed) and
                any(DEX.fullmatch(p) for p in changed),
                'Unsigned/Java changes differ from approved scope: ' + str(changed))
        require(not new.testzip(), 'Final APK CRC error')
        require(dex_contract(new)[0] == old_jni, 'Final APK JNI declaration mismatch')
    receipt = {
        'status': 'SIGNED TEST - PHYSICAL VALIDATION REQUIRED; NOT LOCKED',
        'file': final.name,
        'apk_sha256': digest(final),
        'bytes': final.stat().st_size,
        'parent_apk_sha256': LOCKED_APK_SHA,
        'locked_commit': LOCKED_REF_COMMIT,
        'native_source_commit': PINNED_NATIVE_COMMIT,
        'native_unstripped_sha256': proof['native_sha256'],
        'native_packaged_sha256': digest(packaged_engine),
        'android_source_commit': os.environ.get('GITHUB_SHA','unknown'),
        'same_permanent_signer': SIGNER,
        'package': PACKAGE,
        'version_code': 2103377,
        'version_name': NEW_NAME,
        'changed_apk_entries': changed,
        'all_other_apk_payload_byte_identical': True,
        'resources_byte_identical': True,
        'native_export_and_dependencies_preserved': True,
        'all_existing_core_java_classes_preserved': True,
        'essential_first_exit_policy_built': True,
        '17_diagnostic_owners': True,
        '16_essential_owners': True,
        'verified_android_process_exit': False,
        'verified_first_party_callback_on_device': False,
        'verified_fold_reopen': False,
        'known_fail_closed_native_encoder_route': 'bundled_native_encoder_write_adapter_missing',
        'unverified_other_native_descriptor_aliases': True,
        'physical_device_acceptance_required': True,
        'final_lock_authorized': False,
        'rollback': 'Reinstall the exact locked Rails Handoff RC1 signed APK with matching signer and versionCode. Never uninstall or clear app data.',
    }
    out(args.out / 'ESSENTIAL-FIRST-SIGNED-TEST-PRESERVATION.json', receipt)
    (args.out / 'CERT-VERIFICATION.txt').write_text(cert)
    (args.out / 'SHA256SUMS').write_text(receipt['apk_sha256'] + '  ' + final.name + '\n')
    (args.out / 'TEST-LIMITATIONS.md').write_text(
        '# Infinity Essential-First shutdown — signed diagnostic Fold TEST1\n\n'
        'TEST ONLY. Native and Android logic matched and signed, but this build has NOT '
        'passed physical-device shutdown, reopening, or Kodi first-party callback checks. '
        'The Pillow native encoder route remains fail-closed. Other native descriptor '
        'aliases are not proven; do not claim this as a completed essential-first exit. '
        'If the close screen refuses termination with an essential-write blocker, '
        'preserve the evidence and report it; do not force-close over unsaved data.\n\n'
        'All existing APK assets, skin, Rails and helper assets are unchanged. '
        'Same versionCode/signing certificate allows in-place rollback by reinstalling '
        'the locked Rails Handoff RC1 APK without clearing user data.\n')
    print('PASS: production ARM64 library and updated Android Java jointly packaged; permanently signed test APK.')
    print('LIMITATION: physical essential-first shutdown and native encoder route remain unverified. NOT A LOCK.',flush=True)

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=('java', 'package'))
    p.add_argument('--parent', type=Path,required=True)
    p.add_argument('--source', type=Path)
    p.add_argument('--gradle-dir', type=Path)
    p.add_argument('--donor', type=Path)
    p.add_argument('--native', type=Path)
    p.add_argument('--android', type=Path)
    p.add_argument('--out', type=Path,required=True)
    args=p.parse_args()
    if args.mode=='java':
        require(args.source and args.gradle_dir, 'Android source/build directories required')
        prepared_java(args)
    else:
        require(args.donor and args.native and args.android, 'Compiled donor/native/receipt required')
        args.out.mkdir(parents=True,exist_ok=True)
        signed_package(args)
