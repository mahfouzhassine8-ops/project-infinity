"""Actual unsigned APK negative controls. Never installs or executes the app."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import struct
import tempfile
from zipfile import ZipFile
import zlib

from inventory import HERE, file_sha, load, save
from release_gate import Rejected, inspect_candidate, verify_approved_payload, verify_combination


def replace_member(source, destination, target, transform):
    with ZipFile(source) as original, ZipFile(destination, 'w', allowZip64=True) as output:
        if target not in original.namelist():
            raise ValueError('Negative control member absent')
        for info in original.infolist():
            with output.open(copy.copy(info), 'w', force_zip64=info.file_size >= 2 ** 31) as writer:
                if info.filename == target:
                    before = original.read(info)
                    after = transform(before)
                    if before == after:
                        raise ValueError('Negative control made no change')
                    writer.write(after)
                else:
                    with original.open(info) as reader:
                        shutil.copyfileobj(reader, writer, 4 * 1024 * 1024)


def changed_cobra_setting(raw):
    old, new = b'infinity_cobra_live\0', b'infinity_cobra_test\0'
    if raw.count(old) != 1 or len(old) != len(new):
        raise ValueError('Exact DEX string preimage absent')
    changed = bytearray(raw.replace(old, new))
    # Keep a valid DEX container, so rejection proves semantic owner checking
    # rather than a parser rejecting a corrupt file.
    changed[12:32] = hashlib.sha1(changed[32:]).digest()
    struct.pack_into('<I', changed, 8, zlib.adler32(changed[12:]) & 0xffffffff)
    return changed


def verify(unsigned, jars, out):
    registry = load(HERE / 'accepted-combined-release.json')
    results = []
    with tempfile.TemporaryDirectory(prefix='infinity-actual-controls-') as tmp:
        root = Path(tmp)
        payload, version = inspect_candidate(unsigned, jars, root / 'baseline-dex')
        if version != 2103421:
            raise ValueError('Expected unsigned preservation candidate2103421')
        verify_approved_payload(registry, payload)
        try:
            verify_combination(registry, payload, version, registry['generation'])
        except Rejected as exc:
            if str(exc) != 'UNRESOLVED_RELEASE_BLOCKERS':
                raise
            results.append({'case': 'unchanged_runtime_higher_package_version', 'result': str(exc)})
        else:
            raise ValueError('Unresolved lifecycle accepted')
        cases = [
            ('cobra_settings_dex', 'classes.dex', changed_cobra_setting, 'COBRA'),
            ('infinity_python', 'assets/addons/script.infinity.commandcenter/infinity_search.py',
             lambda raw: raw + b'\n# deliberately unapproved negative control\n', 'INFINITY'),
        ]
        for name, member, transform, owner in cases:
            apk = root / (name + '.apk')
            replace_member(unsigned, apk, member, transform)
            candidate, actual_version = inspect_candidate(apk, jars, root / (name + '-dex'))
            changed = sorted(k for k in candidate if candidate[k] != payload.get(k))
            if not changed or actual_version != version:
                raise ValueError('Negative APK construction mismatch')
            changed_owners = {registry['payload'][k]['owner'] for k in changed}
            if owner not in changed_owners:
                raise ValueError('Target owner not exercised: ' + str(changed_owners))
            try:
                verify_combination(registry, candidate, version, registry['generation'])
            except Rejected as exc:
                if not str(exc).startswith('STALE_OR_MUTATED_OWNER:'):
                    raise
                results.append({'case': name, 'apk_sha256': file_sha(apk), 'result': str(exc),
                                'changed_owner_set': sorted(changed_owners), 'changed_identities': changed})
            else:
                raise ValueError('Mutated actual APK passed signing gate')
    result = {'status': 'PASS_ACTUAL_APK_NEGATIVE_CONTROLS', 'controls': results,
              'installed_or_executed': False, 'signing_credentials_read': False,
              'shutdown_runtime_tested': False}
    save(out, result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('unsigned', 'jars', 'out'):
        parser.add_argument('--' + name, required=True, type=Path)
    print(json.dumps(verify(**vars(parser.parse_args())), indent=2))
