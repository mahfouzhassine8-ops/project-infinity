#!/usr/bin/env python3
"""Compile and exercise the production observer in the pinned CPython 3.11 ABI."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CODE = r'''
#include <Python.h>
#define INFINITY_SCRIPT_OBSERVER_HOST
#include "InfinityPythonPersistence.h"
#include <cassert>
#include <iostream>
#include <cstdlib>
#include <condition_variable>
#include <sys/syscall.h>
// Test-only delay at the real libc write boundary. Production code has no
// waiting thread, timeout or test hook. The protected entry point remains live
// while another Python thread changes the descriptor or namespace.
static std::mutex delayMutex;
static std::condition_variable delayChanged;
static int delayDescriptor = -1;
static bool delayEntered = false, delayReleased = false;
extern "C" ssize_t write(int fd, const void* bytes, size_t count) {
  {
    std::unique_lock<std::mutex> lock(delayMutex);
    if (fd == delayDescriptor && !delayReleased) {
      delayEntered = true; delayChanged.notify_all();
      delayChanged.wait(lock, []{ return delayReleased; });
    }
  }
  return syscall(SYS_write,fd,bytes,count);
}
static void run(const char* code) {
  if (PyRun_SimpleString(code) != 0) { PyErr_Print(); std::exit(20); }
}
int main(int argc, char** argv) {
  assert(argc == 3);
  const std::string mode = argv[1], root = argv[2];
  Py_Initialize(); auto* owner = Py_NewInterpreter(); assert(owner);
  auto* globals = PyModule_GetDict(PyImport_AddModule("__main__"));
  auto* path = PyUnicode_FromString(root.c_str()); PyDict_SetItemString(globals, "root", path); Py_DECREF(path);
  run("import os, io, _io, sqlite3, mmap, ctypes\n"
      "old_write=os.write; old_pwrite=os.pwrite; old_writev=os.writev\n"
      "old_open=_io.open; old_raw=_io.FileIO; old_raw_write=_io.FileIO.write\n"
      "old_rename=os.rename; old_remove=os.remove\n"
      "shared=root+'/profile/state'; private=root+'/cache/state'; binary_buffer=False\n");
  InfinityScriptPersistence::Admit(1, "test.provider:service.py");
  auto* context = InfinityPythonPersistence::Start(1, owner->interp);
  if (PyErr_Occurred()) PyErr_Print();
  if (!context || !context->observer) {
    std::cerr << InfinityScriptPersistence::Failure() << '\n';
    for (const auto& why : InfinityScriptPersistence::EssentialWrites().blockers) std::cerr << why << '\n';
    return 21;
  }
  if (mode == "ambient-contract") {
    const std::string native = std::getenv("KODI_ANDROID_LIBS");
    const auto path = native + "/libinfinityambient.so";
    assert(InfinityPythonPersistence::ApprovedCryptoImage(path));
    for (const auto* symbol : {"create", "destroy", "reset", "feed", "tile", "surface_request",
         "surface_read", "version", "surface_version", "allowed", "surface_present", "surface_error", "memfd"})
      assert(InfinityPythonPersistence::ApprovedCryptoImage(path,"infinity_ambient_"+std::string(symbol)));
    assert(!InfinityPythonPersistence::ApprovedCryptoImage(path,"open"));
    assert(!InfinityPythonPersistence::ApprovedCryptoImage(path,"infinity_ambient_unknown"));
    assert(!InfinityPythonPersistence::ApprovedCryptoImage(root+"/outside/libinfinityambient.so"));
    setenv("KODI_ANDROID_LIBS",(root+"/changed").c_str(),1);
    assert(!InfinityPythonPersistence::ApprovedCryptoImage(root+"/changed/libinfinityambient.so"));
    setenv("KODI_ANDROID_LIBS",(root+"/alias").c_str(),1);
    assert(!InfinityPythonPersistence::ApprovedCryptoImage(root+"/alias/libinfinityambient.so"));
    setenv("KODI_ANDROID_LIBS",native.c_str(),1);
  }
  if (mode == "pathlike") run("class PathLike:\n def __fspath__(self): return shared\nf=old_open(PathLike(),'w'); f.write('essential'); f.flush()\n");
  else if (mode == "buffer-drain") run("f=open(shared,'w'); f.write('essential')\n");
  else if (mode == "layered") run("r=io.FileIO(shared,'w'); b=io.BufferedWriter(r); f=io.TextIOWrapper(b); f.write('essential')\n");
  else if (mode == "cached-buffer") run("f=old_open(shared,'w'); f.write('essential')\n");
  else if (mode == "optional-blocked") run("import threading\ne=threading.Event(); t=threading.Thread(target=e.wait); t.start()\nf=open(private,'w'); f.write('unfinished')\n");
  else if (mode == "sqlite-attach") run("c=sqlite3.connect(root+'/cache/main.db'); c.execute('ATTACH DATABASE ? AS shared',(root+'/profile/history.db',)); c.execute('CREATE TABLE shared.history(value)'); c.execute('INSERT INTO shared.history VALUES(321)'); c.commit(); c.close()\n");
  else if (mode == "buffer-fd-spoof") run("cachefd=os.open(private,os.O_CREAT|os.O_RDWR,0o600)\nclass Raw(old_raw):\n def fileno(self): return cachefd\nf=io.BufferedWriter(Raw(shared,'w')); f.write(b'essential'); binary_buffer=True\n");
  else if (mode == "raw-fd-spoof") run("cachefd=os.open(private,os.O_CREAT|os.O_RDWR,0o600)\nclass Raw(old_raw):\n def fileno(self): return cachefd\nf=Raw(shared,'w'); old_raw_write(f,b'essential')\n");
  else if (mode == "raw") run("f=old_raw(shared,'w'); old_raw_write(f,b'essential')\n");
  else run("fd=os.open(shared, os.O_CREAT|os.O_RDWR, 0o600); os.write(fd,b'essential')\n");
  if (mode == "uname-combined-flags") run("import subprocess\nassert subprocess.check_output(['uname','-rs']).strip()\n");
  if (mode == "unverified-child-output") run("import subprocess\nassert subprocess.call(['uname','-rs'],stdout=fd)==0\n");
  if (mode.rfind("pillow-",0)==0) {
    run("import importlib.util\n"
        "spec=importlib.util.spec_from_file_location('PIL._imaging',os.environ['KODI_ANDROID_LIBS']+'/lib_imaging.so')\n"
        "core=importlib.util.module_from_spec(spec); spec.loader.exec_module(core)\n"
        "im=core.new('RGB',(1,1)); enc=core.raw_encoder('RGB','RGB'); enc.setimage(im)\n");
    if (mode == "pillow-fd") run("enc.encode_to_file(fd); baseline=old_open(shared,'rb').read()\n");
    if (mode == "pillow-ppm") run("im.save_ppm(shared); baseline=old_open(shared,'rb').read()\n");
  }
  if (mode == "memory-buffer") run("memory=io.TextIOWrapper(io.BufferedWriter(io.BytesIO())); memory.write('RAM'); memory.flush()\n");
  if (mode == "unknown-descriptor") run("class Descriptor:\n def __index__(self): return fd\nold_write(Descriptor(),b'essential')\n");
  if (mode == "file-lock") run("import fcntl\nfcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)\n");
  if (mode == "sqlite-row-factory") run("c=sqlite3.connect(private+'.db'); c.row_factory=lambda cursor,row: {'value':row[-1]}; c.execute('ATTACH DATABASE ? AS shared',(shared+'.db',)); c.execute('CREATE TABLE shared.history(value)'); c.execute('INSERT INTO shared.history VALUES(321)'); c.commit(); assert c.row_factory is not None; c.close()\n");
  if (mode.rfind("command-center-",0)==0) {
    run("import sys,runpy,tempfile\n"
        "tempfile.tempdir=root+'/profile'\n"
        "sys.argv=['checkpoint-test','--runtime',os.environ['INFINITY_CC_RUNTIME']]\n"
        "checks=runpy.run_path(os.environ['INFINITY_CC_TEST'])\n"
        "cc=checks['RuntimeTests'](); cc.setUp()\n");
    InfinityScriptPersistence::RegisterParticipant(1);
  }
  if (mode.rfind("compat-",0)==0) {
    run("import importlib.util,json\n"
        "from pathlib import Path\n"
        "spec=importlib.util.spec_from_file_location('compat_actual',os.environ['INFINITY_COMPAT_RUNTIME'])\n"
        "compat=importlib.util.module_from_spec(spec); spec.loader.exec_module(compat)\n"
        "control=Path(root)/'profile'; token='00000000-0000-0000-0000-000000000001'\n"
        "(control/'engine.json').write_text(json.dumps(dict(schema=1,native_api=1,pid=os.getpid(),owner=token)))\n"
        "request=dict(schema=1,pid=os.getpid(),owner=token,session=token,phase='PREPARE')\n"
        "checkpoint=compat.CompatCheckpoint(control); assert not checkpoint.poll()\n");
    if (mode == "compat-failure") run("request['session']='invalid'\n");
    run("(control/'request.json').write_text(json.dumps(request))\n");
    InfinityScriptPersistence::RegisterParticipant(1);
  }
  if (mode == "descriptor-race" || mode == "rename-race") {
    run("import threading\ncachefd=os.open(private,os.O_CREAT|os.O_RDWR,0o600)\n");
    delayDescriptor = static_cast<int>(PyLong_AsLong(PyDict_GetItemString(globals,"cachefd")));
    run("t=threading.Thread(target=lambda: old_write(cachefd,b'pending')); t.start()\n");
    auto* state = PyEval_SaveThread();
    { std::unique_lock<std::mutex> lock(delayMutex);
      assert(delayChanged.wait_for(lock,std::chrono::seconds(5),[]{return delayEntered;})); }
    PyEval_RestoreThread(state);
    if (mode == "descriptor-race") run("os.dup2(fd,cachefd)\n");
    else run("os.rename(private,shared)\n");
  }
  if (mode == "sqlite-renamed") run("c=sqlite3.connect(private+'.db'); c.execute('CREATE TABLE history(value)'); c.execute('INSERT INTO history VALUES(321)'); c.commit(); os.rename(private+'.db',shared+'.db')\n");
  assert(InfinityScriptPersistence::BeginWriteProtection(23, {root+"/profile"}, {root+"/cache"}));
  if (mode == "compat-save") run("assert checkpoint.poll() and checkpoint.parked\nresponse=json.loads((control/'compat-response.json').read_text()); assert response['status']=='PARTICIPANT_COMPLETE' and not response['global_safe_to_terminate']\n");
  if (mode == "compat-failure") {
    run("try: checkpoint.poll()\nexcept ValueError: pass\nelse: raise AssertionError('failed compatibility identity accepted')\nassert checkpoint.parked and not (control/'compat-response.json').exists()\n");
    assert(!InfinityScriptPersistence::EssentialWritesAuthorized(23));
    std::cout << "PASS actual compatibility failure cannot authorize termination\n" << std::flush;
    std::_Exit(0);
  }
  if (mode == "command-center-save") run("cc.test_actual_player_state_saved_and_frozen_player_can_remain_alive(); assert cc.response()['status']=='PARTICIPANT_COMPLETE'\n");
  if (mode == "command-center-failure") {
    run("cc.test_failed_kodi_watched_commit_blocks_completion(); assert cc.response()['status']=='CHECKPOINT_FAILED'\n");
    assert(!InfinityScriptPersistence::EssentialWritesAuthorized(23));
    std::cout << "PASS actual first-party failed save never authorizes termination\n" << std::flush;
    std::_Exit(0);
  }
  if (mode == "sqlite-renamed") run("try: c.execute('INSERT INTO history VALUES(999)')\nexcept sqlite3.DatabaseError: pass\nelse: raise AssertionError('renamed SQLite handle retained optional authorization')\n");
  assert(InfinityScriptPersistence::CloseParticipantWrites(23));
  if (mode == "unverified-child-output") {
    const auto proof = InfinityScriptPersistence::EssentialWrites();
    assert(std::any_of(proof.blockers.begin(),proof.blockers.end(),[](const auto& why) {
      return why.find("unobserved_diagnostic_child_output") != std::string::npos;
    }));
    assert(!InfinityScriptPersistence::SealEssentialWrites(23));
    assert(!InfinityScriptPersistence::EssentialWritesAuthorized(23));
    std::cout << "PASS unverified child output remains an essential blocker\n" << std::flush;
    std::_Exit(0);
  }
  if (mode == "unknown-descriptor") {
    const auto proof = InfinityScriptPersistence::EssentialWrites();
    assert(std::find(proof.blockers.begin(),proof.blockers.end(),"completed_native_write_target_unconfirmed") != proof.blockers.end());
    assert(!InfinityScriptPersistence::SealEssentialWrites(23));
    assert(!InfinityScriptPersistence::EssentialWritesAuthorized(23));
    std::cout << "PASS unresolved actual descriptor conversion fails closed\n" << std::flush;
    std::_Exit(0);
  }
  if (mode == "file-lock") {
    assert(!InfinityScriptPersistence::SealEssentialWrites(23));
    run("fcntl.flock(fd,fcntl.LOCK_UN)\n");
  }
  if (mode == "descriptor-race" || mode == "rename-race") {
    assert(!InfinityScriptPersistence::SealEssentialWrites(23));
    { std::lock_guard<std::mutex> lock(delayMutex); delayReleased = true; delayChanged.notify_all(); }
    run("t.join(5); assert not t.is_alive(); baseline=old_open(shared,'rb').read()\n");
  }
  if (mode == "buffer-drain" || mode == "layered" || mode == "cached-buffer" || mode == "buffer-fd-spoof") {
    assert(!InfinityScriptPersistence::SealEssentialWrites(23));
    run("f.flush()\n");
  }
  const auto before = InfinityScriptPersistence::EssentialWrites();
  for (const auto& why : before.blockers) std::cerr << why << '\n';
  assert(before.blockers.empty());
  assert(InfinityScriptPersistence::SealEssentialWrites(23));
  assert(InfinityScriptPersistence::EssentialWritesAuthorized(23));
  if (mode == "observer-denials") run("from pathlib import Path\nfor operation in (lambda: os.open(shared,os.O_WRONLY|os.O_TRUNC),lambda: open(shared,'w'),lambda: os.mkdir(root+'/profile/late'),lambda: Path(shared).write_text('BAD')):\n try: operation()\n except PermissionError: pass\n else: raise AssertionError('observer admitted a sealed mutation')\n");
  if (mode == "memory-buffer") run("memory.write('still RAM'); memory.flush()\n");
  if (mode == "late-chmod") run("try: os.chmod(shared,0o777)\nexcept PermissionError: pass\nelse: raise AssertionError('metadata mutation crossed seal')\n");
  if (mode == "pillow-fd") run("enc=core.raw_encoder('RGB','RGB'); enc.setimage(im)\ntry: enc.encode_to_file(fd)\nexcept PermissionError: pass\nelse: raise AssertionError('native encoder descriptor write crossed seal')\nassert old_open(shared,'rb').read()==baseline\n");
  if (mode == "pillow-ppm") run("try: im.save_ppm(shared)\nexcept PermissionError: pass\nelse: raise AssertionError('native encoder fopen crossed seal')\nassert old_open(shared,'rb').read()==baseline\n");
  if (mode == "descriptor-race" || mode == "rename-race") run("try: old_write(cachefd,b'BAD')\nexcept PermissionError: pass\nelse: raise AssertionError('retargeted descriptor wrote after seal')\nassert old_open(shared,'rb').read()==baseline\n");
  if (mode == "late-mmap") run("try: mmap.mmap(fd,9)\nexcept PermissionError: pass\nelse: raise AssertionError('writable mapping crossed seal')\n");
  if (mode == "late-ctypes") run("try: ctypes.CDLL(None)\nexcept PermissionError: pass\nelse: raise AssertionError('opaque native capability crossed seal')\n");
  if (mode == "cached-write") run("try: old_write(fd,b'BAD')\nexcept PermissionError: pass\nelse: raise AssertionError('cached os.write escaped')\n");
  if (mode == "cached-pwrite") run("try: old_pwrite(fd,b'BAD',0)\nexcept PermissionError: pass\nelse: raise AssertionError('cached pwrite escaped')\n");
  if (mode == "cached-writev") run("try: old_writev(fd,[b'BAD'])\nexcept PermissionError: pass\nelse: raise AssertionError('cached writev escaped')\n");
  if (mode == "raw" || mode == "raw-fd-spoof") run("try: old_raw_write(f,b'BAD')\nexcept PermissionError: pass\nelse: raise AssertionError('cached raw method escaped')\n");
  if (mode == "late-raw-open") run("try: old_raw(shared,'w')\nexcept PermissionError: pass\nelse: raise AssertionError('raw constructor truncated protected file')\n");
  if (mode == "late-cached-open") run("try: old_open(shared,'w')\nexcept PermissionError: pass\nelse: raise AssertionError('cached open truncated protected file')\n");
  if (mode == "cached-rename") run("try: old_rename(shared,shared+'.moved')\nexcept PermissionError: pass\nelse: raise AssertionError('cached rename escaped')\n");
  if (mode == "cached-remove") run("try: old_remove(shared)\nexcept PermissionError: pass\nelse: raise AssertionError('cached remove escaped')\n");
  if (mode == "buffer-drain" || mode == "layered" || mode == "cached-buffer" || mode == "buffer-fd-spoof") run("try: f.write(b'BAD' if binary_buffer else 'BAD'); f.flush()\nexcept PermissionError: pass\nelse: raise AssertionError('buffered write escaped')\n");
  if (mode == "optional-blocked") run("assert t.is_alive() and not e.is_set()\n");
  // Denied operations are diagnostic; no essential bytes were changed.
  assert(InfinityScriptPersistence::EssentialWritesAuthorized(23));
  if (mode != "optional-blocked" && mode != "sqlite-attach" && mode != "descriptor-race" && mode != "rename-race" && mode.rfind("pillow-",0)!=0) run("assert old_open(shared,'rb').read()==b'essential'\n");
  std::cout << "PASS " << mode << "; actual CPython " << PY_VERSION << "; no interpreter retirement required\n" << std::flush;
  std::_Exit(0); // Whole HOST process only. This is not Android death evidence.
}
'''

def main():
    parser=argparse.ArgumentParser()
    python = parser.add_mutually_exclusive_group(required=True)
    python.add_argument('--python-source',type=Path)
    python.add_argument('--python-prefix',type=Path)
    parser.add_argument('--sqlite-include',type=Path,required=True)
    parser.add_argument('--pillow-library',type=Path)
    parser.add_argument('--command-center-runtime',type=Path)
    parser.add_argument('--compat-runtime',type=Path)
    parser.add_argument('--ambient-library',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    runtime=HERE/'runtime'
    observer=(runtime/'observer.py').read_text()
    header=runtime/'xbmc/interfaces/python/InfinityPythonPersistenceSource.h'
    header.write_text('#pragma once\n// Generated from runtime/observer.py; verified by the source gate.\ninline constexpr const char* INFINITY_PYTHON_PERSISTENCE_SOURCE = R"infinity_source('+observer+')infinity_source";\n')
    base=ROOT/'repairs/android-checkpoint-shutdown/runtime/native/overlay/xbmc'
    with tempfile.TemporaryDirectory(prefix='essential-native-') as folder:
        folder=Path(folder); source=folder/'test.cpp'; binary=folder/'test'
        source.write_text(CODE)
        prefix=args.python_prefix or args.python_source.parent/'python3117'
        library=prefix/'lib' if args.python_prefix else args.python_source
        python_includes=[prefix/'include/python3.11'] if args.python_prefix else [args.python_source/'Include',args.python_source]
        includes=[runtime/'xbmc', runtime/'xbmc/interfaces/python', base, base/'interfaces/python',
                  *python_includes,args.sqlite_include]
        subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-pthread',
                        *['-I'+str(p) for p in includes],str(source),'-L'+str(library),
                        '-lpython3.11','-l:libsqlite3.so.0','-ldl','-lm','-lcrypto','-Wl,--export-dynamic','-o',str(binary)],check=True)
        env=dict(os.environ,LD_LIBRARY_PATH=str(library),
                 PYTHONHOME=str(prefix),PYTHONPATH=str(prefix/'lib/python3.11')+':'+str(prefix/'lib/python3.11/lib-dynload'),
                 PYTHONDONTWRITEBYTECODE='1')
        results=[]
        cases=['cached-write','cached-pwrite','cached-writev','raw','raw-fd-spoof','buffer-fd-spoof','late-raw-open','late-cached-open',
               'cached-rename','cached-remove','late-chmod','late-mmap','late-ctypes','buffer-drain','layered','cached-buffer','optional-blocked','sqlite-attach',
               'descriptor-race','rename-race','sqlite-renamed','sqlite-row-factory','file-lock',
               'pathlike','memory-buffer','observer-denials','unknown-descriptor','uname-combined-flags','unverified-child-output']
        if args.pillow_library:
            native=folder/'native';native.mkdir();(native/'lib_imaging.so').write_bytes(args.pillow_library.read_bytes())
            env['KODI_ANDROID_LIBS']=str(native)
            cases+=['pillow-fd','pillow-ppm']
        if args.command_center_runtime:
            assert hashlib.sha256((args.command_center_runtime/'persistence_participant.py').read_bytes()).hexdigest() == '7658db0f21c20853f272f61832e720df02b2b4b9ebaeba83ca1c7ba8758e1b9b'
            env['INFINITY_CC_RUNTIME']=str(args.command_center_runtime.resolve())
            env['INFINITY_CC_TEST']=str(ROOT/'repairs/android-checkpoint-shutdown/runtime-tests/test_runtime_checkpoint.py')
            cases+=['command-center-save','command-center-failure']
        if args.compat_runtime:
            assert hashlib.sha256(args.compat_runtime.read_bytes()).hexdigest() == 'eb07f7cac8e773b5edc770d853618ca12a21c6279224fcfb04e23801c90077be'
            env['INFINITY_COMPAT_RUNTIME']=str(args.compat_runtime.resolve())
            cases+=['compat-save','compat-failure']
        if args.ambient_library:
            native=folder/'native';native.mkdir(exist_ok=True)
            data=args.ambient_library.read_bytes()
            assert hashlib.sha256(data).hexdigest() == 'a876a76abe4faea63046953579899b0b7a67572722c2ed92331e41fcd1475684'
            (native/'libinfinityambient.so').write_bytes(data)
            env['KODI_ANDROID_LIBS']=str(native)
            cases+=['ambient-contract']
        for case in cases:
            directory=folder/case; (directory/'profile').mkdir(parents=True); (directory/'cache').mkdir()
            if case == 'ambient-contract':
                for name in ('outside','changed','alias'): (directory/name).mkdir()
                (directory/'outside/libinfinityambient.so').write_bytes(data)
                (directory/'changed/libinfinityambient.so').write_bytes(data+b'changed')
                (directory/'alias/libinfinityambient.so').symlink_to(native/'libinfinityambient.so')
            result=subprocess.run([str(binary),case,str(directory)],env=env,capture_output=True,text=True,timeout=20)
            results.append({'case':case,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
            print(case,result.returncode,result.stderr,flush=True)
        report={'scope':'production native Python observer and C entry hooks, pinned CPython 3.11',
                'results':results,'all_passed':all(r['exit_code']==0 for r in results),
                'android_process_death_verified':False,'apk_deliverable':False}
        args.out.write_text(json.dumps(report,indent=2)+'\n')
        if not report['all_passed']: raise SystemExit(1)

if __name__=='__main__': main()
