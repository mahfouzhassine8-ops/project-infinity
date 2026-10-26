"""Python imports through the real signed-manifest native ABI (isolated test key)."""
import ctypes
import hashlib
import importlib
import importlib.util
import os
from pathlib import Path
import py_compile
import subprocess
import sys
import tempfile
import unittest

import test_module_manifest as fixture

ROOT, CC = fixture.ROOT, fixture.CC


class ModuleContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory()
        cls.work = Path(cls.workspace.name)
        cls.key = cls.work/'key.pem'
        subprocess.run(['openssl','genpkey','-algorithm','RSA','-pkeyopt','rsa_keygen_bits:2048','-out',str(cls.key)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        public = subprocess.check_output(['openssl','pkey','-in',str(cls.key),'-pubout']).decode()
        stubs = cls.work/'filesystem'; stubs.mkdir()
        (stubs/'SpecialProtocol.h').write_text('#pragma once\n#include <string>\nclass CSpecialProtocol { public: static std::string TranslatePath(const std::string&); };\n')
        (cls.work/'paths.cpp').write_text('''#include "filesystem/SpecialProtocol.h"
#include <cstdlib>
std::string CSpecialProtocol::TranslatePath(const std::string& p) {
  const char* r=std::getenv("INFINITY_ISOLATED_TEST_ROOT");
  return std::string(r?r:"")+(p=="special://home/addons/"?"/":"/missing/");
}
''')
        source=(ROOT/'isolated-native/InfinityInstalledModules.cpp').read_text()
        actual=(ROOT/'ORIGINAL-INFINITY-PUBLIC-KEY.pem').read_text()
        assert source.count(actual)==1
        isolated=source.replace(actual,public,1)
        assert isolated.replace(public,actual,1)==source
        (cls.work/'test-key-only.cpp').write_text(isolated)
        cls.library_path=cls.work/'test-key-only.so'
        subprocess.run(['g++','-std=c++14','-Wall','-Wextra','-Werror','-fPIC','-shared',
                        '-I',str(cls.work),'-I',str(ROOT/'isolated-native'),str(cls.work/'paths.cpp'),
                        str(cls.work/'test-key-only.cpp'),str(ROOT/'isolated-native/InfinityModuleManifest.cpp'),
                        '-lcrypto','-pthread','-o',str(cls.library_path)],check=True)
        cls.library=ctypes.CDLL(str(cls.library_path))

    @classmethod
    def tearDownClass(cls):
        cls.workspace.cleanup()

    def setUp(self):
        temp=tempfile.TemporaryDirectory(dir=self.work); self.addCleanup(temp.cleanup)
        self.addons=Path(temp.name); self.cc=self.addons/CC; self.cc.mkdir()
        os.environ['INFINITY_ISOLATED_TEST_ROOT']=str(self.addons)
        self.addCleanup(os.environ.pop,'INFINITY_ISOLATED_TEST_ROOT',None)
        for name in fixture.REQUIRED:
            (self.cc/name).write_text('# controlled module fixture\n')
        for name,text in {'_infinity_guarded_probe.py':'value="verified"\n',
                          '_infinity_unowned.py':'value="unrelated"\n'}.items():
            (self.cc/name).write_text(text)
        spec=importlib.util.spec_from_file_location('isolated_module_contract',ROOT/'isolated-python/module_contract.py')
        self.module=importlib.util.module_from_spec(spec); spec.loader.exec_module(self.module)
        native=self.library.InfinityCommandCenterIdentityV1
        native.argtypes=(ctypes.c_char_p,ctypes.POINTER(ctypes.c_char),ctypes.c_size_t,
                         ctypes.POINTER(ctypes.c_char),ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint))
        native.restype=ctypes.c_int
        self.module._native_function=native
        original_path,original_meta=list(sys.path),list(sys.meta_path)
        def restore():
            sys.path[:]=original_path;sys.meta_path[:]=original_meta
            for name in list(sys.modules):
                if name.startswith('_infinity_'):sys.modules.pop(name,None)
            importlib.invalidate_caches()
        self.addCleanup(restore)
        self.sign()

    def sign(self,version='0.3.5.40',protocol=1):
        lines=['INFINITY-MODULES/1','package\t'+version,'protocol\t'+str(protocol)]
        lines += ['capability\t'+x for x in ('checkpoint-v1','first-party-modules-v1')]
        for source in sorted(self.cc.glob('*')):
            if source.suffix not in ('.py','.xml'):continue
            lines.append('file\t'+hashlib.sha256(source.read_bytes()).hexdigest()+'\t'+CC+'/'+source.name)
        lines += ['entry\tcommand_center_client\t'+CC+'/plugin.py','entry\tcommand_center\t'+CC+'/service.py']
        self.payload=self.cc/'INFINITY-MODULES.v1'; self.payload.write_text('\n'.join(lines)+'\n')
        subprocess.run(['openssl','dgst','-sha256','-sign',str(self.key),'-out',str(self.payload)+'.sig',str(self.payload)],check=True)

    def load(self,version='0.3.5.40'):
        return self.module.load_contract(self.cc,version)

    def guard(self):
        contract=self.load();self.module.install_import_guard(contract)
        sys.path.insert(0,str(self.cc));importlib.invalidate_caches()
        return contract

    def test_real_native_package_protocol_and_payload_binding(self):
        identity=self.load().identity
        self.assertEqual(identity.manifest_sha256,hashlib.sha256(self.payload.read_bytes()).hexdigest())
        with self.assertRaises(self.module.ContractRejected):self.load('0.3.5.39')
        self.sign(version='0.3.5.41');self.assertEqual(self.load('0.3.5.41').identity.protocol_api,1)
        self.sign(protocol=2)
        with self.assertRaises(self.module.ContractRejected):self.load()

    def test_missing_native_abi_and_malformed_identity_fail_closed(self):
        self.module._native_function=None
        with self.assertRaises(self.module.ContractRejected):self.load()
        def malformed(root,version,vc,digest,hc,protocol):
            ctypes.memmove(version,b'0.3.5.40\0',9);ctypes.memmove(digest,b'x'*64+b'\0',65)
            ctypes.cast(protocol,ctypes.POINTER(ctypes.c_uint))[0]=1
            return 1
        self.module._native_function=malformed
        with self.assertRaises(self.module.ContractRejected):self.load()

    def test_verified_source_ignores_same_stamp_forged_bytecode(self):
        source=self.cc/'_infinity_guarded_probe.py';original=source.read_bytes()
        source.write_bytes(b'value="forgery!"\n');stamp=source.stat()
        py_compile.compile(str(source),doraise=True)
        source.write_bytes(original);os.utime(source,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
        self.sign();self.guard()
        imported=importlib.import_module('_infinity_guarded_probe')
        self.assertEqual(imported.value,'verified');self.assertIsNone(imported.__cached__)

    def test_unlisted_source_compiled_only_and_changed_source_rejected(self):
        self.guard()
        (self.cc/'_infinity_unknown.py').write_text('raise AssertionError("unlisted executed")\n')
        with self.assertRaises(self.module.ContractRejected):importlib.import_module('_infinity_unknown')
        source=self.cc/'_infinity_guarded_probe.py';py_compile.compile(str(source),cfile=str(source.with_suffix('.pyc')),doraise=True);source.unlink()
        with self.assertRaises(self.module.ContractRejected):importlib.import_module('_infinity_guarded_probe')
        source.write_text('raise AssertionError("changed executed")\n')
        source.with_suffix('.pyc').unlink()
        with self.assertRaises(self.module.ContractRejected):importlib.import_module('_infinity_guarded_probe')

    def test_generation_change_and_symlink_or_fifo_source_rejected(self):
        contract=self.load();source=self.cc/'_infinity_guarded_probe.py';raw=source.read_bytes()
        source.unlink();external=self.addons/'outside.py';external.write_bytes(raw);source.symlink_to(external)
        with self.assertRaises(self.module.ContractRejected):contract.source(CC+'/'+source.name)
        source.unlink();os.mkfifo(source)
        with self.assertRaises(self.module.ContractRejected):contract.source(CC+'/'+source.name)
        source.unlink();source.write_bytes(raw);self.sign(version='0.3.5.41')
        with self.assertRaises(self.module.ContractRejected):contract.current()

    def test_unrelated_import_remains_normal_and_no_worker_is_added(self):
        outside=self.addons/'other';outside.mkdir();(outside/'_infinity_unrelated_probe.py').write_text('value=17\n')
        self.guard();sys.path.insert(0,str(outside))
        result=importlib.import_module('_infinity_unrelated_probe')
        self.assertEqual(result.value,17)
        self.assertIsInstance(result.__loader__,importlib.machinery.SourceFileLoader)
        import threading
        before=tuple(threading.enumerate())
        for _ in range(20):self.load()
        self.assertEqual(tuple(threading.enumerate()),before)


if __name__=='__main__':unittest.main(verbosity=2)
