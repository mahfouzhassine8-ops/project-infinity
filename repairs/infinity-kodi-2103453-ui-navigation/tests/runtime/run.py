"""Dispose a finite isolated renderer; never invoke Kodi shutdown acceptance."""
import json
import os
from pathlib import Path
import subprocess
import time

r = Path('/tmp/kodi-ui-runtime-qa')
config = json.loads((r / 'config.json').read_text())
phase = config['phase']
out = r / 'evidence' / phase;out.mkdir(parents=True, exist_ok=True)
assert not (out / 'RESULT.json').exists(), 'Preserve existing evidence'
env = os.environ.copy()
env.update(DISPLAY=':93', LD_LIBRARY_PATH=str(r/'root/usr/lib/x86_64-linux-gnu')+':'+str(r/'root/usr/lib/x86_64-linux-gnu/samba'),
    KODI_HOME=str(r/'root/usr/share/kodi'), KODI_BIN_HOME=str(r/'root/usr/lib/x86_64-linux-gnu/kodi'),
    LIBGL_ALWAYS_SOFTWARE='1', PYTHONDONTWRITEBYTECODE='1')
resolution = '2160x2250x24' if phase == 'restart' else '1080x2520x24'
x = subprocess.Popen([str(r/'root/usr/bin/Xvfb'), ':93', '-screen', '0', resolution, '-nolisten', 'tcp'],
    env=env, stdout=(out/'xvfb.log').open('w'), stderr=subprocess.STDOUT)
time.sleep(.4)
p = subprocess.Popen([str(r/'root/usr/lib/x86_64-linux-gnu/kodi/kodi.bin'), '--portable', '--windowing=x11', '--audio-backend=alsa', '--debug'],
    env=env, stdout=(out/'console.log').open('w'), stderr=subprocess.STDOUT)
(out/'pids.json').write_text(json.dumps({'kodi':p.pid,'xvfb':x.pid}))
try:
    until = time.monotonic()+180
    while time.monotonic() < until:
        if (out/'RESULT.json').exists():
            print((out/'RESULT.json').read_text());break
        if p.poll() is not None:
            print('QA Kodi process exited:', p.returncode);break
        time.sleep(.5)
    else:
        print('Fixture setup/observation deadline; no passing result claimed')
finally:
    # Only the finite, isolated Linux QA processes created above are disposed.
    if p.poll() is None:p.kill();p.wait()
    if x.poll() is None:x.terminate();x.wait()
    (out/'PROCESS.json').write_text(json.dumps({'exit_code':p.returncode,
        'result_recorded':(out/'RESULT.json').exists(),
        'disposable_qa_process_only':True}, indent=2)+'\n')
