"""Host-only negative controls; synthetic data is never an approved component."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import assemble
import release_gate as gate
from inventory import CERT_SHA, OWNERS, PACKAGE, canonical, digest, parse_dex, validate_names


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


if __name__ == '__main__':
    unittest.main()
