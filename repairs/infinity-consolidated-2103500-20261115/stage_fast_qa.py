#!/usr/bin/env python3
"""Produce a byte-scoped unsigned Infinity500 QA installer input.
Not an installable APK. The sole reviewed original-key signer must authorize
the eventual signed QA output, and 2103502 is a provisional number only.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile, ZipInfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPO = 'mahfouzhassine8-ops/project-infinity'
BRANCH = 'work/infinity-2103500-consolidated-repair-20261115'
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
BASE_APK = '224d5f808587ce4004a96a003331abe7c71cbe7bd08ec6b1d3ec288c6c75cf40'
ENGINE = 'ed2d955d1825bf838ea50a712782e54b69926d40605270a2f241efd913202ee7'
CAST_DEX = '4360efcdf3af08a8388f18846c79353517ab3d7ee6a3c026838b7748c0914c98'
VER = 2103502  # Provisional QA only; authority must reserve before signing.
LABEL = 'assets/experience-component-updates.properties'
NATIVE = 'lib/arm64-v8a/libkodi.so'
DEX = 'classes6.dex'
inputs = {
    'base': ('14128448982', 43632329510, 'sha256:891c587de989319883ed453a7a2fcd583626a0436f363db62021aa3fa779c0dd', 'ccc30a77e07c2cf0abc3800ea60f4a68dc6bd9a3'),
    'native': ('14187138056', 43774504911, 'sha256:532fbbae52e334e367e8582e6427757b7943965ca04338012877bb4098d96b26', 'c3c1e920e17fbeee5b9977eadc9409a9806a06f9'),
    'cast': ('14180278660', 43762472390, 'sha256:be931b1864a1fc08213935e6ae862d8bda37e64a18fede69b33befea74b41e19', '07a0ada538fd397430a6a1b7f3577c3cbfca8b83'),
}


def check(ok, reason):
    if not ok:
        raise RuntimeError(reason)


def sha_file(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def zip_sha(z, name):
    with z.open(name) as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def unique_sha(folder, expected, suffix):
    results = [p for p in Path(folder).rglob('*') if p.is_file() and p.name.endswith(suffix)]
    matches = [p for p in results if sha_file(p) == expected]
    check(len(matches) == 1, 'EXACT_ARTIFACT_MISSING_OR_AMBIGUOUS:' + suffix)
    return matches[0]


def github(path):
    return json.loads(subprocess.check_output(['gh', 'api', 'repos/' + REPO + '/' + path], text=True, timeout=90))


def trust():
    check(os.environ.get('GITHUB_ACTIONS') == 'true', 'CI_ONLY')
    check(os.environ.get('GITHUB_REPOSITORY') == REPO, 'WRONG_REPOSITORY')
    check(os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH, 'WRONG_BRANCH')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True, cwd=ROOT).strip()
    check(head == os.environ.get('GITHUB_SHA'), 'HEAD_MISMATCH')
    sys.path.insert(0, str(HERE))
    import verify_scope
    verify_scope.main()
    pin = json.loads((HERE / 'BASELINE.json').read_text())
    check(pin['APK_sha256'] == BASE_APK and pin['versionCode'] == 2103500, 'UNAUTHENTICATED500')
    policy = json.loads((HERE / 'POLICY-ARM64-INTEGRATION.json').read_text())
    check(policy['ARM64']['native_sha256'] == ENGINE and policy['ARM64']['status'] == 'PASS_FULL_ARM64_LINK_AND_EXACT500_ABI', 'ENGINE_NOT_VERIFIED')
    cast = json.loads((HERE / 'CAST-CLASS-PRESERVATION.json').read_text())
    check(cast['candidate_DEX_sha256'] == CAST_DEX and cast['changed'] == ['Lcom/projectinfinity/kodi/InfinityCastDialog;', 'Lcom/projectinfinity/kodi/InfinityCastSession;'], 'CAST_SCOPE')
    for key, (aid, run, digest, source) in inputs.items():
        row = github('actions/artifacts/' + aid)
        parent = github('actions/runs/' + str(run))
        check(not row['expired'] and row['digest'] == digest and row['workflow_run']['id'] == run and parent['head_sha'] == source and parent['conclusion'] == 'success', 'UNVERIFIED_INPUT:' + key)


def write_zip_member(zout, info, source, replacement=None):
    dst = ZipInfo(info.filename, info.date_time)
    dst.compress_type = info.compress_type
    dst.external_attr = info.external_attr
    dst.create_system = info.create_system
    dst.flag_bits = info.flag_bits & ~1
    dst.comment = info.comment
    with zout.open(dst, 'w', force_zip64=(info.file_size >= 2**31)) as target:
        if replacement is None:
            with source.open(info) as stream:
                shutil.copyfileobj(stream, target, 2 * 1024 * 1024)
        elif isinstance(replacement, bytes):
            target.write(replacement)
        else:
            with Path(replacement).open('rb') as stream:
                shutil.copyfileobj(stream, target, 2 * 1024 * 1024)


def main():
    trust()
    sys.path.insert(0, str(ROOT / 'repairs/dual-experience-isolation-2103420'))
    from inventory import SIGNATURE, validate_names
    from component_bundles import set_version
    base = unique_sha(ROOT / 'fastqa-inputs/base', BASE_APK, '.apk')
    native = unique_sha(ROOT / 'fastqa-inputs/native', ENGINE, 'libkodi.so')
    dex = unique_sha(ROOT / 'fastqa-inputs/cast', CAST_DEX, 'classes.dex')
    sdk = Path(os.environ['ANDROID_HOME']) / 'build-tools/35.0.0'
    verified = subprocess.check_output([str(sdk / 'apksigner'), 'verify', '--verbose', '--print-certs', str(base)], text=True)
    check('certificate SHA-256 digest: ' + CERT in verified and all(re.search(r'Verified using v' + str(n) + r' scheme[^\\n]*: true', verified) for n in (1, 2, 3)), 'ORIGINAL_CERTIFICATE')
    outdir = ROOT / 'fastqa-output'
    outdir.mkdir(exist_ok=True)
    apk = outdir / 'Infinity-2103502-Fast-QA-UNSIGNED-NOT-INSTALLABLE.apk'
    changed = (NATIVE, DEX, LABEL, 'AndroidManifest.xml')
    with ZipFile(base) as old:
        members = set(validate_names(old)) - SIGNATURE
        check(set(changed) <= members, 'BASE_MEMBERS_MISSING')
        check(zip_sha(old, NATIVE) == '3caccc96c23336e220b791118989f3a850b73fa8804267fb7beb2aad3b3afc75', 'BASE_ENGINE_MISMATCH')
        original_manifest = old.read('AndroidManifest.xml')
        new_manifest = set_version(original_manifest, VER)
        old_label = old.read(LABEL)
        check(old_label == b'infinity.last_updated_in=2103500\ncobra.last_updated_in=2103445\n', 'EXACT500_LABEL_REQUIRED')
        updates = {NATIVE: native, DEX: dex, LABEL: b'infinity.last_updated_in=2103502\ncobra.last_updated_in=2103445\n',
                   'AndroidManifest.xml': new_manifest}
        with ZipFile(apk, 'w', allowZip64=True) as dest:
            for info in old.infolist():
                if info.filename in SIGNATURE:
                    continue
                write_zip_member(dest, info, old, updates.get(info.filename))
        with ZipFile(apk) as new:
            check(set(validate_names(new)) == members, 'MEMBERS_CHANGED')
            unchanged = 0
            changes = {}
            for name in sorted(members):
                before = zip_sha(old, name)
                after = zip_sha(new, name)
                wanted = sha_file(updates[name]) if name in updates and isinstance(updates[name], Path) else hashlib.sha256(updates[name]).hexdigest() if name in updates else before
                check(after == wanted, 'UNEXPECTED_CHANGED_MEMBER:' + name)
                if after == before:
                    unchanged += 1
                else:
                    changes[name] = {'before': before, 'after': after}
            check(set(changes) == set(changed), 'FOUR_SCOPED_CHANGES_ONLY')
    receipt = {
        'status': 'PASS_UNSIGNED_QA_STAGING_NOT_INSTALLABLE',
        'baseline': 2103500,
        'baseline_sha256': BASE_APK,
        'provisional_qa_version_not_reserved': VER,
        'no_signing_keys_used': True,
        'signature': 'NONE',
        'expected_original_certificate': CERT,
        'source': os.environ['GITHUB_SHA'],
        'native_sha256': ENGINE,
        'cast_dex_sha256': CAST_DEX,
        'changed_members': changes,
        'unchanged_members': unchanged,
        'Cobra': 'BYTE_IDENTICAL',
        'Search_Watchlist_ContinuePlaying_EmptyShell': 'DEFERRED_UNCHANGED',
        'profile_and_user_data': 'NOT_ACCESSED',
        'owner_installation': 'BLOCKED_PENDING_ORIGINAL_SIGNING_AND_REGISTRY',
    }
    (outdir / 'QA-STAGING.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': receipt['status'], 'unchanged_members': unchanged, 'changed_members': sorted(changes)}))


if __name__ == '__main__':
    main()
