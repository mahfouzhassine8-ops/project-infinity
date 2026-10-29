"""One reviewed launcher-resource exception, never a shared-code permission.

The existing resource owner is retained.  The only shared-owner transition this
module permits is the explicitly authorized 2103429 -> 2103430 icon addition.
The original typed manifest, every shared class/native member, and every old
artwork member remain frozen.  The signer re-derives the icon resource result
from the original table and retained source artwork before reading any key.
"""
import hashlib
import importlib.util
import re
from pathlib import Path
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PREFIX = 'repairs/cobra-next-from-2103427/icon/'
AUTHORIZATION = 'repairs/cobra-next-from-2103427/APPROVED-INFINITY-ICON-LIGHT-DARK-20261029.md'
AUTHORIZATION_SHA256 = 'cb82b470cd19fc8f91d74355ffc0404dea62bd63c94a5a3f5561be27496ead93'
OWNER = 'MINIMAL_ANDROID_CONTRACT'
ORIGINAL_TABLE_SHA256 = '1b8c1788a5a86242635277f063ebdce6b82ed12eafe3cfdf331b902c8eb7e616'
ORIGINAL_COMPONENT_DIGEST = '7443a8645f40e82eac07f6ec732a9dc231f1974416ea3632b5af5d74816f78fb'
ICON_IDS = [0x7f080000, 0x7f080001]
NEW_PATHS = tuple('res/infinity_launcher_light_' + density + '.png'
                  for density in ('mdpi', 'hdpi', 'xhdpi', 'xxhdpi', 'xxxhdpi')) + (
    'res/infinity_launcher_light_v26.xml',
    'res/infinity_launcher_light_v33.xml',
)
FIELDS = {
    'schema', 'authorization', 'authorization_sha256', 'original_resource_table_sha256',
    'original_minimal_component_digest', 'icon_resource_ids', 'candidate_resource_table_sha256',
    'added_members', 'source_inputs',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, reason):
    # Use the signer's one refusal type; do not downgrade a resource failure.
    from release_gate import require as checked
    checked(condition, reason)


def resources_module():
    spec = importlib.util.spec_from_file_location('_infinity_launcher_icon_resources', HERE / 'resources.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate(authority):
    proof = authority.get('launcher_icon_exception')
    require(isinstance(proof, dict) and set(proof) == FIELDS, 'ICON_EXCEPTION_SCHEMA')
    require(proof['schema'] == 1 and proof['authorization'] == AUTHORIZATION, 'ICON_EXCEPTION_AUTHORIZATION')
    require(proof['authorization_sha256'] == AUTHORIZATION_SHA256, 'ICON_AUTHORIZATION_PREIMAGE')
    require(proof['original_resource_table_sha256'] == ORIGINAL_TABLE_SHA256, 'ICON_ORIGINAL_TABLE')
    require(proof['original_minimal_component_digest'] == ORIGINAL_COMPONENT_DIGEST, 'ICON_ORIGINAL_OWNER')
    require(proof['icon_resource_ids'] == ICON_IDS, 'ICON_RESOURCE_IDS')
    require(isinstance(proof['added_members'], dict) and set(proof['added_members']) == set(NEW_PATHS),
            'ICON_EXACT_NEW_PATHS')
    require(isinstance(proof['source_inputs'], dict), 'ICON_SOURCE_BINDING_SCHEMA')
    pins = [proof['authorization_sha256'], proof['candidate_resource_table_sha256'],
            *proof['added_members'].values(), *proof['source_inputs'].values()]
    require(all(isinstance(pin, str) and re.fullmatch('[0-9a-f]{64}', pin) for pin in pins), 'ICON_SHA256_PINS')
    require(proof['candidate_resource_table_sha256'] != ORIGINAL_TABLE_SHA256, 'ICON_TABLE_NOT_UPDATED')
    expected_sources = {PREFIX + n for n in ('resources.py', 'release_guard.py', 'reference/resources.arsc')}
    source_names = set(proof['source_inputs'])
    require(expected_sources <= source_names, 'ICON_MISSING_SOURCE_BINDING')
    require(all(name in expected_sources or (name.startswith(PREFIX + 'reference/') and
                '..' not in name.split('/') and name.endswith(('.png', '.xml'))) for name in source_names),
            'ICON_SOURCE_SCOPE')
    expected = {'resources.arsc': proof['candidate_resource_table_sha256'], **proof['added_members']}
    for name, pin in expected.items():
        require(authority['payload'].get('member:' + name) == {'owner': OWNER, 'sha256': pin},
                'ICON_AUTHORITY_PAYLOAD:' + name)
    return proof


def transition(previous, proposed, targets):
    proof = validate(proposed)
    require(previous['candidate_versionCode'] == 2103429 and proposed['candidate_versionCode'] == 2103430,
            'ICON_EXACT_RELEASE_TRANSITION')
    require(set(targets) == {'COBRA', 'CHOOSER_SHELL', OWNER}, 'ICON_CONSOLIDATED_TARGETS')
    require(previous.get('launcher_icon_exception') is None, 'ICON_EXCEPTION_ALREADY_USED')
    require(previous['components'][OWNER]['digest'] == ORIGINAL_COMPONENT_DIGEST, 'ICON_PREVIOUS_OWNER')
    require(proposed['components'][OWNER]['settings_schema'] == previous['components'][OWNER]['settings_schema'],
            'ICON_SETTINGS_SCHEMA_FROZEN')
    old = {k: v for k, v in previous['payload'].items() if v['owner'] == OWNER}
    new = {k: v for k, v in proposed['payload'].items() if v['owner'] == OWNER}
    table = 'member:resources.arsc'
    require(old.get(table) == {'owner': OWNER, 'sha256': ORIGINAL_TABLE_SHA256}, 'ICON_PREVIOUS_TABLE')
    require(set(old) <= set(new), 'ICON_REMOVED_OR_RECLASSIFIED_SHARED_PAYLOAD')
    require(set(new) - set(old) == {'member:' + n for n in NEW_PATHS}, 'ICON_ONLY_NEW_MEMBERS')
    require({k for k in old if old[k] != new[k]} == {table}, 'ICON_FROZEN_SHARED_PAYLOAD')
    # This also freezes AndroidManifest.xml, every shared class and native file,
    # all original dark images, and all unrelated resource member bytes.
    return proof


def verify_evidence(authority, read):
    proof = validate(authority)
    require(sha(read(AUTHORIZATION)) == proof['authorization_sha256'], 'ICON_AUTHORIZATION_CHANGED')
    for name, pin in proof['source_inputs'].items():
        require(sha(read(name)) == pin, 'ICON_REVIEWED_SOURCE_CHANGED:' + name)
    require(sha(read(PREFIX + 'reference/resources.arsc')) == ORIGINAL_TABLE_SHA256, 'ICON_ORIGINAL_TABLE_SOURCE')
    return True


def make_exception(payload, read):
    """Construct evidence from reviewed local inputs; registration still gates it."""
    paths = {PREFIX + 'resources.py', PREFIX + 'release_guard.py'}
    paths.update(str(p.relative_to(REPO)) for p in (HERE / 'reference').rglob('*') if p.is_file())
    proof = dict(
        schema=1, authorization=AUTHORIZATION, authorization_sha256=sha(read(AUTHORIZATION)),
        original_resource_table_sha256=ORIGINAL_TABLE_SHA256,
        original_minimal_component_digest=ORIGINAL_COMPONENT_DIGEST, icon_resource_ids=ICON_IDS,
        candidate_resource_table_sha256=payload['member:resources.arsc']['sha256'],
        added_members={name: payload['member:' + name]['sha256'] for name in NEW_PATHS},
        source_inputs={name: sha(read(name)) for name in sorted(paths)},
    )
    return proof


def verify_actual_apk(apk, authority):
    proof = validate(authority)
    module = resources_module()
    require(set(module.NEW_PATHS) == set(NEW_PATHS), 'ICON_GENERATOR_PATH_BUDGET')
    original = (HERE / 'reference/resources.arsc').read_bytes()
    require(sha(original) == ORIGINAL_TABLE_SHA256, 'ICON_ORIGINAL_TABLE_SOURCE')
    with ZipFile(apk) as archive:
        members = {name: archive.read(name) for name in archive.namelist()
                   if name == 'resources.arsc' or name == 'AndroidManifest.xml' or name.startswith('res/')}
    require(sha(members['resources.arsc']) == proof['candidate_resource_table_sha256'], 'ICON_ACTUAL_TABLE')
    for name, pin in proof['added_members'].items():
        require(sha(members[name]) == pin, 'ICON_ACTUAL_ARTWORK:' + name)
    # Retained original members are already hash-equal to the exact preceding
    # authority by transition() and actual payload verification.  Use those bytes
    # plus the independently pinned old table to re-derive only the icon change.
    baseline = {name: raw for name, raw in members.items() if name not in NEW_PATHS}
    baseline['resources.arsc'] = original
    try:
        return module.verify_resources(members, baseline)
    except (ValueError, AssertionError, KeyError, TypeError) as exc:
        require(False, 'ICON_RESOURCE_TRANSFORM:' + str(exc))
