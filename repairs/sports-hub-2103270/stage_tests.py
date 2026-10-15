#!/usr/bin/env python3
from pathlib import Path
import argparse, runpy, shutil, sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
UPSTREAM=ROOT/'repairs/responsive-window-2103269/stage_tests.py'

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--inherited',action='store_true');a=p.parse_args()
    argv=[str(UPSTREAM),'--build',str(a.build),'--evidence',str(a.evidence)]
    if a.inherited:argv.append('--inherited')
    old=sys.argv;sys.argv=argv
    try:runpy.run_path(str(UPSTREAM),run_name='__main__')
    finally:sys.argv=old
    target=a.build/'xbmc/src/test/java/com/projectinfinity/kodi/SportsHubTest.java';target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(HERE/'SportsHubTest.java',target)
    print('Staged SportsHubTest on top of the inherited 2103269 product suite.')
if __name__=='__main__':main()
