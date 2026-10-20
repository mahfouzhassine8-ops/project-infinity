#!/usr/bin/env python3
"""Exact first-party release identity gates, not an Android runtime certificate.

A complete accepted native contract is one variant (OR), with every file pinned
inside that variant (AND). Legacy alternatives are not simultaneous requirements.
Nothing here waives durability checks, trusts addon names alone, or edits an APK.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[3]
NATIVE_PATH = 'repairs/android-checkpoint-shutdown/runtime/native/overlay/xbmc/platform/android/activity/InfinityScriptCheckpointContracts.cpp'
CC = 'script.infinity.commandcenter'
CONSUMERS = ('script.infinity.uirepair', 'script.infinity.watchedbridge')
ENDPOINTS = ('service.py', 'plugin.py', 'context.py')
VERSION_PIN = '5711db9be562db665e1db70aa8798c7d254843196cc6beb7520055918758628f'
OLD = {
    'plugin.py': '11a741a694869eeca6f1fbdac17bb6ab02c9f807c73a3aa95a4b43323fc574fd',
    'resume_hub.py': '7794e25ec63348d29f74c45948d81db3e2fa1ba780437c329277fcffb1888eff',
}
FINAL = {
    'plugin.py': 'ded5e435f1db7af205869ae33d9e2eab888825d95f5086095bc4615e09b05b4f',
    'resume_hub.py': '087860b6a551a23fdd8f7f11ab103b367f0ef44be32b5b42cadecf907e548784',
}
MARKER = '    // GROUP7_REVIEWED_CC20_GROUP1_CONTRACTS_V1\n'
BLOCK = re.compile(r'    \{"([^"\n]+)", "([^"\n]+)", "([^"\n]+)", \{\n(.*?)\n    \}\},', re.S)
PAIR = re.compile(r'\{"([^"\n]+)", "([0-9a-f]{64})"\}')

class CoherenceError(ValueError):
    pass

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def contracts(source: str) -> list[dict]:
    result = []
    for match in BLOCK.finditer(source):
        pairs = PAIR.findall(match.group(4))
        if not pairs or len(dict(pairs)) != len(pairs):
            raise CoherenceError('Empty or duplicate native contract pins')
        result.append(dict(script=match.group(1), addon=match.group(2), owner=match.group(3),
                           pins=dict(pairs), block=match.group(0)))
    if len(result) < 9:
        raise CoherenceError('Native contract table was not fully recognized')
    return result

def matching_variants(source: str, addon: str, script: str, hashes: dict[str, str]) -> list[dict]:
    return [v for v in contracts(source)
            if v['addon'] == addon and v['script'] == script
            and all(hashes.get(path) == pin for path, pin in v['pins'].items())]

def append_reviewed_group1_contracts(source: str, payload: dict[str, bytes]) -> str:
    """Retain every legacy contract and add ONLY the reviewed final Group1 trio.

Requires all thirteen actual controller preimages, including unchanged manifest,
checkpoint implementation and eleven other pins. No configurable hash acceptance.
This is a source change requiring a new reviewed native compile, not a binary fix.
"""
    if MARKER in source:
        raise CoherenceError('Reviewed Group1 contract is already present')
    if any(digest(payload.get(CC + '/' + name, b'')) != expected for name, expected in FINAL.items()):
        raise CoherenceError('Actual Group1 controller bytes differ from reviewed final hashes')
    hashes = {path: digest(data) for path, data in payload.items() if path.startswith(CC + '/')}
    additions = []
    original_variants = contracts(source)
    for endpoint in ENDPOINTS:
        variants = [v for v in original_variants if v['script'] == CC + '/' + endpoint
                    and v['addon'] == CC and v['pins'].get(CC + '/addon.xml') == VERSION_PIN]
        if len(variants) != 1 or len(variants[0]['pins']) != 13:
            raise CoherenceError('Expected exactly one original complete CC20 contract per endpoint')
        variant = variants[0]
        wanted = dict(variant['pins'])
        for name, pin in OLD.items():
            if wanted.get(CC + '/' + name) != pin:
                raise CoherenceError('Original controller pin drifted')
            wanted[CC + '/' + name] = FINAL[name]
        if any(hashes.get(path) != value for path, value in wanted.items()):
            raise CoherenceError('Unreviewed controller change outside the two Group1 files')
        block = variant['block']
        for name, pin in OLD.items():
            if block.count(pin) != 1:
                raise CoherenceError('Ambiguous original controller pin')
            block = block.replace(pin, FINAL[name], 1)
        additions.append(block)
    anchor = '  };\n  return *contracts;'
    if source.count(anchor) != 1:
        raise CoherenceError('Unrecognized contract table boundary')
    insertion = MARKER + '\n'.join(additions) + '\n'
    updated = source.replace(anchor, insertion + anchor, 1)
    if updated.replace(insertion, '', 1) != source:
        raise CoherenceError('Original native source was not preserved exactly')
    if len(contracts(updated)) != len(original_variants) + 3:
        raise CoherenceError('Unexpected added native contract variants')
    return updated

def controller_report(payload: dict[str, bytes], source: str, native: bytes | None = None) -> dict:
    errors = []
    hashes = {path: digest(data) for path, data in payload.items() if path.startswith(CC + '/')}
    manifest = ET.fromstring(payload[CC + '/addon.xml'])
    version = manifest.get('version')
    if manifest.get('id') != CC:
        errors.append('controller manifest ID mismatch')
    runtime = payload[CC + '/checkpoint_runtime.py'].decode('utf-8')
    declared = re.findall(r'^ADDON_VERSION\s*=\s*[\"\']([^\"\']+)[\"\']', runtime, re.M)
    if declared != [version]:
        errors.append('checkpoint ADDON_VERSION differs from actual manifest')
    endpoints = []
    for endpoint in ENDPOINTS:
        matching = matching_variants(source, CC, CC + '/' + endpoint, hashes)
        pins_present = bool(matching) and (native is None or any(
            all(pin.encode('ascii') in native for pin in v['pins'].values()) for v in matching))
        endpoints.append(dict(endpoint=endpoint, complete_source_variant=bool(matching),
                              required_pins_present_in_binary=pins_present if native is not None else None))
        if not matching:
            errors.append('no complete native contract: ' + endpoint)
        elif native is not None and not pins_present:
            errors.append('reviewed source contract not represented in shipped binary: ' + endpoint)
    for addon in CONSUMERS:
        pins = json.loads(payload[addon + '/CONTROLLER-PREIMAGES.json'])
        if not isinstance(pins, dict) or len(pins) != 13:
            errors.append('incomplete controller preimages: ' + addon)
            continue
        missing = [name for name, expected in pins.items()
                   if hashes.get(CC + '/' + name) != expected]
        if missing:
            errors.append('controller preimage mismatch in ' + addon + ': ' + ', '.join(missing))
    return dict(controller_version=version, checkpoint_version=declared,
                endpoint_contracts=endpoints, errors=errors,
                coherent=not errors, physical_fold_verified=False,
                binary_pin_check_is_necessary_not_sufficient_runtime_proof=True)

def require_export_coherence(apk: Path, packages: tuple) -> dict:
    """Run before creating any delivery output; never version-spoof a signed payload."""
    with ZipFile(apk) as archive:
        names=archive.namelist()
        if len(names)!=len(set(names)) or archive.testzip() is not None:
            raise CoherenceError('Invalid original APK inventory')
        payload = {name[len('assets/addons/'):]: archive.read(name) for name in names
                   if name.startswith('assets/addons/') and not name.endswith('/')
                   and name[len('assets/addons/'):].split('/')[0] in (CC,) + CONSUMERS}
        for addon, embedded, standalone, _ in packages:
            actual = ET.fromstring(archive.read('assets/addons/' + addon + '/addon.xml')).get('version')
            if actual != embedded or actual != standalone:
                raise CoherenceError('Post-signing version rewrite forbidden: ' + addon +
                                     '; finalize matching manifests before native build and signing')
        report=controller_report(payload, (ROOT/NATIVE_PATH).read_text(),
                                 archive.read('lib/arm64-v8a/libkodi.so'))
    if report['errors']:
        raise CoherenceError('; '.join(report['errors']))
    return report
