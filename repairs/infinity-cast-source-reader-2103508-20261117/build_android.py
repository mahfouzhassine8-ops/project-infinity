"""Retained pinned Cast-only build/isolated production-DEX harness, exact508 base."""
from pathlib import Path
import hashlib,subprocess
ROOT=Path(__file__).resolve().parents[2];OLD='repairs/infinity-cast-hardware-pipeline-2103506-20261117/build_pipeline.py'
raw=subprocess.check_output(['git','show','caf4109e:'+OLD]);assert raw==(ROOT/OLD).read_bytes()
s=raw.decode().replace('work/infinity-2103506-receiver-compatibility-20261117','work/infinity-2103508-cast-source-reader-20261117').replace('Infinity-2103506-Combined-Original-Signer.apk','Infinity-2103508-Combined-Original-Signer.apk').replace('cast506-pipeline-work','cast508-reader-work').replace('CAST506-COMPONENT.json','CAST508-READER-COMPONENT.json').replace('PASS_CAST506_HARDWARE_PIPELINE_ARM64_LINK','PASS_CAST508_SOURCE_READER_ARM64_LINK').replace('baseline=2103506','baseline=2103508').replace("proof['baseline']==2103506","proof['baseline']==2103508").replace("old_exports|{'configureVideo'}","old_exports|{'configureVideo','readBudget','sourceStats'}")
start=s.index(" run('ffmpeg','-nostdin'");end=s.index("\n sdk=",start)
s=s[:start]+''' run('ffmpeg','-nostdin','-v','error','-y','-f','lavfi','-i','color=size=320x180:rate=24','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','24','-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p','-profile:v','high','-level:v','4.1','-b:v','14M','-minrate','14M','-maxrate','14M','-bufsize','14M','-g','96','-keyint_min','96','-sc_threshold','0','-x264-params','nal-hrd=cbr:force-cfr=1:bframes=2','-c:a','eac3','-b:a','384k','-cluster_time_limit','2000',fixtures/'hevc-eac3.mkv')'''+s[end:]
exec(compile(s,str(__file__),'exec'),{'__file__':str(__file__),'__name__':'__main__'})
