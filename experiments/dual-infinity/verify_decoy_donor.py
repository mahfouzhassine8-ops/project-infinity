#!/usr/bin/env python3
"""Verify a G0 compiled shell without claiming it is an installable Kodi decoy."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import struct
import xml.etree.ElementTree as ET
import zipfile

import stage_decoy as stage
from dex_preservation import verified_renames

sys.path.insert(0, str(stage.REPOSITORY / 'repairs/mobile-regressions-2103304'))
from packaging_checks import dex_contract, manifest_tree, resource_ids


def dex_superclasses(archive):
    parents = {}
    for name in archive.namelist():
        if not re.fullmatch(r'classes(?:\d+)?\.dex', name):
            continue
        data = archive.read(name)
        def u32(offset): return struct.unpack_from('<I', data, offset)[0]
        strings = []
        for i in range(u32(56)):
            offset = u32(u32(60) + 4*i)
            while data[offset] & 128: offset += 1
            offset += 1
            # DEX strings are modified UTF-8 (including C0 80 for NUL).
            # Class descriptors are ASCII; arbitrary literal strings are not.
            strings.append(data[offset:data.index(b'\0', offset)].decode('utf-8', errors='replace'))
        types = [strings[u32(u32(68) + 4*i)] for i in range(u32(64))]
        for i in range(u32(96)):
            offset = u32(100) + 32*i
            parent = u32(offset + 8)
            parents[types[u32(offset)]] = None if parent == 0xffffffff else types[parent]
    return parents


def xml_from_aapt(text):
    def value(raw):
        quoted = re.search(r'"([^"\n]*)"', raw)
        if quoted:
            return quoted.group(1)
        boolean = re.fullmatch(r'\(type 0x12\)0x([0-9a-fA-F]+)', raw)
        if boolean:
            return 'true' if int(boolean.group(1), 16) else 'false'
        return raw
    def node(data):
        attributes = {(stage.ANDROID + key.split(':', 1)[1] if key.startswith('android:') else key):
                      value(raw) for key, raw in data['attrs'].items()}
        element = ET.Element(data['tag'], attributes)
        for child in data['children']:
            element.append(node(child))
        return element
    return ET.tostring(node(manifest_tree(text)), encoding='unicode')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'donor', 'build-tools', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--test-results', type=Path)
    p.add_argument('--compiled-source', default=os.environ.get('GITHUB_SHA', ''))
    p.add_argument('--compiled-run', type=int, default=int(os.environ.get('GITHUB_RUN_ID', '0')))
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.base) as old, zipfile.ZipFile(args.donor) as new:
        original_native, original_classes = dex_contract(old)
        native, classes = dex_contract(new)
        stage.require(native == original_native, 'JNI declaration/class identity drift')
        own_classes = {name for name in original_classes if name.startswith('Lcom/projectinfinity/kodi/')}
        missing = sorted(own_classes - classes)
        mappings = verified_renames(old, new, own_classes, classes)
        (args.output / 'DEX-CLASS-INVENTORY.json').write_text(json.dumps({
            'original_classes': len(own_classes), 'missing_exact_names': missing,
            'missing_source_classes': [],
            'verified_compiler_callback_population': len(mappings),
            'verified_generated_name_mapping': {a:b for a,b in mappings.items() if a!=b},
            'added': sorted(classes - original_classes),
            'jni_declarations_unchanged': native == original_native}, indent=2) + '\n')
        stage.require('Lcom/projectinfinity/kodi/InfinityDecoyIdentity;' in classes,
                      'Decoy identity guard missing from compiled DEX')
        stage.require('Lcom/projectinfinity/kodi/dualtest/XBMCBroadcastReceiver;' in classes,
                      'Cached-engine runtime package receiver lookup cannot resolve')
        stage.require(dex_superclasses(new).get('Lcom/projectinfinity/kodi/dualtest/XBMCBroadcastReceiver;') ==
                      'Lcom/projectinfinity/kodi/XBMCBroadcastReceiver;',
                      'Runtime receiver bridge does not inherit the registered JNI callback')
        stage.require('Lcom/projectinfinity/kodi/InfinityDecoyDiagnosticsProvider;' in classes,
                      'Startup evidence export missing from compiled DEX')
        stage.require(not any(name.startswith(('lib/', 'assets/')) and not name.endswith('/')
                              for name in new.namelist()), 'Compile donor must contain no engine/assets')
        stage.require(not new.testzip(), 'Donor APK CRC failure')
    dump = subprocess.check_output([str(args.build_tools / 'aapt'), 'dump', 'xmltree',
                                    str(args.donor), 'AndroidManifest.xml'], text=True)
    (args.output / 'compiled-manifest.txt').write_text(dump)
    decoded = xml_from_aapt(dump)
    stage.validate_manifest(decoded, compiled=True)
    old_ids = resource_ids(args.build_tools / 'aapt2', args.base, args.output / 'parent-ids.txt')
    new_ids = resource_ids(args.build_tools / 'aapt2', args.donor, args.output / 'donor-ids.txt')
    stage.require(all(new_ids.get(name) == rid for name, rid in old_ids.items()),
                  'Original Android resource IDs moved')
    # Require the actual fourteen executable Robolectric ownership/startup tests, not just
    # a Gradle success status or a source string contract.
    report_root = args.test_results or args.donor.parents[3] / 'test-results/testReleaseUnitTest'
    test_path = report_root / 'TEST-com.projectinfinity.kodi.DecoyIdentityTest.xml'
    stage.require(test_path.is_file(), 'Executed decoy test receipt unavailable')
    suite = ET.parse(test_path).getroot()
    stage.require(int(suite.get('tests', '0')) >= 14 and suite.get('failures') == '0' and
                  suite.get('errors') == '0' and suite.get('skipped') == '0',
                  'Decoy ownership tests did not all execute/pass')
    receipt = {'schema': 1, 'purpose': 'G0 compiled identity probe, not a device APK',
               'application_id': stage.INSTALL_ID, 'jni_namespace': stage.NAMESPACE,
               'jni_declarations_unchanged': len(native), 'original_class_inventory_preserved': not missing,
               'original_source_classes_preserved': True,
               'verified_compiler_callback_population': len(mappings),
               'generated_exact_names_missing': missing,
               'original_resource_ids_preserved': len(old_ids),
               'no_shared_uid': True, 'provider_authorities_separate': True,
               'production_control_routes_refused_or_remapped': True,
               'runtime_package_receiver_bridge_present': True,
               'runtime_receiver_inherits_registered_jni_callback': True,
               'source_commit': args.compiled_source,
               'workflow_run_id': args.compiled_run,
               'verification_source_commit': os.environ.get('GITHUB_SHA', ''),
               'verification_run_id': int(os.environ.get('GITHUB_RUN_ID', '0')),
               'donor_sha256': hashlib.sha256(args.donor.read_bytes()).hexdigest(),
               'executed_robolectric_tests': int(suite.get('tests')),
               'native_merged': False, 'second_engine_enabled': False,
               'installable_decoy_created': False, 'native_jni_execution_verified': False,
               'physical_device_pass': False}
    (args.output / 'COMPILED-DECOY-PROBE.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('PASS: compiled decoy identity and exact JNI namespace; donor is not a device APK')


if __name__ == '__main__':
    main()
