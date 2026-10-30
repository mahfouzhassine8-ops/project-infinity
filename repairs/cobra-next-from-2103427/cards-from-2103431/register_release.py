"""Register one successful, source-bound Cards producer; never accept a release.

The default writes a reviewable authority proposal.  Only --apply changes the
existing authority, after checking the downloaded immutable CI artifacts.  This
program does not dispatch a workflow, build an APK, or access signing material.
"""
import argparse
import copy
import json
from pathlib import Path
import re
import subprocess
import sys
from xml.etree import ElementTree
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ISO = REPO / 'repairs/dual-experience-isolation-2103420'
sys.path.insert(0, str(ISO))
from inventory import canonical, digest, file_sha, load, save, validate_names
from component_bundles import OWNED, read_bundle
from release_gate import require
from release_authority import transition, verify_evidence
from build import BASE_SOURCE, compiler_sources
from package_owners import bound_sources

REPOSITORY = 'mahfouzhassine8-ops/project-infinity'
BRANCH = 'work/cobra-only-from-2103427-20261028'
VERSION = 2103432
GENERATION = 17
TARGETS = ('COBRA', 'CHOOSER_SHELL')
FROZEN = ('INFINITY', 'MINIMAL_ANDROID_CONTRACT')
METADATA = 'assets/experience-component-updates.properties'
CHANGED_CLASSES = {'class:Lcom/projectinfinity/kodi/' + n + ';' for n in (
    'InfinityLiveActivity', 'InfinityLiveActivity$CobraPosterChannelCard',
    'InfinityCobraFeatureRuntime', 'CobraLogoRequests', 'CobraComponent')}
NEW_ROOTS = {'class:Lcom/projectinfinity/kodi/' + n for n in (
    'CobraCardsTiles', 'CobraCardsLayout', 'CobraProfileDataReuse', 'CobraCardsReuse')}


def git_bytes(source, path):
    return subprocess.check_output(['git', '-C', str(REPO), 'show', source + ':' + path])


def signed431_authority():
    return json.loads(git_bytes(BASE_SOURCE, str((ISO / 'release-authority.json').relative_to(REPO))))


def previous_authority():
    previous, signed = load(ISO / 'release-authority.json'), signed431_authority()
    require(previous == signed, 'EXACT_SIGNED431_AUTHORITY_REQUIRED')
    require(previous['candidate_versionCode'] == 2103431 and previous['generation'] == 16,
            'EXACT_PREVIOUS_AUTHORITY')
    return previous


def repository_source_files():
    """Compiler, packager, verifier, selection and registration all stay bound."""
    files = set(bound_sources()) | {
        HERE / 'register_release.py', HERE / 'verify_delivery.py',
        HERE / 'integrated-qa/prepare_release.py',
        REPO / '.github/workflows/infinity-saved-navigation-android.yml',
    }
    return {str(p.relative_to(REPO)): file_sha(p) for p in sorted(files)}


def evidence_path(folder, name):
    require(type(name) is str and name and not Path(name).is_absolute(), 'EVIDENCE_RELATIVE_PATH')
    path = (folder / name).resolve()
    require(path.is_relative_to(folder.resolve()) and path.is_file(), 'EVIDENCE_PATH:' + name)
    return path


def validate_payload(previous, catalog, bundles):
    """Recheck owner deltas independently of mutable human-readable receipts."""
    require(set(catalog['bundles']) == set(OWNED), 'EXACT_OWNER_VECTOR')
    require(catalog['schema'] == 1 and catalog['package'] == previous['package'] and
            catalog['certificate_sha256'] == previous['certificate_sha256'] and
            catalog['release_approved'] is False, 'CATALOG_IDENTITY')
    payload, metas = {}, {}
    for owner, row in catalog['bundles'].items():
        require(row['file'] == owner + '.zip', 'CANONICAL_OWNER_FILENAME')
        meta = read_bundle(bundles / row['file'], row)
        require(meta['owner'] == owner, 'BUNDLE_OWNER')
        require(not set(payload) & set(meta['payload']), 'DUPLICATE_PAYLOAD')
        payload.update(meta['payload'])
        metas[owner] = meta
        require(row['settings_schema'] == previous['components'][owner]['settings_schema'],
                'FROZEN_SETTINGS_SCHEMA:' + owner)
        if owner in FROZEN:
            require(row == previous['bundle_catalog']['bundles'][owner], 'FROZEN_OWNER_ZIP:' + owner)
        else:
            require(row['approved_source'] == catalog['source'], 'EXACT_UPDATED_OWNER_SOURCE')
    old = previous['payload']
    require(set(old) <= set(payload), 'REMOVED_PAYLOAD')
    changed = {k for k in old if old[k] != payload[k]}
    added = set(payload) - set(old)
    require(changed == CHANGED_CLASSES | {'member:' + METADATA}, 'EXACT_FIVE_CLASS_AND_VERSION_DELTA')
    require(added and all(k.startswith('class:') and k.split('$')[0].rstrip(';') in NEW_ROOTS and
                         payload[k]['owner'] == 'COBRA' for k in added), 'BOUNDED_NEW_COBRA_HELPERS')
    chooser = metas['CHOOSER_SHELL']
    require(chooser['version'] == '2103432.version-metadata.1', 'GENUINE_CHOOSER_VERSION')
    require(metas['COBRA']['version'] == '2103432.cobra.1', 'GENUINE_COBRA_VERSION')
    with ZipFile(bundles / 'CHOOSER_SHELL.zip') as archive:
        require(archive.read('payload/' + METADATA) ==
                b'infinity.last_updated_in=2103427\ncobra.last_updated_in=2103432\n', 'GENUINE_VERSION_LABELS')
    return payload, metas, changed, added


def validate_ci(evidence, catalog, producer_run, source, previous):
    receipt = load(evidence / 'PRODUCER-RESULT.json')
    require(receipt['schema'] == 1 and receipt['status'] == 'PASS_CARDS_PREPARED_OWNERS', 'PRODUCER_RESULT')
    require(receipt['source'] == source and receipt['run_id'] == producer_run and
            receipt['branch'] == BRANCH, 'PRODUCER_SOURCE_RUN_BRANCH')
    require(receipt['catalog_sha256'] == file_sha(catalog), 'PRODUCER_CATALOG_BINDING')
    files = receipt['files']
    required = {'BUILD.json', 'CORRECTIVE-PRESERVATION.json',
                'PACKAGE-CANONICAL-RESULT.json', 'SOURCE-BINDINGS.json'}
    require(required <= set(files), 'MISSING_PRODUCER_PROOF')
    for name, pin in files.items():
        require(re.fullmatch('[0-9a-f]{64}', pin) is not None, 'EVIDENCE_HASH_FORMAT')
        require(file_sha(evidence_path(evidence, name)) == pin, 'EVIDENCE_CHANGED:' + name)
    compiler = {str(p.relative_to(REPO)): file_sha(p) for p in compiler_sources()}
    require(len(compiler) == 20 and receipt['compiler_source_files'] == compiler, 'COMPLETE_COMPILER_INPUTS')
    tested = receipt['tested_source_files']
    require(repository_source_files().items() <= tested.items(), 'MISSING_SOURCE_BINDING')
    for name, pin in tested.items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'SOURCE_PATH')
        require(file_sha(REPO / name) == pin and digest(git_bytes(source, name)) == pin,
                'TESTED_COMMITTED_SOURCE_CHANGED:' + name)
    built = load(evidence / 'BUILD.json')
    require(built['status'] == 'COMPILED_UNSIGNED_COBRA_OWNER_ONLY' and
            built['baseline_signed_source'] == BASE_SOURCE and
            built['candidate_component_version'] == '2103432.cobra.1', 'COMPILED_OWNER_IDENTITY')
    require(built['compiler_source_files'] == compiler, 'COMPILED_SOURCE_BINDING')
    require(built['baseline_components'] == previous['bundle_catalog'], 'EXACT431_COMPILE_BASE')
    proof = load(evidence / 'PACKAGE-CANONICAL-RESULT.json')
    require(proof['status'] == 'PASS_EXACT_FIVE_CLASS_DELTA' and
            proof['baseline_signed_source'] == BASE_SOURCE and not proof['missing_classes'], 'CANONICAL_PRESERVATION')
    require(proof['build_receipt_sha256'] == files['BUILD.json'] and
            proof['compiler_source_files'] == compiler and
            proof['verifier_source_sha256'] == file_sha(HERE / 'verify_owner_source.py'), 'CANONICAL_SOURCE_BINDING')
    preservation = load(evidence / 'CORRECTIVE-PRESERVATION.json')
    require(preservation['status'] == 'VERIFIED_CARDS_COBRA_ONLY_DELTA_AND_GENUINE_VERSION_METADATA' and
            preservation['source'] == source and preservation['baseline_signed_source'] == BASE_SOURCE and
            preservation['component_catalog'] == load(catalog) and
            preservation['independent_policy_receipt_sha256'] == files['PACKAGE-CANONICAL-RESULT.json'],
            'PACKAGED_OWNER_PRESERVATION')
    bindings = load(evidence / 'SOURCE-BINDINGS.json')
    require(bindings['status'] == 'PASS_FRESH_SOURCE_BOUND_EXACT_FIVE_CLASS_HOST_OVERLAY_NO_BEHAVIOR' and
            bindings['source'] == source and bindings['branch'] == BRANCH and
            bindings['versionCode'] == VERSION and bindings['candidate_generation'] == GENERATION and
            bindings['baseline_signed_source'] == BASE_SOURCE and
            bindings['baseline_APK_sha256'] == load(HERE / 'BASELINE.json')['APK_sha256'] and
            bindings['compiler_source_files'] == compiler and
            bindings['owner_BUILD_sha256'] == files['BUILD.json'] and bindings['owner_BUILD'] == built and
            bindings['helper_source_sha256'] == built['helper_sources'] and
            bindings['verifier_source_sha256'] == file_sha(HERE / 'verify_owner_source.py') and
            bindings['prepare_source_sha256'] == file_sha(HERE / 'integrated-qa/prepare_release.py'), 'HOST_ACTUAL_OWNER_BINDING')
    with ZipFile(catalog.parent / 'COBRA.zip') as archive:
        meta = json.loads(archive.read('component.json'))
    dex = {Path(n).name: pin for n, pin in meta['dex'].items()}
    require(proof['new_DEX_sha256'] == bindings['owner_DEX_sha256'] == dex, 'TESTED_PACKAGED_DEX_BINDING')
    checks = receipt['selected_checks']
    require(isinstance(checks, list) and checks, 'NO_SELECTED_CI_CHECKS')
    names, junit_seen, selections = set(), set(), {}
    for check in checks:
        require(check['name'] not in names and check['status'] == 'PASS', 'SELECTED_CHECK_FAILED_OR_DUPLICATE')
        names.add(check['name'])
        selection = check['selection_file']
        require(selection in files, 'UNBOUND_TEST_SELECTION')
        selected = load(evidence_path(evidence, selection))
        selections[check['name']] = selected
        require(selected['recorded_before_execution'] is True and isinstance(selected['methods'], list) and
                selected['methods'] and len(set(selected['methods'])) == len(selected['methods']), 'EXACT_PRESELECTED_METHODS')
        test_class = selected['class'].rsplit('.', 1)[-1]
        require(re.fullmatch('[A-Za-z_$][A-Za-z0-9_$]*', test_class) is not None, 'SELECTED_CLASS_NAME')
        test_sources = list(HERE.rglob(test_class + '.java'))
        require(len(test_sources) == 1 and str(test_sources[0].relative_to(REPO)) in tested, 'SELECTED_TEST_SOURCE_BOUND')
        inputs_file = check['inputs_file']
        require(inputs_file in files, 'UNBOUND_SELECTED_TEST_INPUTS')
        inputs = load(evidence_path(evidence, inputs_file))
        binding_pin = inputs.get('trusted_source_bindings_sha256', inputs.get('source_binding_sha256'))
        host_pin = inputs.get('production_jar_sha256', inputs.get('classpath', {}).get('production.jar'))
        support_pin = inputs.get('support_jar_sha256', inputs.get('classpath', {}).get('support.jar'))
        require(binding_pin == files['SOURCE-BINDINGS.json'] and host_pin == bindings['production_jar_sha256'] and
                support_pin == bindings['support_jar_sha256'] and inputs['test_sha256'] == file_sha(test_sources[0]),
                'SELECTED_TEST_USED_DIFFERENT_OWNER_OR_SOURCE')
        require(check['junit_files'], 'NO_NATIVE_SELECTED_TEST_RESULT')
        actual_tests = []
        for name in check['junit_files']:
            require(name in files and name not in junit_seen, 'UNBOUND_OR_DUPLICATE_JUNIT')
            junit_seen.add(name)
            tree = ElementTree.parse(evidence_path(evidence, name)).getroot()
            suites = [tree] if tree.tag == 'testsuite' else list(tree.iter('testsuite'))
            require(suites and sum(int(s.get('tests', '0')) for s in suites) > 0, 'NO_EXECUTED_SELECTED_TEST')
            require(all(int(s.get(k, '0')) == 0 for s in suites for k in ('failures', 'errors', 'skipped')),
                    'SELECTED_CI_JUNIT_NOT_PASS')
            for case in tree.iter('testcase'):
                require(case.get('classname', '').rsplit('.', 1)[-1] == test_class and
                        not any(case.find(k) is not None for k in ('failure', 'error', 'skipped')), 'JUNIT_TEST_IDENTITY')
                actual_tests.append(case.get('name'))
        require(len(actual_tests) == len(set(actual_tests)) and set(actual_tests) == set(selected['methods']),
                'EXECUTED_METHODS_DIFFER_FROM_SELECTION')
    return receipt, selections


def producer_artifacts(producer_run, source):
    run = json.loads(subprocess.check_output(['gh', 'api', 'repos/' + REPOSITORY + '/actions/runs/' + str(producer_run)]))
    require(run['status'] == 'completed' and run['conclusion'] == 'success' and run['head_branch'] == BRANCH and
            run['head_sha'] == source, 'SUCCESSFUL_CARDS_PRODUCER_REQUIRED')
    require(run['path'] == '.github/workflows/infinity-saved-navigation-android.yml', 'EXISTING_FEATURE_WORKFLOW')
    pages = json.loads(subprocess.check_output(['gh', 'api', '--paginate', '--slurp',
        'repos/' + REPOSITORY + '/actions/runs/' + str(producer_run) + '/artifacts?per_page=100']))
    available = [r for page in pages for r in page['artifacts'] if not r['expired']]
    selected = {}
    for kind in ('Prepared-Owners', 'Host-Evidence'):
        name = 'Cobra-Cards-' + kind + '-' + str(producer_run)
        matches = [r for r in available if r['name'] == name]
        require(len(matches) == 1, 'EXACT_PRODUCER_ARTIFACT:' + name)
        row = {k: matches[0][k] for k in ('id', 'name', 'digest', 'size_in_bytes')}
        require(re.fullmatch('sha256:[0-9a-f]{64}', row['digest']) is not None, 'GITHUB_ARTIFACT_DIGEST_REQUIRED')
        selected[name] = row
    return selected


def bind_archive(archive_path, artifact, folder, required_files):
    require(file_sha(archive_path) == artifact['digest'].removeprefix('sha256:'), 'OFFICIAL_ARTIFACT_ARCHIVE_HASH')
    with ZipFile(archive_path) as archive:
        names = set(validate_names(archive))
        require(set(required_files) <= names, 'OFFICIAL_ARTIFACT_FILES_MISSING')
        for name in required_files:
            with archive.open(name) as stream:
                import hashlib
                pin = hashlib.file_digest(stream, 'sha256').hexdigest()
            require(pin == file_sha(evidence_path(folder, name)), 'LOCAL_ARTIFACT_FILE_CHANGED:' + name)


def check_registered(bundles, evidence, evidence_archive):
    """Extra pre-key guard; generic authority verification remains unchanged."""
    authority, previous = load(ISO / 'release-authority.json'), signed431_authority()
    require(authority['generation'] == GENERATION and authority['candidate_versionCode'] == VERSION and
            set(authority['target_owners']) == set(TARGETS), 'REGISTERED432_AUTHORITY_REQUIRED')
    transition(previous, authority, TARGETS)
    catalog = load(bundles / 'catalog.json')
    require(catalog == authority['bundle_catalog'], 'REGISTERED_COMPONENT_CATALOG')
    payload, _, _, _ = validate_payload(previous, catalog, bundles)
    require(payload == authority['payload'], 'REGISTERED_COMPONENT_PAYLOAD')
    expected = authority['owner_update_evidence']
    producer_run, source = expected['producer_run'], expected['producer_source']
    receipt, selections = validate_ci(evidence, bundles / 'catalog.json', producer_run, source, previous)
    artifacts = producer_artifacts(producer_run, source)
    name = 'Cobra-Cards-Host-Evidence-' + str(producer_run)
    require(artifacts == expected['artifacts'], 'REGISTERED_OFFICIAL_ARTIFACTS_CHANGED')
    bind_archive(evidence_archive, artifacts[name], evidence, {'PRODUCER-RESULT.json'} | set(receipt['files']))
    require(file_sha(evidence / 'PRODUCER-RESULT.json') == expected['producer_result_sha256'] and
            receipt['tested_source_files'] == expected['tested_source_files'] and
            receipt['compiler_source_files'] == expected['compiler_source_files'] and
            receipt['files'] == expected['evidence_files'] and receipt['selected_checks'] == expected['selected_checks'] and
            selections == expected['selections'], 'REGISTERED_CI_RECEIPT_CHANGED')
    verify_evidence(authority, lambda n: (REPO / n).read_bytes())
    print('PASS registered432 actual producer, selected CI, compiler and packaging sources; no signing or acceptance operation.')


def register(bundles, evidence, owners_archive, evidence_archive, producer_run, out, apply=False):
    bundles, evidence = bundles.resolve(), evidence.resolve()
    require(not out.exists(), 'FRESH_PROPOSAL_OUTPUT')
    previous = previous_authority()
    run = json.loads(subprocess.check_output(['gh', 'api', 'repos/' + REPOSITORY + '/actions/runs/' + str(producer_run)]))
    require(run['status'] == 'completed' and run['conclusion'] == 'success' and run['head_branch'] == BRANCH,
            'SUCCESSFUL_CARDS_PRODUCER_REQUIRED')
    require(run['path'] == '.github/workflows/infinity-saved-navigation-android.yml', 'EXISTING_FEATURE_WORKFLOW')
    source = run['head_sha']
    require(re.fullmatch('[0-9a-f]{40}', source) is not None, 'EXACT_CI_SOURCE')
    catalog = load(bundles / 'catalog.json')
    require(catalog['source'] == source, 'OWNER_PRODUCER_SOURCE')
    payload, metas, changed, added = validate_payload(previous, catalog, bundles)
    receipt, selections = validate_ci(evidence, bundles / 'catalog.json', producer_run, source, previous)
    selected_artifacts = producer_artifacts(producer_run, source)
    artifact_names = ('Cobra-Cards-Prepared-Owners-' + str(producer_run), 'Cobra-Cards-Host-Evidence-' + str(producer_run))
    bind_archive(owners_archive, selected_artifacts[artifact_names[0]], bundles,
        {'catalog.json'} | {r['file'] for r in catalog['bundles'].values()})
    bind_archive(evidence_archive, selected_artifacts[artifact_names[1]], evidence,
        {'PRODUCER-RESULT.json'} | set(receipt['files']))
    proposed = copy.deepcopy(previous)
    proposed.update(generation=GENERATION, last_issued_versionCode=2103431, candidate_versionCode=VERSION,
        update_kind='owner_update', target_owners=list(TARGETS), previous_authority_sha256=digest(canonical(previous)),
        payload=payload, bundle_catalog=catalog, experience_version_labels={'INFINITY': 2103427, 'COBRA': VERSION})
    for owner in TARGETS:
        proposed['components'][owner] = {k: metas[owner][k] for k in ('version', 'settings_schema', 'approved_source', 'digest')}
        proposed['components'][owner]['revision'] = previous['components'][owner]['revision'] + 1
        proposed['bundle_sources'][owner] = dict(run_id=producer_run, build_source=source,
            artifact=artifact_names[0], path=owner + '.zip')
    # Frozen owner records and their existing immutable producer locations stay
    # unchanged; those exact ZIP bytes are also in the signed431 recovery set.
    proposed['source_files'] = {n: file_sha(REPO / n) for n in previous['source_files']}
    proposed['workflow_sha256'] = file_sha(REPO / '.github/workflows/infinity-combined-release.yml')
    proposed['owner_update_evidence'] = dict(owner='COBRA', changed_owners=list(TARGETS),
        producer_source=source, producer_run=producer_run, focused_host_run=producer_run,
        changed_payload=sorted(changed | added), frozen_owners=list(FROZEN),
        chooser_change='Exact431 DEX/UI; cobra.last_updated_in=2103432 only',
        protected_contract='EXACT431', shutdown_tests='NOT_RUN', physical_Fold='PENDING', accepted_pointer_updated=False,
        authorization='repairs/cobra-next-from-2103427/CARDS-ONLY-VISUAL-AND-COBRA-END-TO-END-STABILITY-SPEED-20261029.md',
        tested_source_files=receipt['tested_source_files'], compiler_source_files=receipt['compiler_source_files'],
        producer_result_sha256=file_sha(evidence / 'PRODUCER-RESULT.json'), evidence_files=receipt['files'],
        selected_checks=receipt['selected_checks'], selections=selections, artifacts=selected_artifacts,
        runtime_limits=receipt.get('runtime_limits', 'Host checks only; physical Fold acceptance pending'))
    transition(previous, proposed, TARGETS)
    verify_evidence(proposed, lambda n: (REPO / n).read_bytes())
    save(out, proposed)
    if apply:
        # Re-read immediately before mutation; this is never a promotion/lock.
        require(previous_authority() == previous, 'AUTHORITY_CHANGED_BEFORE_REGISTRATION')
        save(ISO / 'release-authority.json', proposed)
        save(HERE / 'REGISTERED-OWNER-VECTOR.json', dict(generation=GENERATION, versionCode=VERSION,
            producer_source=source, producer_run=producer_run, bundles=catalog['bundles'],
            accepted_pointer_updated=False, physical_Fold='PENDING'))
    print('Verified Cards authority ' + ('registered' if apply else 'proposal saved') + '; physical acceptance remains pending.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('bundles', 'evidence', 'evidence-archive'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--owners-archive', type=Path)
    parser.add_argument('--producer-run', type=int)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--check-registered', action='store_true')
    parser.add_argument('--apply', action='store_true', help='Register only after review; default is a proposal')
    args = vars(parser.parse_args())
    if args.pop('check_registered'):
        require(not args['apply'] and args['producer_run'] is None and args['out'] is None and
                args['owners_archive'] is None, 'CHECK_REGISTERED_HAS_NO_MUTATION_OPTIONS')
        check_registered(**{k: args[k] for k in ('bundles', 'evidence', 'evidence_archive')})
    else:
        require(args['owners_archive'] is not None and args['producer_run'] is not None and args['out'] is not None,
                'REGISTER_REQUIRES_OFFICIAL_ARCHIVES_RUN_AND_FRESH_OUTPUT')
        register(**args)
