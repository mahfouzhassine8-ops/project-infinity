#!/usr/bin/env python3
"""Hash-gated deltas on the actual 2103325 tested source; never update a lock."""
import argparse,hashlib,json,re,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
NATIVE_PARENT_MAP='463dfd2faaf5bd1af1f5ad90946f34a80ff34eb7cd8c878c2abddb02c94b9f1a'
ANDROID_PARENT_MAP='6a43493156623ae117a63815c8378b3a6e60dc40d6313e1e55661238ad2a8d93'
OLD_NATIVE='e244f0ef2de7f0943659c6e721c4b26045f7f2cca18d50bc0c6298a29428ede1'
SRC='tools/android/packaging/xbmc/src/'
def sha(data):return hashlib.sha256(data).hexdigest()
def map_digest(value):return sha(json.dumps(value,sort_keys=True,separators=(',',':')).encode())
def snapshot(source):return {p.relative_to(source).as_posix():sha(p.read_bytes()) for p in source.rglob('*') if p.is_file() and '.git' not in p.relative_to(source).parts}
def require(ok,msg):
 if not ok:raise ValueError(msg)
def apply(kind,source,proof,receipt,native_sha=None):
 expected=json.loads(proof.read_text())['after']
 require(map_digest(expected)==(NATIVE_PARENT_MAP if kind=='native' else ANDROID_PARENT_MAP),'Incorrect immutable source map')
 before=snapshot(source);require(before==expected,'Source is not the exact passed diagnostic parent')
 delta=json.loads((HERE/(kind+'-delta.json')).read_text())
 for n,digest in delta['before'].items():require(before.get(n)==digest,'Unexpected source preimage: '+n)
 patch=HERE/(kind+'.patch')
 subprocess.run(['git','apply','--check',str(patch)],cwd=source,check=True)
 subprocess.run(['git','apply',str(patch)],cwd=source,check=True)
 added=set(delta.get('added',[]))
 for n in added:
  target=source/n;require(not target.exists(),'New source unexpectedly exists');target.write_bytes((HERE/Path(n).name).read_bytes())
 for n,digest in delta['after'].items():require(sha((source/n).read_bytes())==digest,'Source differs from reviewed delta: '+n)
 allowed=set(delta['after'])
 if kind=='android':
  require(native_sha is not None and re.fullmatch('[0-9a-f]{64}',native_sha),'Actual native identity required')
  for name in ['InfinityHealthExport.java.in','InfinityExitDiagnostics.java.in']:
   p=source/SRC/name;t=p.read_text();require(t.count(OLD_NATIVE)==1,'Native identity preimage missing');p.write_text(t.replace(OLD_NATIVE,native_sha));allowed.add(SRC+name)
 after=snapshot(source);changed={n for n in before.keys()|after.keys() if before.get(n)!=after.get(n)}
 require(changed==allowed,'Undeclared source changes: '+repr(changed^allowed))
 require(set(after)-set(before)==added and not(set(before)-set(after)),'Unexpected addition/removal')
 result={'candidate':2103326,'parent':2103325,'locked_rollback':2103324,'kind':kind,'before':before,'after':after,'changed':sorted(changed),'native_sha256':native_sha,'physical_device_verified':False,'locked':False}
 receipt.parent.mkdir(parents=True,exist_ok=True);receipt.write_text(json.dumps(result,indent=2)+'\n');return result
def verify(source,receipt):
 r=json.loads(receipt.read_text());require(r['candidate']==2103326,'Wrong repair receipt')
 for n,digest in r['after'].items():require(sha((source/n).read_bytes())==digest,'Protected source changed after testing: '+n)
 # Native configure generates additional files, never rewrites registered inputs.
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['native','android','verify']);p.add_argument('--source',type=Path,required=True);p.add_argument('--proof',type=Path);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--native-sha');a=p.parse_args()
 if a.mode=='verify':verify(a.source,a.receipt)
 else:apply(a.mode,a.source,a.proof,a.receipt,a.native_sha)
 print('PASS: exact-source '+a.mode+' gate')
