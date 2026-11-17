"""Reuse the exact verified Cast SDK/R8 recipe; only new Cast sources compile."""
from pathlib import Path
import hashlib,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
PATH='repairs/infinity-cast-hardware-pipeline-2103506-20261117/build_component.py'
raw=subprocess.check_output(['git','show','caf4109e:'+PATH]);expected=hashlib.sha256((ROOT/PATH).read_bytes()).hexdigest();assert hashlib.sha256(raw).hexdigest()==expected
code=raw.decode().replace('work/infinity-2103506-receiver-compatibility-20261117','work/infinity-2103508-cast-source-reader-20261117').replace('Infinity-2103506-Combined-Original-Signer.apk','Infinity-2103508-Combined-Original-Signer.apk').replace('cast506-component-work','cast508-reader-component-work').replace('CAST506-COMPONENT.json','CAST508-READER-COMPONENT.json')
exec(compile(code,str(__file__),'exec'),{'__file__':str(__file__),'__name__':'__main__'})
CAST=ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112/cast';sys.path.insert(0,str(CAST));from dex_contract import Dex
p=ROOT/'cast508-reader-component-work/component-reuse86/dex/classes.dex';d=Dex(p.read_bytes());methods=d.classes['Lcom/projectinfinity/kodi/InfinityCastRemuxNative;']['methods'];assert ('readBudget','(JI)J') in [tuple(v) for v in methods] and ('sourceStats','(J)[J') in [tuple(v) for v in methods]
