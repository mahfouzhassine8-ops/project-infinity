#!/usr/bin/env python3
"""Unchanged EPG tests with a no-op observer adapter; recovery is separately executed in run.py."""
from pathlib import Path
import argparse,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode-harness',type=Path,required=True);p.add_argument('--repository',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
 copy=out/'epg-adapters';shutil.copytree(ROOT.parent/'cobra-epg-rc1',copy,dirs_exist_ok=True)
 support=copy/'tests/host_support.java.inc';support.write_text(support.read_text()+'\n  // Host-only presentation observer, not an EPG algorithm. Real inspector tested separately.\n  private void cobraInspectSurfaceRecovery(){}\n')
 commands=[['python3',str(copy/'tests/run_tests.py'),'--source',str(a.source),'--out',str(out/'epg')],['python3',str(copy/'tests/run_short.py'),'--source',str(a.source),'--host',str(out/'epg'),'--out',str(out/'short')],['python3',str(copy/'tests/run_inherited.py'),'--source',str(a.source),'--repository',str(a.repository),'--mode-harness',str(a.mode_harness),'--out',str(out/'algorithms')]]
 for cmd in commands:subprocess.run(cmd,check=True)
if __name__=='__main__':main()
