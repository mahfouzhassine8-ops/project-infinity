"""Reproduce the initial accepted2103420 ledger. Never promote a candidate."""
import argparse
from pathlib import Path
from zipfile import ZipFile

from inventory import APK_SHA, BASE_SOURCE, CERT_SHA, HERE, OWNERS, PACKAGE, file_sha, load, save
from release_gate import component_digest, payload_from_inventory, validate_registry


def bootstrap(apk, evidence, out):
    if file_sha(apk) != APK_SHA:
        raise ValueError('Only the previously user-approved2103420 baseline may initialize this ledger')
    evidence, out = Path(evidence), Path(out)
    ownership = load(evidence / 'OWNERSHIP-MAP.json')
    if ownership['provenance']['apk_sha256'] != APK_SHA:
        raise ValueError('Wrong ownership provenance')
    for name, sha in ownership['shards'].items():
        if file_sha(evidence / name) != sha:
            raise ValueError('Ownership shard mismatch')
    classes = load(evidence / 'DEX-MEMBERS.json.gz')
    with ZipFile(apk) as archive:
        payload = payload_from_inventory(ownership, classes, archive.read('AndroidManifest.xml'))
    registry = {'schema': 1, 'generation': 1, 'package': PACKAGE, 'certificate_sha256': CERT_SHA,
                'accepted_app_versionCode': 2103420, 'accepted_apk_sha256': APK_SHA,
                'accepted_lock_commit': '883c64a4de6f87077893921454de71bba850235b',
                'authority': 'User-approved signed2103420; no new candidate accepted',
                'components': {}, 'payload': payload, 'release_blockers': ownership['release_blockers']}
    module_names = {'INFINITY': 'infinity-core', 'COBRA': 'cobra-core', 'CHOOSER_SHELL': 'app-shell',
                    'MINIMAL_ANDROID_CONTRACT': 'platform-contract', 'UNRESOLVED': 'unresolved-frozen'}
    for owner in OWNERS:
        fingerprint = component_digest(payload, owner)
        version = '2103420' if owner == 'INFINITY' else 'bundled-2103420-' + fingerprint[:16]
        component = {'version': version, 'approved_source': BASE_SOURCE, 'digest': fingerprint,
                     'settings_schema': 'existing-2103420-no-migration'}
        registry['components'][owner] = component
        module = {'schema': 1, 'owner': owner, 'module': module_names[owner], **component,
                  'status': 'FINGERPRINT_PARTITION_ONLY_RUNTIME_ISOLATION_BLOCKED',
                  'baseline_apk_sha256': APK_SHA, 'certificate_sha256': CERT_SHA,
                  'members': {k: v['sha256'] for k, v in payload.items() if v['owner'] == owner}}
        target = out / 'modules' / module_names[owner] / 'component.json'
        if target.exists():
            raise ValueError('Refusing to overwrite an existing component authority')
        save(target, module)
    target = out / 'accepted-combined-release.json'
    if target.exists():
        raise ValueError('Refusing to overwrite an existing accepted registry')
    validate_registry(registry)
    save(target, registry)
    return registry


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('apk', 'evidence', 'out'):
        parser.add_argument('--' + name, required=True, type=Path)
    result = bootstrap(**vars(parser.parse_args()))
    print('Initial accepted baseline registry reproduced; candidate acceptance unchanged')
