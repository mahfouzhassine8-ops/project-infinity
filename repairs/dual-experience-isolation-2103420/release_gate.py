"""Fail-closed combined release verification. No approval/promotion operation.

The registry is supplied by the coordinator from the latest remote authority
ref, not by the component branch. The signer must repeat the authority check
immediately before using credentials and serialize the full signing operation.
"""
import argparse
import copy
import json
from pathlib import Path
import re
import struct
import subprocess
from zipfile import ZipFile

from inventory import (APK_SHA, CERT_SHA, OWNERS, PACKAGE, SIGNATURE, HERE,
                       apk_members, canonical, digest, disassemble, file_sha,
                       load, manifest_tree, parse_dex, save, chunks, string_pool)

AUTHORITY_BRANCH = 'work/infinity-only-stability-speed-from-2103425-20261028'
PROTECTED_REF = 'refs/heads/lock/infinity-2103420-user-approved-baseline-20261026'
PROTECTED_COMMIT = '883c64a4de6f87077893921454de71bba850235b'
COMBINED_PROTECTED_REF = 'refs/heads/lock/infinity-cobra-2103425-fold-approved-chooser-20261028'
COMBINED_PROTECTED_COMMIT = 'db730100a3bfea7e06d2e6c3434e89aeb6fa8a15'
REGISTRY_PATH = 'repairs/dual-experience-isolation-2103420/accepted-combined-release.json'
ANDROID = 'http://schemas.android.com/apk/res/android:'


class Rejected(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise Rejected(reason)


def component_digest(payload, owner):
    return digest(canonical({k: v['sha256'] for k, v in payload.items() if v['owner'] == owner}))


def validate_registry(registry):
    if registry.get('schema') == 2:
        from release_authority import validate
        return validate(registry)
    require(registry.get('schema') == 1, 'REGISTRY_SCHEMA')
    require(registry.get('package') == PACKAGE and registry.get('certificate_sha256') == CERT_SHA, 'IDENTITY')
    require(isinstance(registry.get('generation'), int) and registry['generation'] >= 1, 'REGISTRY_GENERATION')
    require(isinstance(registry.get('accepted_app_versionCode'), int), 'ACCEPTED_VERSION')
    require(set(registry.get('components', {})) == set(OWNERS), 'MISSING_OWNER')
    payload = registry.get('payload', {})
    require(bool(payload), 'EMPTY_PAYLOAD')
    for key, value in payload.items():
        require(key.startswith(('class:', 'member:')), 'UNOWNED_PAYLOAD_KIND')
        require(set(value) == {'owner', 'sha256'} and value['owner'] in OWNERS, 'UNOWNED_PAYLOAD')
        require(bool(re.fullmatch('[0-9a-f]{64}', value['sha256'])), 'PAYLOAD_DIGEST')
    for owner, item in registry['components'].items():
        require(item.get('digest') == component_digest(payload, owner), 'COMPONENT_DIGEST:' + owner)
        require(isinstance(item.get('version'), str) and bool(item['version']), 'COMPONENT_VERSION:' + owner)
        require(bool(re.fullmatch('[0-9a-f]{40}', item.get('approved_source', ''))), 'COMPONENT_SOURCE:' + owner)
        require(isinstance(item.get('settings_schema'), str) and bool(item['settings_schema']), 'SETTINGS_SCHEMA:' + owner)
    require(isinstance(registry.get('release_blockers'), list), 'BLOCKER_FIELD_REQUIRED')
    return registry


def validate_transition(previous, proposed, target_owners):
    """Check an approval proposal without accepting or persisting it."""
    validate_registry(previous)
    validate_registry(proposed)
    targets = set(target_owners)
    require(bool(targets) and targets <= {'INFINITY', 'COBRA'}, 'SEPARATE_SHARED_SCOPE_REQUIRED')
    require(proposed['generation'] == previous['generation'] + 1, 'REGISTRY_GENERATION_RACE')
    require(proposed['accepted_app_versionCode'] > previous['accepted_app_versionCode'], 'APP_ROLLBACK')
    for owner in OWNERS:
        old = {k: v for k, v in previous['payload'].items() if v['owner'] == owner}
        new = {k: v for k, v in proposed['payload'].items() if v['owner'] == owner}
        if owner not in targets:
            require(old == new and previous['components'][owner] == proposed['components'][owner], 'CROSS_OWNER_MUTATION:' + owner)
        elif old != new:
            require(previous['components'][owner]['version'] != proposed['components'][owner]['version'], 'VERSION_NOT_ADVANCED:' + owner)
    require(previous['release_blockers'] == proposed['release_blockers'], 'BLOCKER_REMOVAL_REQUIRES_SEPARATE_REVIEW')


def verify_approved_payload(registry, actual):
    validate_registry(registry)
    require(set(actual) == set(registry['payload']), 'MISSING_OR_UNOWNED_MEMBER')
    for key, value in registry['payload'].items():
        require(actual[key] == value['sha256'], 'STALE_OR_MUTATED_OWNER:' + value['owner'] + ':' + key)


def verify_combination(registry, actual, version, expected_generation):
    if registry.get('schema') == 2:
        from release_authority import verify
        return verify(registry, actual, version, expected_generation)
    verify_approved_payload(registry, actual)
    require(expected_generation == registry['generation'], 'STALE_REGISTRY')
    require(type(version) is int and registry['accepted_app_versionCode'] < version <= 2100000000, 'APP_ROLLBACK')
    require(not registry['release_blockers'], 'UNRESOLVED_RELEASE_BLOCKERS')
    require(not any(v['owner'] == 'UNRESOLVED' for v in registry['payload'].values()), 'UNRESOLVED_OWNER')
    return {'generation': registry['generation'], 'payload_digest': digest(canonical(actual)),
            'component_versions': {k: v['version'] for k, v in registry['components'].items()}}


def normalize_manifest(raw):
    """Normalize only the single typed package version; freeze every other byte."""
    parts = list(chunks(raw))
    strings = string_pool(next(p for _, k, p in parts if k == 1))
    result = bytearray(raw)
    versions = []
    for offset, kind, part in parts:
        if kind != 0x102 or strings[struct.unpack_from('<I', part, 20)[0]] != 'manifest':
            continue
        first, step, count = struct.unpack_from('<3H', part, 24)
        for i in range(count):
            at = 16 + first + i * step
            ns, key = struct.unpack_from('<2I', part, at)
            if strings[key] == 'versionCode':
                require(ns != 0xffffffff and strings[ns] + ':' == ANDROID and part[at + 15] == 0x10, 'TYPED_VERSION_REQUIRED')
                versions.append(struct.unpack_from('<I', part, at + 16)[0])
                struct.pack_into('<I', result, offset + at + 16, 0)
    require(len(versions) == 1, 'EXACTLY_ONE_VERSION_REQUIRED')
    return bytes(result), versions[0]


def payload_from_inventory(ownership, classes, manifest_raw):
    payload = {}
    for name, item in ownership['members'].items():
        if name in SIGNATURE or re.fullmatch(r'classes[0-9]*\.dex', name):
            continue
        sha = digest(normalize_manifest(manifest_raw)[0]) if name == 'AndroidManifest.xml' else item['sha256']
        payload['member:' + name] = {'owner': item['owner'], 'sha256': sha}
    for name, item in classes.items():
        payload['class:' + name] = {'owner': item['owner'], 'sha256': item['sha256']}
    return payload


def inspect_candidate(apk, jars, work):
    members = apk_members(apk)
    dex_names = {n for n in members if re.fullmatch(r'classes[0-9]*\.dex', n)}
    require(dex_names == {'classes.dex'} | {'classes' + str(i) + '.dex' for i in range(2, len(dex_names) + 1)}, 'NONCANONICAL_DEX_SET')
    disassemble(apk, jars, work)
    classes, _, _ = parse_dex(work)
    with ZipFile(apk) as archive:
        raw = archive.read('AndroidManifest.xml')
    normalized, version = normalize_manifest(raw)
    tree = manifest_tree(raw)
    require(tree['attributes'].get('package', {}).get('value') == PACKAGE, 'PACKAGE_ID')
    launchers = []
    application = [n for n in tree['children'] if n['tag'] == 'application']
    require(len(application) == 1, 'APPLICATION_COUNT')
    for node in application[0]['children']:
        if node['tag'] not in ('activity', 'activity-alias'):
            continue
        for intent in node['children']:
            if intent['tag'] == 'intent-filter':
                names = {c['attributes'].get(ANDROID + 'name', {}).get('value') for c in intent['children']}
                if 'android.intent.action.MAIN' in names and 'android.intent.category.LAUNCHER' in names:
                    launchers.append(node['attributes'].get(ANDROID + 'name', {}).get('value'))
    require(launchers == [PACKAGE + '.Splash'], 'ONE_ORIGINAL_LAUNCHER_REQUIRED')
    actual = {'member:' + n: (digest(normalized) if n == 'AndroidManifest.xml' else v['sha256'])
              for n, v in members.items() if n not in SIGNATURE and not re.fullmatch(r'classes[0-9]*\.dex', n)}
    actual.update({'class:' + n: v['sha256'] for n, v in classes.items()})
    return actual, version


def remote_authority(repository, expected_head):
    """Read only exact commits from the configured origin; no branch mutation."""
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repository), *args], text=True).strip()
    origin = git('remote', 'get-url', 'origin')
    require(origin.removesuffix('.git') == 'https://github.com/mahfouzhassine8-ops/project-infinity', 'AUTHORITY_ORIGIN')
    remote = git('ls-remote', 'origin', 'refs/heads/' + AUTHORITY_BRANCH, PROTECTED_REF, COMBINED_PROTECTED_REF)
    refs = dict(reversed(line.split()) for line in remote.splitlines())
    require(refs.get(PROTECTED_REF) == PROTECTED_COMMIT, 'PROTECTED_LOCK_MOVED')
    require(refs.get(COMBINED_PROTECTED_REF) == COMBINED_PROTECTED_COMMIT, 'COMBINED_PROTECTED_LOCK_MOVED')
    require(refs.get('refs/heads/' + AUTHORITY_BRANCH) == expected_head, 'AUTHORITY_HEAD_RACE')
    require(git('rev-parse', 'HEAD') == expected_head, 'SOURCE_HEAD_MISMATCH')
    require(not git('status', '--porcelain', '--untracked-files=no'), 'DIRTY_TRACKED_SOURCE')
    from release_authority import AUTHORITY_PATH, verify_evidence
    exists = subprocess.run(['git','-C',str(repository),'cat-file','-e',expected_head+':'+AUTHORITY_PATH],
                            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode == 0
    path = AUTHORITY_PATH if exists else REGISTRY_PATH
    authority = json.loads(git('show', expected_head + ':' + path))
    if exists:
        verify_evidence(authority, lambda name: subprocess.check_output(['git','-C',str(repository),'show',expected_head+':'+name]))
        for component in authority['components'].values():
            require(git('cat-file','-t',component['approved_source'])=='commit','MISSING_COMPONENT_SOURCE_COMMIT')
        # Compare a changed authority with the actual preceding Git version,
        # never with a predecessor supplied by a component branch.
        change = git('log','-1','--format=%H','--',AUTHORITY_PATH)
        prior = subprocess.run(['git','-C',str(repository),'show',change+'^:'+AUTHORITY_PATH],
                               capture_output=True,text=True)
        if prior.returncode == 0:
            from release_authority import transition
            previous = json.loads(prior.stdout)
            require(digest(canonical(previous)) == authority.get('previous_authority_sha256'),'AUTHORITY_LINEAGE')
            transition(previous,authority,authority.get('target_owners',[]))
        else:
            require(authority['generation']==2 and authority.get('bootstrap_authorization')=='SCOPED-CORRECTION-AUTHORIZATION.json',
                    'SCOPED_BOOTSTRAP_REQUIRED')
    return validate_registry(authority)


def pre_sign(apk, jars, work, repository, expected_head, expected_generation):
    registry = remote_authority(repository, expected_head)
    actual, version = inspect_candidate(apk, jars, work)
    if registry.get('schema') == 2:
        validate_runtime_ownership(registry,work)
    result = verify_combination(registry, actual, version, expected_generation)
    require(remote_authority(repository, expected_head) == registry, 'AUTHORITY_CHANGED_DURING_AUDIT')
    result.update(status='PRE_SIGN_PAYLOAD_VERIFIED', unsigned_apk_sha256=file_sha(apk), source=expected_head,
                  registry_sha256=digest(canonical(registry)), versionCode=version)
    return result


def validate_runtime_ownership(registry,work):
    """Resolve current packaged dependencies, including verified OS outlines."""
    from review_ownership import class_owner,member_owner
    policy=load(HERE/'ownership-reviewed-roots.json')
    classes,calls,_=parse_dex(work)
    owners={}
    for path in Path(work).glob('*-smali/**/*.smali'):
        raw=path.read_text();name=raw.splitlines()[0].split()[-1]
        owners[name]=class_owner(name,raw,policy)
        require(registry['payload'].get('class:'+name,{}).get('owner')==owners[name],'FALSE_CLASS_OWNER:'+name)
    for key,row in registry['payload'].items():
        if key.startswith('member:'):require(member_owner(key[7:])==row['owner'],'FALSE_MEMBER_OWNER:'+key)
    for call in calls:
        target=call['to'];source=call['from']
        if target not in owners:continue
        require({owners[source],owners[target]}!={'INFINITY','COBRA'},'CROSS_FEATURE_IMPORT:'+source)
        if 'ExternalSyntheticApiModelOutline' in source:
            require(not ((call['member'] in classes[target]['methods'] and 'ExternalSyntheticApiModelOutline' not in target)
                         or not call['opcode'].startswith('invoke-')),'FEATURE_BEARING_OS_OUTLINE')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('apk', 'jars', 'work', 'repository', 'out'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--expected-generation', required=True, type=int)
    args = vars(parser.parse_args())
    out = args.pop('out')
    try:
        save(out, pre_sign(**args))
    except (ValueError, subprocess.CalledProcessError) as exc:
        save(out, {'status': 'SIGNING_REFUSED', 'reason': str(exc), 'signed_apk_produced': False})
        raise SystemExit('SIGNING REFUSED: ' + str(exc))
