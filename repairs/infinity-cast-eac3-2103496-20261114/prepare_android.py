from pathlib import Path
import json,sys,shutil
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/release'))
import common_release as c
work=Path(sys.argv[1]).resolve();work.mkdir(exist_ok=True);dest=work/'dolby';dest.mkdir(exist_ok=True);r=c.load(HERE/'ANDROID-REQUEST.json')
for kind in ['native','host']:
 folder=c.obtain(r[kind],'dolby-android-'+kind)
 if kind=='native':
  report=c.load(c.unique(folder,'CAST-DOLBY-NATIVE.json'));assert report['status']=='PASS_REAL_ARM64_DOLBY_FIX_EXACT496_EXISTING_ENGINE' and report['baseline_APK_sha256']=='17a9648070a6d2d1b670c3e550e905d75a99a7dc3f21692a56b8a69c6e9c7ebc'
  p=c.unique(folder,'libinfinitycastremux.so');assert c.sha(p)==report['new_library_sha256'];shutil.copyfile(p,dest/p.name)
 else:
  report=c.load(c.unique(folder,'CAST-DOLBY-HOST.json'));assert report['status']=='PASS_REAL_DOLBY_HEADER_STREAM_COPY_AND_496_AAC_PRESERVATION' and not report['transcoding'];case=report['cases']['eac3_6ch'];p=c.unique(folder,'hevc-eac3_6ch.mkv');assert c.sha(p)==case['fixture_sha256'];shutil.copyfile(p,dest/p.name);c.save(dest/'expected.json',dict(source_packets={k:v['packets'] for k,v in case['packets'].items()}))
 for name,sha in report['source_hashes'].items():assert c.sha(ROOT/name)==sha,'Changed verified source:'+name
 c.save(dest/('CAST-DOLBY-'+kind.upper()+'.json'),report)
c.save(dest/'INPUTS.json',r)
