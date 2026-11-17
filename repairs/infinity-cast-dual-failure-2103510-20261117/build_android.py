"""Pinned Cast-only ARM64/JNI/production-DEX Android integration; no engine build."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
P='repairs/infinity-cast-hardware-pipeline-2103506-20261117/build_pipeline.py'
raw=subprocess.check_output(['git','show','caf4109e:'+P]);assert raw==(ROOT/P).read_bytes()
s=raw.decode().replace('work/infinity-2103506-receiver-compatibility-20261117','work/infinity-2103510-cast-dual-failure-20261117').replace('Infinity-2103506-Combined-Original-Signer.apk','Infinity-2103510-Combined-Original-Signer.apk').replace('cast506-pipeline-work','cast510-dual-work').replace('CAST506-COMPONENT.json','CAST510-DUAL-COMPONENT.json').replace('PASS_CAST506_HARDWARE_PIPELINE_ARM64_LINK','PASS_CAST510_DUAL_ARM64_LINK').replace('baseline=2103506','baseline=2103510').replace("proof['baseline']==2103506","proof['baseline']==2103510").replace("old_exports|{'configureVideo'}","old_exports|{'configureVideo','readBudget','sourceStats'}")
start=s.index(" run('ffmpeg','-nostdin'");end=s.index("\n sdk=",start)
s=s[:start]+" shutil.copyfile(HERE/'fixtures/inband-main10-eac3.mkv',fixtures/'hevc-eac3.mkv');shutil.copyfile(HERE/'fixtures/inband-main10-eac3.control.mkv',fixtures/'direct-hevc.mkv')"+s[end:]
s=s.replace("z.write(fixtures/'hevc-eac3.mkv','assets/hevc-eac3.mkv')","z.write(fixtures/'hevc-eac3.mkv','assets/hevc-eac3.mkv');z.write(fixtures/'direct-hevc.mkv','assets/direct-hevc.mkv')")
exec(compile(s,str(__file__),'exec'),{'__file__':str(__file__),'__name__':'__main__'})
