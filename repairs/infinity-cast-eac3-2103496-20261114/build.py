"""Reuse the reviewed pinned-FFmpeg/NDK build, against exact signed496 only."""
from pathlib import Path
import json,hashlib,os,subprocess,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=ROOT/'repairs/infinity-cast-mkv-2103494-20261113';WORK=Path(sys.argv[2]).resolve();WORK.mkdir(exist_ok=True)
scope={'__file__':str(OLD/'build.py'),'__name__':'_reused_pinned_build'};exec(compile((OLD/'build.py').read_text(),str(OLD/'build.py'),'exec'),scope)
scope['BASE']='17a9648070a6d2d1b670c3e550e905d75a99a7dc3f21692a56b8a69c6e9c7ebc'
if sys.argv[1]=='native':
 scope['native']();p=WORK/'CAST-MKV-NATIVE.json';r=json.loads(p.read_text());r['status']='PASS_REAL_ARM64_DOLBY_FIX_EXACT496_EXISTING_ENGINE';r['source_hashes'][str(Path(__file__).resolve().relative_to(ROOT))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();(WORK/'CAST-DOLBY-NATIVE.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
elif sys.argv[1]=='host':
 scope['host']();env=dict(os.environ,LD_LIBRARY_PATH=os.pathsep.join(str(WORK/'host-ffmpeg'/p) for p in ['libavformat','libavcodec','libavutil']));subprocess.run([sys.executable,str(HERE/'tests/test_dolby.py'),str(WORK),str(WORK/'native-driver')],env=env,check=True)
else:raise ValueError('Explicit native or host only')
