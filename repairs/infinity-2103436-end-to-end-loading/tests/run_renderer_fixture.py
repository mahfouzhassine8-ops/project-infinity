"""Finite isolated Linux Kodi renderer check; disposable profile, no shutdown test."""
import json
import os
from pathlib import Path
import subprocess
import time

r=Path('/tmp/infinity-kodi-renderer')
assert not (r/'evidence/RESULT.json').exists(), 'Preserve existing result before an explicitly justified rerun'
env=os.environ.copy()
env.update(DISPLAY=':93',LD_LIBRARY_PATH=str(r/'root/usr/lib/x86_64-linux-gnu')+':'+str(r/'root/usr/lib/x86_64-linux-gnu/samba'),
           KODI_HOME=str(r/'root/usr/share/kodi'),KODI_BIN_HOME=str(r/'root/usr/lib/x86_64-linux-gnu/kodi'),LIBGL_ALWAYS_SOFTWARE='1',PYTHONDONTWRITEBYTECODE='1')
x=subprocess.Popen([str(r/'root/usr/bin/Xvfb'),':93','-screen','0','1280x720x24','-nolisten','tcp'],env=env,stdout=(r/'xvfb.log').open('w'),stderr=subprocess.STDOUT)
time.sleep(.5)
p=subprocess.Popen([str(r/'root/usr/lib/x86_64-linux-gnu/kodi/kodi.bin'),'--portable','--windowing=x11','--audio-backend=alsa','--debug'],env=env,stdout=(r/'kodi-console.log').open('w'),stderr=subprocess.STDOUT)
(r/'pids.json').write_text(json.dumps(dict(kodi=p.pid,xvfb=x.pid)))
try:
    for i in range(45):
        if (r/'evidence/RESULT.json').exists():
            print((r/'evidence/RESULT.json').read_text());break
        if p.poll() is not None:
            print('Kodi fixture exited:',p.returncode);break
        time.sleep(1)
    else:
        raise RuntimeError('Fixture observation deadline; inspect setup log, no assertions claimed')
finally:
    # Dispose only this isolated QA process. No Kodi shutdown action/assertion.
    if p.poll() is None:p.kill();p.wait()
    if x.poll() is None:x.terminate();x.wait()
