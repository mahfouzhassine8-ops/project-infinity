"""Focused host source-read/timing measurement; excludes device frame pacing."""
from pathlib import Path
import json
import os
import statistics
import sys
import time
from unittest.mock import patch
import test_search_inventory as fixture

HERE=Path(__file__).resolve().parent
case=fixture.Inventory('test_actual_specialty_contracts_and_source_tamper');case.setUp()
try:
    proof=json.loads((HERE/'SPECIALTY-CONTRACTS.json').read_text())
    case.write_contracts(proof['contracts'])
    roots=[]
    for row in proof['provenance']:
        root=Path(os.environ.get('INFINITY_PROVIDER_FIXTURES',str(HERE.parents[3]/'provider-references')))/row['fixture_directory'];roots.append(root)
        case.paths[row['addon']]=root
        case.rows.append(dict(addonid=row['addon'],name=row['addon'],path=str(root),version=row['version'],enabled=True))
    original_open=Path.open;read_count=0;read_bytes=0
    def counted(path,*args,**kwargs):
        global read_count,read_bytes
        if any(path.is_relative_to(root) for root in roots) and (not args or 'r' in args[0]):
            read_count+=1;read_bytes+=path.stat().st_size
        return original_open(path,*args,**kwargs)
    def measure(call):
        global read_count,read_bytes
        read_count=0;read_bytes=0
        start=time.perf_counter();result=call();elapsed=(time.perf_counter()-start)*1000
        return dict(ms=round(elapsed,3),provider_source_reads=read_count,provider_source_bytes=read_bytes,
                    admitted_movie_providers=len(result[0]))
    legacy=fixture.load('legacy_search_measure',HERE.parents[1]/'final-corrective-2103401/overlay/script.infinity.commandcenter/infinity_search.py')
    with patch.object(Path,'open',counted):
        before=[measure(lambda:legacy.providers('movie')) for _ in range(3)]
        cold=measure(lambda:case.inv.eligible('movie',force=True))
        after=[measure(lambda:case.inv.eligible('movie',force=True)) for _ in range(3)]
    result=dict(schema=1,environment='local Python host; real immutable provider source fixtures; Kodi API enumeration stubbed',
                providers=[{k:r[k] for k in ('addon','version')} for r in proof['provenance']],
                before_legacy_repeated_discovery=before,new_cold_verification=cold,after_same_invoker_verified_inventory=after,
                before_median_ms=round(statistics.median(r['ms'] for r in before),3),after_median_ms=round(statistics.median(r['ms'] for r in after),3),
                caveats=['Legacy source parser does not admit these specialty providers; new code verifies stricter reviewed source shapes and admits all three.',
                         'Warm results apply within one Python invoker. Restarts rebuild and reverify, and every dispatched route still hashes its raw sources.',
                         'No Android/Fold latency, FPS, frame-pacing, battery or end-to-end freeze claim.'],
                android_runtime='NOT RUN',physical_fold='NOT RUN')
    (HERE/'SEARCH-INVENTORY-TIMINGS.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2))
finally:case.doCleanups()
