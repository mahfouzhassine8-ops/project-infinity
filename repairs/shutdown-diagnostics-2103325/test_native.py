#!/usr/bin/env python3
"""Real CPython GIL wait evidence; no faked Python API and no device claim."""
import argparse,json,os,shlex,subprocess,tempfile,unittest,sys
from pathlib import Path
import native_patch
HERE=Path(__file__).resolve().parent
HARNESS=r'''
#include <Python.h>
#include "InfinityShutdownTrace.h"
#include <chrono>
#include <fstream>
#include <iostream>
#include <thread>
#include <vector>
#include <cassert>
std::string read(const std::string& p) { std::ifstream f(p);return {std::istreambuf_iterator<char>(f),{}}; }
int main(int argc,char**argv) {
 assert(argc==2); std::string dir=argv[1];
 InfinityShutdownTrace::Configure(dir.c_str());
 { InfinityShutdownTrace::Scope off("startup.disabled"); }
 assert(read(dir+"/infinity-shutdown-native.jsonl").empty());
 InfinityShutdownTrace::Begin();
 errno=EDOM;InfinityShutdownTrace::Event("milestone","test.errno");assert(errno==EDOM);
 Py_Initialize(); auto* owner=PyThreadState_Get(); auto* waiting=PyThreadState_New(owner->interp);
 std::thread worker([&]{
   InfinityShutdownTrace::Scope evidence("python.abort.gil_acquire",77);
   PyEval_RestoreThread(waiting); evidence.End();
   PyThreadState_Clear(waiting);PyThreadState_DeleteCurrent();
 });
 const auto until=std::chrono::steady_clock::now()+std::chrono::seconds(3);
 while(read(dir+"/infinity-shutdown-native.jsonl").find("python.abort.gil_acquire")==std::string::npos) {
   assert(std::chrono::steady_clock::now()<until);std::this_thread::sleep_for(std::chrono::milliseconds(5));
 }
 std::this_thread::sleep_for(std::chrono::milliseconds(250));
 auto blocked=read(dir+"/infinity-shutdown-native.jsonl");
 assert(blocked.find("\"kind\":\"end\"")==std::string::npos);
 PyEval_SaveThread();worker.join();PyEval_RestoreThread(owner);
 { InfinityShutdownTrace::Scope finalizer("python.runtime.finalize");Py_Finalize(); }
 std::vector<std::thread> threads;
 for(int i=0;i<12;i++)threads.emplace_back([]{
   for(int j=0;j<20;j++) {InfinityShutdownTrace::Scope x("test.concurrent");}
 });
 for(auto& t:threads)t.join();
 auto before=read(dir+"/infinity-shutdown-native.jsonl");
 InfinityShutdownTrace::Begin();assert(before==read(dir+"/infinity-shutdown-native.jsonl"));
 std::cout<<"PASS: actual CPython GIL wait persisted, completed after release; concurrent records; no startup I/O; no deadline/kill. Python "<<PY_VERSION<<"\n";
}
'''
class NativeEvidence(unittest.TestCase):
 def test_real_gil_wait_and_concurrent_durable_rows(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);cpp=root/'test.cpp';cpp.write_text(HARNESS);exe=root/'test'
   flags=shlex.split(subprocess.check_output(['python3-config','--embed','--cflags','--ldflags'],text=True))
   libdir=next((f[2:] for f in flags if f.startswith('-L')),None)
   for i,f in enumerate(flags):
    if f.startswith('-lpython') and libdir and not (Path(libdir)/('lib'+f[2:]+'.so')).exists():
     actual=Path(libdir)/('lib'+f[2:]+'.so.1.0')
     if actual.is_file():flags[i]=str(actual)
   subprocess.run(['g++','-std=c++17','-pthread','-DINFINITY_SHUTDOWN_TRACE_TEST','-UNDEBUG','-I'+str(HERE),str(cpp),'-o',str(exe),*flags,'-UNDEBUG'],check=True)
   env=dict(os.environ,PYTHONHOME=subprocess.check_output(['python3-config','--prefix'],text=True).strip())
   if libdir:env['LD_LIBRARY_PATH']=libdir+':'+env.get('LD_LIBRARY_PATH','')
   subprocess.run([str(exe),str(root)],env=env,check=True,timeout=10)
   rows=[json.loads(line) for line in (root/'infinity-shutdown-native.jsonl').read_text().splitlines()]
   begin={r['span_id']:r for r in rows if r['kind']=='begin'};end={r['span_id']:r for r in rows if r['kind']=='end'}
   self.assertEqual(begin.keys(),end.keys());self.assertEqual(len(begin),242)
   blocked=next(r for r in end.values() if r['phase']=='python.abort.gil_acquire')
   self.assertGreaterEqual(blocked['duration_ns']/1000000,250)
   self.assertTrue(all(r['engine']=='infinity-shutdown-2103325-v1' for r in rows));self.assertEqual(len({r['session_start_ns'] for r in rows}),1)
 def test_exact_parent_transforms(self):
  if not SOURCE:return
  parent=json.loads((HERE/'preimages.json').read_text())
  for name in native_patch.FILES:
   text=(SOURCE/name).read_text();self.assertEqual(native_patch.digest(text.encode()),parent[name])
   changed=native_patch.transform(name,text);self.assertNotEqual(changed,text)
   self.assertNotIn('killProcess',changed);self.assertNotIn('BeginShutdown()',changed)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path);args,rest=p.parse_known_args();SOURCE=args.source
 unittest.main(argv=['test_native.py',*rest],verbosity=2)
