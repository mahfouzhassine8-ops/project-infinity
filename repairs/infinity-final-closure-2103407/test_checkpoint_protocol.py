"""Exact407 registration regression; no save/fence/termination implementation mocked as PASS."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest

import patch_checkpoint_protocol as transform

ROOT=Path(__file__).parent


def baseline_root():
    raw=os.environ.get('INFINITY_SIGNED407_SOURCES')
    root=Path(raw) if raw else ROOT.parents[2]/'baseline-2103407/ownership-local/sources'
    return root/'script.infinity.commandcenter'


class CheckpointProtocolTests(unittest.TestCase):
    def setUp(self):
        self.sources=baseline_root();self.raw=(self.sources/'checkpoint_runtime.py').read_bytes()
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.profile=Path(self.temp.name)/'profile';self.control=self.profile/'.android-checkpoint'
        self.control.mkdir(parents=True)
        self.engine={'schema':1,'native_api':1,'pid':os.getpid(),'owner':'verified_engine_owner_12345'}
        self.write_engine()
        oldpath=list(sys.path);sys.path.insert(0,str(self.sources));self.addCleanup(lambda:sys.path.__setitem__(slice(None),oldpath))
        self.contract=ModuleType('module_contract')
        class Rejected(RuntimeError):pass
        self.contract.ContractRejected=Rejected
        self.calls=[]
        def identity(root,version):
            self.calls.append((root,version))
            return SimpleNamespace(package_version=version,protocol_api=1,manifest_sha256='a'*64)
        self.contract.installed_identity=identity
        prior=sys.modules.get('module_contract');sys.modules['module_contract']=self.contract
        def restore():
            if prior is None:sys.modules.pop('module_contract',None)
            else:sys.modules['module_contract']=prior
        self.addCleanup(restore)

    def write_engine(self):
        (self.control/'engine.json').write_text(json.dumps(self.engine))

    def module(self,patched):
        module=ModuleType('checkpoint_fixture');module.__file__=str(self.sources/'checkpoint_runtime.py')
        exec(compile(transform.patch(self.raw) if patched else self.raw,module.__file__,'exec'),module.__dict__)
        return module

    def resident(self,module,version='0.3.5.39'):
        return module.ResidentCheckpoint(self.profile,None,None,None,{'version':lambda:version})

    def test_exact_signed407_reproduces_registration_version_rejection(self):
        module=self.module(False)
        with self.assertRaisesRegex(module.PersistenceError,'unsupported installed'):
            self.resident(module).register()
        self.assertFalse((self.control/'active.json').exists())

    def test_authenticated_package_upgrade_keeps_semantic_protocol_one(self):
        module=self.module(True)
        for version in ('0.3.5.39','0.3.5.40','1.0.0'):
            self.assertTrue(self.resident(module,version).register())
            active=json.loads((self.control/'active.json').read_text())
            self.assertEqual((active['addon_version'],active['participant_api'],active['module_manifest_sha256']),
                             (version,1,'a'*64))
            self.assertEqual((active['pid'],active['owner'],active['required_files']),
                             (os.getpid(),self.engine['owner'],sorted(module.FILES)))
        self.assertEqual(len(self.calls),3)

    def test_unavailable_or_rejected_native_identity_never_registers(self):
        module=self.module(True)
        def reject(root,version):raise self.contract.ContractRejected('native identity rejected')
        self.contract.installed_identity=reject
        with self.assertRaisesRegex(module.PersistenceError,'native identity rejected'):self.resident(module).register()
        self.assertFalse((self.control/'active.json').exists())
        self.assertFalse((self.control/'participant.json').exists())

    def test_protocol_pid_owner_and_native_api_still_fail_closed(self):
        module=self.module(True)
        self.contract.installed_identity=lambda *args:SimpleNamespace(protocol_api=2)
        with self.assertRaisesRegex(module.PersistenceError,'checkpoint protocol'):self.resident(module).register()
        self.setUpIdentity()
        for field,value in (('pid',os.getpid()+1),('native_api',2),('schema',2),('owner','bad')):
            original=self.engine[field];self.engine[field]=value;self.write_engine()
            module=self.module(True)
            expected = ValueError if field == 'owner' else module.PersistenceError
            with self.assertRaises(expected):self.resident(module).register()
            self.engine[field]=original;self.write_engine()
        self.assertFalse((self.control/'active.json').exists())

    def setUpIdentity(self):
        self.contract.installed_identity=lambda root,version:SimpleNamespace(package_version=version,protocol_api=1,manifest_sha256='a'*64)

    def test_all_other_functions_constants_and_checkpoint_operations_exactly_preserved(self):
        after=transform.patch(self.raw);old=ast.parse(self.raw);new=ast.parse(after)
        def protected(tree):
            for n in tree.body:
                if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ADDON_VERSION' for t in n.targets):continue
                if isinstance(n,ast.ClassDef) and n.name=='ResidentCheckpoint':
                    n.body=[f for f in n.body if not isinstance(f,ast.FunctionDef) or f.name!='register']
                yield ast.dump(n,include_attributes=False)
        self.assertEqual(list(protected(old)),list(protected(new)))
        with self.assertRaises(ValueError):transform.patch(self.raw+b'\n')


if __name__=='__main__':unittest.main(verbosity=2)
