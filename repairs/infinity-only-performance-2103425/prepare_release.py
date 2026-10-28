"""Guarded original-key module preparation inside the existing sole signer.

Produces authenticated owner inputs, never an APK. Final combined signing still
requires the reviewed immutable component vector and the unchanged payload gate.
"""
import argparse
import base64
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile

from stage import HERE, REPO, ISOLATION, CC, PREFIX, run as stage, sha, save
from inventory import canonical, file_sha
from component_bundles import record, read_bundle
from release_gate import require, component_digest, AUTHORITY_BRANCH, PROTECTED_REF, PROTECTED_COMMIT, COMBINED_PROTECTED_REF, COMBINED_PROTECTED_COMMIT
from signer_policy import check
from inventory import load


def command(args, env=None):
    return subprocess.check_output(list(map(str, args)), text=True, env=env)


def remote_head(expected):
    origin = command(['git', 'remote', 'get-url', 'origin']).strip().removesuffix('.git')
    require(origin == 'https://github.com/mahfouzhassine8-ops/project-infinity', 'ORIGIN')
    refs = dict(reversed(line.split()) for line in command([
        'git', 'ls-remote', 'origin', 'refs/heads/' + AUTHORITY_BRANCH, PROTECTED_REF, COMBINED_PROTECTED_REF]).splitlines())
    require(refs.get('refs/heads/' + AUTHORITY_BRANCH) == expected, 'PREPARATION_HEAD_RACE')
    require(refs.get(PROTECTED_REF) == PROTECTED_COMMIT, 'PROTECTED_LOCK_MOVED')
    require(refs.get(COMBINED_PROTECTED_REF) == COMBINED_PROTECTED_COMMIT, 'COMBINED_LOCK_MOVED')
    require(command(['git', 'rev-parse', 'HEAD']).strip() == expected, 'LOCAL_HEAD')
    require(not command(['git', 'status', '--porcelain', '--untracked-files=no']).strip(), 'DIRTY_TRACKED_SOURCE')


def patch_bundle(source, expected, owner, changes, version, source_commit, target):
    meta = copy.deepcopy(read_bundle(source, expected))
    require(meta['owner'] == owner, 'OWNER')
    meta['version'], meta['approved_source'] = version, source_commit
    with ZipFile(source) as old, ZipFile(target, 'w') as new:
        for name in old.namelist():
            if name == 'component.json': continue
            raw = old.read(name)
            member = name.removeprefix('payload/')
            if name.startswith('payload/') and member in changes:
                raw = changes[member]
                require(member in meta['members'], 'NO_NEW_PAYLOAD_MEMBER')
                meta['members'][member]['sha256'] = sha(raw)
                meta['payload']['member:' + member]['sha256'] = sha(raw)
            new.writestr(record(name), raw)
        meta['digest'] = component_digest(meta['payload'], owner)
        new.writestr(record('component.json'), canonical(meta))
    row = dict(file=target.name, sha256=file_sha(target), **{
        key: meta[key] for key in ('version', 'digest', 'approved_source', 'settings_schema')})
    actual = read_bundle(target, row)
    original = read_bundle(source, expected)
    require(actual['dex'] == original['dex'], 'FROZEN_DEX')
    require(set(actual['members']) == set(original['members']), 'EXACT_MEMBER_SET')
    differences = {key for key in actual['payload'] if actual['payload'][key] != original['payload'][key]}
    require(differences == {'member:' + name for name in changes}, 'EXACT_AUTHORIZED_DIFF')
    return row, actual


def prepare(baseline, bundles, out):
    baseline, bundles, out = baseline.resolve(), bundles.resolve(), out.resolve()
    permission = load(HERE / 'RELEASE-AUTHORIZATION.json')
    expected = os.environ['GITHUB_SHA']
    require(os.environ.get('GITHUB_WORKFLOW') == 'Infinity combined release | owner gate before original signing', 'SOLE_SIGNER_WORKFLOW')
    require(os.environ.get('GITHUB_REF') == 'refs/heads/' + permission['branch'], 'AUTHORIZED_BRANCH')
    remote_head(expected)
    # The tested feature source/scope cannot be silently replaced during release work.
    for name in ('SCOPE.json', 'stage.py', 'results/SOURCE-SHA256SUMS'):
        old = subprocess.check_output(['git', 'show', permission['tested_source'] + ':' + str((HERE / name).relative_to(REPO))])
        require(old == (HERE / name).read_bytes(), 'TESTED_INPUT_CHANGED:' + name)
    for line in (HERE / 'results/SOURCE-SHA256SUMS').read_text().splitlines():
        pin, path = line.split('  ', 1)
        require(file_sha(HERE / path) == pin, 'TESTED_SOURCE_CHANGED:' + path)
    paths = command(['git', 'diff', '--name-only', permission['baseline_source'], 'HEAD']).splitlines()
    allowed = {'.github/workflows/infinity-combined-release.yml', '.github/workflows/infinity-saved-navigation-android.yml',
               'repairs/dual-experience-isolation-2103420/release_gate.py',
               'repairs/dual-experience-isolation-2103420/test_release_gate.py'}
    require(all(p.startswith('repairs/infinity-only-performance-2103425/') or p in allowed for p in paths), 'PREPARATION_SOURCE_SCOPE')
    test_run = json.loads(command(['gh', 'api', 'repos/mahfouzhassine8-ops/project-infinity/actions/runs/' + str(permission['tested_run'])]))
    require(test_run['head_sha'] == permission['tested_source'] and test_run['conclusion'] == 'success', 'TESTED_RUN_BINDING')
    require(not out.exists(), 'FRESH_OUTPUT')
    out.mkdir()
    stage(baseline, bundles, out / 'source')
    candidate = out / 'source/candidate-addons'
    manifest = candidate / CC / 'INFINITY-MODULES.v1'
    require(file_sha(manifest) == permission['module_manifest_sha256'], 'EXACT_REVIEWED_MANIFEST')
    verifier = out / 'verify-module-bundle'
    firstparty = REPO / 'repairs/infinity-final-closure-2103407'
    command(['g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror',
             firstparty / 'verify_module_bundle.cpp', firstparty / 'isolated-native/InfinityModuleManifest.cpp',
             '-lcrypto', '-o', verifier])
    routes = check(load(ISOLATION / 'signer-policy.json'))
    # Keys are read only after concrete immutable inventory/source verification.
    with tempfile.TemporaryDirectory(prefix='infinity-original-module-') as temporary:
        temp = Path(temporary)
        classes = temp / 'classes'
        classes.mkdir()
        command(['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main', '--release', '8', '-g:none',
                 '-Xlint:all,-options', '-Werror', '-d', classes, firstparty / 'SignInfinityModules.java'])
        remote_head(expected)
        require(check(load(ISOLATION / 'signer-policy.json')) == routes, 'SIGNER_POLICY_RACE')
        key = temp / 'original.jks'
        key.touch(mode=0o600)
        key.write_bytes(base64.b64decode(os.environ['INFINITY_KEYSTORE_B64'], validate=True))
        env = {name: os.environ[name] for name in ('PATH', 'JAVA_HOME', 'INFINITY_STORE_PASSWORD', 'INFINITY_KEY_PASSWORD', 'INFINITY_KEY_ALIAS')}
        proof = command(['java', '-cp', classes, 'SignInfinityModules', key, manifest], env)
    proof += command([verifier, candidate, firstparty / 'ORIGINAL-INFINITY-PUBLIC-KEY.pem'])
    (out / 'MODULE-AUTHENTICATION.txt').write_text(proof)
    require('NATIVE_VERIFIED package=0.3.5.50 protocol=1 files=75' in proof, 'NATIVE_AUTHENTICATION')
    authority = load(ISOLATION / 'release-authority.json')
    catalog = copy.deepcopy(authority['bundle_catalog'])
    catalog['source'] = expected
    destination = out / 'components'
    destination.mkdir()
    changes = {PREFIX + str(p.relative_to(candidate)): p.read_bytes() for p in candidate.rglob('*') if p.is_file() and
               (str(p.relative_to(candidate)) in {CC + '/' + n for n in load(HERE / 'SCOPE.json')['preimages']} or
                p.name in ('INFINITY-MODULES.v1', 'INFINITY-MODULES.v1.sig'))}
    require(len(changes) == 7, 'EXACT_INFINITY_MEMBER_CHANGES')
    metas = {}
    for owner in ('INFINITY', 'CHOOSER_SHELL', 'COBRA', 'MINIMAL_ANDROID_CONTRACT'):
        old = authority['bundle_catalog']['bundles'][owner]
        source, target = bundles / old['file'], destination / old['file']
        if owner == 'INFINITY':
            row, meta = patch_bundle(source, old, owner, changes, permission['Infinity_component'], expected, target)
        elif owner == 'CHOOSER_SHELL':
            exception = permission['chooser_exception']
            with ZipFile(source) as archive:
                require(archive.read('payload/' + exception['only_member']) == exception['before'].encode(), 'EXACT_CHOOSER_METADATA_PREIMAGE')
            row, meta = patch_bundle(source, old, owner, {exception['only_member']: exception['after'].encode()},
                                     old['version'] + '.infinity2103426', expected, target)
        else:
            shutil.copyfile(source, target)
            row, meta = old, read_bundle(target, old)
        catalog['bundles'][owner] = row
        metas[owner] = meta
    save(destination / 'catalog.json', catalog)
    payload = {key: value for meta in metas.values() for key, value in meta['payload'].items()}
    changed = {key for key in payload if payload[key] != authority['payload'][key]}
    require(changed == {'member:' + name for name in changes} | {'member:' + permission['chooser_exception']['only_member']}, 'COMPLETE_OWNER_DIFF')
    remote_head(expected)
    require(check(load(ISOLATION / 'signer-policy.json')) == routes, 'SIGNER_POLICY_RACE')
    save(out / 'PREPARED-OWNERS.json', dict(status='AUTHENTICATED_EXACT_OWNER_INPUTS', source=expected,
         run_id=int(os.environ['GITHUB_RUN_ID']), catalog=catalog, changed_payload=sorted(changed),
         tested_source=permission['tested_source'], tested_run=permission['tested_run'],
         original_module_signature='NATIVE_AND_JCA_VERIFIED', manifest_sha256=file_sha(manifest),
         native_DEX_shutdown_shared_contract='BYTE_IDENTICAL', Cobra='BYTE_IDENTICAL',
         chooser='ONLY_AUTHORIZED_LAST_UPDATED_METADATA', APK_produced=False,
         protected_2103425=permission['baseline_source'], accepted_pointer_updated=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('baseline', 'bundles', 'out'): p.add_argument('--' + name, type=Path, required=True)
    prepare(**vars(p.parse_args()))
