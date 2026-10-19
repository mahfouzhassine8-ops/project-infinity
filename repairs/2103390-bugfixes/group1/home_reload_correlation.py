#!/usr/bin/env python3
"""Offline-only Group 1/19 triage of the existing in-app diagnostic export.

No Kodi API, no addon writes, no worker, and no history/title/source strings
in output. A changed HomeLoad token supports a Home reinitialization event;
repeated directory jobs alone do NOT identify which native invalidation fired.
"""
from __future__ import annotations
import json
import re
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

CONTINUITY = ('skin/continuity.json', 'continuity.json',
              'skin.infinity.diggz/continuity.json')
TIMING = ('resume/timing-current.jsonl', 'timing-current.jsonl')

def find_member(names, candidates):
    exact = [n for n in names if n in candidates]
    if len(exact) == 1:return exact[0]
    # Exporter versions can wrap files in an extra folder. Do not guess if
    # there are multiple candidate paths.
    suffixes = [n for n in names if any(n.endswith('/' + q) for q in candidates)]
    return suffixes[0] if len(suffixes) == 1 else None

def analyze(path: Path):
    with ZipFile(path) as z:
        names=z.namelist()
        cont=find_member(names,CONTINUITY)
        timing=find_member(names,TIMING)
        events=[]
        if cont:
            try:
                info=json.loads(z.read(cont))
                raw=info.get('events', []) if isinstance(info,dict) else []
                events=[e for e in raw if isinstance(e,dict)] if isinstance(raw,list) else []
            except (ValueError,UnicodeDecodeError):pass
        rows=[]
        if timing:
            for line in z.read(timing).decode('utf8','replace').splitlines():
                try:e=json.loads(line)
                except ValueError:continue
                if isinstance(e,dict) and e.get('stage')=='native_start' and e.get('media') in ('movie','tv'):
                    rows.append(e)
        loads=[]
        for e in events:
            if e.get('event') != 'state':continue
            token=e.get('home_load')
            if isinstance(token,str) and re.fullmatch(r'[a-f0-9]{32}',token):
                if not loads or token != loads[-1]:loads.append(token)
        revisions={str(e['revision']) for e in events if 'revision' in e and isinstance(e['revision'],(int,str))}
        return {
            'home_events_present':bool(events),
            'distinct_sequential_home_loads':len(loads),
            'home_reinitialized_at_least_once':len(loads)>1,
            'repeat_directory_starts':len(rows),
            'starts_by_media':dict(Counter(e['media'] for e in rows)),
            'continuity_export_found':bool(cont),
            'timing_export_found':bool(timing),
            'revision_values_present':len(revisions),
            'cause_proven':False,
            'next_required_evidence':('Correlate actual focused Home panel / click, '
                'native DirectoryProvider URL/INVALIDATED/Reset and user progress revision '
                'in ONE physical Fold replay, separately for Umbrella and Continue Watching.'),
            'privacy':'aggregate_only_no_paths_titles_saved_urls_or_process_tokens'
        }

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('diagnostic_zip',type=Path)
    args=a.parse_args();print(json.dumps(analyze(args.diagnostic_zip),indent=2))
