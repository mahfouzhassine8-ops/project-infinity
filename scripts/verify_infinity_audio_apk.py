#!/usr/bin/env python3
"""Reject split/incomplete cumulative APKs; presence/integrity, NOT device proof."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import zipfile

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--apk',type=Path,required=True);p.add_argument('--engine',type=Path,required=True)
p.add_argument('--source-receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
s=importlib.util.spec_from_file_location('cumulative',ROOT/'scripts/verify_infinity_cumulative_media.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
result=m.inspect(a.apk);assert result['static_presence_gate_passed'],result['missing']
receipt=json.loads(a.source_receipt.read_text());assert receipt['versionCode']==2103120
assert receipt['bridge_version']==5 and receipt['platform_hook_api']==2 and receipt['audio_policy_api']==1
preserved=json.loads((ROOT/'patches/infinity-audio-policy/preserved-v5-assets.json').read_text())
with zipfile.ZipFile(a.engine) as base, zipfile.ZipFile(a.apk) as z:
 assert z.testzip() is None
 dex=[z.read(n) for n in z.namelist() if re.fullmatch(r'classes\d*\.dex',n)]
 classes=set().union(*(m.dex_classes(d) for d in dex))
 assert 'Lcom/projectinfinity/kodi/InfinityAudioFocusHook;' in classes
 for needle in (b'acquireAudioFocus',b'releaseAudioFocus',b'updateAudioPolicy'):
  assert any(needle in d for d in dex),needle
 native=z.read('lib/arm64-v8a/libkodi.so')
 for needle in (b'Infinity AudioPolicy API 1 AudioTrack:',b'infinity-audio-policy.json',b'Infinity.AudioPolicyApi'):
  assert needle in native,needle
 # The source-built engine and dex must survive packaging byte-for-byte.
 for name in base.namelist():
  if name.startswith('lib/') or re.fullmatch(r'classes\d*\.dex',name):
   assert base.read(name)==z.read(name),name
 for name,digest in preserved['files'].items():
  assert hashlib.sha256(z.read(name)).hexdigest()==digest,('v5 asset changed',name)
 for filename in ('addon.xml','default.py','contract.json'):
  name='assets/addons/script.infinity.audiopolicy/'+filename
  assert z.read(name)==(ROOT/'addons/script.infinity.audiopolicy'/filename).read_bytes(),name
  if filename=='contract.json':assert json.loads(z.read(name))['api']==1
result.update({'schema':2,'release':'1.0.8-Cumulative-Audio-Policy-1','versionCode':2103120,
               'source_receipt':receipt,'v5_assets_preserved':True,'engine_bytes_preserved':True,
               'audio_policy_api':1,'runtime_tested':False,'audio_track_policy_verified':False,
               'samsung_audio_eraser_eligibility':'unknown'})
a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print('PASS: combined v5/media/audio owners, exact v5 add-on hashes, native/DEX preservation and API 1 config utility')
print('Device tests still required. This does not prove real AudioTrack attributes or Samsung Audio Eraser support.')
