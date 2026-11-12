#!/usr/bin/env python3
"""Actual running-engine read-only lookup across final-save/sealed admission."""
import argparse,json,os,subprocess,sys,sysconfig,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
CPP=r'''
#include <Python.h>
#define INFINITY_SCRIPT_OBSERVER_HOST
#include "InfinityPythonPersistence.h"
#include <cassert>
namespace L=InfinityScriptPersistence;
extern "C" int InfinityCommandCenterIdentityV1(const char*,char*,size_t,char*,size_t,unsigned int*){return 0;}
static bool run(const char* code){if(PyRun_SimpleString(code)!=0){PyErr_Print();return false;}return true;}
extern "C" int probe(const char* root,const char* library){
 auto* owner=PyThreadState_Get();auto* globals=PyModule_GetDict(PyImport_AddModule("__main__"));
 auto* p=PyUnicode_FromString(library);PyDict_SetItemString(globals,"actual_engine",p);Py_DECREF(p);
 auto* r=PyUnicode_FromString(root);PyDict_SetItemString(globals,"qa_root",r);Py_DECREF(r);
 L::Admit(1,"optional.identity_probe:default.py");auto* context=InfinityPythonPersistence::Start(1,owner->interp);
 if(PyErr_Occurred())PyErr_Print();if(!context || !context->observer)return 11;
 auto* args=Py_BuildValue("(s)",library);
 bool exact=InfinityPythonPersistence::ApprovedInfinityModuleIdentityLookup("ctypes.dlopen",args);Py_DECREF(args);if(!exact)return 12;
 assert(L::BeginWriteProtection(23,{std::string(root)+"/profile"},{std::string(root)+"/cache"}));
 assert(L::CloseParticipantWrites(23));
 if(!run("import ctypes\nimage_final=ctypes.CDLL(actual_engine)\nidentity_final=image_final.InfinityCommandCenterIdentityV1\n"))return 13;
 if(!L::SealEssentialWrites(23))return 14;
 if(!run("image_sealed=ctypes.CDLL(actual_engine)\nidentity_sealed=image_sealed.InfinityCommandCenterIdentityV1\ntry:ctypes.CDLL(qa_root+'/shadow/libkodi.so')\nexcept PermissionError:pass\nelse:raise AssertionError('shadow image admitted after seal')\n"))return 15;
 if(!L::EssentialWritesAuthorized(23))return 16;
 return 0;
}
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert sys.version_info[:3]==(3,11,7)
 includes=[HERE/'native/overlay/xbmc',HERE/'native/overlay/xbmc/interfaces/python',HERE/'native/host-baseline/xbmc',HERE/'native/host-baseline/xbmc/interfaces/python',Path(sysconfig.get_path('include'))]
 with tempfile.TemporaryDirectory(prefix='essential-identity-') as tmp:
  d=Path(tmp);(d/'probe.cpp').write_text(CPP);library=d/'libkodi.so';root=d/'profile-root';root.mkdir();(root/'profile').mkdir();(root/'cache').mkdir()
  lib=sysconfig.get_config_var('LDLIBRARY').removeprefix('lib').split('.so')[0]
  subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-pthread','-shared','-fPIC','-Wl,-Bsymbolic',*['-I'+str(p) for p in includes],str(d/'probe.cpp'),'-L'+sysconfig.get_config_var('LIBDIR'),'-Wl,-rpath,'+sysconfig.get_config_var('LIBDIR'),'-l'+lib,'-l:libsqlite3.so.0','-ldl','-lm','-lcrypto','-o',str(library)],check=True)
  driver='import ctypes,os,sys\np=ctypes.PyDLL(sys.argv[1]);f=p.probe;f.argtypes=[ctypes.c_char_p,ctypes.c_char_p];f.restype=ctypes.c_int\nr=f(os.fsencode(sys.argv[2]),os.fsencode(sys.argv[1]));print(r,flush=True);os._exit(r)\n'
  execution=subprocess.run([sys.executable,'-c',driver,str(library),str(root)],text=True,capture_output=True,timeout=30)
  result=dict(status='PASS' if execution.returncode==0 else 'FAIL',case='actual-running-engine-identity-final-save-and-sealed-shadow-denial',exit_code=execution.returncode,stdout=execution.stdout,stderr=execution.stderr,Python=list(sys.version_info[:3]),Android=False,Fold=False)
  a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['status']=='PASS'
if __name__=='__main__':main()
