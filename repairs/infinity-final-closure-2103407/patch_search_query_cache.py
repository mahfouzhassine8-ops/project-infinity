"""Exact signed417 Search cache replacement; all other operation guards intact."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).parent
CC='script.infinity.commandcenter'
PLAN='SEARCH-CACHE-418-PLAN.json'
OLD='''        try:cache=json.loads(home.getProperty(cache_key) or '{}')
        except (ValueError,TypeError):cache={}
        if (cache.get('signature')==signature and isinstance(cache.get('at'),(int,float))
                and 0<=time.monotonic()-cache['at']<300):
            answer=cache['answer'];status='completed'
        else:
            status,answer=_leased_directory(path,home,_VisibleCancellation(cancel,progress))
            if status=='completed' and 'error' not in answer and not cancel.iscanceled():
                cache=json.dumps(dict(signature=signature,at=time.monotonic(),answer=answer))
                if len(cache)<300000:home.setProperty(cache_key,cache)
'''
NEW='''        cache=_query_cache_entries(home.getProperty(cache_key),time.monotonic())
        hit=next((row for row in cache if row['signature']==signature),None)
        if hit is not None:
            answer=hit['answer'];status='completed'
        else:
            status,answer=_leased_directory(path,home,_VisibleCancellation(cancel,progress))
            if status=='completed' and 'error' not in answer and not cancel.iscanceled():
                _remember_query_answer(home,cache_key,cache,signature,answer,time.monotonic())
'''


def patch(name,raw):
    pins=json.loads((ROOT/PLAN).read_text())['source_preimages']
    if hashlib.sha256(raw).hexdigest()!=pins.get(name):raise ValueError('Exact signed417 source required')
    text=raw.decode()
    pairs=[('version="0.3.5.47"','version="0.3.5.48"')] if name=='addon.xml' else [
        ('def _provider_result(provider,query,home,cancel,progress=None):',
         (ROOT/'search_query_cache.py').read_text()+'def _provider_result(provider,query,home,cancel,progress=None):'),
        (OLD,NEW)] if name=='infinity_search.py' else None
    if pairs is None:raise ValueError('Unowned cache source')
    revised=text
    for old,new in pairs:
        if revised.count(old)!=1:raise ValueError('Exact cache source boundary required')
        revised=revised.replace(old,new,1)
    inverse=revised
    for old,new in reversed(pairs):inverse=inverse.replace(new,old,1)
    if inverse!=text:raise ValueError('Unrelated Search code changed')
    if name.endswith('.py'):compile(revised,name,'exec',dont_inherit=True)
    return revised.encode()
