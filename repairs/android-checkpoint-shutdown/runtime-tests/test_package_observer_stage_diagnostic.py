#!/usr/bin/env python3
"""Mutation controls for the isolated diagnostic's APK preservation boundary."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

SPEC = importlib.util.spec_from_file_location('observer_stage_packager',
    Path(__file__).with_name('package_observer_stage_diagnostic.py'))
PACK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACK)


class PayloadBoundary(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.entries = {
            'AndroidManifest.xml': b'unchanged binary manifest',
            'classes.dex': b'unchanged compiled production Java',
            'classes10.dex': b'unchanged additional compiled Java',
            PACK.ENGINE: b'old ARM64 engine',
            'lib/arm64-v8a/libpython3.11.so': b'preserved Python runtime',
            'assets/addons/skin.infinity.diggz/addon.xml': b'custom Infinity skin',
            'assets/addons/service.diggz/service.py': b'preserved addon and service',
            'resources.arsc': b'preserved Android resources',
            'META-INF/services/retained-provider': b'ordinary META-INF payload',
            'META-INF/MANIFEST.MF': b'old signature manifest',
            'META-INF/CERT.SF': b'old signature digest',
            'META-INF/CERT.RSA': b'old signature',
        }
        self.parent = self.write('parent.apk', self.entries)

    def write(self, name, entries):
        path = self.root / name
        with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for key, value in entries.items():
                archive.writestr(key, value)
        return path

    def candidate(self, changes=None, remove=()):
        entries = dict(self.entries)
        entries[PACK.ENGINE] = b'new live-stage ARM64 engine'
        for key in ('META-INF/MANIFEST.MF', 'META-INF/CERT.SF', 'META-INF/CERT.RSA'):
            entries[key] = b'regenerated signature metadata'
        entries.update(changes or {})
        for name in remove:
            del entries[name]
        return self.write('candidate.apk', entries)

    def test_exact_engine_only_payload_passes_with_regenerated_signature_contents(self):
        proof = PACK.payload_identity(self.parent, self.candidate())
        self.assertEqual(proof['changed_payload_entries'], [PACK.ENGINE])
        self.assertEqual(len(proof['signature_metadata_entries_regenerated']), 3)
        self.assertTrue(proof['apk_entry_names_unchanged'])
        self.assertEqual(set(proof['java_dex_sha256']), {'classes.dex', 'classes10.dex'})

    def test_manifest_mutation_fails(self):
        with self.assertRaisesRegex(RuntimeError, 'Unexpected APK payload mutation'):
            PACK.payload_identity(self.parent, self.candidate({'AndroidManifest.xml': b'changed version or component'}))

    def test_java_byte_mutation_fails(self):
        with self.assertRaisesRegex(RuntimeError, 'Unexpected APK payload mutation'):
            PACK.payload_identity(self.parent, self.candidate({'classes.dex': b'rebuilt Java'}))

    def test_skin_mutation_fails(self):
        with self.assertRaisesRegex(RuntimeError, 'Unexpected APK payload mutation'):
            PACK.payload_identity(self.parent, self.candidate({'assets/addons/skin.infinity.diggz/addon.xml': b'replaced skin'}))

    def test_addon_mutation_fails(self):
        with self.assertRaisesRegex(RuntimeError, 'Unexpected APK payload mutation'):
            PACK.payload_identity(self.parent, self.candidate({'assets/addons/service.diggz/service.py': b'disabled service'}))

    def test_other_native_library_mutation_fails(self):
        with self.assertRaisesRegex(RuntimeError, 'Unexpected APK payload mutation'):
            PACK.payload_identity(self.parent, self.candidate({'lib/arm64-v8a/libpython3.11.so': b'changed runtime'}))

    def test_non_signature_meta_inf_is_protected(self):
        with self.assertRaisesRegex(RuntimeError, 'Unexpected APK payload mutation'):
            PACK.payload_identity(self.parent, self.candidate({'META-INF/services/retained-provider': b'changed provider'}))

    def test_added_entry_fails(self):
        with self.assertRaisesRegex(RuntimeError, 'entry-name set changed'):
            PACK.payload_identity(self.parent, self.candidate({'unexpected.txt': b'extra payload'}))

    def test_removed_entry_fails(self):
        with self.assertRaisesRegex(RuntimeError, 'entry-name set changed'):
            PACK.payload_identity(self.parent, self.candidate(remove=('resources.arsc',)))

    def test_signature_name_change_fails(self):
        with self.assertRaisesRegex(RuntimeError, 'entry-name set changed'):
            PACK.payload_identity(self.parent, self.candidate({'META-INF/OTHER.RSA': b'new signer metadata'}, remove=('META-INF/CERT.RSA',)))

    def test_unchanged_engine_cannot_be_reported_as_diagnostic(self):
        with self.assertRaisesRegex(RuntimeError, 'Unexpected APK payload mutation'):
            PACK.payload_identity(self.parent, self.candidate({PACK.ENGINE: self.entries[PACK.ENGINE]}))

    def test_duplicate_candidate_entry_fails(self):
        candidate = self.candidate()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(candidate, 'a') as archive:
                archive.writestr('classes.dex', b'duplicate dex')
        with self.assertRaisesRegex(RuntimeError, 'Duplicate APK entry names'):
            PACK.payload_identity(self.parent, candidate)

    def test_duplicate_parent_entry_fails_before_rewrite(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(self.parent, 'a') as archive:
                archive.writestr('AndroidManifest.xml', b'duplicate manifest')
        engine = self.root / 'engine.so';engine.write_bytes(b'new engine')
        with self.assertRaisesRegex(RuntimeError, 'Duplicate APK entry names'):
            PACK.rewrite_engine(self.parent, engine, self.root / 'unsigned.apk')

    def test_rewrite_preserves_actual_uncompressed_entries_and_signature_scope(self):
        engine = self.root / 'engine.so';engine.write_bytes(b'new engine')
        unsigned = self.root / 'unsigned.apk'
        PACK.rewrite_engine(self.parent, engine, unsigned)
        with zipfile.ZipFile(unsigned) as archive:
            self.assertEqual(set(archive.namelist()), {name for name in self.entries if not PACK.SIGNATURE.fullmatch(name)})
            for name in archive.namelist():
                self.assertEqual(archive.read(name), engine.read_bytes() if name == PACK.ENGINE else self.entries[name])

    def make_saved_rc05_proof(self):
        inputs = self.root / 'rc05-inputs';root = inputs / 'essential-fold-test';root.mkdir(parents=True)
        apk = root / PACK.RC05_APK;apk.write_bytes(self.parent.read_bytes())
        sha = PACK.sha(apk)
        engine_sha = PACK.hashlib.sha256(self.entries[PACK.ENGINE]).hexdigest()
        proof = dict(apk_sha256=sha, file=PACK.RC05_APK, native_source_commit=PACK.RC05_NATIVE_SOURCE,
            android_source_commit=PACK.RC05_SOURCE, native_packaged_sha256=engine_sha, same_permanent_signer=PACK.SIGNER,
            package='com.projectinfinity.kodi', version_code=2103377, version_name='1.0.9-Essential-First-TEST4-RC05',
            apk_deliverable=False, final_lock_authorized=False, java_regressions_verified=True,
            java_producer_adapters_verified=True, signed_test2_baseline_preserved=True, signed_test3_baseline_preserved=True)
        PACK.save(root / 'ESSENTIAL-FIRST-SIGNED-TEST-PRESERVATION.json', proof)
        regression = {key: dict(tests=count, failures=0, errors=0, skipped=0)
                      for key, count in (('original_274', 274), ('new_save_cases', 26), ('completion_race_cases', 8))}
        regression['original_test_sources_unchanged'] = True
        PACK.save(root / 'JAVA-REGRESSION-VERIFICATION.json', regression)
        return inputs, sha, engine_sha

    def test_saved_308_proof_reused_only_with_exact_apk_and_source(self):
        inputs, sha, engine_sha = self.make_saved_rc05_proof()
        with patch.object(PACK, 'RC05_APK_SHA', sha), patch.object(PACK, 'RC05_ENGINE_SHA', engine_sha):
            self.assertEqual(PACK.verify_rc05(inputs), inputs / 'essential-fold-test' / PACK.RC05_APK)
            proof_path = inputs / 'essential-fold-test/ESSENTIAL-FIRST-SIGNED-TEST-PRESERVATION.json'
            proof = PACK.load(proof_path);proof['android_source_commit'] = 'f' * 40;PACK.save(proof_path, proof)
            with self.assertRaisesRegex(RuntimeError, 'source/engine identity mismatch'):
                PACK.verify_rc05(inputs)

    def test_failed_saved_test_cannot_be_reused(self):
        inputs, sha, engine_sha = self.make_saved_rc05_proof()
        path = inputs / 'essential-fold-test/JAVA-REGRESSION-VERIFICATION.json'
        proof = PACK.load(path);proof['completion_race_cases']['failures'] = 1;PACK.save(path, proof)
        with patch.object(PACK, 'RC05_APK_SHA', sha), patch.object(PACK, 'RC05_ENGINE_SHA', engine_sha):
            with self.assertRaisesRegex(RuntimeError, 'Saved Java regression failure'):
                PACK.verify_rc05(inputs)

    def test_apk_bit_change_invalidates_saved_308_association(self):
        inputs, sha, engine_sha = self.make_saved_rc05_proof()
        apk = inputs / 'essential-fold-test' / PACK.RC05_APK
        with apk.open('ab') as stream:stream.write(b'changed after test proof')
        with patch.object(PACK, 'RC05_APK_SHA', sha), patch.object(PACK, 'RC05_ENGINE_SHA', engine_sha):
            with self.assertRaisesRegex(RuntimeError, 'Saved RC05 APK digest mismatch'):
                PACK.verify_rc05(inputs)

    def test_unpinned_native_is_fail_closed(self):
        with patch.object(PACK, 'NATIVE_RUN', 0):
            with self.assertRaisesRegex(RuntimeError, 'have not been pinned'):
                PACK.pinned_native()

    def certificate(self, digests):
        return ('Verified using v2 scheme (APK Signature Scheme v2): true\n'
                'Verified using v3 scheme (APK Signature Scheme v3): true\n' +
                ''.join('Signer #'+str(index)+' certificate SHA-256 digest: '+digest+'\n'
                        for index, digest in enumerate(digests, 1)))

    def android_output(self, certificate):
        def output(*args):
            if str(args[0]).endswith('apksigner'):
                return certificate
            if str(args[0]).endswith('aapt'):
                return ("package: name='com.projectinfinity.kodi' versionCode='2103377' "
                        "versionName='1.0.9-Essential-First-TEST4-RC05'\napplication-label:'Infinity'\n")
            return ''
        return output

    def test_exact_permanent_single_signer_is_required(self):
        with patch.dict(os.environ, {'ANDROID_HOME': str(self.root)}), \
                patch.object(PACK, 'tool_output', side_effect=self.android_output(self.certificate([PACK.SIGNER]))):
            PACK.verify_android(self.parent, self.root, 'exact-cert')
        self.assertTrue((self.root / 'exact-cert-certificate.txt').exists())

    def test_expected_digest_in_unrelated_text_does_not_approve_wrong_signer(self):
        certificate = self.certificate(['f' * 64]) + 'Unrelated expected digest: ' + PACK.SIGNER + '\n'
        with patch.dict(os.environ, {'ANDROID_HOME': str(self.root)}), \
                patch.object(PACK, 'tool_output', side_effect=self.android_output(certificate)):
            with self.assertRaisesRegex(RuntimeError, 'Wrong or multiple permanent signers'):
                PACK.verify_android(self.parent, self.root, 'wrong-cert')

    def test_additional_signer_is_rejected(self):
        with patch.dict(os.environ, {'ANDROID_HOME': str(self.root)}), \
                patch.object(PACK, 'tool_output', side_effect=self.android_output(self.certificate([PACK.SIGNER, 'f' * 64]))):
            with self.assertRaisesRegex(RuntimeError, 'Wrong or multiple permanent signers'):
                PACK.verify_android(self.parent, self.root, 'multiple-cert')


if __name__ == '__main__':
    unittest.main(verbosity=2)
