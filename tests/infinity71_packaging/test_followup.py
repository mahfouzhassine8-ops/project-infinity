#!/usr/bin/env python3
"""Independent packaging/signing gates. Fixtures are NOT installable Kodi engines.

Requires INFINITY_KODI_SOURCE, INFINITY_TEST_DEX, ANDROID_HOME, INFINITY_ANDROID_JAR.
The SDK is real; fake native bytes make these integrity tests, not device tests.
All private signing fixtures live only in a TemporaryDirectory and are deleted.
"""
from pathlib import Path
import base64
import itertools
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'scripts'))
import infinity71 as m

SECRET_NAMES = ('INFINITY_KEYSTORE_B64', 'INFINITY_STORE_PASSWORD',
                'INFINITY_KEY_PASSWORD', 'INFINITY_KEY_ALIAS')


def run(args, env=None):
    return subprocess.run([str(a) for a in args], env=env, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)


def rewrite_apk(source, target, changes):
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(target, 'w') as dst:
        for name in src.namelist():
            data = src.read(name)
            dst.writestr(name, changes[name](data) if name in changes else data)


class FollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='infinity-signing-fixtures-')
        cls.root = Path(cls.temp.name)
        cls.sdk = Path(os.environ['ANDROID_HOME']) / 'build-tools/34.0.0'
        cls.source = Path(os.environ['INFINITY_KODI_SOURCE'])
        cls.env = {k: v for k, v in os.environ.items() if k not in SECRET_NAMES}
        manifest = cls.root / 'AndroidManifest.xml'
        manifest.write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android"
package="com.projectinfinity.kodi" android:versionCode="1" android:versionName="TEST-NOT-INSTALLABLE">
<uses-sdk android:minSdkVersion="21" android:targetSdkVersion="34"/>
<application android:extractNativeLibs="true"><activity android:name=".Main" android:exported="false"/></application>
</manifest>''')
        resource_apk = cls.root / 'resources.apk'
        result = run([cls.sdk / 'aapt2', 'link', '--manifest', manifest,
                      '-I', os.environ['INFINITY_ANDROID_JAR'], '-o', resource_apk])
        if result.returncode:
            raise RuntimeError('Android resource fixture failed: ' + result.stderr)
        cls.base = cls.root / 'fixture-base.apk'
        with zipfile.ZipFile(resource_apk) as src, zipfile.ZipFile(cls.base, 'w') as dst:
            for name in src.namelist():
                dst.writestr(name, src.read(name))
            dst.write(os.environ['INFINITY_TEST_DEX'], 'classes.dex')
            dst.writestr('lib/arm64-v8a/libkodi.so', b'NOT-A-RUNNABLE-ENGINE: SIGNING-TEST-ONLY')
            dst.write(cls.source / 'addons/skin.estuary/xml/VideoOSD.xml', m.SKIN + 'xml/VideoOSD.xml')
        cls.inventory = cls.root / 'engine.json'
        m.record_engine(cls.base, cls.inventory, 'non-installable-audit-fixture')
        cls.unsigned = cls.root / 'fixture-unsigned.apk'
        m.overlay(cls.base, cls.inventory, cls.unsigned)
        cls.key = cls.root / 'fixture.keystore'
        cls.password = 'local-fixture-password-not-a-production-secret'
        result = run(['keytool', '-genkeypair', '-noprompt', '-keystore', cls.key,
                      '-storepass', cls.password, '-keypass', cls.password,
                      '-alias', 'fixture', '-keyalg', 'RSA', '-keysize', '2048',
                      '-validity', '2', '-dname', 'CN=Temporary Signing Test'], cls.env)
        if result.returncode:
            raise RuntimeError('Temporary signing key creation failed')
        cls.stable_env = dict(cls.env, INFINITY_KEYSTORE_B64=base64.b64encode(cls.key.read_bytes()).decode(),
                              INFINITY_STORE_PASSWORD=cls.password, INFINITY_KEY_PASSWORD=cls.password,
                              INFINITY_KEY_ALIAS='fixture')

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def sign(self, name, env):
        out = self.root / (name + '.apk')
        result = run(['bash', REPO / 'scripts/sign-infinity71.sh', self.unsigned, out], env)
        return out, result

    def test_valid_contract_includes_main_and_three_companions(self):
        m.check_apk_contract(self.base)

    def test_bad_companion_native_method_is_rejected(self):
        bad = self.root / 'bad-volume-method.apk'
        rewrite_apk(self.base, bad, {'classes.dex': lambda b: b.replace(b'_onVolumeChanged', b'_onVolumeChangeX')})
        with self.assertRaisesRegex(ValueError, 'XBMCSettingsContentObserver'):
            m.check_apk_contract(bad)

    def test_missing_surface_class_is_rejected(self):
        bad = self.root / 'bad-surface-class.apk'
        rewrite_apk(self.base, bad, {'classes.dex': lambda b: b.replace(
            b'Lcom/projectinfinity/kodi/XBMCMainView;', b'Lcom/projectinfinity/kodi/XBMCMainVieX;')})
        with self.assertRaisesRegex(ValueError, 'XBMCMainView'):
            m.check_apk_contract(bad)

    def test_standalone_verifier_rejects_wrong_metadata(self):
        original = json.loads(self.inventory.read_text())
        for key, value in (('schema', 2), ('bridge_version', 2), ('package', 'org.xbmc.kodi'),
                           ('kodi_sha', 'wrong'), ('source_patch_sha256', '0' * 64)):
            with self.subTest(field=key):
                data = dict(original); data[key] = value
                bad = self.root / ('bad-' + key + '.json'); bad.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    m.verify_overlay(self.unsigned, bad)

    def test_missing_button_is_rejected_even_when_assets_are_present(self):
        bad = self.root / 'missing-button.apk'
        original_osd = (self.source / 'addons/skin.estuary/xml/VideoOSD.xml').read_bytes()
        rewrite_apk(self.unsigned, bad, {m.SKIN + 'xml/VideoOSD.xml': lambda _: original_osd})
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            m.verify_overlay(bad, self.inventory)

    def test_wrong_button_action_is_rejected(self):
        bad = self.root / 'wrong-action.apk'
        rewrite_apk(self.unsigned, bad, {m.SKIN + 'xml/VideoOSD.xml': lambda b: b.replace(
            b'ActivateWindow(1199)', b'ActivateWindow(9999)')})
        with self.assertRaisesRegex(ValueError, 'approved connection'):
            m.verify_overlay(bad, self.inventory)

    def test_duplicate_lock_button_is_rejected(self):
        bad = self.root / 'duplicate-button.apk'
        rewrite_apk(self.unsigned, bad, {m.SKIN + 'xml/VideoOSD.xml': lambda b: b.replace(
            b'</controls>', m.LOCK_BUTTON.encode() + b'</controls>', 1)})
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            m.verify_overlay(bad, self.inventory)

    def test_malformed_osd_is_rejected(self):
        bad = self.root / 'malformed-osd.apk'
        rewrite_apk(self.unsigned, bad, {m.SKIN + 'xml/VideoOSD.xml': lambda _: b'<broken'})
        with self.assertRaisesRegex(ValueError, 'malformed'):
            m.verify_overlay(bad, self.inventory)

    def test_all_fourteen_partial_signing_configurations_fail_closed(self):
        for mask in itertools.product((False, True), repeat=4):
            if sum(mask) in (0, 4):
                continue
            with self.subTest(mask=mask):
                env = dict(self.env)
                env.update({name: self.stable_env[name] for name, enabled in zip(SECRET_NAMES, mask) if enabled})
                out, result = self.sign('partial-' + ''.join(str(int(b)) for b in mask), env)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Incomplete stable signing configuration', result.stderr)
                self.assertFalse(out.exists())
                self.assertNotIn(self.password, result.stdout + result.stderr)

    def test_no_secrets_produces_verified_explicit_test_signature(self):
        out, result = self.sign('ephemeral', self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        m.verify_overlay(out, self.inventory)
        report = out.with_suffix('.signing.txt').read_text()
        self.assertIn('Signing mode: ephemeral-test-only', report)
        self.assertIn('Verified using v2 scheme (APK Signature Scheme v2): true', report)

    def test_same_supplied_key_keeps_certificate_for_two_packages(self):
        certs = []
        for index in (1, 2):
            out, result = self.sign('stable-' + str(index), self.stable_env)
            self.assertEqual(result.returncode, 0, result.stderr)
            m.verify_overlay(out, self.inventory)
            report = out.with_suffix('.signing.txt').read_text()
            self.assertIn('Signing mode: stable-secret', report)
            certs.append(re.search(r'certificate SHA-256 digest: ([0-9a-f]+)', report).group(1))
        self.assertEqual(certs[0], certs[1])
        self.assertEqual(len(certs[0]), 64)

    def test_invalid_supplied_key_never_falls_back_to_a_test_signature(self):
        env = dict(self.stable_env, INFINITY_KEYSTORE_B64='this is not base64')
        out, result = self.sign('invalid-stable', env)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(out.exists())
        self.assertNotIn('new test certificate', result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
