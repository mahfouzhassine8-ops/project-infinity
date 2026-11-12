#!/usr/bin/env python3
"""Focused actual CPython/native ledger checks; no Core image executes on host."""
import argparse,hashlib,json,os,subprocess,sys,sysconfig,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
CPP=r'''
#include <Python.h>
#define INFINITY_SCRIPT_OBSERVER_HOST
#include "InfinityPythonPersistence.h"
#include <cassert>
#include <condition_variable>
#include <iostream>
#include <sys/syscall.h>
namespace L=InfinityScriptPersistence;
extern "C" int InfinityCommandCenterIdentityV1(const char*,char*,size_t,char*,size_t,unsigned int*){return 0;}
static std::mutex gateMutex;static std::condition_variable gateChanged;
static bool pauseChmod=false,entered=false,released=false;
extern "C" int chmod(const char* path,mode_t mode){
 {std::unique_lock<std::mutex> lock(gateMutex);if(pauseChmod){entered=true;gateChanged.notify_all();gateChanged.wait(lock,[]{return released;});}}
 return syscall(SYS_fchmodat,AT_FDCWD,path,mode,0);
}
static void run(const char* code){if(PyRun_SimpleString(code)!=0){PyErr_Print();std::exit(20);}}
int main(int argc,char** argv){
 assert(argc==3);std::string mode=argv[1],root=argv[2];
 for(const auto& p:{root+"/profile/state",root+"/cache/state",root+"/cache/source"}){
  int fd=::open(p.c_str(),O_CREAT|O_WRONLY,0600);assert(fd>=0);assert(::write(fd,"saved",5)==5);::close(fd);
 }
 Py_Initialize();auto* thread=PyThreadState_Get();auto* globals=PyModule_GetDict(PyImport_AddModule("__main__"));
 auto* path=PyUnicode_FromString(root.c_str());PyDict_SetItemString(globals,"root",path);Py_DECREF(path);
 run("import os,ctypes,shutil,threading\nold_chmod=os.chmod\nold_dlopen=ctypes._dlopen\nshared=root+'/profile/state'\nprivate=root+'/cache/state'\n");
 L::Admit(1,"optional.provider:service.py");auto* context=InfinityPythonPersistence::Start(1,thread->interp);
 if(PyErr_Occurred())PyErr_Print();assert(context && context->observer && L::Snapshot().observed==1);
 if(mode=="copy2")run("shutil.copy2(root+'/cache/source',private)\nos.utime(private,ns=(1600000000000000000,1600000000000000010))\nold_chmod(private,0o640)\nassert os.stat(private).st_mode & 0o777 == 0o640\n");
 if(mode=="essential-metadata")run("old_chmod(shared,0o640)\nos.utime(shared,ns=(1600000000000000000,1600000000000000010))\n");
 if(mode=="metadata-errors")run("try:os.setxattr(private,'user.infinity-qa',b'kept',flags=99999)\nexcept OSError:pass\nelse:raise AssertionError('missing original xattr error')\ntry:os.chmod(None,0o600)\nexcept TypeError:pass\nelse:raise AssertionError('missing original TypeError')\n");
 if(mode=="missing-load")run("try:ctypes.CDLL(root+'/no-image-does-not-exist.so')\nexcept OSError as e:assert 'No such file' in str(e)\nelse:raise AssertionError('load succeeded')\n");
 if(mode=="opaque-load")run("library=ctypes.CDLL('libm.so.6')\n");
 if(mode=="bypass-load")run("try:old_dlopen(root+'/no-image-does-not-exist.so')\nexcept OSError:pass\n");
 if(mode=="live-metadata"){
  pauseChmod=true;run("worker=threading.Thread(target=lambda:old_chmod(shared,0o640))\nworker.start()\n");
  auto* saved=PyEval_SaveThread();{std::unique_lock<std::mutex> lock(gateMutex);assert(gateChanged.wait_for(lock,std::chrono::seconds(10),[]{return entered;}));}
  assert(L::BeginWriteProtection(23,{root+"/profile"},{root+"/cache"}));assert(L::CloseParticipantWrites(23));assert(!L::SealEssentialWrites(23));
  assert(L::ActiveProtectedResources()>0);
  {std::lock_guard<std::mutex> lock(gateMutex);released=true;}gateChanged.notify_all();PyEval_RestoreThread(saved);run("worker.join()\n");
 }else{assert(L::BeginWriteProtection(23,{root+"/profile"},{root+"/cache"}));}
 if(mode=="close-admission")run("before=os.stat(shared).st_mode\ntry:old_chmod(shared,0o777)\nexcept PermissionError:pass\nelse:raise AssertionError('optional essential mutation admitted')\nassert os.stat(shared).st_mode==before\nos.chmod(private,0o640)\n");
 if(mode=="essential-participant"){
  L::RegisterParticipant(1);run("os.chmod(shared,0o640)\n");
 }
 if(mode!="live-metadata")assert(L::CloseParticipantWrites(23));
 if(mode=="active-essential" || mode=="unknown-write"){
  // A real already-admitted write obligation remains a blocker independently
  // of actor optionality. Populate it before the final sealed phase.
  auto& s=L::Get();{std::lock_guard<std::mutex> lock(s.mutex);s.protection.phase=0;}
  auto token=L::BeginProtectedOperation(1,mode=="unknown-write"?std::vector<std::string>{}:std::vector<std::string>{root+"/profile/state"},"actual_pending_write");assert(token);
  {std::lock_guard<std::mutex> lock(s.mutex);s.protection.phase=2;}
  assert(!L::SealEssentialWrites(23));L::EndProtectedOperation(token);
 }
 bool expected=mode!="opaque-load" && mode!="bypass-load";
 bool sealed=L::SealEssentialWrites(23);
 if(sealed!=expected){for(const auto& why:L::EssentialWrites().blockers)std::cerr<<why<<'\n';return 22;}
 assert(L::EssentialWritesAuthorized(23)==expected);
 if(expected){
  run("try:old_chmod(private,0o777)\nexcept PermissionError:pass\nelse:raise AssertionError('mutation after seal')\n");
 }
 if(mode=="classifier"){
  auto test=[](const char* path,const char* message,bool expected){auto* e=PyUnicode_FromString(message);assert(InfinityPythonPersistence::LoadRejectedBeforeExecution(path,e)==expected);Py_DECREF(e);};
  test("/tmp/core.so","dlopen failed: library \"/tmp/core.so\" needed or dlopened by \"/data/libkodi.so\" is not accessible for the namespace \"clns-9\"",true);
  test("/tmp/core.so","dlopen failed: library \"/tmp/dependency.so\" is not accessible for the namespace \"clns-9\"",false);
  test("/tmp/core.so","dlopen failed: cannot locate symbol; initialization unknown",false);
 }
 std::cout<<"{\"case\":\""<<mode<<"\",\"passed\":true,\"sealed\":"<<(sealed?"true":"false")<<"}\n"<<std::flush;
 std::_Exit(0);
}
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 assert sys.version_info[:3]==(3,11,7),'Actual pinned CPython required'
 includes=[HERE/'native/overlay/xbmc',HERE/'native/overlay/xbmc/interfaces/python',HERE/'native/host-baseline/xbmc',HERE/'native/host-baseline/xbmc/interfaces/python',Path(sysconfig.get_path('include'))]
 cases=('copy2','essential-metadata','metadata-errors','missing-load','opaque-load','bypass-load','live-metadata','close-admission','essential-participant','active-essential','unknown-write','classifier')
 rows=[]
 with tempfile.TemporaryDirectory(prefix='essential-only-') as tmp:
  d=Path(tmp);(d/'case.cpp').write_text(CPP);binary=d/'case'
  lib=sysconfig.get_config_var('LDLIBRARY').removeprefix('lib').split('.so')[0]
  subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-pthread',*['-I'+str(x) for x in includes],str(d/'case.cpp'),'-L'+sysconfig.get_config_var('LIBDIR'),'-Wl,-rpath,'+sysconfig.get_config_var('LIBDIR'),'-l'+lib,'-l:libsqlite3.so.0','-ldl','-lm','-lcrypto','-Wl,--export-dynamic','-o',str(binary)],check=True)
  for case in cases:
   root=d/case;root.mkdir();(root/'profile').mkdir();(root/'cache').mkdir()
   r=subprocess.run([str(binary),case,str(root)],capture_output=True,text=True,timeout=30)
   rows.append(dict(case=case,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));print(case,r.returncode,r.stderr,flush=True)
  result=dict(status='PASS' if all(r['exit_code']==0 for r in rows) else 'FAIL',cases=rows,Python=list(sys.version_info[:3]),Core_executed=False,Android=False,Fold=False)
  a.out.write_text(json.dumps(result,indent=2)+'\n');assert result['status']=='PASS'
if __name__=='__main__':main()
