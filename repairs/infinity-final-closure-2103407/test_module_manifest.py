"""Run the actual portable C++ verifier; test keys never enter production trust."""
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).parent
CC = 'script.infinity.commandcenter'
REQUIRED = ('addon.xml', 'checkpoint_runtime.py', 'common.py', 'context.py',
            'default.py', 'module_contract.py', 'persistence_participant.py', 'plugin.py', 'service.py')


class ModuleManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory()
        cls.work = Path(cls.workspace.name)
        driver = cls.work / 'verify.cpp'
        driver.write_text(r'''#include "InfinityModuleManifest.h"
#include <fstream>
#include <iostream>
#include <iterator>
int main(int argc, char** argv) {
  if (argc != 5) return 2;
  std::ifstream key(argv[2]);
  std::string pem((std::istreambuf_iterator<char>(key)), std::istreambuf_iterator<char>());
  InfinityModuleManifest::Verified verified;
  std::string failure;
  if (!InfinityModuleManifest::Verify(argv[1],pem,verified,failure)) {
    std::cout << "REJECTED\t" << failure << "\n"; return 1;
  }
  const auto owner=InfinityModuleManifest::EntryOwner(verified,argv[3],argv[4]);
  std::cout << verified.packageVersion << "\t" << verified.protocolApi << "\t"
            << verified.manifestSha256 << "\t" << owner << "\n";
  return owner.empty() ? 3 : 0;
}
''')
        cls.binary = cls.work / 'verify'
        subprocess.run(['g++', '-std=c++14', '-Wall', '-Wextra', '-Werror',
                        '-I', str(ROOT / 'isolated-native'), str(driver),
                        str(ROOT / 'isolated-native/InfinityModuleManifest.cpp'),
                        '-lcrypto', '-o', str(cls.binary)], check=True)
        for prefix in ('trusted-test', 'other-test'):
            subprocess.run(['openssl', 'genpkey', '-algorithm', 'RSA', '-pkeyopt',
                            'rsa_keygen_bits:2048', '-out', str(cls.work / (prefix + '.private.pem'))],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['openssl', 'pkey', '-in', str(cls.work / (prefix + '.private.pem')),
                            '-pubout', '-out', str(cls.work / (prefix + '.public.pem'))], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.workspace.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=self.work)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in REQUIRED:
            path = self.root / CC / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(('controlled fixture: ' + name + '\n').encode())
        self.payload = self.root / CC / 'INFINITY-MODULES.v1'
        self.signature = self.payload.with_name(self.payload.name + '.sig')
        self.write_manifest()

    def write_manifest(self, version='0.3.5.40', protocol=1, change=None):
        lines = ['INFINITY-MODULES/1', 'package\t' + version, 'protocol\t' + str(protocol)]
        for cap in sorted(('checkpoint-v1', 'dialog-reflow-v1', 'first-party-modules-v1', 'title-actions-v1')):
            lines.append('capability\t' + cap)
        for name in sorted(REQUIRED):
            path = CC + '/' + name
            lines.append('file\t' + hashlib.sha256((self.root / path).read_bytes()).hexdigest() + '\t' + path)
        for path in sorted((CC + '/plugin.py', CC + '/service.py')):
            owner = 'command_center' if path.endswith('/service.py') else 'command_center_client'
            lines.append('entry\t' + owner + '\t' + path)
        text = '\n'.join(lines) + '\n'
        self.payload.write_text(change(text) if change else text)
        self.sign()

    def sign(self, key='trusted-test'):
        subprocess.run(['openssl', 'dgst', '-sha256', '-sign', str(self.work / (key + '.private.pem')),
                        '-out', str(self.signature), str(self.payload)], check=True)

    def verify(self, entry=CC + '/service.py', addon=CC, key='trusted-test'):
        return subprocess.run([str(self.binary), str(self.root), str(self.work / (key + '.public.pem')),
                               entry, addon], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_real_signature_and_independent_package_protocol(self):
        for version in ('0.3.5.40', '0.3.5.41', '1.0.0'):
            self.write_manifest(version=version)
            result = self.verify()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(result.stdout.startswith(version + '\t1\t'))
            self.assertIn(hashlib.sha256(self.payload.read_bytes()).hexdigest(), result.stdout)
        self.assertEqual(self.verify(entry=CC + '/plugin.py').returncode, 0)

    def test_wrong_signature_key_or_unsigned_payload_is_rejected(self):
        self.assertEqual(self.verify(key='other-test').returncode, 1)
        self.sign('other-test')
        self.assertEqual(self.verify().returncode, 1)
        self.sign()
        self.payload.write_bytes(self.payload.read_bytes().replace(b'0.3.5.40', b'0.3.5.41'))
        self.assertEqual(self.verify().returncode, 1)
        self.signature.write_bytes(b'')
        self.assertEqual(self.verify().returncode, 1)

    def test_changed_missing_and_replaced_source_rejected_on_each_admission(self):
        path = self.root / CC / 'common.py'
        original = path.read_bytes()
        self.assertEqual(self.verify().returncode, 0)
        path.write_bytes(original + b'unreviewed code')
        self.assertEqual(self.verify().returncode, 1)
        path.unlink()
        self.assertEqual(self.verify().returncode, 1)
        path.write_bytes(original)
        self.assertEqual(self.verify().returncode, 0)

    def test_unknown_protocol_capability_and_owner_are_rejected_even_if_signed(self):
        self.write_manifest(protocol=2)
        self.assertEqual(self.verify().returncode, 1)
        self.write_manifest(change=lambda x:x.replace('title-actions-v1', 'unreviewed-feature'))
        self.assertEqual(self.verify().returncode, 1)
        self.write_manifest(change=lambda x:x.replace('entry\tcommand_center_client', 'entry\tcommand_center'))
        self.assertEqual(self.verify().returncode, 1)

    def test_cobra_external_addons_and_entry_identity_mismatch_never_admitted(self):
        self.assertEqual(self.verify(addon='script.infinity.cobra').returncode, 3)
        self.assertEqual(self.verify(addon='script.infinity.uirepair').returncode, 3)
        self.assertEqual(self.verify(entry=CC + '/common.py').returncode, 3)
        self.write_manifest(change=lambda x:x.replace(CC + '/common.py', 'plugin.video.provider/common.py'))
        self.assertEqual(self.verify().returncode, 1)
        self.write_manifest(change=lambda x:x.replace(CC + '/common.py', CC + '/cobra/common.py'))
        self.assertEqual(self.verify().returncode, 1)

    def test_traversal_duplicate_unsorted_and_control_bytes_rejected(self):
        for replacement in ('../common.py', './common.py', 'x//common.py'):
            self.write_manifest(change=lambda x:x.replace(CC + '/common.py', CC + '/' + replacement))
            self.assertEqual(self.verify().returncode, 1)
        def duplicate(text):
            line = next(x for x in text.splitlines() if x.startswith('file\t'))
            return text.replace(line + '\n', line + '\n' + line + '\n')
        self.write_manifest(change=duplicate)
        self.assertEqual(self.verify().returncode, 1)
        self.write_manifest(change=lambda x:x.replace('package\t', 'package\x00\t'))
        self.assertEqual(self.verify().returncode, 1)
        self.write_manifest(change=lambda x:x.rstrip('\n'))
        self.assertEqual(self.verify().returncode, 1)

    def test_symlink_file_and_parent_directory_rejected(self):
        source = self.root / CC / 'common.py'
        other = self.root / 'outside.py'
        other.write_bytes(source.read_bytes())
        source.unlink()
        source.symlink_to(other)
        self.assertEqual(self.verify().returncode, 1)
        source.unlink()
        source.write_bytes(other.read_bytes())
        saved = self.root / 'saved-cc'
        (self.root / CC).rename(saved)
        (self.root / CC).symlink_to(saved, target_is_directory=True)
        self.assertEqual(self.verify().returncode, 1)

    def test_fifo_source_is_rejected_without_waiting_for_a_writer(self):
        source = self.root / CC / 'common.py'
        source.unlink()
        os.mkfifo(source)
        result = subprocess.run([str(self.binary), str(self.root), str(self.work / 'trusted-test.public.pem'),
                                 CC + '/service.py', CC], text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=3)
        self.assertEqual(result.returncode, 1)

    def test_source_and_payload_limits_and_required_owner_fail_closed(self):
        source = self.root / CC / 'common.py'
        source.write_bytes(b'x' * (4 * 1024 * 1024 + 1))
        self.write_manifest()
        self.assertEqual(self.verify().returncode, 1)
        source.write_bytes(b'')
        self.write_manifest()
        self.assertEqual(self.verify().returncode, 0, 'Empty package __init__ or source may be honestly hashed')
        self.write_manifest(change=lambda x:x + 'x' * (128 * 1024))
        self.assertEqual(self.verify().returncode, 1)
        self.write_manifest(change=lambda x:'\n'.join(line for line in x.splitlines() if not line.startswith('entry\tcommand_center\t'))+'\n')
        self.assertEqual(self.verify().returncode, 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
