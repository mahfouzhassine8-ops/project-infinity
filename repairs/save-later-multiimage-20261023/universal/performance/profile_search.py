"""Source-bound host profiling only; Kodi UI/provider calls are test doubles."""
import argparse
import cProfile
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pstats
import statistics
import sys
import time
import types
from unittest.mock import patch

HERE=Path(__file__).resolve().parent;UNIVERSAL=HERE.parent
sys.path.insert(0,str(UNIVERSAL))
import test_search_inventory as fixture
WORKSPACE=HERE.parents[4]
INPUTS=WORKSPACE/'perf-inputs'
SOURCES=UNIVERSAL/'overlay/script.infinity.commandcenter'


def setup():
    case=fixture.Inventory('test_actual_specialty_contracts_and_source_tamper');case.setUp()
    (case.cc/'NAVIGATION-CONTRACTS.json').write_bytes((SOURCES/'NAVIGATION-CONTRACTS.json').read_bytes())
    proofs=json.loads((UNIVERSAL/'SPECIALTY-CONTRACTS.json').read_text())['provenance']
    roots=[]
    for row in proofs:
        root=WORKSPACE/'provider-references'/row['fixture_directory'];roots.append(root)
        case.paths[row['addon']]=root
        case.rows.append(dict(addonid=row['addon'],name=row['addon'],path=str(root),version=row['version'],enabled=True))
    root=Path('/workspace/scratch/9207f26886c2/pov22/plugin.video.pov');roots.append(root)
    case.paths['plugin.video.pov']=root
    case.rows.append(dict(addonid='plugin.video.pov',name='POV',path=str(root),version='6.10.22',enabled=True))
    headings=[];dispatched=[]
    def keyboard(query,heading,hidden):
        data=json.loads(heading.split(':',1)[1]);headings.append(data)
        answer=json.dumps(dict(token=data['token'],provider='plugin.video.pov',query='The Matrix',history=False))
        return types.SimpleNamespace(doModal=lambda:None,isConfirmed=lambda:True,getText=lambda:answer)
    sys.modules['xbmc'].Keyboard=keyboard
    sys.modules['xbmc'].getInfoLabel=lambda *a:''
    sys.modules['xbmc'].executebuiltin=lambda value:dispatched.append(value)
    case.profiling_roots=roots;case.headings=headings;case.dispatched=dispatched
    return case


def run_condition(search_source, inventory_source, label):
    case=setup()
    try:
        search=fixture.load('profile_search_'+label,search_source)
        inventory=fixture.load('provider_inventory',inventory_source)
        sys.modules['infinity_search']=search
        def cold():
            inventory._cached=None;inventory._verified={};inventory._checked_at=-1
            return search.providers('movie')
        def warm():
            return search.providers('movie',force=True) if label!='signed33' else search.providers('movie')
        def submit():
            inventory._cached=None;inventory._verified={};inventory._checked_at=-1
            return search.open_search('movie')
        result={}
        for name,call in (('cold_discovery',cold),('warm_refresh',warm),('cold_search_submission',submit)):
            # Actual elapsed host time without profiling/counting wrappers.
            durations=[]
            for _ in range(7):
                start=time.perf_counter();answer=call();durations.append((time.perf_counter()-start)*1000)
            counts=dict(source_reads=0,source_bytes=0,provider_lstat_calls=0)
            original_open=Path.open;original_lstat=os.lstat
            def owned(path):
                try:p=Path(path)
                except (TypeError,ValueError):return False
                return any(p.is_relative_to(root) for root in case.profiling_roots)
            def counted_open(path,*args,**kwargs):
                if owned(path) and (not args or 'r' in args[0]):
                    counts['source_reads']+=1;counts['source_bytes']+=path.stat().st_size
                return original_open(path,*args,**kwargs)
            def counted_lstat(path,*args,**kwargs):
                if owned(path):counts['provider_lstat_calls']+=1
                return original_lstat(path,*args,**kwargs)
            with patch.object(Path,'open',counted_open),patch.object(os,'lstat',counted_lstat):call()
            profiler=cProfile.Profile();profiler.runcall(call)
            stats=pstats.Stats(profiler)
            rows=[]
            for (filename,line,function),data in sorted(stats.stats.items(),key=lambda item:item[1][3],reverse=True):
                if any(term in filename for term in ('infinity_search','provider_inventory','signed33_search','cc34_','saved_navigation')):
                    cc,nc,tt,ct,callers=data
                    rows.append(dict(file=Path(filename).name,line=line,function=function,calls=nc,self_ms=round(tt*1000,3),cumulative_ms=round(ct*1000,3)))
            result[name]=dict(median_ms=round(statistics.median(durations),3),min_ms=round(min(durations),3),max_ms=round(max(durations),3),**counts,hot_functions=rows[:12])
        ready,_=warm()
        result['admitted_providers']=[row['id'] for row in ready]
        result['dispatch_sample']=case.dispatched[-1:]
        result['source_sha256']={'search':hashlib.sha256(search_source.read_bytes()).hexdigest(),'inventory':hashlib.sha256(inventory_source.read_bytes()).hexdigest()}
        return result
    finally:case.doCleanups()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('before','after'),required=True);args=parser.parse_args()
    results={}
    if args.phase=='before':
        results['signed33']=run_condition(INPUTS/'signed33_search.py',INPUTS/'cc34_provider_inventory.py','signed33')
        results['current34']=run_condition(INPUTS/'cc34_infinity_search.py',INPUTS/'cc34_provider_inventory.py','current34')
    else:
        optimized=UNIVERSAL.parent/'performance/overlay/script.infinity.commandcenter'
        results['optimized']=run_condition(optimized/'infinity_search.py',optimized/'provider_inventory.py','optimized')
    value=dict(schema=1,phase=args.phase,environment='Local CPython host; actual provider source bytes; Kodi inventory, UI and dispatch stubbed',results=results,
               caveats=['Signed33 admits fewer providers; signed33/current34 aggregate discovery timings are not equivalent-capability comparisons.',
                        'Only current34-to-optimized results use identical provider contracts, fixture set and workloads.',
                        'OS file cache is warm; cold means a fresh Infinity invocation inventory, not cold flash storage.',
                        'No providers executed. No GUI, network, Android/Fold loading latency, frame-pacing or FPS measured.'],android17='NOT RUN',physical_fold='NOT RUN')
    (HERE/('SEARCH-PROFILE-'+args.phase.upper()+'.json')).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
    for label,result in results.items():
        print(label, {key:{k:v for k,v in values.items() if k not in ('hot_functions',)} for key,values in result.items() if isinstance(values,dict) and 'median_ms' in values})
