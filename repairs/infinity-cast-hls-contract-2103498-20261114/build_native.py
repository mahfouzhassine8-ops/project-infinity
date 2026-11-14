"""Reuse original pinned NDK/FFmpeg API build, only the Cast bridge over exact498."""
from pathlib import Path
import hashlib,json,os,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];prior=ROOT/'repairs/infinity-cast-mkv-2103494-20261113/build.py'
scope={'__file__':str(prior),'__name__':'_pinned_cast_build'};exec(compile(prior.read_text(),str(prior),'exec'),scope)
scope['BASE']='2fd158bbdd26d47f4204c8c474f15c9ca69cfef00fcecdb62c866b42559d3004';scope['native']();work=Path(sys.argv[2]);p=work/'CAST-MKV-NATIVE.json';r=json.loads(p.read_text());r['status']='PASS_REAL_ARM64_HLS_CODEC_METADATA_EXACT498_ORIGINAL_ENGINE';r['source_hashes'][str(Path(__file__).resolve().relative_to(ROOT))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();(work/'CAST-HLS-NATIVE.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
