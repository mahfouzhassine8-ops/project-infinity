"""Pinned Cast-only ARM64/JNI/production-DEX Android integration; no engine build."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
P='repairs/infinity-cast-hardware-pipeline-2103506-20261117/build_pipeline.py'
raw=subprocess.check_output(['git','show','caf4109e:'+P]);assert raw==(ROOT/P).read_bytes()
s=raw.decode().replace('work/infinity-2103506-receiver-compatibility-20261117','work/infinity-2103512-cast-reliability-20261117').replace('Infinity-2103506-Combined-Original-Signer.apk','Infinity-2103512-Combined-Original-Signer.apk').replace('cast506-pipeline-work','cast512-reliability-work').replace('CAST506-COMPONENT.json','CAST512-RELIABILITY-COMPONENT.json').replace('PASS_CAST506_HARDWARE_PIPELINE_ARM64_LINK','PASS_CAST512_INTEGRATED_ARM64_LINK').replace('baseline=2103506','baseline=2103512').replace("proof['baseline']==2103506","proof['baseline']==2103512").replace("old_exports|{'configureVideo'}","old_exports|{'configureVideo','readBudget','sourceStats','segmentStream'}")
start=s.index(" run('ffmpeg','-nostdin'");end=s.index("\n sdk=",start)
s=s[:start]+" shutil.copyfile(ROOT/'repairs/infinity-cast-dual-failure-2103510-20261117/fixtures/inband-main-eac3.mkv',fixtures/'hevc-eac3.mkv');shutil.copyfile(ROOT/'repairs/infinity-cast-dual-failure-2103510-20261117/fixtures/inband-main10-eac3.control.mkv',fixtures/'direct-hevc.mkv')"+s[end:]
s=s.replace("z.write(fixtures/'hevc-eac3.mkv','assets/hevc-eac3.mkv')","z.write(fixtures/'hevc-eac3.mkv','assets/hevc-eac3.mkv');z.write(fixtures/'direct-hevc.mkv','assets/direct-hevc.mkv')")
s=s.replace('android:extractNativeLibs="true"','android:extractNativeLibs="true" android:largeHeap="true"')
s=s.replace('String address(){throw new AssertionError();}', 'void warm(long p,Ready r){throw new AssertionError("compile only");}String address(){throw new AssertionError();}')
s=s.replace("names=['InfinityCastRemux'", "names=['InfinityCastResource','InfinityCastRemux'")
s=s.replace("z.write(fixtures/'direct-hevc.mkv','assets/direct-hevc.mkv')", "z.write(fixtures/'direct-hevc.mkv','assets/direct-hevc.mkv');z.write(fixtures/'high-sparse.mkv','assets/high-sparse.mkv')")
s=s.replace("\n sdk=", "\n import gzip\n from sparse_cues import sparse\n (fixtures/'high-sparse.mkv').write_bytes(sparse(gzip.decompress((HERE/'fixtures/high-24s-h264-eac3.mkv.gz').read_bytes())))\n sdk=",1)
exec(compile(s,str(__file__),'exec'),{'__file__':str(__file__),'__name__':'__main__'})
