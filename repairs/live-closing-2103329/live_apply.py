#!/usr/bin/env python3
"""Exact 328 Android parent; read-only stage presentation, no native rewrite."""
import hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
PARENT_MAP='a6f60a7018ad814757f89d502d36e0a5166eaaf2ca98f48f80e0625727629e3c'
TARGET='tools/android/packaging/xbmc/src/InfinityCloseGuardService.java.in'
def sha(b):return hashlib.sha256(b).hexdigest()
def snapshot(root):return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
def require(ok,message):
 if not ok:raise ValueError(message)
def apply(source,proof,receipt):
 before=snapshot(source);parent=json.loads(proof.read_text());delta=json.loads((HERE/'android-delta.json').read_text())
 require(parent['candidate']==2103328,'Wrong parent candidate')
 require(before==parent['after'] and sha(json.dumps(before,sort_keys=True,separators=(',',':')).encode())==PARENT_MAP,'Not exact complete 328 source')
 require({n:before.get(n) for n in delta['before']}==delta['before'],'Unexpected reviewed preimage')
 subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(HERE/'android.patch')],cwd=source,check=True)
 after=snapshot(source);changed={n for n in before.keys()|after.keys() if before.get(n)!=after.get(n)}
 require(changed==set(delta['after']) and {n:after[n] for n in changed}==delta['after'],'Undeclared source delta')
 result={'candidate':2103329,'parent':2103328,'locked_rollback':2103327,'before':before,'after':after,'changed':sorted(changed),'native_changed':False,'locked':False,'physical_device_verified':False}
 receipt.write_text(json.dumps(result,indent=2)+'\n');return result
def verify(source,receipt):
 result=json.loads(receipt.read_text());require(result['candidate']==2103329,'Wrong receipt');require(snapshot(source)==result['after'],'Source changed after tests')
