"""Real composed payload -> actual C++ parser/signature/source verification."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

import compose_firstparty
import module_bundle as bundle

ROOT=Path(__file__).parent


class ModuleBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace=tempfile.TemporaryDirectory()
        cls.base=Path(cls.workspace.name)
        sources=Path(os.environ['INFINITY_SIGNED407_SOURCES'])
        cls.composed=cls.base/'composed'
        compose_firstparty.compose(sources,cls.composed)
        cls.private=cls.base/'test-only.pem';cls.public=cls.base/'test-only.pub'
        subprocess.run(['openssl','genpkey','-algorithm','RSA','-pkeyopt','rsa_keygen_bits:2048','-out',cls.private],check=True,capture_output=True)
        subprocess.run(['openssl','pkey','-in',cls.private,'-pubout','-out',cls.public],check=True,capture_output=True)
        cls.verifier=cls.base/'native-verifier'
        subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',
            str(ROOT/'verify_module_bundle.cpp'),str(ROOT/'isolated-native/InfinityModuleManifest.cpp'),
            '-lcrypto','-o',cls.verifier],check=True,capture_output=True)

    @classmethod
    def tearDownClass(cls):cls.workspace.cleanup()

    def setUp(self):
        self.work=tempfile.TemporaryDirectory(dir=self.base)
        self.root=Path(self.work.name)/'addons'
        shutil.copytree(self.composed,self.root)

    def tearDown(self):self.work.cleanup()

    def sign(self):
        bundle.prepare(self.root)
        manifest=self.root/bundle.CC/bundle.MANIFEST
        subprocess.run(['openssl','dgst','-sha256','-sign',self.private,'-out',str(manifest)+'.sig',manifest],check=True,capture_output=True)

    def verify(self,key=None):
        return subprocess.run([self.verifier,self.root,key or self.public],text=True,capture_output=True)

    def test_actual_composed_payload_is_accepted_by_unchanged_native_core(self):
        self.sign();result=self.verify()
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('protocol=1',result.stdout);self.assertIn('entries=11',result.stdout)
        payload,files=bundle.build(self.root)
        self.assertEqual(payload,(self.root/bundle.CC/bundle.MANIFEST).read_bytes())
        self.assertGreater(len(files),60)
        before={p.relative_to(self.composed):p.read_bytes() for p in self.composed.rglob('*') if p.is_file()}
        self.assertTrue(all((self.root/p).read_bytes()==raw for p,raw in before.items()))

    def test_original_key_rejects_isolated_test_signer_and_no_archives_are_created(self):
        self.sign();result=self.verify(ROOT/'ORIGINAL-INFINITY-PUBLIC-KEY.pem')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('signature_rejected',result.stderr)
        output=Path(self.work.name)/'release'
        with self.assertRaisesRegex(ValueError,'Original permanent RSA'):bundle.archive(self.root,output)
        self.assertFalse(output.exists())

    def test_changed_source_and_signature_are_rejected_without_signed_payload_rewrite(self):
        self.sign();path=self.root/bundle.CC/'common.py';raw=path.read_bytes();path.write_bytes(raw+b'\n')
        self.assertNotEqual(self.verify().returncode,0)
        path.write_bytes(raw)
        signature=self.root/bundle.CC/(bundle.MANIFEST+'.sig');raw=signature.read_bytes()
        signature.write_bytes(bytes([raw[0]^1])+raw[1:])
        self.assertNotEqual(self.verify().returncode,0)

    def test_missing_mandatory_code_unregistered_entry_or_unsupported_version_refuse_build(self):
        path=self.root/bundle.CC/'module_contract.py';raw=path.read_bytes();path.unlink()
        with self.assertRaisesRegex(ValueError,'Missing mandatory'):bundle.build(self.root)
        path.write_bytes(raw)
        addon=self.root/bundle.CC/'addon.xml';original=addon.read_text()
        addon.write_text(original.replace('library="default.py"','library="unverified.py"',1))
        with self.assertRaisesRegex(ValueError,'Unverified registered entry'):bundle.build(self.root)
        version='version="'+compose_firstparty.VERSION+'"'
        self.assertEqual(original.count(version),1)
        addon.write_text(original.replace(version,'version="0.3.bad.40"',1))
        with self.assertRaisesRegex(ValueError,'Invalid Command Center'):bundle.build(self.root)

    def test_unsafe_symlink_bytecode_and_unowned_addon_are_never_packaged(self):
        for name in ('unlisted.pyc','Cobra.py','unsafe name.py'):
            p=self.root/bundle.CC/name;p.write_bytes(b'unreviewed')
            with self.assertRaises(ValueError):bundle.build(self.root)
            p.unlink()
        link=self.root/bundle.CC/'linked.py';link.symlink_to(self.root/bundle.CC/'common.py')
        with self.assertRaisesRegex(ValueError,'Linked'):bundle.build(self.root)
        link.unlink();(self.root/'unrelated.provider').mkdir()
        with self.assertRaisesRegex(ValueError,'Exactly four'):bundle.build(self.root)

    def test_native_limits_and_generation_overwrite_are_enforced(self):
        for field,value in [('FILE_LIMIT',1),('FILE_BYTES',1),('TOTAL_BYTES',1),('PAYLOAD_BYTES',1)]:
            with mock.patch.object(bundle,field,value),self.assertRaises(ValueError):bundle.prepare(self.root)
            self.assertFalse((self.root/bundle.CC/bundle.MANIFEST).exists())
        self.sign()
        manifest=self.root/bundle.CC/bundle.MANIFEST;before=manifest.read_bytes()
        with self.assertRaisesRegex(ValueError,'must not be overwritten'):bundle.prepare(self.root)
        self.assertEqual(manifest.read_bytes(),before)


if __name__=='__main__':unittest.main(verbosity=2)
