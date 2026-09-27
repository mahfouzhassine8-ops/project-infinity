#!/usr/bin/env python3
"""Lossless transport only: verify the complete bundle before exposing plain source files.
The expanded Java, patch, tests and acceptance documents are included in CI evidence.
No downloaded code is evaluated here. Test-only video artwork is not packaged in the APK.
"""
from pathlib import Path
import base64,hashlib,json,lzma
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
print('PASS: expanded 10 checksum-verified source/test/contract files')
