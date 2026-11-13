from pathlib import Path
import hashlib,json,os,shutil,sys
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/release'))
import common_release as c
work=Path(sys.argv[1]).resolve();work.mkdir(exist_ok=True)
r=c.load(HERE/'ANDROID-REQUEST.json');dest=work/'mkv';dest.mkdir(exist_ok=True)
for kind in ['native','host']:
 folder=c.obtain(r[kind],'mkv-android-'+kind)
 if kind=='native':
  receipt=c.load(c.unique(folder,'CAST-MKV-NATIVE.json'))
  assert receipt['status']=='PASS_REAL_ARM64_BRIDGE_LINK_AND_EXACT94_EXISTING_FFMPEG_EXPORTS' and receipt['baseline_APK_sha256']=='fa0da5675443803ff2af42526243f81b9a1be774f7deeecdaf7e7557fff2a36c'
  for p,h in receipt['source_hashes'].items():assert c.sha(ROOT/p)==h,'Native source changed after ARM64 verification: '+p
  lib=c.unique(folder,'libinfinitycastremux.so');assert c.sha(lib)==receipt['new_library_sha256'];shutil.copyfile(lib,dest/lib.name);c.save(dest/'CAST-MKV-NATIVE.json',receipt)
 else:
  receipt=c.load(c.unique(folder,'CAST-MKV-HOST.json'));assert receipt['status']=='PASS_REAL_FFMPEG6_MKV_STREAM_COPY' and not receipt['transcoding']
  for p,h in receipt['source_hashes'].items():assert c.sha(ROOT/p)==h,'Host media test source changed: '+p
  fixture=c.unique(folder,'h264-aac.mkv');assert c.sha(fixture)==receipt['fixture_sha256'];shutil.copyfile(fixture,dest/fixture.name);c.save(dest/'CAST-MKV-HOST.json',receipt)
c.save(dest/'INPUTS.json',r)
print('PASS authenticated exact94 MKV ARM64 and stream-copy inputs for actual Android')
