#!/usr/bin/env python3
"""Group #1/#19 read-only summary of existing in-app timing logs, no media data.

Does NOT alter Kodi, install a cache, touch native directory providers, or report
user titles/sources. Output is aggregated request count with exact PID/revision.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import json
from pathlib import Path
from zipfile import ZipFile


def analyze_zip(path: Path):
    with ZipFile(path) as z:
        lines=z.read('resume/timing-current.jsonl').decode('utf-8',errors='replace').splitlines()
    rows=[]
    for line in lines:
        try: j=json.loads(line)
        except ValueError: continue
        if not isinstance(j,dict) or j.get('media') not in ('movie','tv') or not isinstance(j.get('stage'),str):continue
        rows.append(j)
    requests=defaultdict(list)
    for j in rows:
        req=j.get('request')
        if isinstance(req,str) and req.startswith('n') and req[1:].isdigit(): requests[req].append(j)
    summary=[]
    for req,series in sorted(requests.items(),key=lambda x:int(x[0][1:])):
        stages={row['stage']:row for row in series}
        if 'native_start' not in stages:continue
        summary.append({'request':req,'media':stages['native_start']['media'],
          'start_ms':stages['native_start'].get('monotonic_ms'),
          'complete_ms':stages.get('plugin_complete',{}).get('monotonic_ms'),
          'revision':stages.get('directory_items',{}).get('revision'),
          'cache_hit':stages.get('snapshot_load',{}).get('cache_hit'),
          'results':stages.get('directory_items',{}).get('items')})
    summary.sort(key=lambda x:x['start_ms'] or 0)
    return {
      'requests':len(summary),
      'by_media':dict(Counter(row['media'] for row in summary)),
      'unique_revisions':sorted({str(row['revision']) for row in summary if row['revision'] is not None}),
      'cache_hits':dict(Counter(str(row['cache_hit']) for row in summary)),
      'duration_ms':round(summary[-1]['start_ms']-summary[0]['start_ms'],2) if summary else None,
      'request_repeated_after_first_load':bool(len(summary)>2 and len({row['revision'] for row in summary})==1),
      'results_by_media':{m:dict(Counter(str(row['results']) for row in summary if row['media']==m)) for m in ('movie','tv')},
      'warning':'Proves repeated fresh directory jobs under one revision; does NOT prove exact event causing provider invalidation or show future Fold cache behavior',
    }

if __name__=='__main__':
    import sys
    print(json.dumps(analyze_zip(Path(sys.argv[1])),indent=2))
