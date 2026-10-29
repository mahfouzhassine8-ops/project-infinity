"""Host-only negative controls; synthetic data is never an approved component."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import assemble
import release_gate as gate
from inventory import CERT_SHA, OWNERS, PACKAGE, HERE, canonical, digest, parse_dex, validate_names


def fixture():
    payload = {
        'class:InfinityPlayer': {'owner': 'INFINITY', 'sha256': digest(b'Infinity420')},
        'member:infinity/settings': {'owner': 'INFINITY', 'sha256': digest(b'schema1')},
        'class:CobraPlayer': {'owner': 'COBRA', 'sha256': digest(b'Cobra420')},
        'member:cobra/settings': {'owner': 'COBRA', 'sha256': digest(b'schema1')},
        'member:AndroidManifest.xml': {'owner': 'MINIMAL_ANDROID_CONTRACT', 'sha256': digest(b'one icon')},
        'class:Chooser': {'owner': 'CHOOSER_SHELL', 'sha256': digest(b'unchanged chooser')},
    }
    registry = {'schema': 1, 'package': PACKAGE, 'certificate_sha256': CERT_SHA, 'generation': 1,
                'accepted_app_versionCode': 420, 'release_blockers': [], 'payload': payload, 'components': {}}
    for owner in OWNERS:
        registry['components'][owner] = {'version': 'fixture420', 'approved_source': 'a' * 40,
                                          'settings_schema': 'existing1', 'digest': gate.component_digest(payload, owner)}
    return registry


def actual(registry):
    return {k: v['sha256'] for k, v in registry['payload'].items()}


def update(registry, owner, number):
    result = copy.deepcopy(registry)
    result['generation'] += 1
    result['accepted_app_versionCode'] = number
    key = 'class:' + ('InfinityPlayer' if owner == 'INFINITY' else 'CobraPlayer')
    result['payload'][key]['sha256'] = digest((owner + str(number)).encode())
    result['components'][owner].update(version='fixture' + str(number), approved_source='b' * 40,
                                        digest=gate.component_digest(result['payload'], owner))
    return result


class ReleaseGateTests(unittest.TestCase):
    def test_successive_independent_owner_updates_preserve_other_owner(self):
        base = fixture()
        infinity = update(base, 'INFINITY', 421)
        gate.validate_transition(base, infinity, ['INFINITY'])
        gate.verify_combination(infinity, actual(infinity), 422, 2)
        cobra = update(infinity, 'COBRA', 422)
        gate.validate_transition(infinity, cobra, ['COBRA'])
        gate.verify_combination(cobra, actual(cobra), 423, 3)
        self.assertEqual(infinity['components']['INFINITY'], cobra['components']['INFINITY'])
        self.assertEqual(base['components']['COBRA'], infinity['components']['COBRA'])

    def test_higher_package_version_cannot_hide_stale_infinity(self):
        base = fixture()
        latest = update(update(base, 'INFINITY', 421), 'COBRA', 422)
        candidate = actual(latest)
        candidate['class:InfinityPlayer'] = actual(base)['class:InfinityPlayer']
        with self.assertRaisesRegex(gate.Rejected, 'STALE_OR_MUTATED_OWNER:INFINITY'):
            gate.verify_combination(latest, candidate, 999, 3)

    def test_higher_package_version_cannot_hide_stale_cobra(self):
        base = fixture()
        latest = update(update(base, 'COBRA', 421), 'INFINITY', 422)
        candidate = actual(latest)
        candidate['class:CobraPlayer'] = actual(base)['class:CobraPlayer']
        with self.assertRaisesRegex(gate.Rejected, 'STALE_OR_MUTATED_OWNER:COBRA'):
            gate.verify_combination(latest, candidate, 999, 3)

    def test_target_owner_cannot_change_other_owner_or_common_manifest(self):
        base = fixture()
        for target, forbidden in [('COBRA', 'INFINITY'), ('INFINITY', 'COBRA')]:
            for key in [k for k, v in base['payload'].items() if v['owner'] in (forbidden, 'MINIMAL_ANDROID_CONTRACT', 'CHOOSER_SHELL')]:
                with self.subTest(target=target, key=key):
                    proposed = update(base, target, 421)
                    owner = proposed['payload'][key]['owner']
                    proposed['payload'][key]['sha256'] = digest(b'unexpected callback or field change')
                    proposed['components'][owner]['digest'] = gate.component_digest(proposed['payload'], owner)
                    with self.assertRaisesRegex(gate.Rejected, 'CROSS_OWNER_MUTATION'):
                        gate.validate_transition(base, proposed, [target])

    def test_unowned_and_missing_payload_rejected(self):
        registry = fixture()
        for addition in (True, False):
            candidate = actual(registry)
            if addition:
                candidate['class:UnreviewedWorker'] = digest(b'new background writer')
            else:
                candidate.pop('class:CobraPlayer')
            with self.assertRaisesRegex(gate.Rejected, 'MISSING_OR_UNOWNED_MEMBER'):
                gate.verify_combination(registry, candidate, 421, 1)

    def test_package_and_registry_rollback_rejected(self):
        registry = fixture()
        for version in (419, 420, -1, True, 2100000001):
            with self.subTest(version=version), self.assertRaisesRegex(gate.Rejected, 'APP_ROLLBACK'):
                gate.verify_combination(registry, actual(registry), version, 1)
        with self.assertRaisesRegex(gate.Rejected, 'STALE_REGISTRY'):
            gate.verify_combination(registry, actual(registry), 421, 0)

    def test_settings_payload_rollback_rejected(self):
        registry = fixture()
        for key in ('member:cobra/settings', 'member:infinity/settings'):
            candidate = actual(registry)
            candidate[key] = digest(b'old schema')
            with self.assertRaisesRegex(gate.Rejected, 'STALE_OR_MUTATED_OWNER'):
                gate.verify_combination(registry, candidate, 421, 1)

    def test_unresolved_blocker_cannot_reach_key_read(self):
        with patch.object(assemble, 'pre_sign', side_effect=gate.Rejected('UNRESOLVED_RELEASE_BLOCKERS')), \
             patch.object(assemble.base64, 'b64decode') as key_read:
            with self.assertRaisesRegex(gate.Rejected, 'UNRESOLVED_RELEASE_BLOCKERS'):
                assemble.sign('apk', 'jars', 'work', 'repo', 'head', 1, 'sdk', 'out')
            key_read.assert_not_called()
        registry = fixture()
        registry['release_blockers'] = [{'id': 'shared lifecycle'}]
        with self.assertRaisesRegex(gate.Rejected, 'UNRESOLVED_RELEASE_BLOCKERS'):
            gate.verify_combination(registry, actual(registry), 421, 1)

    def test_component_claims_cannot_replace_fingerprints(self):
        registry = fixture()
        registry['components']['INFINITY']['version'] = 'newer label'
        candidate = actual(registry)
        candidate['class:InfinityPlayer'] = digest(b'old implementation')
        with self.assertRaisesRegex(gate.Rejected, 'STALE_OR_MUTATED_OWNER'):
            gate.verify_combination(registry, candidate, 421, 1)
        registry['components']['COBRA']['digest'] = digest(b'forged')
        with self.assertRaisesRegex(gate.Rejected, 'COMPONENT_DIGEST'):
            gate.validate_registry(registry)

    def test_owner_reclassification_and_shared_scope_rejected(self):
        registry = fixture()
        proposed = update(registry, 'COBRA', 421)
        proposed['payload']['class:InfinityPlayer']['owner'] = 'COBRA'
        for owner in ('INFINITY', 'COBRA'):
            proposed['components'][owner]['digest'] = gate.component_digest(proposed['payload'], owner)
        with self.assertRaisesRegex(gate.Rejected, 'CROSS_OWNER_MUTATION'):
            gate.validate_transition(registry, proposed, ['COBRA'])
        with self.assertRaisesRegex(gate.Rejected, 'SEPARATE_SHARED_SCOPE_REQUIRED'):
            gate.validate_transition(registry, proposed, ['MINIMAL_ANDROID_CONTRACT'])

    def test_duplicate_zip_and_traversal_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'bad.zip'
            for names in (['../x'], ['classes.dex', 'classes.dex']):
                with ZipFile(p, 'w') as z:
                    for name in names:
                        z.writestr(name, b'x')
                with ZipFile(p) as z, self.assertRaises(ValueError):
                    validate_names(z)

    def test_methods_with_and_without_flags_and_duplicate_class(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / 'classes-smali'
            folder.mkdir()
            body = '.class LX;\n.super Ljava/lang/Object;\n.method foo()V\n.registers 1\nreturn-void\n.end method\n'
            (folder / 'X.smali').write_text(body)
            classes, _, _ = parse_dex(root)
            self.assertEqual(list(classes['LX;']['methods']), ['foo()V'])
            (folder / 'Duplicate.smali').write_text(body)
            with self.assertRaisesRegex(ValueError, 'duplicate DEX class'):
                parse_dex(root)

    def test_remote_authority_head_race_is_rejected(self):
        with patch.object(gate.subprocess, 'check_output', side_effect=[
                'https://github.com/mahfouzhassine8-ops/project-infinity.git\n',
                gate.PROTECTED_COMMIT + '\t' + gate.PROTECTED_REF + '\n' +
                gate.COMBINED_PROTECTED_COMMIT + '\t' + gate.COMBINED_PROTECTED_REF + '\n' +
                gate.LATEST_PROTECTED_COMMIT + '\t' + gate.LATEST_PROTECTED_REF + '\n' +
                'b' * 40 + '\trefs/heads/' + gate.AUTHORITY_BRANCH + '\n']):
            with self.assertRaisesRegex(gate.Rejected, 'AUTHORITY_HEAD_RACE'):
                gate.remote_authority('repo', 'a' * 40)

    def test_latest_approved2103427_lock_is_required(self):
        with patch.object(gate.subprocess, 'check_output', side_effect=[
                'https://github.com/mahfouzhassine8-ops/project-infinity.git\n',
                gate.PROTECTED_COMMIT+'\t'+gate.PROTECTED_REF+'\n'+
                gate.COMBINED_PROTECTED_COMMIT+'\t'+gate.COMBINED_PROTECTED_REF+'\n'+
                'a'*40+'\trefs/heads/'+gate.AUTHORITY_BRANCH+'\n']):
            with self.assertRaisesRegex(gate.Rejected,'LATEST_APPROVED_LOCK_MOVED'):
                gate.remote_authority('repo','a'*40)


class IconResourceGateTests(unittest.TestCase):
    """Real pinned icon inputs; these policy fixtures are never owner bundles."""

    @classmethod
    def setUpClass(cls):
        import json
        import release_authority
        cls.authority = release_authority
        cls.guard = release_authority.launcher_icon_guard()
        cls.resources = cls.guard.resources_module()
        reference = cls.guard.HERE / 'reference'
        cls.original = {name: (reference / Path(name).name).read_bytes()
                        for name in cls.resources.BASELINE_SHA256}
        cls.generated = cls.resources.expected_resources(cls.original)
        cls.members = {**cls.original, **cls.generated}
        # Derive a synthetic policy fixture from the real immutable MIN member
        # vector.  Restore its icon inputs if this test runs after registration.
        previous = json.loads((HERE / 'release-authority.json').read_text())
        previous.pop('launcher_icon_exception', None)
        previous.update(generation=14, candidate_versionCode=2103429, last_issued_versionCode=2103428)
        previous['payload']['member:resources.arsc'] = {
            'owner': cls.guard.OWNER, 'sha256': cls.guard.ORIGINAL_TABLE_SHA256}
        for path in cls.guard.NEW_PATHS:
            previous['payload'].pop('member:' + path, None)
        previous['components'][cls.guard.OWNER] = {
            'approved_source': '9efaeabee45389b7c919ae1a3d88c394b1804173',
            'digest': cls.guard.ORIGINAL_COMPONENT_DIGEST, 'revision': 1,
            'settings_schema': 'owner-durability-v1', 'version': 'isolation-contract.1'}
        previous['experience_version_labels'] = {'INFINITY': 2103427, 'COBRA': 2103429}
        previous['payload']['member:assets/experience-component-updates.properties']['sha256'] = digest(
            b'infinity.last_updated_in=2103427\ncobra.last_updated_in=2103429\n')
        for owner in ('COBRA', 'CHOOSER_SHELL'):
            previous['components'][owner].update(version='policy-fixture29-' + owner, revision=1,
                approved_source='a' * 40, digest=gate.component_digest(previous['payload'], owner))
        cls.previous = previous
        proposed = copy.deepcopy(previous)
        proposed.update(generation=15, candidate_versionCode=2103430, last_issued_versionCode=2103429)
        proposed['experience_version_labels']['COBRA'] = 2103430
        proposed['payload']['member:assets/experience-component-updates.properties']['sha256'] = digest(
            b'infinity.last_updated_in=2103427\ncobra.last_updated_in=2103430\n')
        proposed['payload']['class:Lcom/projectinfinity/kodi/CobraComponent;']['sha256'] = digest(b'policy fixture30')
        for path, data in cls.generated.items():
            proposed['payload']['member:' + path] = {'owner': cls.guard.OWNER, 'sha256': digest(data)}
        for owner in ('COBRA', 'CHOOSER_SHELL', cls.guard.OWNER):
            proposed['components'][owner].update(version='policy-fixture30-' + owner,
                revision=previous['components'][owner]['revision'] + 1, approved_source='b' * 40,
                digest=gate.component_digest(proposed['payload'], owner))
        proposed['launcher_icon_exception'] = cls.guard.make_exception(proposed['payload'], cls.read)
        cls.proposed = proposed
        cls.targets = ['COBRA', 'CHOOSER_SHELL', cls.guard.OWNER]

    @staticmethod
    def read(name):
        return (HERE.parents[1] / name).read_bytes()

    def refresh_digest(self, proposed, owner=None):
        owner = owner or self.guard.OWNER
        proposed['components'][owner]['digest'] = gate.component_digest(proposed['payload'], owner)

    def write_apk(self, root, members):
        path = Path(root) / 'policy-fixture-resources.zip'
        with ZipFile(path, 'w') as z:
            for name, data in members.items():
                z.writestr(name, data)
        return path

    def test_exact_consolidated_icon_transition_and_fresh_resources(self):
        self.authority.transition(self.previous, self.proposed, self.targets)
        self.guard.verify_evidence(self.proposed, self.read)
        with tempfile.TemporaryDirectory() as tmp:
            report = self.guard.verify_actual_apk(self.write_apk(tmp, self.members), self.proposed)
        self.assertEqual(report['status'], 'PASS_EXACT_ICON_ONLY_TABLE_TRANSFORM')
        self.assertEqual(report['new_resource_ids'], 0)
        self.assertEqual(report['original_dark_assets'], 'ALL_BYTE_IDENTICAL')

    def test_missing_exception_never_authorizes_shared_target(self):
        proposed = copy.deepcopy(self.proposed)
        proposed.pop('launcher_icon_exception')
        with self.assertRaisesRegex(gate.Rejected, 'ICON_EXCEPTION_SCHEMA'):
            self.authority.transition(self.previous, proposed, self.targets)
        for targets in ([self.guard.OWNER], ['COBRA', self.guard.OWNER]):
            with self.subTest(targets=targets), self.assertRaisesRegex(gate.Rejected, 'ICON_CONSOLIDATED_TARGETS'):
                self.authority.transition(self.previous, self.proposed, targets)

    def test_classes_native_manifest_dark_and_non_icon_members_frozen(self):
        rows = self.previous['payload']
        keys = [next(k for k, v in rows.items() if v['owner'] == self.guard.OWNER and k.startswith('class:')),
                next(k for k in rows if k.endswith('.so')),
                'member:AndroidManifest.xml', 'member:res/n4.png', 'member:res/za.png',
                next(k for k in rows if k.startswith('member:res/') and k[7:] not in self.resources.BASELINE_SHA256)]
        for key in keys:
            owner = rows[key]['owner']
            reason = 'ICON_FROZEN_SHARED_PAYLOAD' if owner == self.guard.OWNER else 'CROSS_OWNER_MUTATION:' + owner
            with self.subTest(key=key, owner=owner), self.assertRaisesRegex(gate.Rejected, reason):
                proposed = copy.deepcopy(self.proposed)
                proposed['payload'][key]['sha256'] = digest(b'forbidden shared change')
                self.refresh_digest(proposed, owner)
                self.authority.transition(self.previous, proposed, self.targets)

    def test_shared_removal_reclassification_and_extra_path_rejected(self):
        key = 'member:res/n4.png'
        for reclassify in (False, True):
            with self.subTest(reclassify=reclassify), self.assertRaisesRegex(
                    gate.Rejected, 'ICON_REMOVED_OR_RECLASSIFIED_SHARED_PAYLOAD'):
                proposed = copy.deepcopy(self.proposed)
                if reclassify:
                    proposed['payload'][key]['owner'] = 'CHOOSER_SHELL'
                    self.refresh_digest(proposed, 'CHOOSER_SHELL')
                else:
                    proposed['payload'].pop(key)
                self.refresh_digest(proposed)
                self.authority.transition(self.previous, proposed, self.targets)
        proposed = copy.deepcopy(self.proposed)
        proposed['payload']['member:res/unreviewed.xml'] = {'owner': self.guard.OWNER, 'sha256': digest(b'extra')}
        self.refresh_digest(proposed)
        with self.assertRaisesRegex(gate.Rejected, 'ICON_ONLY_NEW_MEMBERS'):
            self.authority.transition(self.previous, proposed, self.targets)

    def test_exception_is_single_release_and_keeps_settings_and_contract(self):
        for kind in ('version', 'settings', 'contract'):
            proposed = copy.deepcopy(self.proposed)
            if kind == 'version':
                proposed['candidate_versionCode'] += 1
                reason = 'ICON_EXACT_RELEASE_TRANSITION'
            elif kind == 'settings':
                proposed['components'][self.guard.OWNER]['settings_schema'] = 'not-authorized'
                reason = 'ICON_SETTINGS_SCHEMA_FROZEN'
            else:
                key = next(iter(proposed['protected_contract']))
                proposed['protected_contract'][key] = digest(b'changed protected contract')
                reason = 'PROTECTED_CONTRACT'
            with self.subTest(kind=kind), self.assertRaisesRegex(gate.Rejected, reason):
                self.authority.transition(self.previous, proposed, self.targets)

    def test_exception_does_not_trust_unbound_or_replaced_sources(self):
        for kind in ('missing', 'escape', 'authorization', 'old-table'):
            proposed = copy.deepcopy(self.proposed)
            proof = proposed['launcher_icon_exception']
            if kind == 'missing':
                proof['source_inputs'].pop(self.guard.PREFIX + 'resources.py')
                reason = 'ICON_MISSING_SOURCE_BINDING'
            elif kind == 'escape':
                proof['source_inputs'][self.guard.PREFIX + 'reference/../outside.png'] = digest(b'x')
                reason = 'ICON_SOURCE_SCOPE'
            elif kind == 'authorization':
                proof['authorization_sha256'] = digest(b'other authorization')
                reason = 'ICON_AUTHORIZATION_PREIMAGE'
            else:
                proof['original_resource_table_sha256'] = digest(b'other old table')
                reason = 'ICON_ORIGINAL_TABLE'
            with self.subTest(kind=kind), self.assertRaisesRegex(gate.Rejected, reason):
                self.authority.transition(self.previous, proposed, self.targets)
        name = self.guard.PREFIX + 'resources.py'
        with self.assertRaisesRegex(gate.Rejected, 'ICON_REVIEWED_SOURCE_CHANGED'):
            self.guard.verify_evidence(self.proposed,
                lambda path: b'unreviewed source' if path == name else self.read(path))

    def test_fresh_table_and_artwork_cannot_be_reapproved_by_changing_hash(self):
        for name in ('resources.arsc', self.guard.NEW_PATHS[0]):
            members = dict(self.members)
            raw = bytearray(members[name]); raw[-1] ^= 1; members[name] = bytes(raw)
            proposed = copy.deepcopy(self.proposed)
            proof = proposed['launcher_icon_exception']
            if name == 'resources.arsc':
                proof['candidate_resource_table_sha256'] = digest(members[name])
            else:
                proof['added_members'][name] = digest(members[name])
            proposed['payload']['member:' + name]['sha256'] = digest(members[name])
            self.refresh_digest(proposed)
            with tempfile.TemporaryDirectory() as tmp, self.subTest(name=name):
                apk = self.write_apk(tmp, members)
                with self.assertRaisesRegex(gate.Rejected, 'ICON_RESOURCE_TRANSFORM'):
                    self.guard.verify_actual_apk(apk, proposed)

    def test_fresh_icon_failure_precedes_any_signing_key_read(self):
        members = dict(self.members)
        raw = bytearray(members['resources.arsc']); raw[-1] ^= 1
        members['resources.arsc'] = bytes(raw)
        proposed = copy.deepcopy(self.proposed)
        proposed['launcher_icon_exception']['candidate_resource_table_sha256'] = digest(raw)
        proposed['payload']['member:resources.arsc']['sha256'] = digest(raw)
        self.refresh_digest(proposed)
        with tempfile.TemporaryDirectory() as tmp:
            apk = self.write_apk(tmp, members)
            with patch.object(gate, 'remote_authority', return_value=proposed), \
                 patch.object(gate, 'inspect_candidate', return_value=(actual(proposed), 2103430)), \
                 patch.object(gate, 'validate_runtime_ownership'), \
                 patch.object(assemble.base64, 'b64decode') as key_read:
                with self.assertRaisesRegex(gate.Rejected, 'ICON_RESOURCE_TRANSFORM'):
                    assemble.sign(apk, 'jars', 'work', 'repo', 'head', 15, 'sdk', Path(tmp) / 'out')
                key_read.assert_not_called()
                self.assertFalse((Path(tmp) / 'out').exists())

    def test_density_correction_changes_only_two_pinned_existing_adaptive_xmls(self):
        # Selected 430 -> 431 resource-inflation correction: preserve the exact
        # signed430 predecessor, permit its two adaptive XMLs only, and recheck
        # the final bytes against the independently pinned original artwork.
        previous = copy.deepcopy(self.proposed)
        for name, pin in self.guard.SIGNED30_ICON_SHA256.items():
            previous['payload']['member:' + name]['sha256'] = pin
        previous['payload']['member:resources.arsc']['sha256'] = self.guard.SIGNED30_TABLE_SHA256
        self.refresh_digest(previous)
        self.assertEqual(previous['components'][self.guard.OWNER]['digest'], self.guard.SIGNED30_COMPONENT_DIGEST)
        previous['launcher_icon_exception'] = self.guard.make_exception(previous['payload'], self.read)
        proposed = copy.deepcopy(previous)
        proposed.update(generation=16, candidate_versionCode=2103431, last_issued_versionCode=2103430)
        proposed['experience_version_labels']['COBRA'] = 2103431
        proposed['payload']['member:assets/experience-component-updates.properties']['sha256'] = digest(
            b'infinity.last_updated_in=2103427\ncobra.last_updated_in=2103431\n')
        proposed['payload']['class:Lcom/projectinfinity/kodi/CobraComponent;']['sha256'] = digest(b'policy fixture31')
        for name in self.guard.ADAPTIVE_PATHS:
            proposed['payload']['member:' + name]['sha256'] = digest(self.generated[name])
        for owner in self.targets:
            proposed['components'][owner].update(version='policy-fixture31-' + owner,
                revision=previous['components'][owner]['revision'] + 1, approved_source='c' * 40,
                digest=gate.component_digest(proposed['payload'], owner))
        proposed['launcher_icon_exception'] = self.guard.make_exception(proposed['payload'], self.read)
        self.authority.transition(previous, proposed, self.targets)
        with tempfile.TemporaryDirectory() as tmp:
            report = self.guard.verify_actual_apk(self.write_apk(tmp, self.members), proposed)
        self.assertEqual(report['status'], 'PASS_EXACT_ICON_ONLY_TABLE_TRANSFORM')
        self.assertEqual(report['table_sha256'], self.guard.SIGNED30_TABLE_SHA256)
        for kind in ('table', 'density-png', 'original-dark', 'new-member', 'one-xml', 'generation', 'issued-version'):
            bad = copy.deepcopy(proposed); prior = copy.deepcopy(previous)
            reason = 'ICON_DENSITY_CORRECTION_EXACT_XML_DELTA'
            if kind == 'table':
                bad['payload']['member:resources.arsc']['sha256'] = digest(b'unreviewed table')
            elif kind == 'density-png':
                bad['payload']['member:res/infinity_launcher_light_mdpi.png']['sha256'] = digest(b'unreviewed density PNG')
            elif kind == 'original-dark':
                bad['payload']['member:res/n4.png']['sha256'] = digest(b'unreviewed dark artwork')
            elif kind == 'new-member':
                bad['payload']['member:res/another.xml'] = {'owner': self.guard.OWNER, 'sha256': digest(b'new')}
                reason = 'ICON_DENSITY_CORRECTION_NO_MEMBER_CHANGE'
            elif kind == 'one-xml':
                name = self.guard.ADAPTIVE_PATHS[0]
                bad['payload']['member:' + name]['sha256'] = self.guard.SIGNED30_ICON_SHA256[name]
            elif kind == 'generation':
                prior['generation'] = 14; bad['generation'] = 15
                reason = 'ICON_CORRECTION_GENERATION'
            else:
                bad['last_issued_versionCode'] = 2103429
                reason = 'ICON_CORRECTION_ISSUED_VERSION'
            self.refresh_digest(bad)
            bad['launcher_icon_exception'] = self.guard.make_exception(bad['payload'], self.read)
            with self.subTest(kind=kind), self.assertRaisesRegex(gate.Rejected, reason):
                self.authority.transition(prior, bad, self.targets)


if __name__ == '__main__':
    unittest.main()
