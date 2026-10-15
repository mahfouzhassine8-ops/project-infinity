#!/usr/bin/env python3
"""Fail-closed source contract for the Android task-removal close route."""
import argparse
import json
from pathlib import Path
import android_task_close as patch


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--proof',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    args=parser.parse_args()
    baseline=json.loads(args.proof.read_text())['after']
    before=patch.snapshot(args.source)
    assert before==baseline
    args.work.mkdir(parents=True,exist_ok=True)
    import shutil
    candidate=args.work/'shell-kodi'
    if candidate.exists():shutil.rmtree(candidate)
    shutil.copytree(args.source,candidate)
    receipt=args.work/'android-task-close-source.json'
    patch.apply(candidate,args.proof,receipt)
    patch.verify(candidate,receipt)
    text=(candidate/patch.TARGET).read_text()
    close=text[text.index('static boolean requestNormal(Main owner)'):text.index('static void afterStop(Main owner)')]
    assert 'owner.finishAndRemoveTask();' in close
    assert 'request_string(QUIT)' not in close and 'moveTaskToBack' not in close
    after=text[text.index('static void afterStop(Main owner)'):text.index('static void requestForce(Main owner, Context context)')]
    assert after.index('Phase.ANDROID_TASK_REMOVAL')<after.index('owner.mInfinityExitPlan.stopped')
    assert 'exit.androidTaskRemoval.androidStopped.noKodiQuit' in after
    manifest=(candidate/'tools/android/packaging/xbmc/AndroidManifest.xml.in').read_text()
    splash=manifest[manifest.index('android:name=".Splash"'):manifest.index('<!--\n             Our activity')]
    main=manifest[manifest.index('android:name=".Main"'):manifest.index('<!-- Infinity player-only')]
    assert 'android:process=' not in splash and 'android:process=":kodi"' in main
    main_java=(candidate/'tools/android/packaging/xbmc/src/Main.java.in').read_text()
    assert 'if (isFinishing()) InfinityExtendedBackgroundService.stopForExit(this);' in main_java
    assert before==patch.snapshot(args.source)
    print('PASS: normal close removes the :kodi task, suppresses Kodi Quit dispatch, preserves the separate chooser process and locked baseline')


if __name__=='__main__':main()
