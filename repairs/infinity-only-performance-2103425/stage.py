"""Stage genuine Infinity sources; never forge module authentication or sign.

The sole combined signer currently cannot issue an Infinity-only update without
also changing the frozen chooser metadata. Preserve that refusal and prepare
reviewable, compiled source inputs while the owner conflict is unresolved.
"""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ISOLATION = REPO / 'repairs/dual-experience-isolation-2103420'
sys.path.insert(0, str(ISOLATION))
from inventory import canonical, file_sha, validate_names
from component_bundles import read_bundle
from release_gate import normalize_manifest
sys.path.insert(0, str(REPO / 'repairs/infinity-final-closure-2103407'))
import module_bundle

PREFIX = 'assets/addons/'
CC = 'script.infinity.commandcenter'
ALLOWED = {
    'resume_hub.py': {'entries'},
    'plugin.py': {'_values_for', 'listing'},
    'provider_inventory.py': {'snapshot', 'eligible'},
    'infinity_search.py': {'providers', '_query_file_stamp', '_query_signature',
                           '_provider_result', '_publish_result', '_search_results', '_open_search'},
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def preserved_functions(before, after, allowed):
    def tree(raw):
        return ast.parse(raw.decode('utf-8'))
    old, new = tree(before), tree(after)
    # All imports, global state, class bodies and non-selected functions remain
    # structurally exact. Also compare source bytes for every existing function
    # outside the allowlist, including persistence and worker ownership code.
    def retained(node):
        return [n for n in node.body if not isinstance(n, ast.FunctionDef) or n.name not in allowed]
    assert ast.dump(ast.Module(body=retained(old), type_ignores=[])) == ast.dump(ast.Module(body=retained(new), type_ignores=[]))
    old_functions = {n.name: ast.get_source_segment(before.decode(), n) for n in old.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    new_functions = {n.name: ast.get_source_segment(after.decode(), n) for n in new.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    for name, source in old_functions.items():
        if name not in allowed:
            assert new_functions[name] == source, name
    assert set(new_functions) - set(old_functions) <= allowed
    compile(after, '<staged-owned-source>', 'exec', dont_inherit=True)
    return dict(unchanged_definitions=len(set(old_functions) - allowed),
                selected_definitions=sorted(allowed), compilation='PASS')


def run(baseline, bundles, out):
    scope = json.loads((HERE / 'SCOPE.json').read_text())
    assert file_sha(baseline) == scope['baseline_apk_sha256'], 'Exact signed 2103425 required'
    assert not out.exists(), 'Fresh staging destination required'
    out.mkdir(parents=True)
    authority = json.loads(subprocess.check_output([
        'git', '-C', str(REPO), 'show', scope['baseline_source'] +
        ':repairs/dual-experience-isolation-2103420/release-authority.json']))
    current = json.loads((ISOLATION / 'release-authority.json').read_text())
    assert current == authority, 'Do not modify the current signing authority to force this candidate'
    original_catalog = json.loads((bundles / 'catalog.json').read_text())
    payload = {}
    complete_members = {}
    dex_hashes = set()
    for owner, expected in authority['bundle_catalog']['bundles'].items():
        assert original_catalog['bundles'][owner] == expected
        meta = read_bundle(bundles / expected['file'], expected)
        payload.update(meta['payload'])
        complete_members.update(meta['members'])
        dex_hashes.update(meta['dex'].values())
    assert payload == authority['payload'], 'Owner bundle payload does not match signed authority'
    baseline_root = out / 'baseline-addons'
    baseline_root.mkdir()
    with ZipFile(baseline) as archive:
        validate_names(archive)
        native_dex = {}
        for name, meta in complete_members.items():
            raw = archive.read(name)
            normalized = normalize_manifest(raw)[0] if name == 'AndroidManifest.xml' else raw
            assert sha(normalized) == authority['payload']['member:' + name]['sha256'], name
            if name.endswith('.so'):
                native_dex[name] = sha(raw)
        actual_dex = {name: sha(archive.read(name)) for name in archive.namelist()
                      if name.startswith('classes') and name.endswith('.dex')}
        assert set(actual_dex.values()) == dex_hashes and len(actual_dex) == len(dex_hashes)
        native_dex.update(actual_dex)
        for info in archive.infolist():
            if not info.filename.startswith(PREFIX): continue
            relative = info.filename[len(PREFIX):]
            if relative.split('/')[0] not in module_bundle.IDS: continue
            target = baseline_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))
    # Verify the original first-party source inventory and original RSA proof.
    old_payload, old_files = module_bundle.build(baseline_root)
    assert old_payload == (baseline_root / CC / module_bundle.MANIFEST).read_bytes()
    verified = subprocess.check_output([
        'openssl', 'dgst', '-sha256', '-verify',
        str(REPO / 'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem'),
        '-signature', str(baseline_root / CC / (module_bundle.MANIFEST + '.sig')),
        str(baseline_root / CC / module_bundle.MANIFEST)], text=True).strip()
    assert verified == 'Verified OK'
    candidate = out / 'candidate-addons'
    shutil.copytree(baseline_root, candidate)
    changes, functions = {}, {}
    for name, expected in scope['preimages'].items():
        before = old_files[CC + '/' + name]
        assert sha(before) == expected, name
        after = (HERE / 'overlay' / CC / name).read_bytes()
        assert before != after, 'Unnecessary overlay: ' + name
        key = 'member:' + PREFIX + CC + '/' + name
        assert authority['payload'][key]['owner'] == 'INFINITY'
        if name in ALLOWED:
            functions[name] = preserved_functions(before, after, ALLOWED[name])
        else:
            assert name == 'addon.xml'
            assert before.replace(b'version="0.3.5.49"', b'version="0.3.5.50"', 1) == after
        (candidate / CC / name).write_bytes(after)
        changes[key] = dict(owner='INFINITY', before_sha256=sha(before), after_sha256=sha(after))
    # The old signature must never be attached to a new source generation.
    for leaf in (module_bundle.MANIFEST, module_bundle.MANIFEST + '.sig'):
        (candidate / CC / leaf).unlink()
    module = module_bundle.prepare(candidate)
    new_payload, new_files = module_bundle.build(candidate)
    assert set(new_files) == set(old_files), 'No added or removed application source'
    changed = {name for name in old_files if old_files[name] != new_files[name]}
    assert changed == {CC + '/' + name for name in scope['preimages']}
    assert not (candidate / CC / (module_bundle.MANIFEST + '.sig')).exists()
    # Frozen service, checkpoint, common IO, writer and all helper source bytes
    # are checked by the full inventory above, not by executing their behavior.
    save(out / 'PRESERVATION.json', dict(
        status='PASS_SOURCE_AND_IMMUTABLE_BASELINE_INVENTORY', baseline_apk_sha256=file_sha(baseline),
        baseline_original_module_signature=verified,
        baseline_authority_source=scope['baseline_source'], all_baseline_members_checked=len(complete_members),
        original_owner_bundles={owner: row['sha256'] for owner, row in original_catalog['bundles'].items()},
        changed_application_sources=changes, unchanged_firstparty_sources=len(old_files) - len(changed),
        changed_function_review=functions, native_and_DEX_frozen=native_dex,
        Cobra='BYTE_IDENTICAL_INPUT', chooser='BYTE_IDENTICAL_INPUT', shared_contract='BYTE_IDENTICAL_INPUT',
        protected_shutdown_sources='BYTE_IDENTICAL', shutdown_tests='NOT_RUN',
        candidate_module=module, candidate_module_manifest_sha256=sha(new_payload),
        candidate_module_signature='NOT_ISSUED_ORIGINAL_SIGNER_REQUIRED',
        installable_APK_produced=False, accepted_pointer_updated=False))
    blockers = dict(
        status='SIGNING_BLOCKED_BY_EXPLICIT_OWNER_CONFLICT', installable_APK_produced=False,
        blockers=[
            dict(file='repairs/dual-experience-isolation-2103420/release_authority.py',
                 function='transition', reason='Infinity update requires candidate_versionCode in the Infinity last-updated label, then UPDATED_LABELS_REQUIRE_SHELL_BUNDLE; validate binds labels to chooser-owned assets/experience-component-updates.properties. Chooser changes are explicitly prohibited.'),
            dict(file='repairs/dual-experience-isolation-2103420/release_gate.py',
                 function='remote_authority', reason='AUTHORITY_BRANCH is the old work/infinity-cobra-isolation-from-2103420-20261026 branch, while all work is required on work/infinity-only-stability-speed-from-2103425-20261028.'),
            dict(file='.github/workflows/infinity-combined-release.yml',
                 function='jobs.combined.if / selected-owner build', reason='Sole original-key pipeline is restricted to the old branch and consumes already approved owner ZIPs. New authenticated Infinity module generation needs a guarded original-key manifest-signing stage within that same pipeline before final owner approval. No alternate signer has been added.')],
        protected_baseline_ref='lock/infinity-cobra-2103425-fold-approved-chooser-20261028',
        protected_baseline_source=scope['baseline_source'], proposed_versionCode=2103426,
        proposed_Infinity_component='2103420.isolation.1.performance.1',
        proposed_Command_Center_version='0.3.5.50', physical_Fold='NOT_RUN')
    save(out / 'SIGNING-BLOCKERS.json', blockers)
    print(json.dumps(dict(staged=str(out), changed_sources=len(changes), module=module,
                          installable_APK_produced=False), indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--bundles', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    run(**vars(p.parse_args()))
