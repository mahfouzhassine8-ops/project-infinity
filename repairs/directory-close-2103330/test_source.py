#!/usr/bin/env python3
"""Reconstruct and verify Android delta before waiting for native compilation."""
import argparse,json,shutil,tempfile
from pathlib import Path
import android_repair as repair
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--proof',type=Path,required=True);a=p.parse_args()
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)/'source';shutil.copytree(a.source,root)
    receipt=Path(tmp)/'proof.json'
    repair.apply(root,a.proof,receipt,'1'*64);repair.verify(root,receipt)
    guard=(root/repair.GUARD).read_text();progress=(root/repair.PROGRESS).read_text()
    assert 'new Intent(this,Splash.class)' in guard
    assert 'setProgress(0,0,true)' in guard and 'setUsesChronometer(true)' in guard
    assert 'MAX_PROTECTION_MS=150000' in guard and 'BIND_FLAGS=Context.BIND_IMPORTANT' in guard
    assert 'notice(message)' in guard and 'Last reported: ' in guard
    assert 'infinity-shutdown-2103330-v1' in progress
    assert 'Waiting for the next shutdown stage' in progress
    assert 'new RandomAccessFile(file,"r")' in progress and 'FileOutputStream' not in progress
    assert not (root/(repair.SRC+'InfinityClosingActivity.java.in')).exists()
    for path in [root/repair.GUARD,root/repair.MANIFEST,root/repair.INSTALL,root/repair.POWER]:
        assert 'InfinityClosingActivity' not in path.read_text(),path
    proof=json.loads(receipt.read_text())
    print('PASS: full 3327 Android parent, five-file notification/identity delta; no extra activity; chooser, dispatch, guard deadline and native lease retained')
