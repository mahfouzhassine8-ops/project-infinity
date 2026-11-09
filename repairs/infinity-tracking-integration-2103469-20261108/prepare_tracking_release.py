"""Exact signed69 + three Python sources, using the unchanged original tools.

Inputs emit unsigned complete80 manifests for the existing original module
signer. APK assembly is not selected or implemented here. The member comparison
is retained for subsequent reviewed release preparation. No signer, registry
mutation, native build, device access, or acceptance assertion is implemented.
"""
import argparse
import copy
import hashlib
import importlib
import json
import os
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
CC = 'script.infinity.commandcenter'
MANIFEST = 'INFINITY-MODULES.v1'
PYTHON = {'plugin.py', 'resume_hub.py', 'service.py'}
NATIVE = 'lib/arm64-v8a/libkodi.so'
LABEL = 'assets/experience-component-updates.properties'
PREFIX = 'assets/addons/' + CC + '/'
HOST_EVIDENCE = ('INTEGRATION-SOURCE-PROOF.json', 'ACTUAL-SOURCE-HOST-RESULT.json', 'PROJECTION-HOST-RESULT.json')


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
                    latest_signed_versionCode=2103469, candidate_versionCode=2103470, recovery_versionCode=2103471,
                    candidate_CC='0.3.5.68', recovery_CC='0.3.5.69', reserved=False)
    require(all(type(a.get(k)) is type(v) and a[k] == v for k, v in expected.items()), 'ROOT_CONFIRMED_UNUSED_FORWARD_PAIR_REQUIRED')
    return [(a['candidate_versionCode'], a['candidate_CC']), (a['recovery_versionCode'], a['recovery_CC'])]


def source_inputs():
    proof = load(HERE / 'INTEGRATION-SOURCE-PROOF.json')
    require(proof['status'] == 'PASS_SCOPED_SOURCE_PRESERVATION_NOT_ANDROID' and
            proof['protected_APK_SHA256'] == BASE_APK and set(proof['files']) == PYTHON, 'EXACT_THREE_SOURCE_PRESERVATION_PROOF')
    overlay = HERE / 'overlay' / CC
    actual = {name: file_sha(overlay / name) for name in PYTHON}
    require(actual == {name: row['overlay_sha256'] for name, row in proof['files'].items()}, 'FROZEN_THREE_PYTHON_SOURCE_HASHES')
    # Only these explicit files are copied. Host __pycache__ files are never payload inputs.
    return proof, actual


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


def allowed_members(recovery):
    metadata = {PREFIX + n for n in ('addon.xml', MANIFEST, MANIFEST + '.sig')} | {LABEL, 'AndroidManifest.xml'}
    return metadata if recovery else metadata | {PREFIX + n for n in PYTHON}


def validate_member_change(name, before, after, declared, version, recovery):
    require(name in allowed_members(recovery) and name in declared and digest(after) == declared[name], 'UNDECLARED_MEMBER_CHANGE:' + name)
    if name == 'AndroidManifest.xml':
        t = load_tools()
        require(t.normalize_manifest(after) == (t.normalize_manifest(before)[0], version), 'TYPED_ANDROID_VERSION_ONLY')


def compare(apk, candidate, preparation, out=None):
    t = load_tools()
    require(file_sha(apk) == BASE_APK, 'EXACT_SIGNED69_COMPARISON_BASE')
    proof = load(preparation)
    require(proof['baseline_sha256'] == BASE_APK and proof['versionCode'] in (2103470, 2103471) and
            proof['recovery'] is (proof['versionCode'] == 2103471) and not proof['added_members'], 'EXACT_FORWARD_PAIR_COMPARE_METADATA')
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
    report = dict(status='PASS_EXACT69_THREE_PYTHON_OR_METADATA_RECOVERY_MEMBERS', baseline_sha256=BASE_APK,
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
        require(changed == expected and not (after.keys() - before.keys()) and
                before.keys() - after.keys() == {CC + '/' + MANIFEST + '.sig'}, 'ONLY_DECLARED_TRACKING_GENERATION_CHANGES')
        save(work / 'INPUTS.json', dict(versionCode=version, CC=cc_version, source=source,
             modules=after, module_manifest_sha256=digest(payload), authenticated_source_count=80,
             native_sha256=BASE_NATIVE, recovery=index == 1, helper_authenticated_inactive=True,
             Trakt='1.2.8.1', APK_produced=False))
        metadata[str(version)] = file_sha(work / 'INPUTS.json')
    save(out / 'SOURCE-PINS.json', dict(source=source, overlay_sha256=overlay,
         original_tools=t.pins, baseline_APK_sha256=BASE_APK,
         baseline_preparation_sha256=file_sha(prepared / 'PREPARATION.json'),
         baseline_components_sha256=hashes(prepared / 'components'),
         input_metadata_sha256=metadata, version_admission_sha256=file_sha(admission_file),
         source_preservation_sha256=file_sha(HERE / 'INTEGRATION-SOURCE-PROOF.json'),
         host_evidence_sha256={name: file_sha(HERE / name) for name in HOST_EVIDENCE},
         native_sha256=BASE_NATIVE, APK_produced=False, registry_mutated=False,
         signing='PENDING_EXISTING_ORIGINAL_SIGNER', Android='NOT_RUN', public_release=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='operation', required=True)
    p = commands.add_parser('inputs')
    for name in ('apk', 'prepared', 'admission-file', 'out'):
        p.add_argument('--' + name, type=Path, required=True)
    p = commands.add_parser('compare')
    for name in ('apk', 'candidate', 'preparation', 'out'):
        p.add_argument('--' + name, type=Path, required=True)
    args = vars(parser.parse_args())
    globals()[args.pop('operation')](**args)
