#!/usr/bin/env python3
"""Compile and exercise the production observer in the pinned CPython 3.11 ABI."""
import argparse
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
      "shared=root+'/profile/state'; private=root+'/cache/state'\n");
  InfinityScriptPersistence::Admit(1, "test.provider:service.py");
  auto* context = InfinityPythonPersistence::Start(1, owner->interp);
  if (PyErr_Occurred()) PyErr_Print();
  if (!context || !context->observer) {
    std::cerr << InfinityScriptPersistence::Failure() << '\n';
    for (const auto& why : InfinityScriptPersistence::EssentialWrites().blockers) std::cerr << why << '\n';
    return 21;
  }
  if (mode == "buffer-drain") run("f=open(shared,'w'); f.write('essential')\n");
  else if (mode == "layered") run("r=io.FileIO(shared,'w'); b=io.BufferedWriter(r); f=io.TextIOWrapper(b); f.write('essential')\n");
  else if (mode == "cached-buffer") run("f=old_open(shared,'w'); f.write('essential')\n");
  else if (mode == "optional-blocked") run("import threading\ne=threading.Event(); t=threading.Thread(target=e.wait); t.start()\nf=open(private,'w'); f.write('unfinished')\n");
  else if (mode == "sqlite-attach") run("c=sqlite3.connect(root+'/cache/main.db'); c.execute('ATTACH DATABASE ? AS shared',(root+'/profile/history.db',)); c.execute('CREATE TABLE shared.history(value)'); c.execute('INSERT INTO shared.history VALUES(321)'); c.commit(); c.close()\n");
  else if (mode == "raw") run("f=old_raw(shared,'w'); old_raw_write(f,b'essential')\n");
  else run("fd=os.open(shared, os.O_CREAT|os.O_RDWR, 0o600); os.write(fd,b'essential')\n");
  assert(InfinityScriptPersistence::BeginWriteProtection(23, {root+"/profile"}, {root+"/cache"}));
  assert(InfinityScriptPersistence::CloseParticipantWrites(23));
  if (mode == "buffer-drain" || mode == "layered" || mode == "cached-buffer") {
    assert(!InfinityScriptPersistence::SealEssentialWrites(23));
    run("f.flush()\n");
  }
  const auto before = InfinityScriptPersistence::EssentialWrites();
  for (const auto& why : before.blockers) std::cerr << why << '\n';
  assert(before.blockers.empty());
  assert(InfinityScriptPersistence::SealEssentialWrites(23));
  assert(InfinityScriptPersistence::EssentialWritesAuthorized(23));
  if (mode == "late-chmod") run("try: os.chmod(shared,0o777)\nexcept PermissionError: pass\nelse: raise AssertionError('metadata mutation crossed seal')\n");
  if (mode == "late-mmap") run("try: mmap.mmap(fd,9)\nexcept PermissionError: pass\nelse: raise AssertionError('writable mapping crossed seal')\n");
  if (mode == "late-ctypes") run("try: ctypes.CDLL(None)\nexcept PermissionError: pass\nelse: raise AssertionError('opaque native capability crossed seal')\n");
  if (mode == "cached-write") run("try: old_write(fd,b'BAD')\nexcept PermissionError: pass\nelse: raise AssertionError('cached os.write escaped')\n");
  if (mode == "cached-pwrite") run("try: old_pwrite(fd,b'BAD',0)\nexcept PermissionError: pass\nelse: raise AssertionError('cached pwrite escaped')\n");
  if (mode == "cached-writev") run("try: old_writev(fd,[b'BAD'])\nexcept PermissionError: pass\nelse: raise AssertionError('cached writev escaped')\n");
  if (mode == "raw") run("try: old_raw_write(f,b'BAD')\nexcept PermissionError: pass\nelse: raise AssertionError('cached raw method escaped')\n");
  if (mode == "late-raw-open") run("try: old_raw(shared,'w')\nexcept PermissionError: pass\nelse: raise AssertionError('raw constructor truncated protected file')\n");
  if (mode == "late-cached-open") run("try: old_open(shared,'w')\nexcept PermissionError: pass\nelse: raise AssertionError('cached open truncated protected file')\n");
  if (mode == "cached-rename") run("try: old_rename(shared,shared+'.moved')\nexcept PermissionError: pass\nelse: raise AssertionError('cached rename escaped')\n");
  if (mode == "cached-remove") run("try: old_remove(shared)\nexcept PermissionError: pass\nelse: raise AssertionError('cached remove escaped')\n");
  if (mode == "buffer-drain" || mode == "layered" || mode == "cached-buffer") run("try: f.write('BAD'); f.flush()\nexcept PermissionError: pass\nelse: raise AssertionError('buffered write escaped')\n");
  if (mode == "optional-blocked") run("assert t.is_alive() and not e.is_set()\n");
  // Denied operations are diagnostic; no essential bytes were changed.
  assert(InfinityScriptPersistence::EssentialWritesAuthorized(23));
  if (mode != "optional-blocked" && mode != "sqlite-attach") run("assert old_open(shared,'rb').read()==b'essential'\n");
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
                        '-lpython3.11','-l:libsqlite3.so.0','-ldl','-lm','-lcrypto','-o',str(binary)],check=True)
        env=dict(os.environ,LD_LIBRARY_PATH=str(library),
                 PYTHONHOME=str(prefix),PYTHONPATH=str(prefix/'lib/python3.11')+':'+str(prefix/'lib/python3.11/lib-dynload'),
                 PYTHONDONTWRITEBYTECODE='1')
        results=[]
        for case in ['cached-write','cached-pwrite','cached-writev','raw','late-raw-open','late-cached-open',
                     'cached-rename','cached-remove','late-chmod','late-mmap','late-ctypes','buffer-drain','layered','cached-buffer','optional-blocked','sqlite-attach']:
            directory=folder/case; (directory/'profile').mkdir(parents=True); (directory/'cache').mkdir()
            result=subprocess.run([str(binary),case,str(directory)],env=env,capture_output=True,text=True,timeout=20)
            results.append({'case':case,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
            print(case,result.returncode,result.stderr,flush=True)
        report={'scope':'production native Python observer and C entry hooks, pinned CPython 3.11',
                'results':results,'all_passed':all(r['exit_code']==0 for r in results),
                'android_process_death_verified':False,'apk_deliverable':False}
        args.out.write_text(json.dumps(report,indent=2)+'\n')
        if not report['all_passed']: raise SystemExit(1)

if __name__=='__main__': main()
