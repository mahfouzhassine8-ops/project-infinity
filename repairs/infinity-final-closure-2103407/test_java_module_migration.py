"""Real adapter/JCA algorithm on disposable host fixtures; never Android PASS."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import compose_firstparty
import module_bundle as bundle
import module_dex

ROOT=Path(__file__).parent


class JavaModuleMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace=tempfile.TemporaryDirectory();cls.base=Path(cls.workspace.name)
        cls.sources=Path(os.environ['INFINITY_SIGNED407_SOURCES'])
        cls.java=Path(os.environ['JAVA_HOME'])/'bin/java';javac=cls.java.with_name('javac')
        cls.private=cls.base/'test-only.pem';cls.public=cls.base/'test-only.pub'
        subprocess.run(['openssl','genpkey','-algorithm','RSA','-pkeyopt','rsa_keygen_bits:2048','-out',cls.private],check=True,capture_output=True)
        subprocess.run(['openssl','pkey','-in',cls.private,'-pubout','-out',cls.public],check=True,capture_output=True)
        cls.composed=cls.base/'composed';compose_firstparty.compose(cls.sources,cls.composed)
        bundle.prepare(cls.composed)
        manifest=cls.composed/bundle.CC/bundle.MANIFEST
        subprocess.run(['openssl','dgst','-sha256','-sign',cls.private,'-out',str(manifest)+'.sig',manifest],check=True,capture_output=True)
        original=subprocess.check_output(['openssl','pkey','-pubin','-in',ROOT/'ORIGINAL-INFINITY-PUBLIC-KEY.pem','-outform','DER'])
        test=subprocess.check_output(['openssl','pkey','-pubin','-in',cls.public,'-outform','DER'])
        literal=lambda raw:'new byte[]{'+','.join(str(v if v<128 else v-256) for v in raw)+'}'
        source=module_dex.source();cls.original_source=source
        if source.count(literal(original))!=1:raise ValueError('Immutable production key insertion changed')
        # Exactly one isolated key literal changes in the host-only copy.
        source=source.replace(literal(original),literal(test),1)
        file=cls.base/'InfinityInstalledCheckpointInstaller.java';file.write_text(source)
        cls.classes=cls.base/'classes';cls.classes.mkdir()
        files=sorted((ROOT/'host-java').rglob('*.java'))
        result=subprocess.run([javac,'--release','8','-g:none','-Xlint:all,-options','-Werror','-d',cls.classes,file,*files],text=True,capture_output=True)
        if result.returncode:raise RuntimeError(result.stdout+result.stderr)
        cls.verifier=cls.base/'native-verifier'
        subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',ROOT/'verify_module_bundle.cpp',
            ROOT/'isolated-native/InfinityModuleManifest.cpp','-lcrypto','-o',cls.verifier],check=True,capture_output=True)

    @classmethod
    def tearDownClass(cls):cls.workspace.cleanup()

    def setUp(self):
        self.work=tempfile.TemporaryDirectory(dir=self.base);self.path=Path(self.work.name)
        self.storage=self.path/'storage';self.addons=self.storage/'.kodi/addons'
        shutil.copytree(self.sources,self.addons)
        self.assets=self.path/'assets';shutil.copytree(self.composed,self.assets/'addons')
        self.sentinel=self.storage/'.kodi/userdata/profile-database-sentinel';self.sentinel.parent.mkdir(parents=True)
        self.sentinel.write_bytes(b'existing-profile-database-no-reset')
        self.extra=self.addons/bundle.CC/'unrecognized-preserved.txt';self.extra.write_bytes(b'preserve unknown original file')

    def tearDown(self):self.work.cleanup()

    def call(self,mode=None,fail=None):
        env=dict(os.environ)
        if fail is not None:env['INFINITY_HOST_FAIL_RENAME']=str(fail)
        return subprocess.run([self.java,'-cp',self.classes,'com.projectinfinity.kodi.Main',self.storage,self.assets,*([mode] if mode else [])],env=env,text=True,capture_output=True)

    def snapshot(self):
        return {p.relative_to(self.storage).as_posix():('link',os.readlink(p)) if p.is_symlink() else ('file',p.read_bytes())
                for p in self.storage.rglob('*') if p.is_file() or p.is_symlink()}

    def assert_migrated(self):
        result=subprocess.run([self.verifier,self.addons,self.public],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(self.sentinel.read_bytes(),b'existing-profile-database-no-reset')
        self.assertEqual(self.extra.read_bytes(),b'preserve unknown original file')
        for p in (self.assets/'addons').rglob('*'):
            if p.is_file():self.assertEqual((self.addons/p.relative_to(self.assets/'addons')).read_bytes(),p.read_bytes())

    def test_actual_jca_initial_migration_preserves_profile_unknown_files_and_old_code_backup(self):
        original=(self.addons/bundle.CC/'plugin.py').read_bytes()
        result=self.call();self.assertEqual(result.returncode,0,result.stderr);self.assertIn('VERIFIED_VERSION=0.3.5.40',result.stdout)
        self.assert_migrated()
        self.assertEqual((self.addons/'.infinity-module-baseline407'/bundle.CC/'plugin.py').read_bytes(),original)
        self.assertEqual((self.addons/'script.infinity.watchedbridge/service.py').read_bytes(),(self.sources/'script.infinity.watchedbridge/service.py').read_bytes())

    def test_interrupted_atomic_write_and_signature_only_generation_resume_without_reset(self):
        result=self.call(fail=3);self.assertNotEqual(result.returncode,0)
        self.assertIn('Injected host atomic-write failure',result.stderr)
        marker=self.addons/bundle.CC/bundle.MANIFEST
        self.assertFalse(marker.exists())
        shutil.copyfile(self.assets/'addons'/bundle.CC/(bundle.MANIFEST+'.sig'),self.addons/bundle.CC/(bundle.MANIFEST+'.sig'))
        result=self.call();self.assertEqual(result.returncode,0,result.stderr);self.assert_migrated()
        # Actual Android Os.open reports ErrnoException for a missing file.
        # A committed same-generation pair may recover only from its exact APK.
        (self.addons/bundle.CC/'plugin.py').unlink()
        result=self.call();self.assertEqual(result.returncode,0,result.stderr);self.assert_migrated()

    def test_unrecognized_installed_code_or_backup_refuses_before_any_write(self):
        p=self.addons/bundle.CC/'common.py';p.write_bytes(p.read_bytes()+b'\n# unknown local change\n')
        before=self.snapshot();result=self.call();self.assertNotEqual(result.returncode,0)
        self.assertIn('Unrecognized installed source',result.stderr);self.assertEqual(self.snapshot(),before)
        shutil.copyfile(self.sources/bundle.CC/'common.py',p)
        p=self.addons/'.infinity-module-baseline407'/bundle.CC/'plugin.py';p.parent.mkdir(parents=True);p.write_bytes(b'unknown backup')
        before=self.snapshot();result=self.call();self.assertNotEqual(result.returncode,0)
        self.assertIn('Unrecognized baseline backup',result.stderr);self.assertEqual(self.snapshot(),before)

    def test_wrong_asset_signature_or_linked_installed_code_never_changes_profile(self):
        sig=self.assets/'addons'/bundle.CC/(bundle.MANIFEST+'.sig');original=sig.read_bytes();sig.write_bytes(bytes([original[0]^1])+original[1:])
        before=self.snapshot();result=self.call();self.assertNotEqual(result.returncode,0);self.assertEqual(self.snapshot(),before)
        sig.write_bytes(original);p=self.addons/bundle.CC/'common.py';p.unlink();p.symlink_to(self.sources/bundle.CC/'common.py')
        before=self.snapshot();result=self.call();self.assertNotEqual(result.returncode,0)
        self.assertIn('Linked installed source',result.stderr);self.assertEqual(self.snapshot(),before)

    def test_complete_newer_signed_generation_is_reused_and_incomplete_newer_never_downgraded(self):
        self.assertEqual(self.call().returncode,0)
        addon=self.addons/bundle.CC/'addon.xml';addon.write_text(addon.read_text().replace('version="0.3.5.40"','version="0.3.5.41"',1))
        # Build from the exact signed files, without the deliberately preserved
        # unrelated old-code/backup members in this installed runtime tree.
        newer=self.path/'newer';shutil.copytree(self.composed,newer)
        (newer/bundle.CC/'addon.xml').write_bytes(addon.read_bytes())
        (newer/bundle.CC/bundle.MANIFEST).unlink();(newer/bundle.CC/(bundle.MANIFEST+'.sig')).unlink()
        bundle.prepare(newer)
        manifest=newer/bundle.CC/bundle.MANIFEST
        subprocess.run(['openssl','dgst','-sha256','-sign',self.private,'-out',str(manifest)+'.sig',manifest],check=True,capture_output=True)
        for name in (bundle.MANIFEST,bundle.MANIFEST+'.sig'):shutil.copyfile(newer/bundle.CC/name,self.addons/bundle.CC/name)
        before=self.snapshot();result=self.call();self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('VERIFIED_VERSION=0.3.5.41',result.stdout);self.assertEqual(self.snapshot(),before)
        (self.addons/bundle.CC/'plugin.py').unlink();before=self.snapshot();result=self.call()
        self.assertNotEqual(result.returncode,0);self.assertIn('must not be downgraded',result.stderr);self.assertEqual(self.snapshot(),before)

    def test_other_context_and_wrong_root_preserve_original_ownership_boundary(self):
        for mode,message in [('other','Legacy verifier stand-in'),('wrong-root','Unowned module root')]:
            before=self.snapshot();result=self.call(mode=mode)
            self.assertNotEqual(result.returncode,0);self.assertIn(message,result.stderr);self.assertEqual(self.snapshot(),before)

    def test_originally_signed_but_unsupported_protocol_and_path_fail_before_code_writes(self):
        manifest=self.assets/'addons'/bundle.CC/bundle.MANIFEST;original=manifest.read_bytes()
        for raw in (original.replace(b'protocol\t1\n',b'protocol\t2\n',1),
                    original.replace(b'script.infinity.commandcenter/addon.xml',b'script.infinity.commandcenter/../addon.xml',1),
                    original.replace(b'entry\tcommand_center\t',b'entry\tcommand_center_client\t',1)):
            manifest.write_bytes(raw)
            subprocess.run(['openssl','dgst','-sha256','-sign',self.private,'-out',str(manifest)+'.sig',manifest],check=True,capture_output=True)
            before=self.snapshot();result=self.call();self.assertNotEqual(result.returncode,0,result.stderr);self.assertEqual(self.snapshot(),before)


if __name__=='__main__':unittest.main(verbosity=2)
