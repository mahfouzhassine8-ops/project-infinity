#!/usr/bin/env python3
"""Verify the complete exported 303 source proof, then emit only two Java edits."""
from pathlib import Path
from difflib import unified_diff
import argparse,hashlib,json
HERE=Path(__file__).resolve().parent
JAVA=Path('tools/android/packaging/xbmc/src')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--proof',type=Path,required=True);a=p.parse_args()
    proof=json.loads(a.proof.read_text())
    assert proof['source_commit']=='0a8d8a13efff44cc8be0c99416a1d239b3066e8c'
    for name,digest in proof['files'].items():
        assert hashlib.sha256((a.source/name).read_bytes()).hexdigest()==digest,name
    print('*** Begin Patch')
    for name in ['InfinityAndroidKeyboard.java.in','InfinityGlassOptions.java.in']:
        path=a.source/JAVA/name;before=path.read_text();after=(HERE/name).read_text()
        print('*** Update File: '+str(path))
        for line in list(unified_diff(before.splitlines(),after.splitlines(),n=3))[2:]:
            print('@@' if line.startswith('@@') else line)
    print('*** End Patch')
