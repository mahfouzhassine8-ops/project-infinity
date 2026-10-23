"""Execute the collected cache implementation without opening a user database."""
import argparse
import ast
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sqlite3
import types


def run(installed, published, logs):
    captured=(installed/'resources/lib/caches/meta_cache.py').read_bytes()
    reference=(published/'resources/lib/caches/meta_cache.py').read_bytes()
    if captured!=reference:raise RuntimeError('Collected cache differs from the public source')
    base=(published/'resources/lib/caches/__init__.py').read_bytes()
    # Compile the unchanged published base class; its module import binds only
    # the database/context peers below. Compile the collected actual class/body.
    tree=ast.parse(base);definition=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='BaseCache')
    base_scope={'json':json}
    exec(compile(ast.Module(body=[definition],type_ignores=[]),'public-BaseCache.py','exec'),base_scope)
    memory={};database_calls=[]
    class GuardedBase(base_scope['BaseCache']):
        def __enter__(self):
            database_calls.append(True)
            raise RuntimeError('User database access is forbidden in this test')
    tree=ast.parse(captured)
    body=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))]
    scope=dict(BaseCache=GuardedBase,datetime=__import__('datetime').datetime,
               timedelta=__import__('datetime').timedelta,metacache_db='FORBIDDEN-USER-DATABASE',
               get_property=lambda k:memory.get(k,''),set_property=lambda k,v:memory.__setitem__(k,v),
               clear_property=lambda k:memory.pop(k,None))
    exec(compile(ast.Module(body=body,type_ignores=[]),'collected-meta_cache.py','exec'),scope)
    cache=scope['MetaCache']();now=cache._get_timestamp(datetime.now())
    if type(now) is not int:raise RuntimeError('Timestamp generator did not return int')
    meta={'tmdb_id':'330430','title':'Love After Lockup: Relationship Rehab'}
    cache.set_memory_cache('tvshow','tmdb_id',meta,now+3600,'330430')
    if cache.get('tvshow','tmdb_id','330430')!=meta:raise RuntimeError('Valid cache regression')
    stored=json.loads(next(iter(memory.values())))
    if type(stored[0]) is not int:raise RuntimeError('Current serialization changed expiry type')
    outcomes=[]
    for bad in ([str(now+3600),meta], {'expires':now+3600,'meta':meta}):
        key=scope['prop_get']('meta','tvshow','tmdb_id','330430')
        memory[key]=json.dumps(bad)
        try:cache.get('tvshow','tmdb_id','330430')
        except TypeError as error:
            if str(error)!="'<' not supported between instances of 'str' and 'int'":raise
            outcomes.append(dict(shape='string expiry array' if isinstance(bad,list) else 'two-key object',
                                 exception_type=type(error).__name__,message=str(error)))
        else:raise RuntimeError('Original failure was not reproduced')
    if database_calls:raise RuntimeError('Failure occurred after database access')
    # Demonstrate a POSSIBLE producer, without claiming this row existed on the
    # Fold: SQLite INTEGER affinity permits nonnumeric TEXT and compares it as
    # greater than an integer. The actual provider then copies that type to JSON.
    with sqlite3.connect(':memory:') as db:
        db.execute('CREATE TABLE metadata(expires INTEGER,meta TEXT)')
        db.execute('INSERT INTO metadata VALUES (?,?)',('legacy timestamp',json.dumps(meta)))
        expiry=db.execute('SELECT expires FROM metadata WHERE expires > ?',(now,)).fetchone()[0]
        if type(expiry) is not str:raise RuntimeError('SQLite type test changed')
        cache.set_memory_cache('tvshow','tmdb_id',meta,expiry,'330430')
        try:cache.get('tvshow','tmdb_id','330430')
        except TypeError:pass
        else:raise RuntimeError('Database-to-memory propagation did not reproduce failure')
    log=logs.read_text()
    if "meta_cache.py\", line 78" not in log or "'<' not supported between instances of 'str' and 'int'" not in log:
        raise RuntimeError('Physical traceback is absent')
    return dict(passed=True,collected_source_sha256=hashlib.sha256(captured).hexdigest(),
        collected_matches_published=True,published_base_source_sha256=hashlib.sha256(base).hexdigest(),
        actual_collected_reader_executed=True,current_timestamp_type='int',invalid_comparison_left_operand='str',
        valid_current_serializer_preserves_integer=True,failure_precedes_database_read=True,
        exact_exception_reproductions=outcomes,sqlite_text_propagation_reproduced_in_memory=True,
        physical_malformed_cache_payload_available=False,physical_original_producer_proven=False,
        physical_database_modified=False,third_party_code_modified=False,
        conclusion='Invalid cached value/schema at the expiry reader; current timestamp/JSON round trip does not introduce the mismatch. Physical original producer is unknown.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('installed','published','logs','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=run(a.installed,a.published,a.logs);a.out.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2))
