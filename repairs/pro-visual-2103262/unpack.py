#!/usr/bin/env python3
"""Verify source transport, then apply explicitly bounded compatibility corrections.
Expanded Java, patches, tests and acceptance documents are preserved in CI evidence.
Test-only video artwork is never packaged in the APK.
"""
from pathlib import Path
import base64,hashlib,json,lzma,subprocess
root=Path(__file__).resolve().parent
encoded=''.join((root/('bundle'+str(i)+'.b64')).read_text().strip() for i in range(4))
raw=lzma.decompress(base64.b64decode(encoded,validate=True))
assert hashlib.sha256(raw).hexdigest()=='017df1b6b60fa5ac51417114de94f14b14de653d7adb49ff0d27d8de9b245a66','Source bundle checksum mismatch'
files=json.loads(raw)
expected={'CobraProUi.java.in','ProVisualTest.java','ProActionsTest.java','integration.patch','java_members.py','apply.py','stage_tests.py','DEVICE-TEST.md','PRO-CORRECTION-CONTRACT.md','test-video-fixture.webp'}
assert set(files)==expected,set(files)
for name,data in files.items():
    assert Path(name).name==name
    payload=base64.b64decode(data,validate=True) if name.endswith('.webp') else data.encode('utf-8')
    (root/name).write_bytes(payload)
# Existing application imports AndroidX Media3. Correct only the new Pro types.
patch=root/'integration.patch';s=patch.read_text()
assert s.count('com.google.android.exoplayer2.Player')==4
patch.write_text(s.replace('com.google.android.exoplayer2.Player','androidx.media3.common.Player'))
for name in ['stage_tests.py','ProActionsTest.java']:
    path=root/name;s=path.read_text();assert s.count('com.google.android.exoplayer2.ExoPlayer')==1
    path.write_text(s.replace('com.google.android.exoplayer2.ExoPlayer','androidx.media3.exoplayer.ExoPlayer'))
subprocess.run(['python3',str(root/'refine.py')],check=True)
print('PASS: source bundle verified; new Pro listener/tests use existing Media3 types')
