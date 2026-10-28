"""Register exact prepared owner inputs after successful original-key auth.

This proposes an engineering candidate; it never changes physical acceptance
or a protected recovery ref. The sole signer independently repeats all checks.
"""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import tempfile
from zipfile import ZipFile

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from prepare_release import REPO, ISOLATION, command, load, require
HERE = Path(__file__).resolve().parent
from inventory import canonical, digest, file_sha, save
from component_bundles import read_bundle
from release_authority import transition, verify_evidence


def register(bundles, producer_run):
    permission = load(HERE / 'RELEASE-AUTHORIZATION.json')
    previous = load(ISOLATION / 'release-authority.json')
    require(previous['candidate_versionCode'] == 2103426 and previous['generation'] == 11, 'EXACT_PREVIOUS_AUTHORITY')
    run = json.loads(command(['gh', 'api', 'repos/mahfouzhassine8-ops/project-infinity/actions/runs/' + str(producer_run)]))
    require(run['conclusion'] == 'success' and run['head_branch'] == permission['branch'], 'SUCCESSFUL_OWNER_PRODUCER')
    source = run['head_sha']
    catalog = load(bundles / 'catalog.json')
    payload, metas = {}, {}
    for owner, row in catalog['bundles'].items():
        meta = read_bundle(bundles / row['file'], row)
        metas[owner] = meta
        payload.update(meta['payload'])
        if owner in ('COBRA', 'MINIMAL_ANDROID_CONTRACT'):
            require(row == previous['bundle_catalog']['bundles'][owner], 'FROZEN_OWNER:' + owner)
        else:
            require(meta['approved_source'] == source, 'EXACT_OWNER_SOURCE')
    expected = {'member:' + name for name in load(HERE / 'SOURCE-PLAN.json')}
    expected.update(('member:assets/addons/script.infinity.commandcenter/INFINITY-MODULES.v1.sig',
                     'member:' + permission['metadata_member']))
    require(set(payload) == set(previous['payload']), 'EXACT_PAYLOAD_SET')
    require({key for key in payload if payload[key] != previous['payload'][key]} == expected, 'EXACT_REVIEWED_OWNER_DIFF')
    with ZipFile(bundles / 'INFINITY.zip') as archive, tempfile.TemporaryDirectory() as temporary:
        temp = Path(temporary)
        for leaf in ('INFINITY-MODULES.v1', 'INFINITY-MODULES.v1.sig'):
            (temp / leaf).write_bytes(archive.read('payload/assets/addons/script.infinity.commandcenter/' + leaf))
        require(file_sha(temp / 'INFINITY-MODULES.v1') == permission['module_manifest_sha256'], 'EXACT_MODULE')
        command(['openssl', 'dgst', '-sha256', '-verify',
                 REPO / 'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem',
                 '-signature', temp / 'INFINITY-MODULES.v1.sig', temp / 'INFINITY-MODULES.v1'])
    proposed = copy.deepcopy(previous)
    proposed.update(generation=12, last_issued_versionCode=2103426, candidate_versionCode=2103427,
                    update_kind='owner_update', target_owners=['INFINITY', 'CHOOSER_SHELL'],
                    previous_authority_sha256=digest(canonical(previous)), payload=payload,
                    bundle_catalog=catalog, experience_version_labels={'INFINITY': 2103427, 'COBRA': 2103423})
    for owner in ('INFINITY', 'CHOOSER_SHELL'):
        proposed['components'][owner] = {name: metas[owner][name] for name in ('version', 'settings_schema', 'approved_source', 'digest')}
        proposed['components'][owner]['revision'] = previous['components'][owner]['revision'] + 1
        proposed['bundle_sources'][owner] = dict(run_id=producer_run, build_source=source,
            artifact='Infinity-Performance-Prepared-Owners-' + str(producer_run), path=owner + '.zip')
    proposed['source_files'] = {name: file_sha(REPO / name) for name in previous['source_files']}
    proposed['workflow_sha256'] = file_sha(REPO / '.github/workflows/infinity-combined-release.yml')
    proposed['owner_update_evidence'] = dict(
        owner='INFINITY', changed_owners=['INFINITY', 'CHOOSER_SHELL'],
        chooser_change='Only user-authorized Infinity last-updated metadata; all classes/resources exact',
        producer_source=source, producer_run=producer_run, tested_source=permission['tested_source'],
        focused_host_run=permission['tested_run'], module_manifest_sha256=permission['module_manifest_sha256'],
        original_module_signature='NATIVE_AND_JCA_VERIFIED_BY_PRODUCER',
        changed_payload=sorted(expected), frozen_owners=['COBRA', 'MINIMAL_ANDROID_CONTRACT'],
        native_DEX_shutdown='BYTE_IDENTICAL', shutdown_tests='NOT_RUN',
        release_exception_authorization='repairs/infinity-only-performance-2103425/continuation/RELEASE-AUTHORIZATION.json',
        physical_Fold='PENDING', accepted_pointer_updated=False)
    transition(previous, proposed, proposed['target_owners'])
    verify_evidence(proposed, lambda name: (REPO / name).read_bytes())
    save(ISOLATION / 'release-authority.json', proposed)
    save(HERE / 'REGISTERED-OWNER-VECTOR.json', dict(generation=12, versionCode=2103427,
         producer_source=source, producer_run=producer_run, bundles=catalog['bundles'],
         changed_payload=sorted(expected), accepted_pointer_updated=False, physical_Fold='PENDING'))
    print('Registered concrete reviewed owner vector; physical acceptance remains pending.')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--bundles', type=Path, required=True)
    p.add_argument('--producer-run', type=int, required=True)
    register(**vars(p.parse_args()))
