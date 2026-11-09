"""Exact signed69 + three Python sources, using the unchanged original tools.

Inputs emit unsigned complete80 manifests for the existing original module
signer. finish reuses the original component assembler for unsigned APKs only.
No signer, registry mutation, native build, device access, or acceptance
assertion is implemented.
"""
import argparse
import ast
import copy
import hashlib
import importlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIRST = ROOT / 'repairs/infinity-final-closure-2103407'
ISO = ROOT / 'repairs/dual-experience-isolation-2103420'
AUTHORITY = 'repairs/dual-experience-isolation-2103420/release-authority.json'
BASE_SOURCE = 'a76e29b84996304241e6b309d56a31e6659ad190'
BASE_APK = '804eebc57af2e4ef4e5418b56994bda64eb7fd7e7f2c0653b5c6e2a9f7833058'
BASE_NATIVE = 'ee3be7c7a95b86f8357539001fcd50bedbd80217b02f130d649f7f57e6075794'
BASE_MANIFEST_SHA = '6fb82d58f2488a2eac23d2f0aa0e8a4eaa600f5fcf35901a24445b32beb852d2'
PREPARED_SOURCE = 'a56ef7d9e96146a167afe84e5a8a6fcf904f40cb'
BRIDGE_SOURCE = 'e410f30ba9e38182e4e77810e5237e5442cbd31a'
SOURCE_FREEZE = HERE / 'SERVICE-SURVIVAL-SOURCE-PROOF.json'
ORIGINAL_REVIEWED = '2e52b7befd0228a09449f79eaf9774a3946dfa1c'
CC = 'script.infinity.commandcenter'
MANIFEST = 'INFINITY-MODULES.v1'
PYTHON = {'plugin.py', 'resume_hub.py', 'service.py'}
NATIVE = 'lib/arm64-v8a/libkodi.so'
LABEL = 'assets/experience-component-updates.properties'
PREFIX = 'assets/addons/' + CC + '/'
HOST_EVIDENCE = ('INTEGRATION-SOURCE-PROOF.json', 'ACTUAL-SOURCE-HOST-RESULT.json', 'PROJECTION-HOST-RESULT.json')
CURRENT_EVIDENCE = ('CURRENT-SOURCE-PROOF.json', 'TV-IDENTITY-SAFETY-BRIDGE-HOST-RESULT.json',
                    'TV-IDENTITY-SAFETY-BRIDGE-REVIEW.json')


def require(value, label):
    if not value:
        raise RuntimeError(label)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(path):
    return json.loads(Path(path).read_bytes())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *map(str, args)])


def hashes(root):
    return {p.relative_to(root).as_posix(): file_sha(p) for p in root.rglob('*') if p.is_file()}


def load_tools():
    """Validate immutable original executable dependencies BEFORE importing any."""
    authority = json.loads(git('show', BASE_SOURCE + ':' + AUTHORITY))
    pins = dict(authority['source_files'])
    for name in ('module_bundle.py', 'FIRSTPARTY-COMPOSITION-PLAN.json', 'ORIGINAL-INFINITY-PUBLIC-KEY.pem',
                 'SignInfinityModules.java', 'InfinityInstalledModules.java.in', 'module_dex.py', 'p0/manifest.py'):
        path = (FIRST / name).relative_to(ROOT).as_posix()
        pins[path] = digest(git('show', BASE_SOURCE + ':' + path))
    for name, wanted in pins.items():
        require(file_sha(ROOT / name) == wanted, 'UNCHANGED_ORIGINAL_TOOL_BEFORE_IMPORT:' + name)
    sys.path[:0] = [str(FIRST), str(ISO)]
    modules = {}
    for name, path in (('inventory', ISO / 'inventory.py'), ('release_gate', ISO / 'release_gate.py'),
                       ('module_bundle', FIRST / 'module_bundle.py'), ('component_bundles', ISO / 'component_bundles.py')):
        if name in sys.modules:
            require(Path(sys.modules[name].__file__).resolve() == path.resolve(), 'ORIGINAL_IMPORT_ORIGIN:' + name)
        modules[name] = importlib.import_module(name)
    inventory, components = modules['inventory'], modules['component_bundles']
    return SimpleNamespace(**modules, pins=pins, canonical=inventory.canonical, SIGNATURE=inventory.SIGNATURE,
                           validate_names=inventory.validate_names, read_bundle=components.read_bundle,
                           record=components.record, combine=components.combine, set_version=components.set_version,
                           normalize_manifest=modules['release_gate'].normalize_manifest,
                           component_digest=modules['release_gate'].component_digest)


def verify_signature(modules):
    load_tools()
    manifest = modules / CC / MANIFEST
    subprocess.run(['openssl', 'dgst', '-sha256', '-verify', str(FIRST / 'ORIGINAL-INFINITY-PUBLIC-KEY.pem'),
                    '-signature', str(manifest) + '.sig', str(manifest)], check=True, capture_output=True)


def admission(path):
    a = load(path)
    expected = dict(status='CONFIRMED_UNUSED_FORWARD_PAIR', authority_source=BASE_SOURCE, generation=56,
                    latest_signed_versionCode=2103469, candidate_versionCode=2103474, recovery_versionCode=2103475,
                    candidate_CC='0.3.5.72', recovery_CC='0.3.5.73', reserved=False,
                    APK_build=False, version_issued=False, publication=False)
    require(all(type(a.get(k)) is type(v) and a[k] == v for k, v in expected.items()), 'ROOT_CONFIRMED_UNUSED_FORWARD_PAIR_REQUIRED')
    return [(a['candidate_versionCode'], a['candidate_CC']), (a['recovery_versionCode'], a['recovery_CC'])]


def source_inputs():
    for name in HOST_EVIDENCE:
        path = HERE / name
        require(path.read_bytes() == git('show', ORIGINAL_REVIEWED + ':' + path.relative_to(ROOT).as_posix()),
                'UNCHANGED_ORIGINAL40_SOURCE_EVIDENCE:' + name)
    for name in CURRENT_EVIDENCE:
        path = HERE / name
        require(path.read_bytes() == git('show', BRIDGE_SOURCE + ':' + path.relative_to(ROOT).as_posix()),
                'EXACT_REVIEWED_BRIDGE_EVIDENCE:' + name)
    original = load(HERE / 'INTEGRATION-SOURCE-PROOF.json')
    proof = load(HERE / 'CURRENT-SOURCE-PROOF.json')
    require(original['protected_APK_SHA256'] == BASE_APK and set(original['files']) == PYTHON and
            proof['original40_receipts_preserved'] is True and
            proof['original_integration_proof_sha256'] == file_sha(HERE / 'INTEGRATION-SOURCE-PROOF.json') and
            set(proof['current3source_sha256']) == PYTHON, 'EXACT_THREE_SOURCE_PRESERVATION_PROOF')
    bridge_map = proof['current3source_sha256']
    for name, wanted in bridge_map.items():
        path = (HERE / 'overlay' / CC / name).relative_to(ROOT).as_posix()
        require(digest(git('show', BRIDGE_SOURCE + ':' + path)) == wanted, 'EXACT_E410_BRIDGE_SOURCE:' + name)
    host = load(HERE / CURRENT_EVIDENCE[1])
    review = load(HERE / CURRENT_EVIDENCE[2])
    require(host['status'] == 'PASS_FOCUSED_HOST_UNNUMBERED_EPISODE_LIST_BRIDGE' and host['tests_passed'] == 14 and
            file_sha(HERE / CURRENT_EVIDENCE[1]) == proof['new_host_cases']['receipt'] == review['host_receipt_sha256'] and
            file_sha(HERE / CURRENT_EVIDENCE[2]) == proof['independent_review'] and
            review['status'] == 'ACCEPTED_INDEPENDENT_BOUNDED_BRIDGE_SOURCE_REVIEW_ONLY' and
            review['source_sha256'] == bridge_map and review['host_tests'] == 14, 'SOURCE_BOUND14_HOST_AND_ASTRA_REVIEW')
    require(SOURCE_FREEZE.is_file(), 'SERVICE_SURVIVAL_SOURCE_FREEZE_REQUIRED')
    candidate = load(SOURCE_FREEZE)
    source = candidate.get('production_source')
    require(isinstance(source, str) and re.fullmatch('[0-9a-f]{40}', source) and
            source != BRIDGE_SOURCE and candidate['bridge_checkpoint'] == BRIDGE_SOURCE,
            'EXACT_SUCCESSOR_SOURCE_CHECKPOINT_REQUIRED')
    actual = {name: file_sha(HERE / 'overlay' / CC / name) for name in PYTHON}
    require(actual == candidate['new3source_sha256'] and
            {n for n in PYTHON if actual[n] != bridge_map[n]} == {'service.py'},
            'FROZEN_SERVICE_ONLY_CORRECTION_OF_E410_REQUIRED')
    for name, wanted in actual.items():
        path = (HERE / 'overlay' / CC / name).relative_to(ROOT).as_posix()
        require(digest(git('show', source + ':' + path)) == wanted, 'EXACT_SUCCESSOR_SOURCE:' + name)
    for kind in ('host_receipt', 'independent_review', 'delta_proof'):
        row = candidate[kind]
        path = Path(row['path'])
        require(not path.is_absolute() and '..' not in path.parts and (ROOT / path).parent == HERE and
                re.fullmatch('[0-9a-f]{64}', row['sha256']), 'TASK_SCOPED_FROZEN_CORRECTION_RECEIPT:' + kind)
        require(file_sha(ROOT / path) == row['sha256'] and
                (ROOT / path).read_bytes() == git('show', source + ':' + path.as_posix()),
                'EXACT_SOURCE_BOUND_CORRECTION_RECEIPT:' + kind)
    host = load(ROOT / candidate['host_receipt']['path'])
    review = load(ROOT / candidate['independent_review']['path'])
    delta = load(ROOT / candidate['delta_proof']['path'])
    require(host['status'] == 'PASS_NEW_FOCUSED_SERVICE_LOADING_AND_NATIVE_HISTORY_GUARDS' and host['tests'] == 9 and
            review['status'] == 'ACCEPTED_NARROW_SERVICE_LOADING_SURVIVAL_AND_TEST_HISTORY_SOURCE_ONLY' and
            review['concrete_blockers'] == [] and delta['only_service_changed'] is True and
            delta['new3source_sha256'] == actual and
            review['source_sha256']['overlay/script.infinity.commandcenter/service.py'] == actual['service.py'],
            'EXACT_NINE_CASE_SERVICE_CORRECTION_AND_REVIEW')
    # Only these explicit files are copied. Host __pycache__ files never enter.
    return candidate, actual


def baseline(apk, prepared, modules):
    t = load_tools()
    require(file_sha(apk) == BASE_APK, 'ONLY_EXACT_ORIGINAL_SIGNED69_BASE')
    authority = json.loads(git('show', BASE_SOURCE + ':' + AUTHORITY))
    proof = load(prepared / 'PREPARATION.json')
    require(proof['versionCode'] == 2103469 and proof['source'] == PREPARED_SOURCE and proof['run_id'] == 42512905724 and
            proof['native_sha256'] == BASE_NATIVE and proof['CC'] == '0.3.5.67' and proof['Trakt'] == '1.2.8.1', 'OFFICIAL_PREPARED69_GENERATION')
    require(file_sha(prepared / 'PREPARATION.json') == authority['owner_update_evidence']['preparation_sha256'], 'CANONICAL69_PREPARATION_HASH')
    catalog = load(prepared / 'components/catalog.json')
    require(catalog == authority['bundle_catalog'], 'EXACT_CANONICAL69_WHOLE_COMPONENT_CATALOG')
    metas = {o: t.read_bundle(prepared / 'components' / row['file'], row) for o, row in catalog['bundles'].items()}
    modules.mkdir(parents=True)
    with ZipFile(apk) as z:
        names = set(t.validate_names(z)) - t.SIGNATURE
        members = {n for meta in metas.values() for n in meta['members']}
        dex = [(o, n) for o in ('CHOOSER_SHELL', 'MINIMAL_ANDROID_CONTRACT', 'INFINITY', 'COBRA') for n in sorted(metas[o]['dex'])]
        dex_names = {'classes' + (str(i) if i > 1 else '') + '.dex' for i in range(1, len(dex) + 1)}
        require(names == members | dex_names, 'EXACT_COMPLETE69_APK_MEMBER_VECTOR')
        for owner, meta in metas.items():
            with ZipFile(prepared / 'components' / catalog['bundles'][owner]['file']) as bundle:
                for name in meta['members']:
                    raw = bundle.read('payload/' + name)
                    require(z.read(name) == (t.set_version(raw, 2103469) if name == 'AndroidManifest.xml' else raw), 'PREPARED69_APK_MEMBER:' + name)
        for i, (owner, name) in enumerate(dex, 1):
            require(digest(z.read('classes' + (str(i) if i > 1 else '') + '.dex')) == metas[owner]['dex'][name], 'EXACT69_DEX_BYTES')
        require(digest(z.read(NATIVE)) == BASE_NATIVE, 'UNCHANGED_NATIVE466_69')
        for name in names:
            if any(name.startswith('assets/addons/' + aid + '/') for aid in t.module_bundle.IDS):
                target = modules / name.removeprefix('assets/addons/')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(z.read(name))
    payload, files = t.module_bundle.build(modules)
    require(len(files) == 80 and digest(payload) == BASE_MANIFEST_SHA and payload == (modules / CC / MANIFEST).read_bytes(), 'EXACT_COMPLETE80_SIGNED69_BASELINE')
    verify_signature(modules)
    require((modules / CC / 'INSTALL-BASELINE.v1').read_bytes() == t.module_bundle.baseline_inventory(), 'UNCHANGED_ORIGINAL_INSTALL_PREIMAGES')
    return catalog


def recovery_service():
    """Original69 service bytes plus the exact already-reviewed C1 guard only."""
    freeze, _ = source_inputs()
    reference = HERE / 'reference' / CC / 'service.py'
    raw = reference.read_bytes()
    require(raw == git('show', BRIDGE_SOURCE + ':' + reference.relative_to(ROOT).as_posix()), 'UNCHANGED_PROTECTED69_SERVICE_REFERENCE')
    candidate_path = (HERE / 'overlay' / CC / 'service.py').relative_to(ROOT).as_posix()
    candidate = git('show', freeze['production_source'] + ':' + candidate_path).decode()
    helpers = [n for n in ast.parse(candidate).body if isinstance(n, ast.FunctionDef) and n.name == '_tick_loading_observer']
    require(len(helpers) == 1, 'EXACT_C1_LOADING_SURVIVAL_HELPER_REQUIRED')
    helper = '\n'.join(candidate.splitlines()[helpers[0].lineno - 1:helpers[0].end_lineno]) + '\n\n'
    changes = (
        ('    from action_loading import make_monitor\n    loading = make_monitor(xbmc, xbmcgui)',
         '    import action_loading as loading_owner\n    loading = loading_owner.make_monitor(xbmc, xbmcgui)'),
        ('            loading.tick(foreground=False)', '            _tick_loading_observer(loading, loading_owner, foreground=False)'),
        ('        loading.tick()', '        _tick_loading_observer(loading, loading_owner)'),
    )
    original, result = raw.decode(), raw.decode()
    for before, after in changes:
        require(result.count(before) == 1 and candidate.count(after) == 1, 'EXACT_ORIGINAL69_AND_C1_LOADING_CALL_SITES')
        result = result.replace(before, after, 1)
    require(result.count('def main():') == 1 and 'def _tick_loading_observer(' not in result, 'EXACT_RECOVERY_HELPER_INSERTION_POINT')
    result = result.replace('def main():', helper + 'def main():', 1)
    # Round-trip bytes prove every original69 byte outside these selected edits
    # is retained, including all tracking and playback functions/main nodes.
    restored = result.replace(helper, '', 1)
    for before, after in reversed(changes):
        restored = restored.replace(after, before, 1)
    require(restored == original, 'ALL_UNDECLARED_ORIGINAL69_RECOVERY_BYTES_IDENTICAL')
    recovered_helper = next(n for n in ast.parse(result).body if isinstance(n, ast.FunctionDef) and n.name == '_tick_loading_observer')
    require(ast.dump(recovered_helper, include_attributes=False) == ast.dump(helpers[0], include_attributes=False), 'EXACT_C1_HELPER_AST_IN_RECOVERY')
    return result.encode()


def recovery_source(name):
    require(name in PYTHON, 'EXACT_THREE_RECOVERY_SOURCE_NAMES')
    if name == 'service.py':
        return recovery_service()
    path = HERE / 'reference' / CC / name
    require(path.read_bytes() == git('show', BRIDGE_SOURCE + ':' + path.relative_to(ROOT).as_posix()), 'UNCHANGED_PROTECTED69_RECOVERY_REFERENCE')
    return path.read_bytes()


def allowed_members(recovery):
    metadata = {PREFIX + n for n in ('addon.xml', MANIFEST, MANIFEST + '.sig')} | {LABEL, 'AndroidManifest.xml'}
    return metadata | {PREFIX + 'service.py'} if recovery else metadata | {PREFIX + n for n in PYTHON}


def validate_member_change(name, before, after, declared, version, recovery):
    require(name in allowed_members(recovery) and name in declared and digest(after) == declared[name], 'UNDECLARED_MEMBER_CHANGE:' + name)
    if name == 'AndroidManifest.xml':
        t = load_tools()
        require(t.normalize_manifest(after) == (t.normalize_manifest(before)[0], version), 'TYPED_ANDROID_VERSION_ONLY')


def compare(apk, candidate, preparation, out=None):
    t = load_tools()
    require(file_sha(apk) == BASE_APK, 'EXACT_SIGNED69_COMPARISON_BASE')
    proof = load(preparation)
    require(proof['baseline_sha256'] == BASE_APK and proof['versionCode'] in (2103474, 2103475) and
            proof['recovery'] is (proof['versionCode'] == 2103475) and not proof['added_members'], 'EXACT_FORWARD_PAIR_COMPARE_METADATA')
    differences = {}
    with ZipFile(apk) as a, ZipFile(candidate) as b:
        names = set(t.validate_names(a)) - t.SIGNATURE
        require(set(t.validate_names(b)) - t.SIGNATURE == names, 'NO_ADDED_OR_REMOVED_APK_MEMBERS')
        for name in sorted(names):
            before, after = a.read(name), b.read(name)
            if before != after:
                validate_member_change(name, before, after, proof['changed_members'], proof['versionCode'], proof['recovery'])
                differences[name] = digest(after)
    require(differences == proof['changed_members'] and set(differences) == allowed_members(proof['recovery']), 'ALL_AND_ONLY_THREE_SOURCE_OR_RECOVERY_METADATA_CHANGES')
    report = dict(status='PASS69_SCOPED_SOURCE_AND_GUARDED_RECOVERY_MEMBERS', baseline_sha256=BASE_APK,
                  APK_sha256=file_sha(candidate), changed_members=differences, public_release=False,
                  accepted_pointer_updated=False, signing='NOT_VERIFIED_BY_MEMBER_COMPARE', Android='NOT_RUN_BY_PREPARATION')
    if out:
        save(out, report)
    return report


def inputs(apk, prepared, admission_file, out):
    """Stage full unsigned module generations, without assembling an APK."""
    t = load_tools()
    pairs = admission(admission_file)
    proof, overlay = source_inputs()
    recovery_raw = recovery_source('service.py')
    recovery_proof = load(HERE / 'RECOVERY-SERVICE-PRESERVATION.json')
    recovery_review = load(HERE / 'RECOVERY-SERVICE-REVIEW.json')
    require(recovery_proof['recovery_service_sha256'] == digest(recovery_raw) and
            recovery_proof['production_source'] == proof['production_source'] and
            recovery_proof['only_reviewed_loading_guard_added'] is True and
            recovery_review['status'] == 'ACCEPTED_SOURCE_PRESERVATION_ORIGINAL69_PLUS_EXACT_REVIEWED_LOADING_GUARD_ONLY' and
            recovery_review['concrete_blockers'] == [] and
            recovery_review['recovery_service_sha256'] == digest(recovery_raw) and
            recovery_review['preservation_receipt_sha256'] == file_sha(HERE / 'RECOVERY-SERVICE-PRESERVATION.json'),
            'ROOT_REVIEWED_RECOVERY_SOURCE_PRESERVATION_REQUIRED')
    require(not out.exists(), 'FRESH_PREPARATION_DIRECTORY')
    out.mkdir(parents=True)
    baseline(apk, prepared, out / 'baseline-modules')
    before = hashes(out / 'baseline-modules')
    source = git('rev-parse', 'HEAD').decode().strip()
    for name, wanted in overlay.items():
        path = (HERE / 'overlay' / CC / name).relative_to(ROOT).as_posix()
        require(digest(git('show', source + ':' + path)) == wanted, 'EXACT_COMMITTED_TRACKING_SOURCE:' + name)
    shutil.copyfile(admission_file, out / 'VERSION-ADMISSION.json')
    metadata = {}
    for index, (version, cc_version) in enumerate(pairs):
        work = out / str(version)
        modules = work / 'modules'
        shutil.copytree(out / 'baseline-modules', modules)
        if index == 0:
            for name in sorted(PYTHON):
                shutil.copyfile(HERE / 'overlay' / CC / name, modules / CC / name)
        else:
            (modules / CC / 'service.py').write_bytes(recovery_raw)
        xml = modules / CC / 'addon.xml'
        raw = xml.read_bytes()
        require(raw.count(b'version="0.3.5.67"') == 1, 'EXACT_CC67_METADATA_PREIMAGE')
        xml.write_bytes(raw.replace(b'version="0.3.5.67"', ('version="' + cc_version + '"').encode(), 1))
        (modules / CC / (MANIFEST + '.sig')).unlink()
        payload, files = t.module_bundle.build(modules)
        require(len(files) == 80, 'COMPLETE80_SOURCE_GENERATION')
        (modules / CC / MANIFEST).write_bytes(payload)
        after = hashes(modules)
        changed = {name for name in before.keys() & after.keys() if before[name] != after[name]}
        expected = {CC + '/' + name for name in ('addon.xml', MANIFEST)}
        if index == 0:
            expected |= {CC + '/' + name for name in PYTHON}
        else:
            expected.add(CC + '/service.py')
        require(changed == expected and not (after.keys() - before.keys()) and
                before.keys() - after.keys() == {CC + '/' + MANIFEST + '.sig'}, 'ONLY_DECLARED_TRACKING_GENERATION_CHANGES')
        save(work / 'INPUTS.json', dict(versionCode=version, CC=cc_version, source=source,
             modules=after, module_manifest_sha256=digest(payload), authenticated_source_count=80,
             native_sha256=BASE_NATIVE, recovery=index == 1, helper_authenticated_inactive=True,
             recovery_service_only_loading_guard=index == 1,
             Trakt='1.2.8.1', APK_produced=False))
        metadata[str(version)] = file_sha(work / 'INPUTS.json')
    save(out / 'SOURCE-PINS.json', dict(source=source, overlay_sha256=overlay,
         original_tools=t.pins, baseline_APK_sha256=BASE_APK,
         baseline_preparation_sha256=file_sha(prepared / 'PREPARATION.json'),
         baseline_components_sha256=hashes(prepared / 'components'),
         input_metadata_sha256=metadata, version_admission_sha256=file_sha(admission_file),
         source_preservation_sha256=file_sha(SOURCE_FREEZE),
         production_source=proof['production_source'],
         correction_receipt_sha256={k: proof[k] for k in ('host_receipt', 'independent_review')},
         host_evidence_sha256={name: file_sha(HERE / name) for name in (*HOST_EVIDENCE, *CURRENT_EVIDENCE)},
         installer_selection_sha256=file_sha(HERE / 'CURRENT-INPUT-FIXTURE.json'),
         native_sha256=BASE_NATIVE, APK_produced=False, registry_mutated=False,
         signing='PENDING_EXISTING_ORIGINAL_SIGNER', Android='NOT_RUN', public_release=False))


def core_clearance(proof, source_map):
    path = HERE / 'EXPERIMENTAL-RELEASE-CLEARANCE.json'
    require(path.is_file(), 'ROOT_REVIEWED_EXPERIMENTAL_DISPOSITION_REQUIRED')
    value = load(path)
    require(value['production_source'] == proof['production_source'] and value['source_sha256'] == source_map and
            value['source_pins_sha256'] == proof['source_pins_sha256'] and value['baseline_APK_sha256'] == BASE_APK and
            value['experimental'] is True and value['publication'] is False and value['accepted_pointer_updated'] is False and
            isinstance(value['remaining_unverified'], list) and all(isinstance(v, str) and v for v in value['remaining_unverified']),
            'SOURCE_BOUND_REVIEWED_EXPERIMENTAL_DISPOSITION')
    owner_path = HERE / 'EXPERIMENTAL-RELEASE-AUTHORIZATION.json'
    owner = load(owner_path)
    require(owner['operation'] == 'prepare-owner-experimental-infinity-tracking-and-forward-recovery' and
            owner['prospective_candidate_APK'] == 2103474 and owner['prospective_recovery_APK'] == 2103475 and
            owner['signing_protection_bypasses'] is False and owner['public_release_selected'] is False and
            value['owner_authorization_sha256'] == file_sha(owner_path),
            'EXACT_OWNER_EXPERIMENTAL_AUTHORIZATION_WITHOUT_SIGNING_BYPASS')
    core = value['core_checks']
    if value['status'] == 'ROOT_REVIEWED_EXPERIMENTAL_CORE_CLEARANCE':
        require(core == {'service_survival': 'PASS', 'movie_stop_continue': 'PASS', 'tv_ui_resume': 'PASS',
                         'actual_schema2_recovery_read_save': 'PASS'}, 'ACTUAL_FOUR_CORE_CHECKS_REQUIRED')
    else:
        require(value['status'] == 'ROOT_REVIEWED_EXPERIMENTAL_RUNTIME_BLOCKED' and
                owner['runtime_blocked_experimental_authorized'] is True and bool(value['remaining_unverified']) and
                {k: core[k] for k in ('service_survival', 'movie_stop_continue', 'tv_ui_resume')} ==
                {k: 'NOT_RUN_NATIVE_CONSTRUCTOR_BLOCK' for k in ('service_survival', 'movie_stop_continue', 'tv_ui_resume')} and
                core.get('actual_schema2_recovery_read_save') == 'NOT_RUN_PENDING_ACTUAL_MOVIE_PROGRESS',
                'HONEST_OWNER_AUTHORIZED_RUNTIME_BLOCKED_DISPOSITION')
        outcome_path = HERE / 'C1-42604600259-OUTCOME-REVIEW.json'
        outcome_name = outcome_path.relative_to(ROOT).as_posix()
        require(value['evidence_source_files'].get(outcome_name) == file_sha(outcome_path), 'EXACT_NATIVE_BLOCK_OUTCOME_REVIEW')
        outcome = load(outcome_path)
        require(outcome['run'] == 42604600259 and
                outcome['status'] == 'C1_ANDROID_BLOCKED_BY_OBSERVED_NATIVE_STARTUP_CRASH_TRACKING_NOT_RUN' and
                outcome['source_preservation']['checkpoint'] == proof['production_source'] and
                outcome['source_preservation']['source_sha256'] == source_map and
                outcome['tracking_result']['C1_native_identity'] == 'NOT_REACHED' and
                outcome['tracking_result']['movie'] == outcome['tracking_result']['TV'] == 'NOT_RUN',
                'EXACT_C1_UNEXECUTED_FEATURE_AND_NATIVE_BLOCK_EVIDENCE')
        available = value.get('available_schema2_preservation')
        if available is not None:
            compat_path = HERE / 'OBSERVED-SCHEMA2-COMPATIBILITY.json'
            require(available['status'] == 'PASS_OBSERVED_TV_AND_WATCHLIST_ONLY' and
                    available['movie_progress'] == 'NOT_OBSERVED' and available['runtime'] == 'NOT_RUN' and
                    available['receipt'] == {'path': compat_path.relative_to(ROOT).as_posix(), 'sha256': file_sha(compat_path)} and
                    value['evidence_source_files'].get(compat_path.relative_to(ROOT).as_posix()) == file_sha(compat_path),
                    'EXACT_SEPARATE_OBSERVED_COMPATIBILITY_RECEIPT')
            compat = load(compat_path)
            require(compat['status'] == 'PASS_OBSERVED_TV_AND_WATCHLIST_ONLY' and compat['movie_progress'] == 'NOT_OBSERVED' and
                    compat['original69_APK_sha256'] == BASE_APK, 'NO_UNOBSERVED_MOVIE_PROGRESS_COMPATIBILITY_CLAIM')
    # Signed-APK PackageManager installation/data retention has a separate
    # post-sign owner-delivery gate. It never means boot/functional recovery.
    require(value.get('signed_APK_install_forward_recovery', 'PENDING_POST_SIGN_OWNER_DELIVERY') ==
            'PENDING_POST_SIGN_OWNER_DELIVERY' and value.get('owner_delivery_cleared', False) is False,
            'SIGNED_APK_TEST_CANNOT_BE_CLAIMED_BY_PRE_SIGN_CLEARANCE')
    evidence = value['evidence_source_files']
    require(bool(evidence), 'RETAINED_ACTUAL_EVIDENCE_REQUIRED')
    result = {path.relative_to(ROOT).as_posix(): file_sha(path), owner_path.relative_to(ROOT).as_posix(): file_sha(owner_path)}
    for name, wanted in evidence.items():
        relative = Path(name)
        require(not relative.is_absolute() and '..' not in relative.parts and
                relative.is_relative_to(HERE.relative_to(ROOT)) and file_sha(ROOT / relative) == wanted,
                'UNCHANGED_ACTUAL_EVIDENCE:' + name)
        result[name] = wanted
    return value, result


def official_module_fixture(fixture, pin_file):
    """Read the exact original signed80 artifact; never rewrite its provenance."""
    pin = load(pin_file)
    def api(path):
        return json.loads(subprocess.check_output(['gh', 'api', 'repos/mahfouzhassine8-ops/project-infinity/' + path], timeout=30))
    run = api('actions/runs/' + str(pin['run']))
    require(run['workflow_id'] == 397702717 and run['path'] == '.github/workflows/infinity-combined-release.yml' and
            run['head_sha'] == pin['source'] and run['head_branch'] == 'work/infinity-tracking-integration-20261108' and
            run['status'] == 'completed' and run['conclusion'] == 'success', 'ORIGINAL_OFFICIAL_MODULE_PRODUCER')
    row = api('actions/artifacts/' + str(pin['id']))
    require(not row['expired'] and row['workflow_run']['id'] == pin['run'] and
            all(row[k] == pin[k] for k in ('id', 'name', 'digest', 'size_in_bytes')), 'EXACT_SIGNED_MODULE_ARTIFACT')
    archive = fixture.parent / 'artifact.zip'
    require(file_sha(archive) == pin['digest'].removeprefix('sha256:') and archive.stat().st_size == pin['size_in_bytes'],
            'WHOLE_SIGNED_MODULE_ARCHIVE_DIGEST')
    t = load_tools()
    with ZipFile(archive) as zipped:
        names = {n for n in t.validate_names(zipped) if not n.endswith('/')}
        require(names == {p.relative_to(fixture).as_posix() for p in fixture.rglob('*') if p.is_file()}, 'EXACT_SIGNED_MODULE_ARCHIVE_FILES')
        for name in names:
            with zipped.open(name) as stream:
                require(hashlib.file_digest(stream, 'sha256').hexdigest() == file_sha(fixture / name), 'SIGNED_MODULE_ARCHIVE_MEMBER:' + name)
    proof = load(fixture / 'MODULE-FIXTURE.json')
    require(proof['source'] == pin['source'] and proof['run_id'] == pin['run'] and
            proof['APK_build'] is False and proof['APK_present'] is False and proof['original80_source_signatures'] is True and
            proof['source_pins_sha256'] == file_sha(fixture / 'pair/SOURCE-PINS.json') == pin['source_pins_sha256'],
            'IMMUTABLE_OFFICIAL_MODULE_SOURCE_PINS')
    return pin


def finish(apk, prepared, admission_file, fixture, module_pin, out, audit):
    """Original69 bundles + authenticated full80 -> unsigned original assembly.

    Reuses the existing Watchlist finish ownership/combine method. No native
    input, source compilation, signing, registration, or behavior clearance.
    """
    t = load_tools()
    pairs = admission(admission_file)
    source_proof, overlay = source_inputs()
    pair = fixture / 'pair'
    pins = load(pair / 'SOURCE-PINS.json')
    # This guard precedes assembly/output mutation. Module QA alone cannot admit
    # unsigned APK preparation or experimental signing.
    core_clearance(dict(production_source=source_proof['production_source'],
                        source_pins_sha256=file_sha(pair / 'SOURCE-PINS.json')), overlay)
    module_producer = official_module_fixture(fixture, module_pin)
    require(not out.exists(), 'FRESH_POST_CLEARANCE_APK_PREPARATION_OUTPUT')
    require(pins['original_tools'] == t.pins and file_sha(apk) == BASE_APK and
            file_sha(admission_file) == pins['version_admission_sha256'] and
            file_sha(prepared / 'PREPARATION.json') == pins['baseline_preparation_sha256'] and
            hashes(prepared / 'components') == pins['baseline_components_sha256'] and
            pins['overlay_sha256'] == overlay and pins['production_source'] == source_proof['production_source'] and
            pins['source_preservation_sha256'] == file_sha(SOURCE_FREEZE) and
            pins['installer_selection_sha256'] == file_sha(HERE / 'CURRENT-INPUT-FIXTURE.json'),
            'FROZEN_EXACT69_PREPARATION_AND_SUCCESSOR_SOURCE')
    result = load(audit)
    selection = tuple(load(HERE / 'CURRENT-INPUT-FIXTURE.json')['selected_installer_cases'])
    require(result['status'] == 'PASS_FOUR_REAL_JAVA_CURRENT80_GENERATION_CASES' and
            tuple(row['case'] for row in result['cases']) == selection and len(selection) == 4 and
            result['complete80_signatures_verified'] is True and result['original_installer_changed'] is False and
            result['source_pins_sha256'] == file_sha(pair / 'SOURCE-PINS.json') and
            result['verifier_sha256'] == file_sha(HERE / 'verify_tracking_modules.py') and
            result['selected_tests_sha256'] == file_sha(HERE / 'CURRENT-INPUT-FIXTURE.json'),
            'ACTUAL_NEW_GENERATION_ORIGINAL_INSTALLER_EVIDENCE')
    catalog_base = load(prepared / 'components/catalog.json')
    authority = json.loads(git('show', BASE_SOURCE + ':' + AUTHORITY))
    require(catalog_base == authority['bundle_catalog'], 'EXACT_CANONICAL69_COMPONENT_CATALOG')
    producer_source = git('rev-parse', 'HEAD').decode().strip()
    for index, (version, cc_version) in enumerate(pairs):
        work, recovery = out / str(version), index == 1
        module_work = pair / str(version)
        modules = module_work / 'modules'
        require(file_sha(module_work / 'INPUTS.json') == pins['input_metadata_sha256'][str(version)], 'FROZEN_PAIR_INPUTS')
        meta = load(module_work / 'INPUTS.json')
        now = hashes(modules)
        signature = CC + '/' + MANIFEST + '.sig'
        require({n: h for n, h in now.items() if n != signature} == meta['modules'] and signature in now and
                now == result['signed_inputs'][str(version)]['source_sha256'], 'EXACT_ACTUALLY_TESTED_SIGNED80_TREE')
        payload, files = t.module_bundle.build(modules)
        require(len(files) == 80 and digest(payload) == meta['module_manifest_sha256'] and
                payload == (modules / CC / MANIFEST).read_bytes(), 'COMPLETE_FROZEN80_MANIFEST')
        verify_signature(modules)
        changes = {LABEL: ('infinity.last_updated_in=' + str(version) + '\ncobra.last_updated_in=2103445\n').encode()}
        with ZipFile(apk) as baseline_apk:
            original = set(t.validate_names(baseline_apk))
            for path in sorted(modules.rglob('*')):
                if path.is_file():
                    name = 'assets/addons/' + path.relative_to(modules).as_posix()
                    require(name in original, 'NO_NEW_APK_SOURCE_MEMBERS')
                    raw = path.read_bytes()
                    if raw != baseline_apk.read(name):
                        changes[name] = raw
        require(set(changes) == allowed_members(recovery) - {'AndroidManifest.xml'}, 'ONLY_DECLARED69_SOURCE_AND_VERSION_METADATA')
        dest = work / 'publish/components'
        dest.mkdir(parents=True, exist_ok=False)
        catalog = copy.deepcopy(catalog_base)
        catalog['source'] = producer_source
        for owner, row in catalog_base['bundles'].items():
            original_bundle = prepared / 'components' / row['file']
            component = t.read_bundle(original_bundle, row)
            if owner not in ('INFINITY', 'CHOOSER_SHELL'):
                shutil.copyfile(original_bundle, dest / row['file'])
                continue
            selected = {n: raw for n, raw in changes.items() if (n == LABEL) == (owner == 'CHOOSER_SHELL')}
            require(set(selected) <= set(component['members']), 'UNCHANGED_OWNER_MEMBER_VECTOR')
            component.update(version=str(version) + '.' + owner.lower() + '.1', approved_source=producer_source)
            for name, raw in selected.items():
                component['members'][name]['sha256'] = digest(raw)
                component['payload']['member:' + name] = dict(owner=owner, sha256=digest(raw))
            component['digest'] = t.component_digest(component['payload'], owner)
            target = dest / row['file']
            with ZipFile(original_bundle) as old, ZipFile(target, 'w') as new:
                for name in old.namelist():
                    if name != 'component.json':
                        new.writestr(t.record(name), selected.get(name.removeprefix('payload/'), old.read(name)))
                new.writestr(t.record('component.json'), t.canonical(component))
            catalog['bundles'][owner] = dict(file=target.name, sha256=file_sha(target),
                **{k: component[k] for k in ('version', 'digest', 'approved_source', 'settings_schema')})
            t.read_bundle(target, catalog['bundles'][owner])
        save(dest / 'catalog.json', catalog)
        unsigned = work / 'combined-unsigned.apk'
        t.combine(dest, catalog, unsigned, version)
        with ZipFile(unsigned) as built:
            changed = {name: digest(raw) for name, raw in changes.items()}
            changed['AndroidManifest.xml'] = digest(built.read('AndroidManifest.xml'))
        proof_path = work / 'publish/PREPARATION.json'
        save(proof_path, dict(status='PREPARED_UNSIGNED_69_TRACKING_EXPERIMENTAL_PAIR',
            versionCode=version, CC=cc_version, Trakt='1.2.8.1', source=producer_source,
            production_source=source_proof['production_source'], run_id=int(os.environ.get('GITHUB_RUN_ID', '0')),
            baseline_sha256=BASE_APK, unsigned_sha256=file_sha(unsigned), native_sha256=BASE_NATIVE,
            changed_members=changed, added_members=[], module_source_count=80, module_manifest_sha256=digest(payload),
            source_pins_sha256=file_sha(pair / 'SOURCE-PINS.json'), module_audit_sha256=file_sha(audit),
            module_producer_source=pins['source'], signed_module_artifact=module_producer,
            recovery=recovery, recovery_functional_base=2103469, recovery_service_only_loading_guard=recovery,
            Cobra_bundle_byte_identical=True, minimal_contract_bundle_byte_identical=True, all_DEX_byte_identical=True,
            skin_Trakt_providers_byte_identical=True, inactive_helper_unchanged=True, INSTALL_baseline_unchanged=True,
            registry_mutated=False, APK_signing='NOT_RUN', Android='NOT_RUN_BY_PREPARATION',
            signed_APK_install_forward_recovery='PENDING_POST_SIGN_OWNER_DELIVERY', owner_delivery_cleared=False,
            Fold='NOT_RUN', public_release=False, publication=False, accepted_pointer_updated=False))
        compare(apk, unsigned, proof_path, work / 'publish/APK-PRESERVATION.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='operation', required=True)
    p = commands.add_parser('inputs')
    for name in ('apk', 'prepared', 'admission-file', 'out'):
        p.add_argument('--' + name, type=Path, required=True)
    p = commands.add_parser('compare')
    for name in ('apk', 'candidate', 'preparation', 'out'):
        p.add_argument('--' + name, type=Path, required=True)
    p = commands.add_parser('finish')
    for name in ('apk', 'prepared', 'admission-file', 'fixture', 'module-pin', 'out', 'audit'):
        p.add_argument('--' + name, type=Path, required=True)
    args = vars(parser.parse_args())
    globals()[args.pop('operation')](**args)
