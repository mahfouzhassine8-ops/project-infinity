#!/usr/bin/env python3
"""Compile actual baseline and proposed dispatch bodies in the same test harness."""
import argparse, subprocess, tempfile
from pathlib import Path
from native_patch import transform, PATH
HERE=Path(__file__).resolve().parent
def body(s):
    start=s.index('EVENT_RESULT CGUIControlGroupList::SendMouseEvent(')
    return s[start:s.index('\nvoid CGUIControlGroupList::UnfocusFromPoint(',start)]
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args()
    baseline=subprocess.check_output(['git','-C',str(a.source),'show','HEAD:'+PATH],text=True)
    harness=(HERE/'test_scroll_hit.cpp').read_text()
    with tempfile.TemporaryDirectory(prefix='infinity-hit-test-') as temp:
        for name,text,expect in [('baseline',baseline,False),('candidate',transform(baseline),True)]:
            binary=Path(temp)/name
            subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-x','c++','-','-o',str(binary)],
                input=harness.replace('// PRODUCTION_METHOD',body(text)),text=True,check=True)
            result=subprocess.run([str(binary)],capture_output=True,text=True)
            assert (result.returncode==0)==expect,(name,result.stdout,result.stderr)
            print(result.stdout.strip() if expect else 'PASS: baseline reproduces the rejected partial-row tap')
