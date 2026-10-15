#!/usr/bin/env python3
"""Verify the exact parent and keep changes within the requested Android scope."""
import argparse
import json
import shutil
from pathlib import Path
import close_progress_isolation as patch


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--proof',type=Path,required=True);p.add_argument('--work',type=Path,required=True)
    a=p.parse_args();before=patch.snapshot(a.source);assert before==json.loads(a.proof.read_text())['after']
    a.work.mkdir(parents=True,exist_ok=True);candidate=a.work/'shell-kodi'
    if candidate.exists():shutil.rmtree(candidate)
    shutil.copytree(a.source,candidate);receipt=a.work/'close-progress-source.json'
    patch.apply(candidate,a.proof,receipt);patch.verify(candidate,receipt)
    assert before==patch.snapshot(a.source)
    for name in ['InfinityKodiShutdown.java.in','InfinityLiveActivity.java.in','Main.java.in','InfinityPowerControlActivity.java.in','InfinityPowerMenuRoutes.java.in']:
        assert (candidate/patch.PREFIX/name).read_bytes()==(a.source/patch.PREFIX/name).read_bytes(),name
    parent_gear=(a.source/patch.GEAR).read_text();new_gear=(candidate/patch.GEAR).read_text()
    start='    @Override protected void onDraw(Canvas c){\n      float s=Math.min(getWidth(),getHeight()),cx=getWidth()/2f,cy=getHeight()/2f;'
    end='      if(!cobra && (closePending || closeReady || closeFailed)){'
    assert parent_gear[parent_gear.index(start):parent_gear.index(end)]==new_gear[new_gear.index(start):new_gear.index(end)]
    normal=(candidate/patch.close315.TARGET).read_text()
    normal=normal[normal.index('static boolean requestNormal'):normal.index('static void afterStop')]
    assert 'owner.finishAndRemoveTask();' in normal and 'request_string(QUIT)' not in normal
    print('PASS: only close coordinator, Infinity arc and Splash routing change; native monitor, Main, Cobra player/close and gear drawing preserved')


if __name__=='__main__':main()
