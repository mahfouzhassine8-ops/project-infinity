"""Actual CPython/ELF lookup boundary for the read-only native identity API."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import unittest

import stage_native_modules as stage

ROOT=Path(__file__).parent


class IdentityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace=tempfile.TemporaryDirectory();cls.work=Path(cls.workspace.name)
        native=Path(os.environ.get('FINAL_NATIVE_SOURCE_ROOT',ROOT.parents[2]/'baseline-2103407/reconstructed407-native'))
        include=cls.work/'include';include.mkdir()
        header=include/'InfinityPythonCryptoContract.h'
        header.write_bytes(stage.patch(stage.CRYPTO,(native/stage.CRYPTO).read_bytes()))
        api=include/'platform/android/activity';api.mkdir(parents=True)
        shutil.copyfile(ROOT/'isolated-native/InfinityInstalledModules.h',api/'InfinityInstalledModules.h')
        filesystem=include/'filesystem';filesystem.mkdir()
        (filesystem/'SpecialProtocol.h').write_text('#pragma once\n#include <string>\nclass CSpecialProtocol { public: static std::string TranslatePath(const std::string&); };\n')
        stub=cls.work/'native-paths.cpp'
        stub.write_text('''#include "filesystem/SpecialProtocol.h"
static int calls=0;
std::string CSpecialProtocol::TranslatePath(const std::string&) {++calls;return "/nonexistent-native-module-test-root/";}
extern "C" int InfinityTestRootCalls(){return calls;}
''')
        subprocess.run(['g++','-std=c++14','-Wall','-Wextra','-Werror','-fPIC','-shared',
                        '-I',str(include),'-I',str(ROOT/'isolated-native'),str(stub),
                        str(ROOT/'isolated-native/InfinityInstalledModules.cpp'),
                        str(ROOT/'isolated-native/InfinityModuleManifest.cpp'),'-lcrypto','-pthread',
                        '-o',str(cls.work/'libkodi.so')],check=True)
        shadow=cls.work/'shadow';shadow.mkdir();(shadow/'shadow.cpp').write_text('''#include <cstddef>
extern "C" int InfinityCommandCenterIdentityV1(const char*,char*,size_t,char*,size_t,unsigned int*){return 1;}
''')
        subprocess.run(['g++','-fPIC','-shared',str(shadow/'shadow.cpp'),'-o',str(shadow/'libkodi.so')],check=True)
        source=cls.work/'audit.cpp'
        source.write_text(r'''#include <Python.h>
#include <cerrno>
#include <climits>
#include <cstring>
#include <cstdlib>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>
#include <string>
#include <cassert>
namespace InfinityPythonPersistence {std::string Path(PyObject*v){return PyUnicode_Check(v)?PyUnicode_AsUTF8(v):"";}}
#include "InfinityPythonCryptoContract.h"
extern "C" int InfinityTestRootCalls();
int approvals=0,denials=0;
int Audit(const char*event,PyObject*args,void*) {
 const int decision=InfinityPythonPersistence::InfinityModuleIdentityLookupDecision(event,args);
 if(decision>0){++approvals;return 0;}
 if(decision<0){++denials;PyErr_SetString(PyExc_PermissionError,"identity requires actual engine");return -1;}
 return 0; // Test observer only; unrelated policies are audited by source inverse-diff.
}
int main(int argc,char**argv){assert(argc==4);Py_Initialize();
 const std::string root=argv[1],mode=argv[2],module=argv[3];
 const std::string path=root+"/libkodi.so",shadow=root+"/shadow/libkodi.so";
 void* engine=::dlopen(path.c_str(),RTLD_NOW|RTLD_NOLOAD);assert(engine);
 void* fake=::dlopen(shadow.c_str(),RTLD_NOW|RTLD_LOCAL);assert(fake);
 using namespace InfinityPythonPersistence;
 if(mode=="boundary") {
  auto*args=Py_BuildValue("(s)",path.c_str());
  assert(InfinityModuleIdentityLookupDecision("ctypes.dlopen",args)==1);
  assert(!ApprovedNativeLookup("ctypes.dlopen",args));Py_DECREF(args);
  args=Py_BuildValue("(ks)",reinterpret_cast<unsigned long>(engine),"InfinityCommandCenterIdentityV1");
  assert(InfinityModuleIdentityLookupDecision("ctypes.dlsym/handle",args)==1);
  assert(!ApprovedNativeLookup("ctypes.dlsym/handle",args));Py_DECREF(args);
  for(const auto handle:{reinterpret_cast<unsigned long>(fake),1UL,0UL}) {
   args=Py_BuildValue("(ks)",handle,"InfinityCommandCenterIdentityV1");
   assert(InfinityModuleIdentityLookupDecision("ctypes.dlsym/handle",args)==-1);Py_DECREF(args);
  }
  args=Py_BuildValue("(ks)",reinterpret_cast<unsigned long>(engine),"open");
  assert(InfinityModuleIdentityLookupDecision("ctypes.dlsym/handle",args)==0);Py_DECREF(args);
  args=Py_BuildValue("(s)",shadow.c_str());assert(InfinityModuleIdentityLookupDecision("ctypes.dlopen",args)==0);Py_DECREF(args);
  args=Py_BuildValue("(s)","/tmp/script.infinity.cobra/libOther.so");
  for(int i=0;i<10000;++i)assert(InfinityModuleIdentityLookupDecision("ctypes.dlopen",args)==0);
  Py_DECREF(args);assert(InfinityTestRootCalls()==0);
 } else if(mode=="factory") {
  assert(PyRun_SimpleString("import ctypes,importlib.util,os")==0);
  assert(PySys_AddAuditHook(Audit,nullptr)==0);
  auto*main=PyImport_AddModule("__main__");auto*globals=PyModule_GetDict(main);
  auto*filename=PyUnicode_FromString(module.c_str());PyDict_SetItemString(globals,"contract_source",filename);Py_DECREF(filename);
  auto*directory=PyUnicode_FromString(root.c_str());PyDict_SetItemString(globals,"native_root",directory);Py_DECREF(directory);
  const char*program=R"PY(os.environ['KODI_ANDROID_LIBS']=native_root
spec=importlib.util.spec_from_file_location('actual_module_contract',contract_source)
contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)
function=contract._native()
assert function is contract._native()
contract._native_function=None;contract._native_library=None
os.environ['KODI_ANDROID_LIBS']=native_root+'/shadow'
try:contract._native()
except contract.ContractRejected:pass
else:raise AssertionError('shadow engine impersonated the native trust anchor')
)PY";
  assert(PyRun_SimpleString(program)==0);assert(approvals>=2 && denials==1);
  assert(InfinityTestRootCalls()==0); // Lookup never scans providers/profiles or executes the API.
 } else return 2;
 ::dlclose(fake);::dlclose(engine);assert(Py_FinalizeEx()==0);
}
''')
        folder=Path(sysconfig.get_config_var('LIBDIR'));library=folder/sysconfig.get_config_var('LDLIBRARY')
        if not library.exists():library=Path(str(library)+'.1.0')
        if not library.exists():
            folder=Path(sys.prefix)/'lib';library=folder/sysconfig.get_config_var('LDLIBRARY')
            if not library.exists():library=Path(str(library)+'.1.0')
        if not library.exists():raise RuntimeError('Matching CPython shared library required')
        cls.binary=cls.work/'audit'
        subprocess.run(['g++','-std=c++14','-Wall','-Wextra','-Werror','-I',sysconfig.get_path('include'),
                        '-I',str(include),str(source),'-L',str(cls.work),'-Wl,-rpath,'+str(cls.work),'-lkodi',
                        str(library),'-Wl,-rpath,'+str(folder),'-lcrypto','-ldl','-lm','-pthread','-o',str(cls.binary)],check=True)

    @classmethod
    def tearDownClass(cls):cls.workspace.cleanup()

    def invoke(self,mode):
        subprocess.run([str(self.binary),str(self.work),mode,str(ROOT/'isolated-python/module_contract.py')],
                       check=True,timeout=15)

    def test_exact_running_image_and_address_only_no_generic_writer_exception(self):self.invoke('boundary')
    def test_real_python_noload_factory_rejects_shadow_native_identity(self):self.invoke('factory')


if __name__=='__main__':unittest.main(verbosity=2)
