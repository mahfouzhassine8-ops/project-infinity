#!/usr/bin/env python3
"""Disposable state-save mock: actual SQLite WAL transactions and file fsync."""
import os
from pathlib import Path
import signal
import sqlite3
import sys
import threading
import time

root=Path(sys.argv[1]); mode=sys.argv[2]
root.mkdir(parents=True,exist_ok=True)

def open_db(name):
    db=sqlite3.connect(str(root/name),timeout=10)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA synchronous=FULL')
    db.execute('CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT NOT NULL)')
    return db

def seed(db,key,val):
    db.execute('INSERT OR REPLACE INTO kv(k,v) VALUES(?,?)',(key,val))
    db.commit()

def atomic_skin(value):
    tmp=root/'skin-settings.xml.tmp'
    with tmp.open('w') as stream:
        stream.write('<settings>'+value+'</settings>\n')
        stream.flush();os.fsync(stream.fileno())
    os.replace(tmp,root/'skin-settings.xml')
    directory=os.open(root,os.O_RDONLY)
    try:os.fsync(directory)
    finally:os.close(directory)

videos=open_db('MyVideos.db')
resume=open_db('ResumeHub.db')
seed(videos,'watched','old')
seed(resume,'position','old')
atomic_skin('old')
seed(videos,'watched','new')
atomic_skin('new')

# Simulate a second required writer not protected by flushing videos + skin.
resume.execute('BEGIN IMMEDIATE')
resume.execute('UPDATE kv SET v=? WHERE k=?',('new','position'))
if mode=='hard_stop':
    entered=threading.Event()
    def invoker():
        entered.set()
        while True:time.sleep(0.04)
    worker=threading.Thread(target=invoker,daemon=True);worker.start()
    assert entered.wait(timeout=2)
    signal.pthread_kill(worker.ident,signal.SIGTERM)
    raise RuntimeError('Hard SIGTERM did not terminate the process')
elif mode=='graceful':
    stop=threading.Event();entered=threading.Event()
    def invoker():
        entered.set()
        stop.wait(5)
    worker=threading.Thread(target=invoker);worker.start()
    assert entered.wait(timeout=2)
    stop.set();worker.join(timeout=2)
    assert not worker.is_alive()
    resume.commit();videos.close();resume.close()
    print('cooperative_worker_retired_and_all_writes_committed',flush=True)
elif mode=='isolated_worker':
    import subprocess
    optional=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],start_new_session=True)
    optional.terminate();optional.wait(timeout=2)
    assert optional.returncode==-signal.SIGTERM
    resume.commit();videos.close();resume.close()
    print('isolated_worker_terminated_parent_saved_all',flush=True)
else:
    raise ValueError(mode)
