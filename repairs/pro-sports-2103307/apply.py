#!/usr/bin/env python3
"""Apply only the two Cobra presentation source edits to the verified 3306 Android base."""
import argparse,hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
PREFIX='tools/android/packaging/xbmc/src/'
ALLOWED={PREFIX+'InfinityLiveActivity.java.in',PREFIX+'CobraProUi.java.in'}
def manifest(root):return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--proof',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 proof=json.loads(a.proof.read_text());before=manifest(a.source)
 assert proof['source_commit']=='0d955ae4959b40da63e21975f9cf83d8d42fbd12'
 assert len(before)==250 and before==proof['files'],'Source differs from exact inherited Android export'
 subprocess.run(['patch','-p1','--batch','--forward','-i',str(HERE/'source.patch')],cwd=a.source,check=True)
 after=manifest(a.source);assert before.keys()==after.keys()
 changed={n for n in before if before[n]!=after[n]};assert changed==ALLOWED,changed
 a.out.mkdir(parents=True,exist_ok=True)
 (a.out/'SOURCE-PRESERVATION.json').write_text(json.dumps({'apk_base':2103306,'apk_sha256':'55f1d47bb3ec647b92a5dfbb9de0c0b926027404d9bfecd75a761fd1ed749bc0','skin_base':'1.0.5.201','skin_sha256':'c07ac8f44078dae2697a90544ba58ba47523eba766f4986edd15c0414ca611e5','source_commit':proof['source_commit'],'before':before,'after':after,'changed':sorted(changed),'unchanged_files':len(before)-len(changed),'infinity_source_unchanged':True,'native_rebuild':False,'physical_device_verified':False},indent=2)+'\n')
 print('Verified exact 250-file source base. Changed only two Cobra files; other 248 files identical.')
if __name__=='__main__':main()
