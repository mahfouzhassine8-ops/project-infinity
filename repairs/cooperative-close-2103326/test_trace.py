#!/usr/bin/env python3
"""Actual writer: independent late-phase capture, errno, real CPython GIL and ABI smoke."""
import argparse,json,os,shlex,subprocess,tempfile,unittest
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args()
header=a.source.resolve()/'xbmc/platform/android/activity'
root=Path(__file__).resolve().parent
code=r'''
#include "InfinityShutdownTrace.h"
#include <cerrno>
int main(int argc,char**argv){
 if(argc!=2)return 2;
 InfinityShutdownTrace::Configure(argv[1]);InfinityShutdownTrace::Begin();
 errno=EDOM;InfinityShutdownTrace::Event("check","capture.errno");if(errno!=EDOM)return 3;
 for(unsigned i=0;i<9000;i++)InfinityShutdownTrace::Event("check","thread.low_level");
 {InfinityShutdownTrace::Scope end("cleanup.after_detail_limit");}
 InfinityShutdownTrace::Event("milestone","process.exit_requested");
 return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 d=Path(d);cpp=d/'test.cpp';cpp.write_text(code);exe=d/'test'
 subprocess.run(['g++','-std=c++17','-pthread','-Wall','-Wextra','-Werror','-Wshadow','-Wconversion','-I'+str(header),str(cpp),'-o',str(exe)],check=True)
 subprocess.run([str(exe),str(d)],check=True)
 detail=[json.loads(x) for x in (d/'infinity-shutdown-native.jsonl').read_text().splitlines()]
 critical=[json.loads(x) for x in (d/'infinity-shutdown-native.jsonl.critical').read_text().splitlines()]
 assert len(detail)==8193 and detail[-1]['kind']=='limit'
 assert critical[-1]['phase']=='process.exit_requested'
 assert any(r['phase']=='cleanup.after_detail_limit' and r['kind']=='end' for r in critical)
 old=(d/'infinity-shutdown-native.jsonl.critical').read_bytes()
 subprocess.run([str(exe),str(d)],check=True)
 assert (d/'infinity-shutdown-native.jsonl.critical.previous').read_bytes()==old
 print('PASS: detail saturation does not hide later cleanup; independent previous capture; errno intact')
 if os.environ.get('GITHUB_ACTIONS')=='true':
  compiler=Path(os.environ['ANDROID_HOME'])/'ndk'/os.environ['NDK_VER']/'toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android21-clang++'
  subprocess.run([str(compiler),'-std=c++17','-Wall','-Wextra','-Werror','-Wconversion','-Wshadow','-I'+str(header),str(cpp),'-o',str(d/'android-api21')],check=True)
  print('PASS: exact NDK ARM64/API-21 link (not executed on host)')
# Reuse the established *real* CPython test with the new production header.
legacy=root.parent/'shutdown-diagnostics-2103325/test_native.py'
text=legacy.read_text().split("if __name__=='__main__':",1)[0].replace('infinity-shutdown-2103325-v1','infinity-shutdown-2103326-v1')
ns={'__file__':str(legacy),'__name__':'real_gil_trace_test'}
import sys
sys.path.insert(0,str(legacy.parent));exec(compile(text,str(legacy),'exec'),ns)
ns['HERE']=header;ns['SOURCE']=None
suite=unittest.TestSuite([ns['NativeEvidence']('test_real_gil_wait_and_concurrent_durable_rows')])
if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():raise SystemExit(1)
