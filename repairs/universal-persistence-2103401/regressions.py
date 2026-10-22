"""Run existing native gates against exact candidate inputs without editing old tests."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
NATIVE_CASES = ['cached-write','cached-pwrite','cached-writev','raw','raw-fd-spoof',
 'buffer-fd-spoof','late-raw-open','late-cached-open','cached-rename','cached-remove',
 'late-chmod','late-mmap','late-ctypes','buffer-drain','layered','cached-buffer',
 'optional-blocked','sqlite-attach','descriptor-race','rename-race','sqlite-renamed',
 'sqlite-row-factory','file-lock','pathlike','memory-buffer','observer-denials',
 'unknown-descriptor','unverified-posix-spawn','late-native-child','marker-filename',
 'readonly-proc-close','readonly-proc-flush','readonly-proc-late','readonly-regular-input',
 'readonly-proc-user-sync-failure','writable-proc-real-write','readonly-proc-override',
 'readonly-proc-writable-retarget','writable-reader-retarget']
SQLITE_CASES = ['pending','pending-wal','attach','attach-wal','optional-pending',
 'late-write','late-write-wal','uri-vfs']

def load(name):
    spec=importlib.util.spec_from_file_location(name,HERE.parent/'essential-first-2103377'/('test_runtime_'+name+'.py'))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','overlay','python-prefix','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();prefix=a.python_prefix.resolve()
    includes=[a.overlay.resolve()/'xbmc',a.overlay.resolve()/'xbmc/interfaces/python',
              a.source.resolve()/'xbmc',a.source.resolve()/'xbmc/interfaces/python',
              prefix/'include/python3.11',Path('/usr/local/include')]
    env=dict(os.environ,LD_LIBRARY_PATH=str(prefix/'lib'),PYTHONHOME=str(prefix),
             PYTHONPATH=str(prefix/'lib/python3.11')+':'+str(prefix/'lib/python3.11/lib-dynload'),
             PYTHONDONTWRITEBYTECODE='1')
    results=[]
    with tempfile.TemporaryDirectory(prefix='universal-regressions-') as tmp:
        root=Path(tmp)
        for kind,cases in [('native',NATIVE_CASES),('sqlite',SQLITE_CASES)]:
            module=load(kind);cpp=root/(kind+'.cpp');binary=root/(kind+'-test')
            cpp.write_text(module.CODE if kind=='native' else module.BRIDGE)
            command=['g++','-std=c++17','-Wall','-Wextra','-Werror','-pthread',*['-I'+str(i) for i in includes],str(cpp),'-l:libsqlite3.so.0','-o',str(binary)]
            if kind=='native':command+=['-L'+str(prefix/'lib'),'-lpython3.11','-ldl','-lm','-lcrypto','-Wl,--export-dynamic']
            else:command+=['-fPIC','-shared']
            subprocess.run(command,check=True)
            for case in cases:
                directory=root/case;(directory/'profile').mkdir(parents=True);(directory/'cache').mkdir()
                command=[str(binary),case,str(directory)] if kind=='native' else [str(prefix/'bin/python3.11'),module.__file__,'--library',str(binary),'--case',case]
                r=subprocess.run(command,env=env,capture_output=True,text=True,timeout=30)
                record=dict(kind=kind,case=case,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr)
                if kind=='sqlite' and r.returncode==0:
                    receipt=json.loads(r.stdout);folder=Path(receipt['folder'])
                    with sqlite3.connect(folder/'profile/history.db') as db:
                        assert [list(row) for row in db.execute('SELECT position FROM history')]==receipt['expected']
                        assert db.execute('PRAGMA integrity_check').fetchone()==('ok',)
                    record['reopened_rows_and_integrity_verified']=True;shutil.rmtree(folder)
                results.append(record);print(kind,case,r.returncode,r.stderr,flush=True)
    report=dict(scope='existing regression code with full matching candidate native source and overlay',
                results=results,passed=all(r['exit_code']==0 for r in results),
                android_validated=False,physical_fold_verified=False)
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if report['passed'] else 1)

if __name__=='__main__':main()
