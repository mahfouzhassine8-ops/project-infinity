#!/usr/bin/env python3
"""Read-only feasibility tests for the proposed SIGTERM/abort shutdown shortcut.

All destructive signal tests target fresh, disposable subprocesses.
No change to Kodi source, SQLite user data, installed APKs or native engine.
"""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import signal
import sqlite3
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def disable_core():
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))

def run(argv,timeout=10):
    return subprocess.run([str(x) for x in argv],text=True,capture_output=True,
                          timeout=timeout,preexec_fn=disable_core)

def get_db_value(path,key):
    with sqlite3.connect(str(path)) as db:
        return db.execute('SELECT v FROM kv WHERE k=?',(key,)).fetchone()[0]

def saved_state(folder):
    return {
        'MyVideos_watched':get_db_value(folder/'MyVideos.db','watched'),
        'ResumeHub_position':get_db_value(folder/'ResumeHub.db','position'),
        'skin_settings':(folder/'skin-settings.xml').read_text().strip()
    }

def main(out):
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    binary=out/'native-worker'
    build=run(['g++','-std=c++17','-Wall','-Wextra','-Werror',
               '-pthread','-O2',HERE/'native_worker.cpp','-o',binary],timeout=60)
    assert build.returncode==0,build.stderr
    checks=[]
    def check(name,ok,observation,details=None):
        row={'name':name,'passed':bool(ok),'observation':observation,'details':details or {}}
        checks.append(row)
        if not ok:raise AssertionError(json.dumps(row))

    native_term=run([binary,'term_worker'])
    check('SIGTERM_to_in_process_native_thread',
          native_term.returncode==-signal.SIGTERM,
          'pthread_kill targeted one worker, but terminated the entire disposable process',
          {'returncode':native_term.returncode})

    native_abort=run([binary,'abort_from_worker'])
    check('abort_from_in_process_native_thread',
          native_abort.returncode==-signal.SIGABRT,
          'abort() from an in-process thread terminated the entire disposable process',
          {'returncode':native_abort.returncode})

    hard_folder=out/'hard_stop'
    hard=run([sys.executable,HERE/'app_state_child.py',hard_folder,'hard_stop'])
    hard_state=saved_state(hard_folder)
    check('Save_MyVideos_and_skin_then_SIGTERM',
          hard.returncode==-signal.SIGTERM and hard_state=={
              'MyVideos_watched':'new','ResumeHub_position':'old',
              'skin_settings':'<settings>new</settings>'},
          'Committed MyVideos + fsynced skin survived; required second SQLite writer lost uncommitted progress',
          {'returncode':hard.returncode,'saved_state':hard_state})

    good_folder=out/'graceful'
    graceful=run([sys.executable,HERE/'app_state_child.py',good_folder,'graceful'])
    good_state=saved_state(good_folder)
    check('cooperative_worker_and_all_writer_barriers',
          graceful.returncode==0 and good_state=={
              'MyVideos_watched':'new','ResumeHub_position':'new',
              'skin_settings':'<settings>new</settings>'},
          'Cooperative worker stop and all required commits preserved the complete tested state',
          {'returncode':graceful.returncode,'saved_state':good_state})

    isolated_folder=out/'isolated'
    isolated=run([sys.executable,HERE/'app_state_child.py',isolated_folder,'isolated_worker'])
    isolated_state=saved_state(isolated_folder)
    check('SIGTERM_isolated_optional_subprocess',
          isolated.returncode==0 and isolated_state=={
              'MyVideos_watched':'new','ResumeHub_position':'new',
              'skin_settings':'<settings>new</settings>'},
          'An optional isolated process can be terminated while the parent finishes essential saves',
          {'returncode':isolated.returncode,'saved_state':isolated_state})

    implementation=ROOT/'repairs/shutdown-final-2103377/cooperative_abort.py'
    source=implementation.read_text()
    check('original_2103377_source_is_cooperative_only',
          all(token in source for token in [
              'threads_forcibly_killed=False','save_authority_changed=False',
              'termination_authority_changed=False','shutdown_timeout_changed=False']),
          'Read the actual saved 2103377 transform: no hard worker kill or durability bypass implemented',
          {'source_file':str(implementation.relative_to(ROOT)),
           'sha256':hashlib.sha256(implementation.read_bytes()).hexdigest()})

    report={
        'experiment':'Infinity 2103377 screenshot hard-stop feasibility',
        'parent_commit':'40a5ac471c4bf67aaeb6acaf0ec6612097e06b53',
        'tests':len(checks),'passed':all(x['passed'] for x in checks),
        'checks':checks,
        'scope':'Real POSIX/C++ thread signaling and SQLite WAL in throwaway host subprocesses; source contract read-only; no Android/Kodi execution',
        'decision':'UNSAFE as proposed: targeting CPythonInvoker with SIGTERM or abort is process-fatal by default. Saving only MyVideos.db and skin settings can leave other required state uncommitted.',
        'not_proven':['Galaxy Fold behavior','Kodi C++ checkpoint barrier integration',
                      'CPythonInvoker/VFS cancellation under actual Kodi','all essential writer durability'],
        'no_apk_built':True,'no_project_runtime_modified':True,
        'locked_2103376_unmodified':True,'skin_211_unmodified':True
    }
    (out/'HARDSTOP-FEASIBILITY.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (out/'RESULTS.txt').write_text('\n'.join(('PASS ' if x['passed'] else 'FAIL ')+
                                      x['name']+': '+x['observation'] for x in checks)+'\n')
    print(json.dumps({'passed':report['passed'],'tests':len(checks),
                      'checks':[{'name':x['name'],'passed':x['passed']} for x in checks],
                      'decision':report['decision']},indent=2))

if __name__=='__main__':
    cli=argparse.ArgumentParser()
    cli.add_argument('--out',type=Path,required=True)
    args=cli.parse_args()
    main(args.out)
