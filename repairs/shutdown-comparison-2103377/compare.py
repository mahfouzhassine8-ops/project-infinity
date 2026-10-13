#!/usr/bin/env python3
"""HOST-ONLY reproducible comparison of two proposed Infinity shutdown policies.

Runs real Linux processes, SQLite WAL transactions, fsync and a socket-blocked worker;
contains NO Kodi runtime integration and touches NO real user database or APK.
"""
import argparse
import json
import os
import signal
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

DBS = {
    'MyVideos.db':'watched', 'ResumeHub.db':'position',
    'Addons.db':'addons', 'Trakt.db':'sync',
}
XMLS = ['skin-settings.xml', 'guisettings.xml', 'favourites.xml', 'profiles.xml']
TARGETS = {
    'gemini_kill_before_all_writers_finish': False,
    'gemini_kill_after_all_writers_finish': True,
    'ours_cancel_socket_and_prove_all_writers': True,
    'ours_abandon_proven_optional_worker_only': True,
    'ours_allow_essential_writer_over_2s': True,
    'ours_refuse_exit_when_essential_writer_unknown': True,
}


def atomic(path, value):
    temp = path.with_name(path.name+'.pending')
    with temp.open('w') as f:
        f.write(value)
        f.flush(); os.fsync(f.fileno())
    os.replace(temp, path)
    fd = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)


def conn(path):
    c = sqlite3.connect(str(path), timeout=0.08)
    c.execute('PRAGMA busy_timeout=80')
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('PRAGMA synchronous=FULL')
    c.execute('CREATE TABLE IF NOT EXISTS kv(k TEXT PRIMARY KEY,v TEXT NOT NULL)')
    c.commit()
    return c


def seed(root):
    for name,key in DBS.items():
        c=conn(root/name)
        c.execute('INSERT OR REPLACE INTO kv VALUES (?,?)',(key,'old'))
        c.commit(); c.close()
    for name in XMLS:
        atomic(root/name,'old')


def monitor(root):
    state={}
    for name,key in DBS.items():
        db=sqlite3.connect(str(root/name),timeout=0.1)
        try:
            state[name]=db.execute('SELECT v FROM kv WHERE k=?',(key,)).fetchone()[0]
            state[name+'.integrity']=db.execute('PRAGMA integrity_check').fetchone()[0]
        finally:db.close()
    for name in XMLS:
        state[name]=(root/name).read_text()
    return state


def child(mode, root):
    root.mkdir(parents=True,exist_ok=True)
    seed(root)
    ready=[threading.Event(),threading.Event()]
    release=threading.Event()
    done=[threading.Event(),threading.Event()]
    def essential_writer(i,dbn):
        c=conn(root/dbn)
        c.execute('BEGIN IMMEDIATE')
        c.execute('UPDATE kv SET v=? WHERE k=?',('new',DBS[dbn]))
        ready[i].set()
        if release.wait(10):c.commit()
        else:c.rollback()
        c.close();done[i].set()
    writers=[threading.Thread(target=essential_writer,args=(0,'ResumeHub.db'),daemon=True),
             threading.Thread(target=essential_writer,args=(1,'Trakt.db'),daemon=True)]
    for w in writers:w.start()
    assert all(event.wait(1.5) for event in ready),'writer failed to begin transaction'
    sender, receiver=socket.socketpair()
    optional_stop=threading.Event(); optional_ready=threading.Event(); optional_done=threading.Event()
    def optional_socket_worker():
        optional_ready.set()
        try: receiver.recv(1)
        except OSError:pass
        optional_done.set()
    def optional_uncancellable_worker():
        optional_ready.set()
        optional_stop.wait(10)
        optional_done.set()
    worker=threading.Thread(target=optional_uncancellable_worker if mode=='ours_abandon_proven_optional_worker_only' else optional_socket_worker,daemon=True)
    worker.start();assert optional_ready.wait(1)
    # Primary settings and other database owners have finished; two genuine
    # *different* database writer transactions remain in-flight.
    for name in ('MyVideos.db','Addons.db'):
        c=conn(root/name)
        c.execute('UPDATE kv SET v=? WHERE k=?',('new',DBS[name]))
        c.commit();c.close()
    for name in XMLS:atomic(root/name,'new')
    begin=time.monotonic()
    evidence={'mode':mode,'checkpoint':{},'essential_writers_pending_at_close':2}

    def check_wal():
        # Used as the Gemini pseudocode requests; the result must be verified
        # rather than treated as a magic commit of another connection.
        for name in DBS:
            c=sqlite3.connect(str(root/name),timeout=0.03)
            c.execute('PRAGMA busy_timeout=30')
            try:evidence['checkpoint'][name]=list(c.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone())
            except sqlite3.Error as exc:evidence['checkpoint'][name]='ERROR: '+str(exc)
            c.close()
        os.sync()

    def flush_evidence(outcome):
        evidence['outcome']=outcome
        evidence['elapsed_until_shutdown_decision_seconds']=round(time.monotonic()-begin,3)
        atomic(root/'child_evidence.json',json.dumps(evidence,indent=2,sort_keys=True))

    if mode=='gemini_kill_before_all_writers_finish':
        check_wal()
        evidence['uncommitted_essential_writers']=[DBS['ResumeHub.db'],DBS['Trakt.db']]
        flush_evidence('forced_exit_with_two_required_transactions_still_open')
        os._exit(0)
    if mode=='gemini_kill_after_all_writers_finish':
        release.set()
        assert all(d.wait(2) for d in done)
        check_wal()
        flush_evidence('all_required_transactions_committed_before_forced_exit')
        os._exit(0)
    if mode=='ours_cancel_socket_and_prove_all_writers':
        sender.shutdown(socket.SHUT_RDWR)
        assert optional_done.wait(1),'optional socket did not cancel'
        release.set()
        assert all(d.wait(2) for d in done)
        check_wal()
        flush_evidence('optional_socket_cancelled_and_all_required_writes_committed')
        os._exit(0)
    if mode=='ours_abandon_proven_optional_worker_only':
        release.set()
        assert all(d.wait(2) for d in done)
        assert not optional_done.is_set(),'optional worker was expected blocked'
        check_wal()
        flush_evidence('optional_nonwriting_worker_remained_but_all_required_writes_committed')
        os._exit(0)
    if mode=='ours_allow_essential_writer_over_2s':
        time.sleep(2.20)
        release.set()
        assert all(d.wait(2) for d in done)
        check_wal()
        flush_evidence('honored_delayed_required_commits_took_more_than_two_seconds')
        os._exit(0)
    if mode=='ours_refuse_exit_when_essential_writer_unknown':
        # No exit authorization: cannot claim safe normal Close or fake receipt.
        assert not any(d.is_set() for d in done)
        with sqlite3.connect(str(root/'ResumeHub.db')) as c:
            evidence['resume_visible_at_shutdown_decision']=c.execute('SELECT v FROM kv WHERE k=?',('position',)).fetchone()[0]
        with sqlite3.connect(str(root/'Trakt.db')) as c:
            evidence['trakt_visible_at_shutdown_decision']=c.execute('SELECT v FROM kv WHERE k=?',('sync',)).fetchone()[0]
        flush_evidence('UNSAFE_TO_EXIT: essential_writers_still_active')
        # Only this disposable test cleans up and returns failure status.
        release.set();assert all(d.wait(2) for d in done)
        sender.shutdown(socket.SHUT_RDWR)
        optional_stop.set()
        sender.close();receiver.close()
        return 42
    raise ValueError(mode)


def verify(base):
    base.mkdir(parents=True,exist_ok=True)
    results=[]
    for mode,expected_durable in TARGETS.items():
        root=base/mode
        start=time.monotonic()
        proc=subprocess.run([sys.executable,__file__,'--child',mode,'--dir',str(root)],capture_output=True,text=True,timeout=12)
        elapsed=round(time.monotonic()-start,3)
        assert (root/'child_evidence.json').exists(),(mode,proc.returncode,proc.stderr)
        evidence=json.loads((root/'child_evidence.json').read_text())
        state=monitor(root)
        all_durable=all(state[name]=='new' for name in [*DBS,*XMLS])
        integrity_ok=all(state[name+'.integrity']=='ok' for name in DBS)
        busy_count=sum(isinstance(v,list) and v[0]!=0 for v in evidence['checkpoint'].values())
        match=all_durable==expected_durable and integrity_ok and (proc.returncode==(42 if mode.endswith('unknown') else 0))
        if mode=='gemini_kill_before_all_writers_finish':
            match=match and state['ResumeHub.db']=='old' and state['Trakt.db']=='old' and busy_count>=2
        if mode=='ours_allow_essential_writer_over_2s':
            match=match and elapsed>2
        if mode=='ours_refuse_exit_when_essential_writer_unknown':
            match=match and evidence['outcome'].startswith('UNSAFE_TO_EXIT') and evidence['resume_visible_at_shutdown_decision']=='old' and evidence['trakt_visible_at_shutdown_decision']=='old'
        results.append({'case':mode,'passed':bool(match),'all_required_state_durable':all_durable,
            'sqlite_integrity_ok':integrity_ok,'shutdown_process_elapsed_s':elapsed,
            'checkpoint_busy_databases':busy_count,'resume_hub':state['ResumeHub.db'],'trakt':state['Trakt.db'],
            'exit_code':proc.returncode,'decision':evidence['outcome'],'checkpoint_results':evidence['checkpoint']})
        print(('PASS' if match else 'FAIL'),mode,'elapsed=',elapsed,'resume=',state['ResumeHub.db'],
              'trakt=',state['Trakt.db'],'wal_busy=',busy_count,flush=True)
        if not match:print('ERROR',proc.stderr, state,evidence,flush=True)
    report={'scope':'HOST-ONLY SQLite WAL, actual fsync, in-process socket IO, process _exit; not Kodi/Fold',
            'tests':len(results),'passed':sum(x['passed'] for x in results),
            'all_passed':all(x['passed'] for x in results),
            'runs':results,'protected_production':True,
            'conclusion':'A verified complete persistence barrier can precede _exit; sync and WAL checkpoint of some DBs do not commit other writers. The 2.0s bound cannot guarantee both safety and promptness if a required writer is delayed.'}
    atomic(base/'COMPARE-RESULTS.json',json.dumps(report,indent=2,sort_keys=True))
    print('SUMMARY',report['passed'],'/',report['tests'],flush=True)
    return 0 if report['all_passed'] else 1


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--child',choices=list(TARGETS));p.add_argument('--dir',type=Path)
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    if a.child:sys.exit(child(a.child,a.dir))
    sys.exit(verify(a.out or Path(tempfile.mkdtemp(prefix='infinity-shutdown-compare-'))))
