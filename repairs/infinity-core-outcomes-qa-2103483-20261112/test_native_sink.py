#!/usr/bin/env python3
"""Actual native QA callback/loader delegate host checks; no Core execution."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import sysconfig
import tempfile

HERE=Path(__file__).resolve().parent
CPP=r'''
#include <Python.h>
#include <cassert>
#include <cerrno>
#include <iostream>
#include <string>
#include <vector>
static std::vector<std::string> logs;
void InfinityCoreQaHostLog(const char* text){logs.emplace_back(text);errno=EINTR;}
namespace InfinityStartupTrace {inline bool host=true;inline bool InfinityProcess(){return host;}}
#define INFINITY_CORE_OUTCOMES_HOST 1
#include "InfinityCoreOutcomeTrace.h"
int main(int argc,char** argv){
 assert(argc==3);Py_Initialize();
 auto* globals=PyDict_New();assert(globals);
 PyDict_SetItemString(globals,"__builtins__",PyEval_GetBuiltins());
 InfinityCoreQA::BindLoadSink(77,globals);
 assert(PyDict_GetItemString(globals,"_INFINITY_CORE_NATIVE_EVENT"));
 auto* path=PyUnicode_FromString(argv[1]);PyDict_SetItemString(globals,"TEST_DELEGATE",path);Py_DECREF(path);
 auto* run=PyRun_String("exec(open(TEST_DELEGATE).read())",Py_file_input,globals,globals);
 if(!run){PyErr_Print();return 2;}Py_DECREF(run);
 assert(logs.size()>=8);
 unsigned began=0,returned=0,failed=0;
 for(const auto& row:logs){
  began+=row.find("core.load.begin")!=std::string::npos;
  returned+=row.find("core.load.returned")!=std::string::npos;
  failed+=row.find("core.load.error")!=std::string::npos;
  assert(row.find("secret-token")==std::string::npos);
 }
 assert(began==2 && returned==1 && failed==1);
 auto old=logs.size();InfinityStartupTrace::host=false;InfinityCoreQA::Log(77,"{}");assert(logs.size()==old);InfinityStartupTrace::host=true;
 errno=EDOM;PyErr_SetString(PyExc_ValueError,"retained error");
 auto* dict=Py_BuildValue("{s:s}","line","{\"event\":\"host.check\"}");auto* self=PyLong_FromLong(77);
 auto* result=InfinityCoreQA::Emit(self,dict);Py_DECREF(dict);Py_DECREF(result);Py_DECREF(self);
 assert(errno==EDOM && PyErr_ExceptionMatches(PyExc_ValueError));PyErr_Clear();
 InfinityCoreQA::Install(77,"service.adulthideout.core",argv[2],globals);
 auto* qa=PyDict_GetItemString(globals,"_INFINITY_CORE_OUTCOMES_GLOBALS");assert(qa);
 auto* state=PyDict_GetItemString(qa,"state");assert(state);
 InfinityCoreQA::BeforeFinish(globals,PyThreadState_Get());
 auto* closed=PyObject_GetAttrString(state,"closed");assert(closed==Py_True);Py_DECREF(closed);
 assert(!PyErr_Occurred());
 InfinityCoreQA::records.store(8192);InfinityCoreQA::limitReported.store(false);
 auto before=logs.size();for(int n=0;n<10;++n)InfinityCoreQA::Log(77,"{}");assert(logs.size()==before+1);
 Py_DECREF(globals);Py_FinalizeEx();
 std::cout<<"PASS actual native sink, unchanged loader results/errors, foreign-process exclusion, errno/PyErr retention, source-bound install/cleanup and log bound\n";
}
'''


def main():
 p=argparse.ArgumentParser();p.add_argument('--overlay',type=Path,required=True);p.add_argument('--service',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 assert sys.version_info[:3]==(3,11,7),'Pinned3.11.7 required'
 source=(a.overlay/'xbmc/interfaces/python/InfinityPythonPersistenceSource.h').read_text()
 raw=source.split('R"infinity_source(',1)[1].split(')infinity_source"',1)[0]
 tree=ast.parse(raw);klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Observer');method=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='install_crypto_loads')
 body=ast.get_source_segment(raw,method)
 delegate='''import ctypes,_ctypes,os,importlib
_INFINITY_INITIALIZATION_STAGE='host'
def _infinity_report_initialization_stage():pass
saved_native=_ctypes.dlopen
saved_ctypes=ctypes._dlopen
sentinel=object()
expected=OSError('secret-token not accessible for the namespace test')
calls=[]
def original(name,*args,**kwargs):
 calls.append((name,args,kwargs))
 if name=='/fixture/fail/libadulthideout_core.so':raise expected
 return sentinel
_ctypes.dlopen=original
ctypes._dlopen=original
class Harness:
 def patch(self,module,name,value):setattr(module,name,value)
'''+''.join(' '+line+'\n' for line in body.splitlines())+'''
try:
 Harness().install_crypto_loads()
 assert _ctypes.dlopen is ctypes._dlopen
 assert ctypes._dlopen('/fixture/libadulthideout_core.so',7,mode=9) is sentinel
 try:ctypes._dlopen('/fixture/fail/libadulthideout_core.so')
 except OSError as error:assert error is expected
 else:raise AssertionError('missing real failure')
 assert ctypes._dlopen('/fixture/unrelated.so') is sentinel
 assert calls[0]==('/fixture/libadulthideout_core.so',(7,),{'mode':9})
finally:
 _ctypes.dlopen=saved_native
 ctypes._dlopen=saved_ctypes
'''
 with tempfile.TemporaryDirectory(prefix='coreqa-native-') as name:
  d=Path(name);(d/'case.cpp').write_text(CPP);(d/'delegate.py').write_text(delegate)
  include=a.overlay/'xbmc/interfaces/python';library=sysconfig.get_config_var('LDLIBRARY');libname=library.removeprefix('lib').split('.so')[0]
  command=['g++','-std=c++17','-Wall','-Wextra','-Werror','-pthread','-I'+sysconfig.get_path('include'),'-I'+str(include),str(d/'case.cpp'),'-L'+sysconfig.get_config_var('LIBDIR'),'-Wl,-rpath,'+sysconfig.get_config_var('LIBDIR'),'-l'+libname,'-lcrypto','-ldl','-o',str(d/'case')]
  subprocess.run(command,check=True,timeout=90)
  execution=subprocess.run([str(d/'case'),str(d/'delegate.py'),str(a.service)],check=True,text=True,capture_output=True,timeout=20)
 proof=dict(status='PASS_ACTUAL_NATIVE_CALLBACK_AND_PINNED_PYTHON_LOADER_DELEGATE',Python=list(sys.version_info[:3]),native_Core_executed=False,Android=False,shutdown_acceptance=False,stdout=execution.stdout.strip(),source_sha256=hashlib.sha256(CPP.encode()).hexdigest(),production_loader_method_sha256=hashlib.sha256(body.encode()).hexdigest())
 a.out.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))


if __name__=='__main__':main()
