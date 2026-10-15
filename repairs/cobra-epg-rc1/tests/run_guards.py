#!/usr/bin/env python3
"""Fail-closed patcher and exact-source protection checks; no device side effects."""
import argparse, json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from apply_epg_repair import patch, span, digest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a=p.parse_args(); original=a.source.read_bytes(); before=original.decode()
    a.out.mkdir(parents=True, exist_ok=True)
    after,receipt=patch(before); checks=[]
    def reject(value, name):
        try: patch(value)
        except ValueError: checks.append(name); return
        raise AssertionError(name)
    reject(after, 'Reject reapplying the patch')
    reject(before+'\n', 'Reject unknown whole-source digest')
    reject(before.replace('loadGuideAsync', 'unexpectedGuideAsync', 1), 'Reject altered source member')
    first=patch(before)[0]; assert first==after; checks.append('Deterministic output')
    for name in ('CobraModeLayout','CobraBroadcastRow','CobraMobileChannelRow','CobraCompactChannelRow','CobraPosterChannelCard','CobraFocusQueueRow'):
        x,y=span(before,name,'class');s,e=span(after,name,'class');assert before[x:y]==after[s:e]
        checks.append('Byte-identical '+name)
    for name in ('startCobraPreview','releaseSinglePlayer','promoteCobraPreviewToFullscreen','setMultiAudio','cobraLayoutMultiTiles','cobraRenderGridMode'):
        x,y=span(before,name);s,e=span(after,name);assert before[x:y]==after[s:e]
        checks.append('Byte-identical '+name)
    r=subprocess.run([sys.executable,str(ROOT/'apply_epg_repair.py'),'--source',str(a.source),'--output',str(a.source),'--receipt',str(a.out/'must-not-exist.json')],capture_output=True,text=True)
    assert r.returncode!=0 and a.source.read_bytes()==original and not (a.out/'must-not-exist.json').exists()
    checks.append('CLI refuses to overwrite the original source')
    result={'passed':len(checks),'checks':checks,'before_sha256':digest(original),'after_sha256':digest(after),'protected_method_count':receipt['protected_method_count'],'device_verified':False}
    (a.out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS:',len(checks),'patcher and protected-member checks')
if __name__=='__main__': main()
