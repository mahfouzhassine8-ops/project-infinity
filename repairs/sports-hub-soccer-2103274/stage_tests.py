#!/usr/bin/env python3
from pathlib import Path
import argparse,runpy,shutil,sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
UPSTREAM=ROOT/'repairs/pro-sports-soccer-2103273/stage_tests.py'

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--inherited',action='store_true');a=p.parse_args()
    argv=[str(UPSTREAM),'--build',str(a.build),'--evidence',str(a.evidence)]
    if a.inherited:argv.append('--inherited')
    old=sys.argv;sys.argv=argv
    try:runpy.run_path(str(UPSTREAM),run_name='__main__')
    finally:sys.argv=old
    out=a.build/'xbmc/src/test/java/com/projectinfinity/kodi';shutil.copy2(HERE/'SportsHubSoccerVisibilityTest.java',out/'SportsHubSoccerVisibilityTest.java')
    print('Staged 2103274 Soccer Hub visibility tests on top of locked 2103273 Pro Sports regressions.')
if __name__=='__main__':main()
