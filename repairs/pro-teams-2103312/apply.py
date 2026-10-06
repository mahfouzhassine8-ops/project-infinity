#!/usr/bin/env python3
import argparse,hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
PREFIX='tools/android/packaging/xbmc/src/'
OWNERS=['InfinityLiveActivity','CobraProUi','InfinityCobraFeatureRuntime','InfinityCobraReminderReceiver']
CHANGED={PREFIX+n+'.java.in' for n in OWNERS}|{'cmake/scripts/android/Install.cmake','tools/android/packaging/xbmc/AndroidManifest.xml.in'}
ADDED={PREFIX+n+'.java.in' for n in ['CobraSportsPreferences','CobraSportsReminderJob']}
def sha(b):return hashlib.sha256(b).hexdigest()
def manifest(root):return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--parent-proof',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 before=manifest(a.source);parent=json.loads(a.parent_proof.read_text())
 assert before==parent['after'],'Source is not the verified complete 2103311 source'
 subprocess.run(['patch','--dry-run','-p1','--fuzz=0','-i',str((HERE/'source.patch').resolve())],cwd=a.source,check=True)
 subprocess.run(['patch','-p1','--fuzz=0','-i',str((HERE/'source.patch').resolve())],cwd=a.source,check=True)
 after=manifest(a.source)
 assert set(after)-set(before)==ADDED and not(set(before)-set(after)),'Unexpected source files'
 assert {n for n in before if before[n]!=after[n]}==CHANGED,'Unexpected modified files'
 a.out.mkdir(parents=True,exist_ok=True);(a.out/'SOURCE-PRESERVATION.json').write_text(json.dumps({'base':2103311,'before':before,'after':after,'changed':sorted(CHANGED),'added':sorted(ADDED)},indent=2)+'\n')
 print('PASS: exact 3311 source; only declared Cobra owners, service registration and CMake additions changed')
if __name__=='__main__':main()
