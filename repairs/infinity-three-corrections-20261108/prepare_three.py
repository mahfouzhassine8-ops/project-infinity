"""Prepare the reviewed three-scope pair with existing owner-bundle tooling.

No signing implementation, provider changes, DEX rebuild, or device access.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIRST = ROOT / 'repairs/infinity-final-closure-2103407'
ISO = ROOT / 'repairs/dual-experience-isolation-2103420'
sys.path[:0] = [str(FIRST), str(ISO)]
import module_bundle
from component_bundles import read_bundle, record, combine
from inventory import canonical, digest, file_sha, load, save, SIGNATURE, validate_names
from release_gate import require, normalize_manifest, component_digest
from verify_device_sources import audit as audit_device

BASE_APK = 'eb4ea5594d18d83c5638d10c0c1b22b2124e6c61c303d41908108dcd02b6ae54'
BASE_NATIVE = '6fc35b8718621ef2e941540b8c858d7d7cd7f408c810ed2fd0d14f7031e8fbb7'
NEW_NATIVE = 'ee3be7c7a95b86f8357539001fcd50bedbd80217b02f130d649f7f57e6075794'
CC = 'script.infinity.commandcenter'
TRAKT = 'script.module.tmdbhelper.sync.trakt'
LABEL = 'assets/experience-component-updates.properties'
NATIVE = 'lib/arm64-v8a/libkodi.so'
PAIRS = ((2103466, '0.3.5.64', '1.2.8.1'), (2103467, '0.3.5.65', '1.2.8.2'))
OVERLAY = ROOT / 'repairs/infinity-only-performance-2103425/overlay' / CC


def command(*args):
    return subprocess.check_output(list(map(str, args)), text=True).strip()


def hashes(root):
    return {p.relative_to(root).as_posix(): file_sha(p) for p in root.rglob('*') if p.is_file()}


def versions(out):
    """Read the sole signer history once before selecting the forward pair."""
    authority = load(ISO / 'release-authority.json')
    require(authority['candidate_versionCode'] == 2103465 and authority['generation'] == 52, 'EXACT_LAST_ISSUED_AUTHORITY')
    repo = 'repos/mahfouzhassine8-ops/project-infinity/'
    issued = []
    for page in range(1, 21):
        runs = json.loads(command('gh', 'api', repo + 'actions/workflows/397702717/runs?per_page=100&page=' + str(page)))['workflow_runs']
        for row in runs:
            if row['id'] == int(os.environ.get('GITHUB_RUN_ID', '0')):
                continue
            require(row['status'] == 'completed', 'CONCURRENT_ORIGINAL_SIGNER')
            if row['conclusion'] != 'success':
                continue
            artifacts = json.loads(command('gh', 'api', repo + 'actions/runs/' + str(row['id']) + '/artifacts?per_page=100'))['artifacts']
            if not any(a['name'] == 'Infinity-Combined-Original-Signer-' + str(row['id']) for a in artifacts):
                continue
            previous = json.loads(command('git', 'show', row['head_sha'] + ':repairs/dual-experience-isolation-2103420/release-authority.json'))
            issued.append(dict(run=row['id'], version=previous['candidate_versionCode'], source=row['head_sha']))
        if len(runs) < 100:
            break
    else:
        raise RuntimeError('VERSION_HISTORY_PAGINATION_LIMIT')
    require(issued and max(r['version'] for r in issued) == 2103465, 'EXACT_LATEST_SIGNED_RECOVERY465')
    refs = command('git', 'ls-remote', '--heads', '--tags', 'origin')
    codes = [int(n) for n in re.findall(r'(?<!\d)(210\d{4})(?!\d)', refs)]
    require(not codes or max(codes) < 2103466, 'NEWER_VERSION_REF_REQUIRES_REVIEW')
    save(out, dict(status='PASS_UNUSED_FORWARD_PAIR_AFTER_OFFICIAL_SIGNER_HISTORY', versions=[p[0] for p in PAIRS], issued=issued, reserved=False))


def inputs(apk, baseline, native, archive, out):
    require(not out.exists(), 'FRESH_PREPARATION_DIRECTORY')
    out.mkdir(parents=True)
    require(file_sha(apk) == BASE_APK and file_sha(native / 'libkodi.so') == NEW_NATIVE, 'PINNED_SIGNED464_AND_REUSED_ARM64_ENGINE')
    native_proof = load(native / 'ARM64-LINK-VERIFIED.json')
    require(native_proof['source_commit'] == 'a2e803e7927c06ed4b7a8e526b688a730a1f31da' and native_proof['native_sha256'] == NEW_NATIVE, 'EXACT_PASSING_NATIVE_LINK')
    require(file_sha(HERE / 'native/xbmc/interfaces/legacy/ModuleXbmc.cpp') == native_proof['source_sha256'], 'NO_UNCOMPILED_NATIVE_CHANGE')
    proof = load(baseline / 'PREPARATION.json')
    require(proof['versionCode'] == 2103464 and proof['source'] == 'de5bf4643a647659d772f96ebc28680a8cf7a58c', 'AUTHENTICATED464_COMPONENT_PROVENANCE')
    catalog = load(baseline / 'components/catalog.json')
    current = load(ISO / 'release-authority.json')
    for owner, row in catalog['bundles'].items():
        read_bundle(baseline / 'components' / row['file'], row)
        if owner in ('COBRA', 'MINIMAL_ANDROID_CONTRACT'):
            require(row == current['bundle_catalog']['bundles'][owner], 'LATEST_PROTECTED_OWNER:' + owner)
    source_report = audit_device(archive, out / 'device-audit', False)
    require(source_report['Trakt_candidate_unchanged'] == 143, 'INSTALLED_TRAKT_CUSTOMIZATIONS_PRESERVED')
    staged_base = out / 'baseline-modules'
    staged_base.mkdir()
    with ZipFile(apk) as z:
        for name in validate_names(z):
            if any(name.startswith('assets/addons/' + aid + '/') for aid in module_bundle.IDS) and not name.endswith('/'):
                target = staged_base / name.removeprefix('assets/addons/')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(z.read(name))
        require(not any(n.startswith('assets/addons/' + TRAKT + '/') for n in z.namelist()), 'NO_EXISTING_BUNDLED_TRAKT_TO_OVERWRITE')
        require(digest(z.read(NATIVE)) == BASE_NATIVE, 'EXACT464_ORIGINAL_ENGINE')
    payload, sources = module_bundle.build(staged_base)
    require(len(sources) == 78 and payload == (staged_base / CC / module_bundle.MANIFEST).read_bytes(), 'EXACT_COMPLETE78_BASELINE')
    subprocess.run(['openssl', 'dgst', '-sha256', '-verify', str(FIRST / 'ORIGINAL-INFINITY-PUBLIC-KEY.pem'), '-signature', str(staged_base / CC / (module_bundle.MANIFEST + '.sig')), str(staged_base / CC / module_bundle.MANIFEST)], check=True, capture_output=True)
    before = hashes(staged_base)
    for version, cc_version, trakt_version in PAIRS:
        work = out / str(version)
        modules = work / 'modules'
        shutil.copytree(staged_base, modules)
        controller = modules / CC
        # Recovery authenticates the same already-present helper as inactive
        # source. No stale-code deletion or unknown-file cleanup is needed.
        shutil.copyfile(OVERLAY / 'native_search_compatibility.py', controller / 'native_search_compatibility.py')
        if version == PAIRS[0][0]:
            shutil.copyfile(OVERLAY / 'provider_inventory.py', controller / 'provider_inventory.py')
        xml = controller / 'addon.xml'
        data = xml.read_bytes()
        require(data.count(b'version="0.3.5.62"') == 1, 'CC_ROOT_VERSION_ONLY')
        xml.write_bytes(data.replace(b'version="0.3.5.62"', ('version="' + cc_version + '"').encode(), 1))
        payload, files = module_bundle.build(modules)
        require(len(files) == 79, 'COMPLETE79_AUTHENTICATED_FILES')
        (controller / module_bundle.MANIFEST).write_bytes(payload)
        (controller / (module_bundle.MANIFEST + '.sig')).unlink()
        copied = hashes(modules)
        allowed = {CC + '/' + n for n in ('addon.xml', module_bundle.MANIFEST, 'provider_inventory.py')}
        require(set(copied) - set(before) == {CC + '/native_search_compatibility.py'}, 'ONE_NEW_COMMANDCENTER_SOURCE')
        require(set(before) - set(copied) == {CC + '/' + module_bundle.MANIFEST + '.sig'}, 'ONLY_OLD_SIGNATURE_REMOVED')
        require({n for n in copied if n in before and copied[n] != before[n]} <= allowed, 'NO_UNRELATED_MODULE_SOURCE_CHANGE')
        trakt = work / TRAKT
        variant = 'candidate' if version == PAIRS[0][0] else 'reference'
        shutil.copytree(out / 'device-audit/trakt' / variant, trakt)
        xml = trakt / 'addon.xml'
        data = xml.read_bytes()
        require(data.count(b'version="1.2.8"') == 1, 'TRAKT_ROOT_VERSION_ONLY')
        xml.write_bytes(data.replace(b'version="1.2.8"', ('version="' + trakt_version + '"').encode(), 1))
        actual = source_report['installed_Trakt_source_hashes']
        changed = {n for n, h in hashes(trakt).items() if actual[n] != h}
        expected = {'addon.xml'}
        if version == PAIRS[0][0]:
            expected |= {'resources/lib/tmdbhelper_sync_trakt/api/authenticator.py', 'resources/lib/tmdbhelper_sync_trakt/api/token.py'}
        require(changed == expected, 'ONLY_VERIFIED_TRAKT_PATCH_AND_FORWARD_METADATA')
        save(work / 'INPUTS.json', dict(versionCode=version, CC=cc_version, Trakt=trakt_version, modules=copied, trakt=hashes(trakt), native_sha256=NEW_NATIVE if version == PAIRS[0][0] else BASE_NATIVE, source=command('git', 'rev-parse', 'HEAD')))
    save(out / 'INPUTS-VERIFIED.json', dict(status='PASS_PINNED464_PLUS_THREE_APPROVED_CORRECTIONS', source=command('git', 'rev-parse', 'HEAD'), baseline_APK_sha256=BASE_APK, owner_evidence_sha256=file_sha(archive), native_sha256=NEW_NATIVE, source_tests='DEVICE-SOURCE-VERIFICATION.json;14 actual-source host cases', APK=False, signing=False, Android='NOT_RUN', Fold='NOT_RUN'))


def finish(apk, baseline, native, out):
    proof = load(out / 'INPUTS-VERIFIED.json')
    require(proof['source'] == command('git', 'rev-parse', 'HEAD') and file_sha(apk) == BASE_APK, 'EXACT_REVIEWED_SOURCE_AND_BASELINE')
    source = proof['source']
    base = load(baseline / 'components/catalog.json')
    for version, cc_version, trakt_version in PAIRS:
        work = out / str(version)
        modules = work / 'modules'
        pin = load(work / 'INPUTS.json')
        now = hashes(modules)
        require({n: h for n, h in now.items() if n != CC + '/' + module_bundle.MANIFEST + '.sig'} == pin['modules'], 'MODULE_BYTES_CHANGED_AFTER_PREFLIGHT')
        require(hashes(work / TRAKT) == pin['trakt'], 'TRAKT_BYTES_CHANGED_AFTER_PREFLIGHT')
        subprocess.run(['openssl', 'dgst', '-sha256', '-verify', str(FIRST / 'ORIGINAL-INFINITY-PUBLIC-KEY.pem'), '-signature', str(modules / CC / (module_bundle.MANIFEST + '.sig')), str(modules / CC / module_bundle.MANIFEST)], check=True, capture_output=True)
        changes = {LABEL: ('infinity.last_updated_in=' + str(version) + '\ncobra.last_updated_in=2103445\n').encode()}
        if version == PAIRS[0][0]:
            changes[NATIVE] = (native / 'libkodi.so').read_bytes()
        with ZipFile(apk) as z:
            original = set(z.namelist())
            for root in (modules, work / TRAKT):
                for p in root.rglob('*'):
                    if not p.is_file():
                        continue
                    name = 'assets/addons/' + (p.relative_to(root).as_posix() if root == modules else TRAKT + '/' + p.relative_to(root).as_posix())
                    raw = p.read_bytes()
                    if name not in original or z.read(name) != raw:
                        changes[name] = raw
        added = {n for n in changes if n not in original}
        require(added == {'assets/addons/' + CC + '/native_search_compatibility.py'} | {'assets/addons/' + TRAKT + '/' + n for n in pin['trakt']}, 'EXACT_ADDITIONAL_SOURCE_MEMBERS')
        dest = work / 'publish/components'
        dest.mkdir(parents=True)
        catalog = copy.deepcopy(base)
        catalog['source'] = source
        for owner, row in base['bundles'].items():
            meta = read_bundle(baseline / 'components' / row['file'], row)
            if owner not in ('INFINITY', 'CHOOSER_SHELL'):
                shutil.copyfile(baseline / 'components' / row['file'], dest / row['file'])
                continue
            selected = {n: raw for n, raw in changes.items() if (n == LABEL) == (owner == 'CHOOSER_SHELL')}
            require(set(selected) - set(meta['members']) <= added and (not added or owner == 'INFINITY' or not (set(selected) & added)), 'OWNER_SCOPED_NEW_SOURCES')
            meta.update(version=str(version) + '.' + owner.lower() + '.1', approved_source=source)
            for name, raw in selected.items():
                member = meta['members'].setdefault(name, dict(compress_type=8, external_attr=0o100644 << 16))
                member['sha256'] = digest(raw)
                meta['payload']['member:' + name] = dict(owner=owner, sha256=digest(raw))
            meta['digest'] = component_digest(meta['payload'], owner)
            path = dest / row['file']
            with ZipFile(baseline / 'components' / row['file']) as original_bundle, ZipFile(path, 'w') as z:
                existing = set(original_bundle.namelist())
                for name in original_bundle.namelist():
                    if name != 'component.json':
                        z.writestr(record(name), selected.get(name.removeprefix('payload/'), original_bundle.read(name)))
                for name in sorted(set(selected) - {n.removeprefix('payload/') for n in existing if n.startswith('payload/')}):
                    z.writestr(record('payload/' + name), selected[name])
                z.writestr(record('component.json'), canonical(meta))
            catalog['bundles'][owner] = dict(file=path.name, sha256=file_sha(path), **{k: meta[k] for k in ('version', 'digest', 'approved_source', 'settings_schema')})
            read_bundle(path, catalog['bundles'][owner])
        save(dest / 'catalog.json', catalog)
        unsigned = work / 'combined-unsigned.apk'
        combine(dest, catalog, unsigned, version)
        differences = {}
        with ZipFile(apk) as a, ZipFile(unsigned) as b:
            names = set(validate_names(a)) - SIGNATURE
            require(set(validate_names(b)) == names | added, 'EXACT_APK_MEMBER_SET')
            for name in sorted(names | added):
                before, after = a.read(name) if name in names else None, b.read(name)
                if before == after:
                    continue
                if name == 'AndroidManifest.xml':
                    require(normalize_manifest(after) == (normalize_manifest(before)[0], version), 'TYPED_ANDROID_VERSION_ONLY')
                else:
                    require(name in changes and after == changes[name], 'UNAPPROVED_APK_MEMBER:' + name)
                differences[name] = digest(after)
        require(set(differences) == set(changes) | {'AndroidManifest.xml'}, 'ALL_AND_ONLY_APPROVED_PAYLOAD_CHANGES')
        save(work / 'publish/PREPARATION.json', dict(status='PASS_EXACT464_THREE_CORRECTIONS_OR_FORWARD_RECOVERY', versionCode=version, CC=cc_version, Trakt=trakt_version, skin='1.0.5.270_UNCHANGED', source=source, run_id=int(os.environ.get('GITHUB_RUN_ID', '0')), baseline_sha256=BASE_APK, unsigned_sha256=file_sha(unsigned), native_sha256=pin['native_sha256'], changed_members=differences, added_members=sorted(added), Cobra_bundle_byte_identical=True, minimal_contract_bundle_byte_identical=True, all_DEX_byte_identical=True, account_settings_or_database_changes=False, Android='NOT_RUN', Fold='NOT_RUN', public_release=False))
    print('PASS complete79 signed-module inputs and scoped pair prepared; APK signing/Android NOT RUN')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('operation', choices=['versions', 'inputs', 'finish'])
    for name in ('apk', 'baseline', 'native', 'archive', 'out'):
        p.add_argument('--' + name, type=Path)
    a = vars(p.parse_args())
    op = a.pop('operation')
    if op == 'versions':
        versions(a['out'])
    else:
        if op == 'finish':
            a.pop('archive')
        globals()[op](**a)
