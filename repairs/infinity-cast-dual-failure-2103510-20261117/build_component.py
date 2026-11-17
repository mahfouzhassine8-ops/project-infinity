"""Reuse the pinned Cast-only compiler/linker. Exact signed510, no engine build."""
from pathlib import Path
import subprocess,hashlib
ROOT=Path(__file__).resolve().parents[2]
P='repairs/infinity-cast-hardware-pipeline-2103506-20261117/build_component.py'
raw=subprocess.check_output(['git','show','caf4109e:'+P]);assert raw==(ROOT/P).read_bytes()
s=raw.decode().replace('work/infinity-2103506-receiver-compatibility-20261117','work/infinity-2103510-cast-dual-failure-20261117').replace('Infinity-2103506-Combined-Original-Signer.apk','Infinity-2103510-Combined-Original-Signer.apk').replace('cast506-component-work','cast510-dual-component-work').replace('CAST506-COMPONENT.json','CAST510-DUAL-COMPONENT.json')
exec(compile(s,str(__file__),'exec'),{'__file__':str(__file__),'__name__':'__main__'})
