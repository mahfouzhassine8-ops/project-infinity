"""Key-free original83 owner-bundle preparation; no signing or installation.

Only a frozen successful ARM64 artifact and successful, explicitly scoped native
injection Android evidence can admit staging. The request starts disabled.
Original83, its permanent signer and all undeclared APK bytes stay protected.
"""
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
from types import SimpleNamespace
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
AUTHORITY = 'repairs/dual-experience-isolation-2103420/release-authority.json'
BASE = '3d9709bb1226a2ffa3a474cf04b3d3842b084611'
APK83 = '0c597a2976d9667796a4baac18ed9b624960e22399c94c9f62b1a52393d43236'
NATIVE83 = 'f14ff78865158337eb6fd19dfe549912d57f2a6a912e5b3440ed28880ee0cb0c'
CERT = 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
LIB = 'lib/arm64-v8a/libkodi.so'
LABEL = 'assets/experience-component-updates.properties'
CHANGES = {LIB, LABEL, 'AndroidManifest.xml'}
REFERENCE = 'repairs/infinity-functional-startup-2103482-20261111/package_internal_qa.py'
REFERENCE_SOURCE = '43dac4a78fb3429ec6d62e7d3f0d2ec208a4e0b9'
REFERENCE_SHA = 'b4d03488be53396f0aa471da911f425ccfdf8d21869587151fe7f3485b435e89'


def require(value, label):
    if not value:
        raise RuntimeError(label)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path):
    return json.loads(Path(path).read_bytes())


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], timeout=45)


def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', 'repos/mahfouzhassine8-ops/project-infinity/' + path], timeout=45))


def tools():
    authority = json.loads(git('show', BASE + ':' + AUTHORITY))
    for name, wanted in authority['source_files'].items():
        require(sha(ROOT / name) == wanted, 'ORIGINAL_TOOL_CHANGED_BEFORE_IMPORT:' + name)
    require((ROOT / REFERENCE).read_bytes() == git('show', REFERENCE_SOURCE + ':' + REFERENCE) and
            sha(ROOT / REFERENCE) == REFERENCE_SHA, 'IMMUTABLE_STREAMING_OWNER_ASSEMBLER_REFERENCE')
    sys.path.insert(0, str(ROOT / 'repairs/dual-experience-isolation-2103420'))
    import component_bundles as cb
    import inventory
    require(Path(cb.__file__).resolve() == ROOT / 'repairs/dual-experience-isolation-2103420/component_bundles.py' and
            Path(inventory.__file__).resolve() == ROOT / 'repairs/dual-experience-isolation-2103420/inventory.py',
            'ORIGINAL_OWNER_TOOL_IMPORT_ORIGIN')
    spec = importlib.util.spec_from_file_location('original83_streaming_owner_reference', ROOT / REFERENCE)
    ref = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ref)
    return SimpleNamespace(cb=cb, inventory=inventory, ref=ref, authority=authority)


def producer(row):
    run = api('actions/runs/' + str(row['run']))
    require(run['status'] == 'completed' and run['conclusion'] == 'success' and run['head_sha'] == row['source'] and
            run['workflow_id'] == row['workflow_id'], 'EXACT_SUCCESSFUL_PRODUCER')
    artifact = api('actions/artifacts/' + str(row['id']))
    require(not artifact['expired'] and artifact['workflow_run']['id'] == row['run'] and
            all(artifact[k] == row[k] for k in ('id', 'name', 'digest', 'size_in_bytes')), 'EXACT_LIVE_INPUT_ARTIFACT')


def member_sha(archive, name):
    with archive.open(name) as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def receipt(path, spec):
    require(sha(path) == spec['sha256'] and re.fullmatch('PASS(?:_[A-Z0-9]+)*', spec['status']), 'FROZEN_PASS_RECEIPT_REQUIRED')
    value = load(path)
    require(value['status'] == spec['status'] and bool(spec['required_fields']) and
            all(value.get(key) == expected for key, expected in spec['required_fields'].items()), 'EXACT_REVIEWED_PROOF_CONTRACT')
    return value


def compare(baseline, candidate, version, native_sha, t):
    require(sha(baseline) == APK83, 'EXACT_ORIGINAL_SIGNED83_REQUIRED')
    with ZipFile(baseline) as old, ZipFile(candidate) as new:
        names = set(t.inventory.validate_names(old)) - set(t.inventory.SIGNATURE)
        require(set(t.inventory.validate_names(new)) - set(t.inventory.SIGNATURE) == names, 'APK_MEMBER_VECTOR_CHANGED')
        changes = {}
        for name in names:
            before_sha, after_sha = member_sha(old, name), member_sha(new, name)
            if before_sha != after_sha:
                changes[name] = dict(before=before_sha, after=after_sha)
        require(set(changes) == CHANGES and member_sha(old, LIB) == NATIVE83 and member_sha(new, LIB) == native_sha,
                'ONLY_NATIVE_VERSION_AND_INFINITY_LABEL_MAY_CHANGE')
        before, old_version = t.cb.normalize_manifest(old.read('AndroidManifest.xml'))
        after, new_version = t.cb.normalize_manifest(new.read('AndroidManifest.xml'))
        require(old_version == 2103483 and new_version == version and before == after, 'TYPED_MANIFEST_VERSION_ONLY')
        require(new.read(LABEL) == ('infinity.last_updated_in=' + str(version) + '\ncobra.last_updated_in=2103445\n').encode(),
                'EXACT_INFINITY_LABEL_AND_UNCHANGED_COBRA_LABEL')
        return changes, len(names) - len(changes)


def stage(request, baseline, components, owners_archive, native, native_archive, android, android_archive, sdk, out):
    r = load(request)
    require(r['enabled'] is True and r['operation'] == 'stage-original83-native-observation-unsigned-QA' and
            r['signing'] is False and r['registry_mutation'] is False and r['owner_delivery'] is False,
            'EXPLICIT_REVIEWED_KEY_FREE_STAGE_REQUEST')
    require(os.environ.get('GITHUB_REPOSITORY') == 'mahfouzhassine8-ops/project-infinity' and
            os.environ.get('GITHUB_REF') == 'refs/heads/' + r['branch'] and
            git('rev-parse', 'HEAD').decode().strip() == os.environ.get('GITHUB_SHA') and
            not git('status', '--porcelain', '--untracked-files=no').strip(), 'CLEAN_EXACT_CI_PREPARATION_SOURCE')
    commit = git('rev-parse', 'HEAD').decode().strip()
    for path in (request.resolve(), Path(__file__).resolve(), HERE / 'BASELINE83.json'):
        require(path.is_relative_to(ROOT) and path.read_bytes() ==
                git('show', commit + ':' + path.relative_to(ROOT).as_posix()), 'FROZEN_COMMITTED_PREPARATION_INPUT:' + path.name)
    require(not out.exists() and sha(baseline) == APK83, 'FRESH_OUTPUT_AND_LOCKED83')
    t = tools()
    base = load(HERE / 'BASELINE83.json')
    require(base['authority_source'] == BASE and base['bundle_catalog'] == t.authority['bundle_catalog'], 'EXACT_REGISTERED83_CATALOG')
    for key in ('signed_apk', 'prepared_owners'):
        producer(base[key])
    require(api('git/ref/heads/work/infinity-2103460-nine-corrections-20261106')['object']['sha'] == BASE,
            'LIVE_AUTHORITY_ADVANCED_RECONCILE_BEFORE_STAGING')
    version = r['provisional_versionCode']
    require(type(version) is int and 2103483 < version <= 2100000000 and r['version_reserved'] is False, 'UNRESERVED_REVIEWED_FORWARD_VERSION')
    certificate = subprocess.check_output([str(sdk / 'apksigner'), 'verify', '--verbose', '--print-certs', str(baseline)], text=True, timeout=90)
    require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)', certificate) == [CERT], 'ORIGINAL83_PERMANENT_CERTIFICATE')
    require('sha256:' + sha(owners_archive) == base['prepared_owners']['digest'] and
            owners_archive.stat().st_size == base['prepared_owners']['size_in_bytes'], 'AUTHENTICATED83_OWNER_ARCHIVE')
    catalog = load(components / 'catalog.json')
    require(catalog == base['bundle_catalog'] and set(catalog['bundles']) == set(t.cb.OWNED), 'COMPLETE_EXACT83_OWNER_VECTOR')
    with ZipFile(owners_archive) as archive:
        t.inventory.validate_names(archive)
        for name in ['catalog.json'] + [row['file'] for row in catalog['bundles'].values()]:
            require(member_sha(archive, 'components/' + name) == sha(components / name), 'OWNER_FILE_NOT_FROM83_ARTIFACT:' + name)
    metas = {owner: t.cb.read_bundle(components / row['file'], row) for owner, row in catalog['bundles'].items()}
    # Reconcile all baseline members and original DEX ordering to the exact83
    # owner inputs before substituting a single engine byte.
    with ZipFile(baseline) as apk:
        members = {n for meta in metas.values() for n in meta['members']}
        dex = [(o, n) for o in ('CHOOSER_SHELL', 'MINIMAL_ANDROID_CONTRACT', 'INFINITY', 'COBRA') for n in sorted(metas[o]['dex'])]
        dex_names = {'classes' + (str(i) if i > 1 else '') + '.dex' for i in range(1, len(dex) + 1)}
        require(set(t.inventory.validate_names(apk)) - set(t.inventory.SIGNATURE) == members | dex_names, 'COMPLETE83_APK_MEMBER_VECTOR')
        for owner, row in catalog['bundles'].items():
            with ZipFile(components / row['file']) as bundle:
                for name in metas[owner]['members']:
                    expected = (hashlib.sha256(t.cb.set_version(bundle.read('payload/' + name), 2103483)).hexdigest()
                                if name == 'AndroidManifest.xml' else member_sha(bundle, 'payload/' + name))
                    require(member_sha(apk, name) == expected, 'EXACT83_OWNER_APK_MEMBER:' + name)
        for i, (owner, name) in enumerate(dex, 1):
            require(member_sha(apk, 'classes' + (str(i) if i > 1 else '') + '.dex') == metas[owner]['dex'][name], 'ORIGINAL83_DEX_BYTES')
    producer(r['native_producer'])
    require(r['native_producer']['workflow_id'] != 397702717 and 'sha256:' + sha(native_archive) == r['native_producer']['digest'] and
            native_archive.stat().st_size == r['native_producer']['size_in_bytes'],
            'KEY_FREE_AUTHENTICATED_NATIVE_PRODUCER')
    with ZipFile(native_archive) as archive:
        t.inventory.validate_names(archive)
        for name in ['libkodi.so'] + [spec['file'] for spec in r['native_proofs'].values()]:
            require(member_sha(archive, name) == sha(native / name), 'EXACT_NATIVE_ARTIFACT_MEMBER:' + name)
    engine_sha = sha(native / 'libkodi.so')
    require(engine_sha == r['native_sha256'] and engine_sha != NATIVE83, 'ACTUAL_NEW_OBSERVATION_ENGINE_REQUIRED')
    require(set(r['native_proofs']) == {'build', 'source_preservation'}, 'LINK_ABI_AND_SOURCE_PROOFS_REQUIRED')
    require(r['native_proofs']['build']['required_fields'].get('native_sha256') == engine_sha and
            r['native_proofs']['build']['required_fields'].get('source_commit') == r['native_producer']['source'] and
            NATIVE83 in r['native_proofs']['source_preservation']['required_fields'].values() and
            r['native_producer']['source'] in r['native_proofs']['source_preservation']['required_fields'].values(),
            'EXPLICIT_NEW_ENGINE_SOURCE_AND_ORIGINAL83_NATIVE_PROOF_BINDINGS')
    for spec in r['native_proofs'].values():
        receipt(native / spec['file'], spec)
    producer(r['android_producer'])
    require('sha256:' + sha(android_archive) == r['android_producer']['digest'] and
            android_archive.stat().st_size == r['android_producer']['size_in_bytes'], 'AUTHENTICATED_ANDROID_EVIDENCE_ARCHIVE')
    with ZipFile(android_archive) as archive:
        t.inventory.validate_names(archive)
        require(member_sha(archive, r['android_proof']['file']) == sha(android / r['android_proof']['file']),
                'ANDROID_RECEIPT_NOT_FROM_FROZEN_PRODUCER')
    observed = receipt(android / r['android_proof']['file'], r['android_proof'])
    require(observed['native_sha256'] == engine_sha and observed['baseline_APK_sha256'] == APK83 and
            observed['native_injection'] is True and observed['APK_modified'] is False and
            observed['before_first_launch'] is True and observed['owner_device'] is False,
            'ACTUAL_ANDROID_INJECTED_NATIVE83_SCOPE_REQUIRED')
    source = git('rev-parse', 'HEAD').decode().strip()
    out.mkdir()
    owners = out / 'components'
    owners.mkdir()
    updated = copy.deepcopy(catalog)
    updated.update(source=source, release_approved=False)
    for owner in t.cb.OWNED:
        row = updated['bundles'][owner]
        before, target = components / row['file'], owners / row['file']
        if owner in ('INFINITY', 'CHOOSER_SHELL'):
            changed = {'payload/' + LIB: native / 'libkodi.so'} if owner == 'INFINITY' else {
                'payload/' + LABEL: ('infinity.last_updated_in=' + str(version) + '\ncobra.last_updated_in=2103445\n').encode()}
            meta = t.ref.rebuild_owner(before, target, owner, source, version, changed)
            row.update(sha256=sha(target), **{k: meta[k] for k in ('version', 'digest', 'approved_source')})
        else:
            shutil.copyfile(before, target)
            require(sha(target) == sha(before), 'PROTECTED_WHOLE_OWNER_BUNDLE_CHANGED')
        t.cb.read_bundle(target, row)
    (owners / 'catalog.json').write_bytes(t.inventory.canonical(updated))
    candidate = out / ('Infinity-' + str(version) + '-Core-Outcomes-UNSIGNED-NOT-INSTALLABLE.apk')
    t.cb.combine(owners, updated, candidate, version)
    changes, retained = compare(baseline, candidate, version, engine_sha, t)
    proof = dict(status='PASS_KEY_FREE_UNSIGNED83_NATIVE_OBSERVATION_THREE_MEMBER_PRESERVATION',
        source=source, baseline_version=2103483, baseline_APK_sha256=APK83, authority_source=BASE,
        versionCode=version, version_reserved=False, native_sha256=engine_sha, native_producer=r['native_producer'],
        Android_native_injection='PASS_SELECTED_SCOPE_ONLY_NOT_APK_INSTALL_ACCEPTANCE',
        Android_producer=r['android_producer'], Android_proof_sha256=r['android_proof']['sha256'],
        unsigned_sha256=sha(candidate), changed_members=changes, unchanged_payload_members=retained,
        request_sha256=sha(request), stage_tool_sha256=sha(Path(__file__)), baseline_metadata_sha256=sha(HERE / 'BASELINE83.json'),
        original_tools_sha256=t.authority['source_files'], reference_assembler_sha256=REFERENCE_SHA,
        Core_path_or_source_patch=False, preserved_owner_bundles={o: sha(owners / catalog['bundles'][o]['file']) for o in ('COBRA', 'MINIMAL_ANDROID_CONTRACT')},
        signed=False, original_key_used=False, registry_mutated=False, APK_install_over='NOT_RUN_REQUIRES_ORIGINAL_SIGNING',
        owner_delivery=False, Fold='NOT_RUN', shutdown_or_Core_outcome_repair='NOT_ESTABLISHED_BY_PACKAGING')
    (out / 'UNSIGNED-QA-PRESERVATION.json').write_text(json.dumps(proof, indent=2, sort_keys=True) + '\n')
    (out / 'ORIGINAL83-SIGNATURE.txt').write_text(certificate)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('request', 'baseline', 'components', 'owners-archive', 'native', 'native-archive', 'android', 'android-archive', 'sdk', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    stage(**vars(parser.parse_args()))
