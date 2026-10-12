#!/usr/bin/env python3
"""Assemble a separate-install G0 bootstrap with the exact cached parent engine.

This does not implement two engines or certify Android runtime acceptance.
Production files, skin/add-ons, native libraries and signing identity stay intact.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import stage_decoy as stage
from source_gate import compiled_manifest
from verify_decoy_donor import xml_from_aapt

sys.path.insert(0, str(stage.REPOSITORY / 'repairs/mobile-regressions-2103304'))
from packaging_checks import DEX, SIGNATURE, dex_contract, resource_ids

ENGINE = 'lib/arm64-v8a/libkodi.so'
ENGINE_SHA = 'bd6be87e3c7d6c510973a55018029ed0e3488cd5328d7a81565cbbfdd44fefb9'
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def android_entry(name):
    return name in ('AndroidManifest.xml', 'resources.arsc') or name.startswith('res/') or DEX.fullmatch(name)


def merge(base, donor, output):
    with zipfile.ZipFile(base) as parent, zipfile.ZipFile(donor) as shell:
        stage.require(len(parent.namelist()) == len(set(parent.namelist())) and
                      len(shell.namelist()) == len(set(shell.namelist())), 'Duplicate APK entries')
        stage.require(sha(parent.read(ENGINE)) == ENGINE_SHA, 'Incorrect cached native engine')
        stage.require(dex_contract(parent)[0] == dex_contract(shell)[0], 'JNI namespace/method drift')
        stage.require(not any(n.startswith(('lib/', 'assets/')) and not n.endswith('/')
                              for n in shell.namelist()), 'Shell donor contains unreviewed engine/assets')
        with zipfile.ZipFile(output, 'w') as result:
            for item in parent.infolist():
                if not android_entry(item.filename) and not SIGNATURE.fullmatch(item.filename):
                    result.writestr(copy.copy(item), parent.read(item.filename))
            for item in shell.infolist():
                if android_entry(item.filename):
                    result.writestr(copy.copy(item), shell.read(item.filename))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'donor', 'probe-evidence', 'build-tools', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    _, parent_identity = compiled_manifest('native')
    stage.require(sha(args.base.read_bytes()) == parent_identity['parent_apk_sha256'], 'Wrong parent APK')
    probe = json.loads((args.probe_evidence / 'COMPILED-DECOY-PROBE.json').read_text())
    stage.require(probe['application_id'] == stage.INSTALL_ID and
                  probe['jni_namespace'] == stage.NAMESPACE and
                  probe['executed_robolectric_tests'] >= 14 and probe['no_shared_uid'] and
                  probe['provider_authorities_separate'] and not probe['native_merged'],
                  'Verified shell prerequisite missing')
    stage.require(probe['donor_sha256'] == sha(args.donor.read_bytes()) and
                  probe['runtime_receiver_inherits_registered_jni_callback'] and
                  len(probe['source_commit']) == 40 and probe['workflow_run_id'] > 0,
                  'Compiled receiver bridge or exact donor provenance missing')
    source = json.loads((stage.HERE / 'evidence/G0-SOURCE-COMPLETE.json').read_text())
    stage.require(source['native_source_passed'] and source['native_verified_files'] == 9390,
                  'Exact native-source prerequisite unavailable')
    # No ephemeral signer fallback, key extraction, production update or install.
    for name in ('INFINITY_KEYSTORE_B64', 'INFINITY_STORE_PASSWORD',
                 'INFINITY_KEY_PASSWORD', 'INFINITY_KEY_ALIAS'):
        stage.require(bool(os.environ.get(name)), 'Permanent signing configuration unavailable')
    args.output.mkdir(parents=True, exist_ok=True)
    unsigned = args.output / 'bootstrap-unsigned.apk'
    merge(args.base, args.donor, unsigned)
    final = args.output / 'Infinity-Dual-Test-G0-Bootstrap-2-Startup-Repair.apk'
    subprocess.run(['bash', str(stage.REPOSITORY / 'scripts/sign-infinity71.sh'),
                    str(unsigned), str(final)], check=True)
    signing = subprocess.check_output([str(args.build_tools / 'apksigner'), 'verify',
                                       '--verbose', '--print-certs', str(final)], text=True)
    stage.require(CERT in signing.lower(), 'Protected permanent signer changed')
    dump = subprocess.check_output([str(args.build_tools / 'aapt'), 'dump', 'xmltree',
                                    str(final), 'AndroidManifest.xml'], text=True)
    stage.validate_manifest(xml_from_aapt(dump), compiled=True)
    (args.output / 'final-manifest.txt').write_text(dump)
    old_ids = resource_ids(args.build_tools / 'aapt2', args.base, args.output / 'parent-ids.txt')
    new_ids = resource_ids(args.build_tools / 'aapt2', final, args.output / 'final-ids.txt')
    stage.require(all(new_ids.get(name) == rid for name, rid in old_ids.items()), 'Original resource ID drift')
    with zipfile.ZipFile(args.base) as old, zipfile.ZipFile(final) as new:
        protected = [name for name in old.namelist()
                     if not android_entry(name) and not SIGNATURE.fullmatch(name)]
        stage.require(all(old.read(name) == new.read(name) for name in protected),
                      'Protected native, skin, add-on or other payload changed')
        stage.require(sha(new.read(ENGINE)) == ENGINE_SHA, 'Cached engine changed during signing')
        stage.require(not new.testzip(), 'Final APK CRC failure')
    receipt = {'schema': 1, 'purpose': 'G0 one-engine bootstrap, not Dual Infinity acceptance',
               'file': final.name, 'sha256': sha(final.read_bytes()), 'size_bytes': final.stat().st_size,
               'application_id': stage.INSTALL_ID, 'version_code': stage.VERSION_CODE,
               'version_name': stage.VERSION_NAME, 'jni_namespace': stage.NAMESPACE,
               'source_commit': os.environ['GITHUB_SHA'],
               'shell_compilation_commit': probe['source_commit'],
               'shell_compilation_run': probe['workflow_run_id'],
               'donor_sha256': probe['donor_sha256'],
               'shell_verification_source': probe['verification_source_commit'],
               'shell_verification_run': probe['verification_run_id'],
               'original_source_classes_preserved': probe['original_source_classes_preserved'],
               'verified_compiler_callback_population': probe['verified_compiler_callback_population'],
               'runtime_receiver_bridge_verified': True,
               'first_bootstrap_device_result': 'FAILED_STARTUP_IN_18411_MP4',
               'native_compilation_commit': parent_identity['compiled_parent_commit'],
               'native_compilation_run': 38137092930, 'native_sha256': ENGINE_SHA,
               'native_recompiled': False, 'native_payload_unchanged': True,
               'protected_entries_unchanged': len(protected), 'signer_certificate_sha256': CERT,
               'engine_slots_enabled': 1, 'second_engine_implemented': False,
               'independent_shutdown_tested': False, 'dual_playback_tested': False,
               'audio_handover_tested': False, 'provider_compatibility_tested': False,
               'physical_install_or_native_bootstrap_verified': False,
               'device_acceptance': 'PENDING', 'production_integration_ready': False}
    (args.output / 'BOOTSTRAP-DELIVERY.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('G0 bootstrap signed under separate installation ID; cached engine unchanged; device acceptance pending')


if __name__ == '__main__':
    main()
