#!/usr/bin/env python3
"""Preserve a complete native preimage and allow only declared candidate edits."""
from pathlib import Path
import argparse,hashlib,json
import native_controls,native_keyboard,native_health

def snapshot(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['apply','verify'])
    ap.add_argument('--source',type=Path,required=True);ap.add_argument('--receipt',type=Path,required=True)
    a=ap.parse_args()
    if a.command=='apply':
        before=snapshot(a.source);deltas=[]
        for transform in [native_controls.apply,native_keyboard.apply,native_health.apply]:
            deltas+=transform(a.source)
        after=snapshot(a.source)
        declared={row['path'] for row in deltas}
        changed={n for n in before.keys()|after.keys() if before.get(n)!=after.get(n)}
        assert changed==declared,(changed^declared)
        a.receipt.parent.mkdir(parents=True,exist_ok=True)
        a.receipt.write_text(json.dumps({'before':before,'after':after,'deltas':deltas,
            'changed':sorted(changed),'historical_crash_owner_proven':False},indent=2)+'\n')
        print('Native candidate:',len(changed),'declared source files; every other baseline file preserved')
    else:
        data=json.loads(a.receipt.read_text());actual=snapshot(a.source)
        # Build-generated new files are not source preimages. Every captured
        # source must still match, including all declared new native helpers.
        mismatches=[n for n,digest in data['after'].items() if actual.get(n)!=digest]
        assert not mismatches,mismatches
        print('PASS native candidate source preservation:',len(data['after']),'files')

if __name__=='__main__':main()
