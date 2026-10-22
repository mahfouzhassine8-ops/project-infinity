"""Disposable emulator-only future provider. Never installed on a user device."""
import json
import hashlib
import os
import sqlite3
import subprocess
import threading
import xbmc
import xbmcaddon
import xbmcvfs

addon=xbmcaddon.Addon()
identity=addon.getAddonInfo('id')
root=xbmcvfs.translatePath(addon.getAddonInfo('profile'))
os.makedirs(root,exist_ok=True)
mode=addon.getSettingString('test_mode') or 'safe'
cycle=str(os.getpid())
monitor=xbmc.Monitor()
worker_errors=[]
worker_ready=threading.Event()

def worker():
    try:
        with open(os.path.join(root,'worker-'+cycle),'w') as stream:
            stream.write('child buffered state')
            worker_ready.set()
            while not monitor.waitForAbort(.2): pass
            stream.flush()
    except BaseException as error:
        worker_errors.append(repr(error));worker_ready.set();raise

# Exercise the real production xbmcvfs binding under its installed observer.
essential_vfs=xbmcvfs.translatePath('special://profile')+'/future-essential-vfs-'+cycle
f=xbmcvfs.File(essential_vfs,'w')
assert f.write('text') is True
assert f.write(b'bytes') is True
assert f.write(bytearray(b'array')) is True
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
buffer=open(os.path.join(root,'buffered-'+cycle),'w');buffer.write('buffered state')
child=threading.Thread(target=worker);child.start();assert worker_ready.wait(10) and not worker_errors
command_output=subprocess.check_output(['uname','-rs']).strip()
assert command_output
versioncheck=xbmcaddon.Addon('service.xbmc.versioncheck')
versioncheck_path=xbmcvfs.translatePath(versioncheck.getAddonInfo('path'))
with open(os.path.join(versioncheck_path,'resources/lib/version_check/service.py'),'rb') as stream:
    versioncheck_hash=hashlib.sha256(stream.read()).hexdigest()
with open(os.path.join(root,'ready-'+cycle+'.json'),'w') as stream:
    json.dump(dict(addon=identity,pid=os.getpid(),mode=mode,errors=errors,worker_ready=True,
                   supported_child_returned=True,essential_vfs=essential_vfs,
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
buffer.flush();buffer.close()
child.join(10);assert not child.is_alive() and not worker_errors
# In pending mode, leave the real transaction unresolved. It must block safe exit.
