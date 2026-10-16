#!/usr/bin/env python3
"""Initialization controls against the production CPython observer, not a Fold clone.

Retained-module fixtures demonstrate shared dependency failures. They are not
evidence that any module in the user's Diggz installation is defective.
"""
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
#include <sstream>
#include <sys/syscall.h>
static void run(const char* code) {
  if(PyRun_SimpleString(code)!=0) { PyErr_Print();std::_Exit(20); }
}
static std::string json(const std::string& text) {
  std::string result="\"";
  const char* hex="0123456789abcdef";
  for(unsigned char c:text) {
    if(c=='"' || c=='\\') { result+='\\';result+=c; }
    else if(c<32) { result+="\\u00";result+=hex[c>>4];result+=hex[c&15]; }
    else result+=c;
  }
  return result+'"';
}
int main(int argc,char** argv) {
  assert(argc==4);
  const std::string mode=argv[1],root=argv[2],output=argv[3];
  const bool concurrent=mode=="concurrent-37";
  const bool bad=mode!="fresh" && mode!="loaded-37" && !concurrent;
  const unsigned count=(mode=="loaded-37" || mode=="retained-module-shadow-37" || concurrent)?37:1;
  Py_Initialize();auto* main=PyThreadState_Get();
  std::vector<PyThreadState*> bootstrap;
  std::vector<std::thread> workers;
  std::vector<std::string> pendingErrors(count),stages(count);
  const auto initialize=[&](unsigned index) {
    auto* owner=Py_NewInterpreter();assert(owner);
    auto* globals=PyModule_GetDict(PyImport_AddModule("__main__"));
    auto* path=PyUnicode_FromString(root.c_str());assert(path);
    assert(PyDict_SetItemString(globals,"fixture_root",path)==0);Py_DECREF(path);
    // Production imports a real Kodi VFS module. The host adapter exposes its
    // required File entry point; a separate failure control deliberately omits it.
    run("import sys, types\nvfs=types.ModuleType('xbmcvfs')\nvfs.File=object\nsys.modules['xbmcvfs']=vfs\n");
    if(mode=="vfs-missing-file")run("del vfs.File\n");
    if(mode=="native-descriptor-reader")
      run("import _io\nclass ChangedFileIO(_io.FileIO):\n def writable(self): return False\n_io.FileIO=ChangedFileIO\n");
    if(mode=="retained-module-shadow-37" || mode=="deep-import-trace" || mode=="constructor-ctypes" ||
       mode=="native-import" || mode=="exception-format-failure")
      run("sys.path.insert(0, fixture_root+'/retained-addon/lib')\n");
    const int id=static_cast<int>(index+1);
    if(mode=="pending-entry-exception") {
      auto* raised=PyRun_String("raise RuntimeError('entry-state-sentinel')",Py_file_input,globals,globals);
      assert(!raised && PyErr_Occurred());
    }
    auto* context=InfinityPythonPersistence::Start(id,owner->interp);
    if(mode=="pending-entry-exception")assert(!context);else assert(context);
    stages[index]=context?context->initializationStage:"native.entry.pending_exception";
    if(bad) {
      if(mode=="native-descriptor-reader")assert(!PyErr_Occurred());
      else {
        assert(PyErr_Occurred());
        PyObject *type=nullptr,*value=nullptr,*trace=nullptr;
        PyErr_Fetch(&type,&value,&trace);
        assert(type && value && trace);
        pendingErrors[index]=reinterpret_cast<PyTypeObject*>(type)->tp_name;
        // Formatting failure must not replace the actual original exception.
        if(mode=="exception-format-failure")assert(pendingErrors[index]=="OriginalFailure");
        else if(mode=="vfs-missing-file")assert(type==PyExc_AttributeError);
        else if(mode=="native-import")assert(type==PyExc_ImportError);
        else assert(type==PyExc_RuntimeError);
        PyErr_Restore(type,value,trace);PyErr_Clear();
      }
      assert(!context || !context->observer);
    } else assert(context->observer && context->connectionType && context->rawWrite && !PyErr_Occurred());
    if(concurrent)PyEval_ReleaseThread(owner);
    else PyThreadState_Swap(main);
  };
  for(unsigned i=0;i<count;++i) {
    InfinityScriptPersistence::Admit(static_cast<int>(i+1),"fixture.loaded."+std::to_string(i+1)+":service.py");
    if(concurrent)bootstrap.push_back(PyThreadState_New(main->interp));
  }
  if(concurrent) {
    auto* saved=PyEval_SaveThread();
    for(unsigned i=0;i<count;++i)workers.emplace_back([&,i]{PyEval_AcquireThread(bootstrap[i]);initialize(i);});
    for(auto& worker:workers)worker.join();
    PyEval_RestoreThread(saved);
  } else for(unsigned i=0;i<count;++i)initialize(i);
  const auto proof=InfinityScriptPersistence::Snapshot();
  assert(proof.active==count && proof.observed==(bad?0:count));
  if(bad) {
    assert(proof.blockingCount>=count);
    assert(InfinityScriptPersistence::BeginWriteProtection(23,{root+"/profile"},{root+"/cache"}));
    assert(InfinityScriptPersistence::CloseParticipantWrites(23));
    assert(!InfinityScriptPersistence::SealEssentialWrites(23));
    assert(!InfinityScriptPersistence::EssentialWritesAuthorized(23));
  } else assert(proof.blockingCount==0);
  std::ostringstream report;
  report<<"{\"active\":"<<proof.active<<",\"observed\":"<<proof.observed
        <<",\"blocking_count\":"<<proof.blockingCount<<",\"fail_closed\":"<<(bad?"true":"false")
        <<",\"stage\":"<<json(stages[0])<<",\"original_exception\":"<<json(pendingErrors[0])<<",\"blockers\":[";
  bool first=true;
  for(const auto& item:proof.blockers) {
    if(!first)report<<',';
    first=false;
    report<<"{\"reason\":"<<json(item.reason)<<",\"detail\":"<<json(item.detail)<<'}';
  }
  report<<"]}\n";
  const auto bytes=report.str();
  const int fd=::open(output.c_str(),O_CREAT|O_TRUNC|O_WRONLY,0600);assert(fd>=0);
  assert(syscall(SYS_write,fd,bytes.data(),bytes.size())==static_cast<long>(bytes.size()));assert(::close(fd)==0);
  std::_Exit(0); // Host observer scope only; never Android process-death evidence.
}
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--python-prefix', type=Path, required=True)
    parser.add_argument('--sqlite-include', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    prefix = args.python_prefix.resolve()
    runtime = HERE/'runtime'
    observer = (runtime/'observer.py').read_text()
    expected = '#pragma once\n// Generated from runtime/observer.py; verified by the source gate.\ninline constexpr const char* INFINITY_PYTHON_PERSISTENCE_SOURCE = R"infinity_source('+observer+')infinity_source";\n'
    assert (runtime/'xbmc/interfaces/python/InfinityPythonPersistenceSource.h').read_text() == expected
    cases = {
        'fresh': None,
        'loaded-37': None,
        'concurrent-37': None,
        'pending-entry-exception': ('', '', 'native.entry.pending_exception', 'RuntimeError', 'entry-state-sentinel'),
        'retained-module-shadow-37': ('sqlite3.py', "raise RuntimeError('retained-addon-sqlite-sentinel')\n", 'python.import.sqlite3', 'RuntimeError', 'retained-addon-sqlite-sentinel'),
        'deep-import-trace': ('sqlite3.py', "def wrapped(depth):\n if depth: return wrapped(depth-1)\n import fixture_origin\nwrapped(30)\n", 'python.import.sqlite3', 'RuntimeError', 'deep-trace-origin'),
        'constructor-ctypes': ('ctypes.py', "raise RuntimeError('retained-addon-ctypes-sentinel')\n", 'python.import.ctypes', 'RuntimeError', 'retained-addon-ctypes-sentinel'),
        'native-import': ('fcntl.py', "raise ImportError('retained-addon-fcntl-sentinel')\n", 'native.import.fcntl', 'ImportError', 'retained-addon-fcntl-sentinel'),
        'native-descriptor-reader': ('', '', 'native.descriptor_reader.FileIO.writable', '<none>', ''),
        'vfs-missing-file': ('', '', 'python.install.xbmcvfs', 'AttributeError', "has no attribute 'File'"),
        'exception-format-failure': ('sqlite3.py', "class OriginalFailure(Exception):\n def __str__(self): raise ValueError('formatting-error-must-not-replace-original')\nraise OriginalFailure('original-message')\n", 'python.import.sqlite3', 'OriginalFailure', ''),
    }
    results = []
    with tempfile.TemporaryDirectory(prefix='infinity-init-') as temp:
        folder = Path(temp)
        source, binary = folder/'test.cpp', folder/'test'
        source.write_text(CODE)
        base = ROOT/'repairs/android-checkpoint-shutdown/runtime/native/overlay/xbmc'
        includes = [runtime/'xbmc', runtime/'xbmc/interfaces/python', base, prefix/'include/python3.11', args.sqlite_include]
        subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-pthread', *['-I'+str(p) for p in includes], str(source), '-L'+str(prefix/'lib'), '-lpython3.11', '-l:libsqlite3.so.0', '-ldl', '-lm', '-lcrypto', '-Wl,--export-dynamic', '-o', str(binary)], check=True)
        env = dict(os.environ, PYTHONHOME=str(prefix), LD_LIBRARY_PATH=str(prefix/'lib'), PYTHONDONTWRITEBYTECODE='1')
        for name, fixture in cases.items():
            root = folder/name
            for child in ('profile', 'cache', 'retained-addon/lib'): (root/child).mkdir(parents=True)
            hashes = {}
            if fixture and fixture[0]:
                path = root/'retained-addon/lib'/fixture[0]
                path.write_text(fixture[1])
                hashes[fixture[0]] = hashlib.sha256(path.read_bytes()).hexdigest()
                if name == 'deep-import-trace':
                    origin = root/'retained-addon/lib/fixture_origin.py'
                    origin.write_text("raise RuntimeError('deep-trace-origin')\n")
                    hashes[origin.name] = hashlib.sha256(origin.read_bytes()).hexdigest()
            output = root/'result.json'
            completed = subprocess.run([str(binary), name, str(root), str(output)], env=env, capture_output=True, text=True, timeout=90)
            assert completed.returncode == 0, (name, completed.returncode, completed.stderr)
            result = json.loads(output.read_text())
            if fixture:
                detail = next(b['detail'] for b in result['blockers'] if b['detail'])
                assert fixture[2] in detail and 'exception='+fixture[3] in detail and fixture[4] in detail, (name, detail)
                assert ':-1:' not in detail, detail
                assert result['fail_closed']
                if fixture[0]:
                    assert ':<module>' in detail and fixture[0] in detail, detail
                    for filename, digest in hashes.items():
                        assert hashlib.sha256((root/'retained-addon/lib'/filename).read_bytes()).hexdigest() == digest
                if name == 'deep-import-trace':
                    assert detail.index('fixture_origin.py:1:<module>') < detail.index('sqlite3.py'), detail
            results.append(dict(case=name, exit_code=completed.returncode, retained_fixture_sha256=hashes, **result))
            print(name, 'PASS', result['active'], result['observed'], flush=True)
    report = dict(scope='production observer initialization in pinned CPython 3.11.7 with host Kodi VFS adapter', results=results, all_passed=True, physical_fold_reproduced=False, actual_diggz_ecosystem_tested=False, verified_fold_userdata_tested=False, android_process_death_verified=False, apk_deliverable=False)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
