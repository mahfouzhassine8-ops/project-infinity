"""Disposable emulator-only future provider. Never installed on a user device."""
import json
import hashlib
import os
import sqlite3
import subprocess
import sys
import threading
from pathlib import Path
import xbmc
import xbmcaddon
import xbmcvfs

# Kodi deliberately sets Py_OptimizeFlag=1. Assertions and their expressions
# disappear there; all fixture actions and checks must execute under -O/-OO.
def require(condition, message):
    if not condition:raise AssertionError(message)

addon=xbmcaddon.Addon()
identity=addon.getAddonInfo('id')
root=xbmcvfs.translatePath(addon.getAddonInfo('profile'))
os.makedirs(root,exist_ok=True)
mode=addon.getSettingString('test_mode') or 'safe'
cycle=str(os.getpid())
monitor=xbmc.Monitor()
worker_errors=[]
worker_ready=threading.Event()

def drain_identity(label, handle):
    raw=getattr(handle, '_infinity_handle', handle)
    descriptor=raw.fileno()
    chain=[]
    current=raw
    for _ in range(5):
        chain.append(type(current).__module__+'.'+type(current).__name__)
        if hasattr(current,'buffer'):current=current.buffer
        elif hasattr(current,'raw'):current=current.raw
        else:break
    method=handle.flush
    function=getattr(method,'__func__',None)
    closure=[repr(cell.cell_contents)[:160] for cell in (getattr(function,'__closure__',None) or ())]
    def stat_identity(target, descriptor=False):
        try:
            info=os.fstat(target) if descriptor else os.lstat(target)
            return dict(device=info.st_dev,inode=info.st_ino,mode=info.st_mode,links=info.st_nlink,size=info.st_size)
        except OSError as error:return dict(error=repr(error))
    link=os.readlink('/proc/self/fd/'+str(descriptor))
    named=raw.name
    xbmc.log('INFINITY_FUTURE_IDENTITY '+json.dumps(dict(label=label,pid=os.getpid(),fd=descriptor,
        path=link,name=named,descriptor_stat=stat_identity(descriptor,True),name_stat=stat_identity(named),
        proc_target_stat=stat_identity(link),chain=chain,closure=closure)),xbmc.LOGINFO)

def worker():
    try:
        with open(os.path.join(root,'worker-'+cycle),'w') as stream:
            stream.write('child buffered state')
            worker_ready.set()
            while not monitor.waitForAbort(.2): pass
            xbmc.log('INFINITY_FUTURE_DRAIN worker_flush_begin '+cycle,xbmc.LOGINFO)
            drain_identity('worker_first_flush',stream)
            stream.flush()
            xbmc.log('INFINITY_FUTURE_DRAIN worker_flush_done '+cycle,xbmc.LOGINFO)
        xbmc.log('INFINITY_FUTURE_DRAIN worker_close_done '+cycle,xbmc.LOGINFO)
    except BaseException as error:
        worker_errors.append(repr(error));worker_ready.set();raise

# Exercise the real production xbmcvfs binding under its installed observer.
essential_vfs=xbmcvfs.translatePath('special://profile')+'/future-essential-vfs-'+cycle
f=xbmcvfs.File(essential_vfs,'w')
vfs_writes=[]
expected_vfs=b''
for payload in ('text',b'bytes',bytearray(b'array')):
    returned=f.write(payload)
    require(returned is True, 'Original VFS write did not return True')
    expected_vfs+=payload.encode() if isinstance(payload,str) else bytes(payload)
    with open(essential_vfs,'rb') as independent:actual=independent.read()
    checkpoint=dict(value_type=type(payload).__name__,returned=returned,
                    native_size=f.size(),native_position=f.seek(0,1),
                    stat_size=os.stat(essential_vfs).st_size,readback=actual.decode())
    vfs_writes.append(checkpoint)
    xbmc.log('INFINITY_FUTURE_VFS '+json.dumps(checkpoint),xbmc.LOGINFO)
    require(actual==expected_vfs, 'VFS write readback mismatch: '+repr(actual))
errors=[]
for value in (None,42,memoryview(b'invalid')):
    try:f.write(value)
    except TypeError as error:errors.append({'value_type':type(value).__name__,'exception':type(error).__name__,'message':str(error)})
    else:raise AssertionError('invalid native VFS argument was swallowed')

with open(os.path.join(root,'plain-'+cycle),'w') as stream:stream.write('ordinary state')
directory=os.path.join(root,'namespace-'+cycle)
os.mkdir(directory)
with open(os.path.join(directory,'tmp'),'w') as stream:stream.write('replaced state')
os.replace(os.path.join(directory,'tmp'),os.path.join(directory,'final'))
os.rename(os.path.join(directory,'final'),os.path.join(root,'replaced-'+cycle))
os.rmdir(directory)
os.makedirs(root,exist_ok=True)  # Ordinary repeated parent preparation preserves removed-child evidence.
addon.setSettingString('preserved_setting','future-provider-state')
db=sqlite3.connect(os.path.join(root,'history.db'))
db.execute('PRAGMA journal_mode=WAL')
db.execute('CREATE TABLE IF NOT EXISTS history(cycle TEXT PRIMARY KEY,position INTEGER)')
db.execute('INSERT INTO history VALUES(?,37)',(cycle,));db.commit()
db.execute('ATTACH DATABASE ? AS extra',(os.path.join(root,'watched.db'),))
db.execute('CREATE TABLE IF NOT EXISTS extra.watched(cycle TEXT PRIMARY KEY,watched INTEGER)')
db.execute('INSERT INTO extra.watched VALUES(?,1)',(cycle,));db.commit()
history_count=db.execute('SELECT COUNT(*) FROM history').fetchone()[0]
watched_count=db.execute('SELECT COUNT(*) FROM extra.watched').fetchone()[0]
try:db.execute('INSERT INTO nonexistent_table VALUES(1)')
except sqlite3.OperationalError:db.rollback()
else:raise AssertionError('failed transaction was not reported')
if mode=='pending':db.execute('INSERT INTO history VALUES(?,999)',('uncommitted-'+cycle,))
else:db.close()
# Deferred foreign-key enforcement guarantees a genuine failed COMMIT without
# relying on host/emulator filesystem reader-lock behavior. Rollback is explicit.
commit_writer=sqlite3.connect(os.path.join(root,'commit-controls.db'))
commit_writer.execute('PRAGMA foreign_keys=ON')
require(commit_writer.execute('PRAGMA foreign_keys').fetchone()==(1,), "Fixture check failed: commit_writer.execute('PRAGMA foreign_keys').fetchone()==(1,)")
commit_writer.execute('CREATE TABLE IF NOT EXISTS parents(value INTEGER PRIMARY KEY)')
commit_writer.execute('CREATE TABLE IF NOT EXISTS commits(cycle TEXT PRIMARY KEY,value INTEGER REFERENCES parents(value) DEFERRABLE INITIALLY DEFERRED)')
commit_writer.execute('INSERT OR IGNORE INTO parents VALUES(1)')
commit_writer.execute('INSERT INTO commits VALUES(?,1)',(cycle,));commit_writer.commit()
commit_writer.execute('UPDATE commits SET value=7 WHERE cycle=?',(cycle,))
try:commit_writer.commit()
except sqlite3.IntegrityError as error:
    require(error.sqlite_errorcode & 255 == sqlite3.SQLITE_CONSTRAINT and commit_writer.in_transaction, 'Fixture check failed: error.sqlite_errorcode & 255 == sqlite3.SQLITE_CONSTRAINT and commit_writer.in_transaction')
else:raise AssertionError('deferred constraint did not cause a real COMMIT failure')
commit_writer.rollback();require(not commit_writer.in_transaction, 'Fixture check failed: not commit_writer.in_transaction')
# The ordinary context-manager API performs its own rollback after a failed
# COMMIT. That failure is still raised, and the native ledger must verify the
# resulting transaction state rather than retain an unrelated sticky blocker.
try:
    with commit_writer:
        commit_writer.execute('UPDATE commits SET value=7 WHERE cycle=?',(cycle,))
except sqlite3.IntegrityError as error:
    require(error.sqlite_errorcode & 255 == sqlite3.SQLITE_CONSTRAINT and not commit_writer.in_transaction, 'Fixture check failed: error.sqlite_errorcode & 255 == sqlite3.SQLITE_CONSTRAINT and not commit_writer.in_transaction')
else:raise AssertionError('context COMMIT did not fail and roll back')
sentinel=ValueError('fixture caller exception')
try:
    with commit_writer:
        commit_writer.execute('UPDATE commits SET value=7 WHERE cycle=?',(cycle,))
        raise sentinel
except ValueError as error:require(error is sentinel and not commit_writer.in_transaction, 'Fixture check failed: error is sentinel and not commit_writer.in_transaction')
else:raise AssertionError('context swallowed the caller exception')
with commit_writer:
    commit_writer.execute('UPDATE commits SET value=1 WHERE cycle=?',(cycle,))
require(commit_writer.execute('SELECT value FROM commits WHERE cycle=?',(cycle,)).fetchall()==[(1,)], "Fixture check failed: commit_writer.execute('SELECT value FROM commits WHERE cycle=?',(cycle,)).fetchall()==[(1,)]")
commit_writer.close()
buffer=open(os.path.join(root,'buffered-'+cycle),'w');buffer.write('buffered state')
child=threading.Thread(target=worker);child.start();require(worker_ready.wait(10) and not worker_errors, 'Fixture check failed: worker_ready.wait(10) and not worker_errors')
command_output=subprocess.check_output(['uname','-rs']).strip()
require(command_output, 'Fixture check failed: command_output')
versioncheck=xbmcaddon.Addon('service.xbmc.versioncheck')
versioncheck_path=xbmcvfs.translatePath(versioncheck.getAddonInfo('path'))
with open(os.path.join(versioncheck_path,'resources/lib/version_check/service.py'),'rb') as stream:
    versioncheck_hash=hashlib.sha256(stream.read()).hexdigest()
with open(Path(root)/('ready-'+cycle+'.json'),'w') as stream:
    json.dump(dict(addon=identity,pid=os.getpid(),mode=mode,errors=errors,worker_ready=True,
                   python_optimization=sys.flags.optimize,vfs_writes=vfs_writes,checks_always_executed=True,
                   supported_child_returned=True,pathlike_io=True,failed_commit_rolled_back=True,context_commit_rolled_back=True,essential_vfs=essential_vfs,
                   history_count=history_count,watched_count=watched_count,
                   versioncheck_version=versioncheck.getAddonInfo('version'),
                   versioncheck_service_sha256=versioncheck_hash),stream)
while not monitor.waitForAbort(.2):pass
# Admission must be closed before cooperative retirement. Existing handles can
# drain, but no new payload may cross the write boundary after this signal.
try:f.write('forbidden late bytes')
except PermissionError:xbmc.log('INFINITY_FUTURE_FIXTURE_LATE_WRITE_REJECTED '+cycle,xbmc.LOGINFO)
else:raise AssertionError('late VFS payload crossed shutdown admission')
f.close()
xbmc.log('INFINITY_FUTURE_DRAIN vfs_close_done '+cycle,xbmc.LOGINFO)
xbmc.log('INFINITY_FUTURE_DRAIN main_flush_begin '+cycle,xbmc.LOGINFO)
drain_identity('main_first_flush',buffer)
buffer.flush()
xbmc.log('INFINITY_FUTURE_DRAIN main_flush_done '+cycle,xbmc.LOGINFO)
buffer.close()
xbmc.log('INFINITY_FUTURE_DRAIN main_close_done '+cycle,xbmc.LOGINFO)
child.join(10);require(not child.is_alive() and not worker_errors, 'Fixture check failed: not child.is_alive() and not worker_errors')
xbmc.log('INFINITY_FUTURE_DRAIN all_handles_drained '+cycle,xbmc.LOGINFO)
# In pending mode, leave the real transaction unresolved. It must block safe exit.
