"""Reuse authenticated498 fixtures/output; only new Cast bridge built in this job."""
from pathlib import Path
import json,sys,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/release'))
import common_release as c
work=Path(sys.argv[1]).resolve();dest=work/'hls';dest.mkdir(parents=True,exist_ok=True)
r=c.load(ROOT/'repairs/infinity-cast-eac3-2103496-20261114/ANDROID-REQUEST.json');folder=c.obtain(r['host'],'hls-authenticated-fixture');report=c.load(c.unique(folder,'CAST-DOLBY-HOST.json'));case=report['cases']['eac3_6ch'];fixture=c.unique(folder,'hevc-eac3_6ch.mkv');assert c.sha(fixture)==case['fixture_sha256'];shutil.copyfile(fixture,dest/fixture.name)
row=c.load(ROOT/'repairs/infinity-cast-eac3-2103496-20261114/ANDROID-PASS.json')['producer'];baseline=c.unique(c.obtain(row,'hls498-output'),'mkv-remux.mp4')
native=c.load(ROOT/'cast-hls-native/CAST-HLS-NATIVE.json');assert native['status']=='PASS_REAL_ARM64_HLS_CODEC_METADATA_EXACT498_ORIGINAL_ENGINE' and native['baseline_APK_sha256']=='2fd158bbdd26d47f4204c8c474f15c9ca69cfef00fcecdb62c866b42559d3004'
for name,sha in native['source_hashes'].items():assert c.sha(ROOT/name)==sha
p=ROOT/'cast-hls-native/native/libinfinitycastremux.so';assert c.sha(p)==native['new_library_sha256'];shutil.copyfile(p,dest/p.name);c.save(dest/'CAST-HLS-NATIVE.json',native)
c.save(dest/'expected.json',dict(source_packets={k:v['packets'] for k,v in case['packets'].items()},baseline_output_sha256=c.sha(baseline)))
c.save(dest/'INPUTS.json',dict(fixture_producer=r['host'],verified_original498_Dolby_output_producer=row))
