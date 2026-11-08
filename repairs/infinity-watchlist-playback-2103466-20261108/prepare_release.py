"""Prepare unsigned Watchlist successor/recovery inputs with the original tools.

No credentials, signing, registry mutation, application execution or acceptance.
`inputs` emits full unsigned module manifests for the existing owner workflow;
`finish` accepts their original-key detached signatures and assembles unsigned
APKs through the unchanged component_bundles.combine implementation.
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
import tempfile
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

BASE = '5ee1c7ae0bbe295c311aa34c02f6b62688ccb5a7'
BASE_APK = 'd366e4b8aadba8484768cfcc0d362c2fc8e0181d78123ea77e04af4f028a3135'
BASE_NATIVE = 'ee3be7c7a95b86f8357539001fcd50bedbd80217b02f130d649f7f57e6075794'
BASE_NATIVE_MAP = 'f48df24caabdf36fee25d69d47b0a2ad3c98df3936949c8dcd6d07a92e2f0412'
PRODUCER = 'ec4d011e1dfd0bec7949e8b442dbde5ee42deabf'
AUTHORITY_SOURCE = '2aa41804821264581fe69e0fb1d10703e6583baf'
CC = module_bundle.CC
NATIVE = 'lib/arm64-v8a/libkodi.so'
LABEL = 'assets/experience-component-updates.properties'
PYTHON = {'service.py', 'resume_hub.py', 'plugin.py'}
HELPER = 'saved_playback.py'
NATIVE_SOURCES = {'xbmc/guilib/InfinitySavedNavigation.h', 'xbmc/guilib/InfinitySavedNavigationState.h',
                  'xbmc/filesystem/PluginDirectory.cpp', 'xbmc/interfaces/json-rpc/PlayerOperations.cpp',
                  'xbmc/interfaces/generic/ScriptInvocationManager.cpp', 'xbmc/interfaces/legacy/Player.cpp'}
TOOLS = [FIRST / n for n in ('module_bundle.py', 'FIRSTPARTY-COMPOSITION-PLAN.json',
         'SignInfinityModules.java', 'ORIGINAL-INFINITY-PUBLIC-KEY.pem', 'InfinityInstalledModules.java.in')]
TOOLS += [ISO / n for n in ('component_bundles.py', 'assemble_modules.py', 'release_gate.py', 'inventory.py')]


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *map(str, args)])


def hashes(root):
    return {p.relative_to(root).as_posix(): file_sha(p) for p in root.rglob('*') if p.is_file()}


def tool_pins():
    pins = {}
    for p in TOOLS:
        name = p.relative_to(ROOT).as_posix()
        require(p.read_bytes() == git('show', BASE + ':' + name), 'UNCHANGED_ORIGINAL_TOOL:' + name)
        pins[name] = file_sha(p)
    return pins


def verify_signature(modules):
    controller = modules / CC
    subprocess.run(['openssl', 'dgst', '-sha256', '-verify', str(FIRST / 'ORIGINAL-INFINITY-PUBLIC-KEY.pem'),
                    '-signature', str(controller / (module_bundle.MANIFEST + '.sig')),
                    str(controller / module_bundle.MANIFEST)], check=True, capture_output=True)


def extract(apk, modules):
    modules.mkdir(parents=True)
    with ZipFile(apk) as z:
        for name in validate_names(z):
            if not name.endswith('/') and any(name.startswith('assets/addons/' + aid + '/') for aid in module_bundle.IDS):
                target = modules / name.removeprefix('assets/addons/')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(z.read(name))


def baseline(apk, prepared, modules):
    require(file_sha(apk) == BASE_APK, 'ONLY_ORIGINAL_SIGNED466_INPUT')
    proof = load(prepared / 'PREPARATION.json')
    require(proof['versionCode'] == 2103466 and proof['source'] == PRODUCER and proof['run_id'] == 42460784588,
            'OFFICIAL466_PREPARED_PROVENANCE')
    require(proof['CC'] == '0.3.5.64' and proof['Trakt'] == '1.2.8.1' and proof['native_sha256'] == BASE_NATIVE,
            'EXACT466_COMPONENT_GENERATION')
    catalog = load(prepared / 'components/catalog.json')
    metas = {o: read_bundle(prepared / 'components' / r['file'], r) for o, r in catalog['bundles'].items()}
    with ZipFile(apk) as z:
        names = set(validate_names(z)) - SIGNATURE
        bundled = {n for m in metas.values() for n in m['members']}
        require(names - bundled == {n for n in names if re.fullmatch(r'classes\d*\.dex', n)}, 'COMPLETE_BASELINE_MEMBER_CATALOG')
        for meta in metas.values():
            for name, row in meta['members'].items():
                raw = z.read(name)
                if name == 'AndroidManifest.xml':
                    with ZipFile(prepared / 'components' / catalog['bundles'][meta['owner']]['file']) as bundle:
                        require(normalize_manifest(raw)[0] == normalize_manifest(bundle.read('payload/' + name))[0], 'BASELINE_TYPED_ANDROID_METADATA_ONLY')
                else:
                    require(digest(raw) == row['sha256'], 'BASELINE_BUNDLE_APK_MEMBER:' + name)
        require(digest(z.read(NATIVE)) == BASE_NATIVE, 'EXACT466_RECOVERY_ENGINE')
        require(normalize_manifest(z.read('AndroidManifest.xml'))[1] == 2103466, 'EXACT466_ANDROID_VERSION')
        require(b'version="1.2.8.1"' in z.read('assets/addons/script.module.tmdbhelper.sync.trakt/addon.xml'), 'TRAKT_AS_IS')
        dex_order = ('CHOOSER_SHELL', 'MINIMAL_ANDROID_CONTRACT', 'INFINITY', 'COBRA')
        dex = [(o, n) for o in dex_order for n in sorted(metas[o]['dex'])]
        for i, (owner, name) in enumerate(dex, 1):
            apk_name = 'classes' + (str(i) if i > 1 else '') + '.dex'
            require(digest(z.read(apk_name)) == metas[owner]['dex'][name], 'EXACT_BASELINE_DEX:' + apk_name)
    extract(apk, modules)
    payload, files = module_bundle.build(modules)
    require(len(files) == 79 and payload == (modules / CC / module_bundle.MANIFEST).read_bytes(), 'COMPLETE_AUTHENTICATED79_BASELINE')
    verify_signature(modules)
    install = (modules / CC / 'INSTALL-BASELINE.v1').read_bytes()
    require(install == module_bundle.baseline_inventory(), 'RETAIN_ORIGINAL_INSTALL_BASELINE_PREIMAGES')
    return catalog, dict(status='PASS_READ_ONLY_SIGNED466_MODULE_AND_BUNDLE_INVENTORY', baseline_APK_sha256=BASE_APK,
        prepared_producer=PRODUCER, prepared_artifact=13609546660, prepared_run=42460784588,
        module_manifest_sha256=digest(payload), authenticated_source_count=79,
        install_baseline_sha256=digest(install), install_baseline_preimages=install.decode('ascii').splitlines()[2:],
        baseline_native_sha256=BASE_NATIVE, original_tool_sha256=tool_pins(), application_tests=False, signing=False)


def admission(path):
    a = load(path)
    require(a['status'] == 'CONFIRMED_UNUSED_FORWARD_PAIR' and a['authority_source'] == AUTHORITY_SOURCE and
            a['generation'] == 54 and a['latest_signed_versionCode'] == 2103467 and a['reserved'] is False,
            'ROOT_CONFIRMED_LIVE_VERSION_REGISTRY_REQUIRED')
    require(a['candidate_versionCode'] == 2103468 and a['recovery_versionCode'] == 2103469 and
            a['candidate_CC'] == '0.3.5.66' and a['recovery_CC'] == '0.3.5.67', 'EXACT_CONFIRMED_FORWARD_PAIR')
    return [(a['candidate_versionCode'], a['candidate_CC']), (a['recovery_versionCode'], a['recovery_CC'])]


def native_admission(native):
    p = load(native / 'ARM64-LINK-VERIFIED.json')
    require(p['status'] == 'PASS_REAL_FOUR_ARM64_OBJECTS_FULL_NATIVE_LINK_UNCHANGED_ABI' and
            p['native_sha256'] == file_sha(native / 'libkodi.so') and set(p['changed_native_sources']) == NATIVE_SOURCES,
            'EXACT_PASSING_WATCHLIST_ARM64_LINK')
    current = {n: file_sha(HERE / 'native' / n) for n in NATIVE_SOURCES}
    source = p['source_commit']
    require(re.fullmatch('[0-9a-f]{40}', source) is not None, 'NATIVE_SOURCE_COMMIT')
    for name, sha in current.items():
        path = (HERE / 'native' / name).relative_to(ROOT).as_posix()
        require(digest(git('show', source + ':' + path)) == sha, 'COMPILED_NATIVE_SOURCE_PIN:' + name)
    base_map_path = HERE / 'contract-evidence/BASE466-NATIVE-SOURCE-MAP.json'
    require(file_sha(base_map_path) == BASE_NATIVE_MAP, 'IMMUTABLE_SIGNED466_FULL_NATIVE_SOURCE_MAP')
    base_map = load(base_map_path)
    new_map = load(native / 'NATIVE-SOURCE-MAP.json')
    require(len(base_map) == 9411 and set(new_map) == set(base_map) and {n for n in base_map if base_map[n] != new_map[n]} == NATIVE_SOURCES,
            'EXACT_SIX_SOURCE_NATIVE_PRESERVATION')
    require(all(new_map[n] == sha for n, sha in current.items()), 'FULL_LINKED_SOURCE_MAP_MATCH')
    return p, current


def inventory(apk, prepared, out, **unused):
    require(not out.exists(), 'FRESH_INVENTORY_REPORT')
    with tempfile.TemporaryDirectory() as tmp:
        _, report = baseline(apk, prepared, Path(tmp) / 'modules')
    save(out, report)


def inputs(apk, prepared, native_artifact, admission_file, out, **unused):
    pairs = admission(admission_file)
    native_proof, native_sources = native_admission(native_artifact)
    runtime_pins = load(HERE / 'RUNTIME-SOURCE-PINS.json')
    overlay = HERE / 'overlay' / CC
    require(set(hashes(overlay)) in (PYTHON, PYTHON | {HELPER}), 'ONLY_THREE_CC_FILES_AND_ONE_HELPER')
    require(runtime_pins['native'] == native_sources and runtime_pins['python'] == hashes(overlay), 'FROZEN_COMPLETE_NATIVE_AND_PYTHON_PINS')
    require(not out.exists(), 'FRESH_PREPARATION_DIRECTORY')
    out.mkdir(parents=True)
    _, report = baseline(apk, prepared, out / 'baseline-modules')
    save(out / 'BASELINE-INVENTORY.json', report)
    shutil.copyfile(admission_file, out / 'VERSION-ADMISSION.json')
    before = hashes(out / 'baseline-modules')
    helper = (overlay / HELPER).is_file()
    source = git('rev-parse', 'HEAD').decode().strip()
    for name, sha in hashes(overlay).items():
        path = (overlay / name).relative_to(ROOT).as_posix()
        require(digest(git('show', source + ':' + path)) == sha, 'COMMITTED_FROZEN_PYTHON_SOURCE:' + name)
    input_pins = {}
    for index, (version, cc_version) in enumerate(pairs):
        work = out / str(version)
        modules = work / 'modules'
        shutil.copytree(out / 'baseline-modules', modules)
        controller = modules / CC
        if index == 0:
            for name in PYTHON:
                shutil.copyfile(overlay / name, controller / name)
        if helper:
            shutil.copyfile(overlay / HELPER, controller / HELPER)
        xml = controller / 'addon.xml'
        raw = xml.read_bytes()
        require(raw.count(b'version="0.3.5.64"') == 1, 'CC_ROOT_VERSION_ONLY')
        xml.write_bytes(raw.replace(b'version="0.3.5.64"', ('version="' + cc_version + '"').encode(), 1))
        payload, files = module_bundle.build(modules)
        require(len(files) == 79 + int(helper), 'COMPLETE79_OR80_AUTHENTICATED_SOURCES')
        (controller / module_bundle.MANIFEST).write_bytes(payload)
        (controller / (module_bundle.MANIFEST + '.sig')).unlink()
        after = hashes(modules)
        allowed = {CC + '/' + n for n in PYTHON | {'addon.xml', module_bundle.MANIFEST}}
        require(set(after) - set(before) == ({CC + '/' + HELPER} if helper else set()), 'ONE_NEW_HELPER_ONLY')
        require(set(before) - set(after) == {CC + '/' + module_bundle.MANIFEST + '.sig'}, 'ONLY_OLD_SIGNATURE_REMOVED')
        require({n for n in after.keys() & before.keys() if after[n] != before[n]} <= allowed, 'CC_SCOPE_ONLY')
        if index == 1:
            require(all(after[CC + '/' + n] == before[CC + '/' + n] for n in PYTHON), 'RECOVERY_EXACT466_FUNCTIONAL_PYTHON')
        save(work / 'INPUTS.json', dict(versionCode=version, CC=cc_version, Trakt='1.2.8.1', source=source,
            modules=after, module_manifest_sha256=digest(payload), authenticated_source_count=len(files),
            native_sha256=native_proof['native_sha256'] if index == 0 else BASE_NATIVE,
            native_source_sha256=native_sources if index == 0 else {}, recovery=index == 1,
            helper_authenticated_inactive=index == 1 and helper))
        input_pins[str(version)] = file_sha(work / 'INPUTS.json')
    save(out / 'SOURCE-PINS.json', dict(source=source, overlay_sha256=hashes(overlay), native_source_sha256=native_sources,
        native_artifact_sha256=file_sha(native_artifact / 'libkodi.so'), native_proof_sha256=file_sha(native_artifact / 'ARM64-LINK-VERIFIED.json'),
        original_tools=tool_pins(), baseline_APK_sha256=BASE_APK, baseline_preparation_sha256=file_sha(prepared / 'PREPARATION.json'),
        baseline_components_sha256=hashes(prepared / 'components'), input_metadata_sha256=input_pins,
        version_admission_sha256=file_sha(admission_file), module_signing='PENDING_EXISTING_OWNER_WORKFLOW', registry_mutated=False,
        runtime_source_pins_sha256=file_sha(HERE / 'RUNTIME-SOURCE-PINS.json'),
        reused_host_projection_evidence_sha256=file_sha(HERE / 'HOST-PROJECTION-RESULT.json'), APK=False, Android='NOT_RUN', Fold='NOT_RUN'))


def compare(apk, candidate, preparation, out=None):
    require(file_sha(apk) == BASE_APK, 'EXACT_SIGNED466_COMPARISON_PARENT')
    proof = load(preparation)
    differences = {}
    with ZipFile(apk) as a, ZipFile(candidate) as b:
        old = set(validate_names(a)) - SIGNATURE
        names = set(validate_names(b)) - SIGNATURE
        require(names == old | set(proof['added_members']), 'EXACT_DECLARED_APK_MEMBER_SET')
        for name in sorted(names):
            before, after = a.read(name) if name in old else None, b.read(name)
            if before == after:
                continue
            require(name in proof['changed_members'] and digest(after) == proof['changed_members'][name], 'UNAPPROVED_MEMBER:' + name)
            if name == 'AndroidManifest.xml':
                require(normalize_manifest(after) == (normalize_manifest(before)[0], proof['versionCode']), 'TYPED_ANDROID_VERSION_ONLY')
            differences[name] = digest(after)
    require(differences == proof['changed_members'], 'EXACT_FROZEN_MEMBER_CHANGES')
    result = dict(status='PASS_EXACT466_DECLARED_NATIVE_CC_METADATA_MEMBERS', baseline_sha256=BASE_APK,
                  APK_sha256=file_sha(candidate), changed_members=differences, signing='NOT_VERIFIED_BY_COMPARE', Android='NOT_RUN', Fold='NOT_RUN')
    if out:
        save(out, result)
    return result


def finish(apk, prepared, native_artifact, admission_file, out, **unused):
    pairs = admission(admission_file)
    pins = load(out / 'SOURCE-PINS.json')
    require(tool_pins() == pins['original_tools'] and file_sha(apk) == BASE_APK and
            file_sha(admission_file) == pins['version_admission_sha256'] and
            file_sha(prepared / 'PREPARATION.json') == pins['baseline_preparation_sha256'] and
            hashes(prepared / 'components') == pins['baseline_components_sha256'], 'FROZEN_INPUT_PROVENANCE')
    require(hashes(HERE / 'overlay' / CC) == pins['overlay_sha256'], 'FROZEN_CC_SOURCES')
    require(file_sha(HERE / 'RUNTIME-SOURCE-PINS.json') == pins['runtime_source_pins_sha256'], 'FROZEN_RUNTIME_PINS')
    native_proof, native_sources = native_admission(native_artifact)
    require(native_sources == pins['native_source_sha256'] and native_proof['native_sha256'] == pins['native_artifact_sha256'] and
            file_sha(native_artifact / 'ARM64-LINK-VERIFIED.json') == pins['native_proof_sha256'], 'FROZEN_COMPILED_NATIVE')
    base = load(prepared / 'components/catalog.json')
    for index, (version, cc_version) in enumerate(pairs):
        work = out / str(version)
        modules = work / 'modules'
        require(file_sha(work / 'INPUTS.json') == pins['input_metadata_sha256'][str(version)], 'FROZEN_PAIR_METADATA')
        pin = load(work / 'INPUTS.json')
        now = hashes(modules)
        sig = CC + '/' + module_bundle.MANIFEST + '.sig'
        require({n: h for n, h in now.items() if n != sig} == pin['modules'] and sig in now, 'ONLY_ORIGINAL_SIGNATURE_ADDED')
        payload, files = module_bundle.build(modules)
        require(digest(payload) == pin['module_manifest_sha256'] and payload == (modules / CC / module_bundle.MANIFEST).read_bytes(), 'COMPLETE_FROZEN_MODULE_MANIFEST')
        verify_signature(modules)
        changes = {LABEL: ('infinity.last_updated_in=' + str(version) + '\ncobra.last_updated_in=2103445\n').encode()}
        if index == 0:
            changes[NATIVE] = (native_artifact / 'libkodi.so').read_bytes()
        with ZipFile(apk) as z:
            original = set(validate_names(z))
            for p in modules.rglob('*'):
                if p.is_file():
                    name = 'assets/addons/' + p.relative_to(modules).as_posix()
                    raw = p.read_bytes()
                    if name not in original or z.read(name) != raw:
                        changes[name] = raw
        added = set(changes) - original
        require(added == ({'assets/addons/' + CC + '/' + HELPER} if CC + '/' + HELPER in pin['modules'] else set()), 'ONE_DECLARED_NEW_HELPER')
        allowed = {NATIVE, LABEL} | {'assets/addons/' + CC + '/' + n for n in PYTHON | {HELPER, 'addon.xml', module_bundle.MANIFEST, module_bundle.MANIFEST + '.sig'}}
        require(set(changes) <= allowed, 'ONLY_DECLARED_NATIVE_CC_AND_METADATA')
        dest = work / 'publish/components'
        dest.mkdir(parents=True, exist_ok=False)
        catalog = copy.deepcopy(base)
        catalog['source'] = pins['source']
        for owner, row in base['bundles'].items():
            meta = read_bundle(prepared / 'components' / row['file'], row)
            if owner not in ('INFINITY', 'CHOOSER_SHELL'):
                shutil.copyfile(prepared / 'components' / row['file'], dest / row['file'])
                continue
            selected = {n: raw for n, raw in changes.items() if (n == LABEL) == (owner == 'CHOOSER_SHELL')}
            require(set(selected) - set(meta['members']) <= added, 'ORIGINAL_OWNER_MEMBERSHIP')
            meta.update(version=str(version) + '.' + owner.lower() + '.1', approved_source=pins['source'])
            for name, raw in selected.items():
                meta['members'].setdefault(name, dict(compress_type=8, external_attr=0o100644 << 16))['sha256'] = digest(raw)
                meta['payload']['member:' + name] = dict(owner=owner, sha256=digest(raw))
            meta['digest'] = component_digest(meta['payload'], owner)
            path = dest / row['file']
            with ZipFile(prepared / 'components' / row['file']) as old, ZipFile(path, 'w') as z:
                existing = set(old.namelist())
                for name in old.namelist():
                    if name != 'component.json':
                        z.writestr(record(name), selected.get(name.removeprefix('payload/'), old.read(name)))
                for name in sorted(set(selected) - set(meta_name.removeprefix('payload/') for meta_name in existing if meta_name.startswith('payload/'))):
                    z.writestr(record('payload/' + name), selected[name])
                z.writestr(record('component.json'), canonical(meta))
            catalog['bundles'][owner] = dict(file=path.name, sha256=file_sha(path), **{k: meta[k] for k in ('version', 'digest', 'approved_source', 'settings_schema')})
            read_bundle(path, catalog['bundles'][owner])
        save(dest / 'catalog.json', catalog)
        unsigned = work / 'combined-unsigned.apk'
        combine(dest, catalog, unsigned, version)
        with ZipFile(unsigned) as z:
            changed = {name: digest(raw) for name, raw in changes.items()}
            changed['AndroidManifest.xml'] = digest(z.read('AndroidManifest.xml'))
        preparation = work / 'publish/PREPARATION.json'
        save(preparation, dict(status='PASS_PREPARED_UNSIGNED_EXACT466_WATCHLIST_OR_FORWARD_RECOVERY', versionCode=version,
            CC=cc_version, Trakt='1.2.8.1', skin='1.0.5.270_UNCHANGED', source=pins['source'], run_id=int(os.environ.get('GITHUB_RUN_ID', '0')),
            baseline_sha256=BASE_APK, unsigned_sha256=file_sha(unsigned), native_sha256=pin['native_sha256'],
            changed_members=changed, added_members=sorted(added), module_source_count=len(files), module_manifest_sha256=digest(payload),
            source_pins_sha256=file_sha(out / 'SOURCE-PINS.json'), recovery=index == 1, recovery_functional_base=2103466,
            Cobra_bundle_byte_identical=True, minimal_contract_bundle_byte_identical=True, all_DEX_byte_identical=True,
            Search_and_providers_byte_identical=True, Trakt_byte_identical=True, original_installer_unchanged=True,
            account_settings_or_database_changes=False, registry_mutated=False, APK_signing='NOT_RUN', Android='NOT_RUN', Fold='NOT_RUN', public_release=False))
        compare(apk, unsigned, preparation, work / 'publish/APK-PRESERVATION.json')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest='operation', required=True)
    for op in ('inventory', 'inputs', 'finish'):
        a = commands.add_parser(op)
        for name in ('apk', 'prepared', 'out'):
            a.add_argument('--' + name, type=Path, required=True)
        if op != 'inventory':
            for name in ('native-artifact', 'admission-file'):
                a.add_argument('--' + name, type=Path, required=True)
    a = commands.add_parser('compare')
    for name in ('apk', 'candidate', 'preparation', 'out'):
        a.add_argument('--' + name, type=Path, required=True)
    args = vars(p.parse_args())
    globals()[args.pop('operation')](**args)
