"""Reproduce captured POV column order using unchanged cache classes and disposable DBs."""
import argparse
import ast
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile

def sha(data):return hashlib.sha256(data).hexdigest()
def definitions(raw,filename,scope,classes_only=False):
    tree=ast.parse(raw)
    body=[n for n in tree.body if isinstance(n,ast.ClassDef)] if classes_only else [n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))]
    exec(compile(ast.Module(body=body,type_ignores=[]),filename,'exec'),scope)

def run(published,collected,summary):
    cache=published/'resources/lib/caches'
    meta_raw=(cache/'meta_cache.py').read_bytes()
    if meta_raw!=(collected/'resources/lib/caches/meta_cache.py').read_bytes():
        raise RuntimeError('Collected actual cache reader/writer differs from this source')
    reported=json.loads(summary.read_text())
    columns={(db['file'],table['table']):table['columns'] for db in reported for table in db.get('tables',[])}
    expected={('metacache.db','metadata'):['db_type','tmdb_id','imdb_id','tvdb_id','expires','meta'],
              ('metacache.db','season_metadata'):['tmdb_id','expires','meta'],
              ('maincache.db','maincache'):['id','expires','data']}
    for pair in expected:
        if set(columns[pair])!=set(expected[pair]):raise RuntimeError('Unrecognized captured schema')
    results=[]
    with tempfile.TemporaryDirectory(prefix='pov-schema-evidence-') as directory:
        for shape in ('current_source_order','captured_fold_order'):
            memory={}
            mainpath=str(Path(directory)/(shape+'-main.db'))
            metapath=str(Path(directory)/(shape+'-meta.db'))
            schema=expected if shape=='current_source_order' else columns
            for pair in expected:
                file,table=pair;path=mainpath if file=='maincache.db' else metapath
                unique='UNIQUE(db_type,tmdb_id)' if table=='metadata' else 'UNIQUE('+('id' if table=='maincache' else 'tmdb_id')+')'
                declarations=[name+(' INTEGER' if name=='expires' else ' TEXT') for name in schema[pair]]
                with sqlite3.connect(path) as db:db.execute('CREATE TABLE '+table+' ('+','.join(declarations+[unique])+')')
            scope=dict(json=json,datetime=datetime,timedelta=timedelta,database_connect=sqlite3.connect,
                maincache_db=mainpath,metacache_db=metapath,
                get_property=lambda key:memory.get(key,''),set_property=lambda key,value:memory.__setitem__(key,value),
                clear_property=lambda key:memory.pop(key,None))
            definitions((cache/'__init__.py').read_bytes(),'unchanged-pov-BaseCache.py',scope,True)
            definitions(meta_raw,'collected-pov-meta_cache.py',scope)
            definitions((cache/'main_cache.py').read_bytes(),'published-pov-main_cache.py',scope)
            meta=scope['MetaCache']();main=scope['MainCache']()
            payload=dict(tmdb_id='330430',tvdb_id='482439',imdb_id='tt48447471',title='Love After Lockup: Relationship Rehab')
            meta.set('tvshow','tmdb_id',payload)
            main.set('schema-probe',{'items':[330430]},timedelta(hours=1))
            if meta.get('tvshow','tmdb_id','330430')!=payload:raise RuntimeError('Immediate valid memory behavior changed')
            # A fresh test memory dictionary models the next interpreter/session.
            # This touches only this disposable fixture, never a provider profile.
            memory.clear()
            cases=[]
            for table,path,getter in [('metadata',metapath,lambda:meta.get('tvshow','tmdb_id','330430')),
                                      ('maincache',mainpath,lambda:main.get('schema-probe'))]:
                with sqlite3.connect(path) as db:
                    expiry_type=db.execute('SELECT typeof(expires) FROM '+table).fetchone()[0]
                first=getter()
                if shape=='current_source_order':
                    if expiry_type!='integer' or not isinstance(first,dict) or getter()!=first:
                        raise RuntimeError('Current schema round trip failed')
                    outcome='valid dictionary and integer expiry'
                else:
                    if expiry_type!='text' or type(first) is not int:
                        raise RuntimeError('Captured column-order reproduction differs')
                    try:getter()
                    except TypeError as error:
                        if str(error)!="'<' not supported between instances of 'str' and 'int'":raise
                        outcome=str(error)
                    else:raise RuntimeError('Original error was not reproduced')
                cases.append(dict(table=table,expiry_storage_type=expiry_type,first_read_type=type(first).__name__,second_read=outcome))
            results.append(dict(schema=shape,cases=cases))
    return dict(passed=True,collected_reader_writer_sha256=sha(meta_raw),
        published_base_sha256=sha((cache/'__init__.py').read_bytes()),
        captured_column_order={table:columns[(file,table)] for file,table in expected},
        expected_positional_insert_order={table:names for (_,table),names in expected.items()},
        actual_class_methods_executed=True,results=results,
        physical_schema_order_mismatch_verified=True,physical_exact_bad_row_exported=False,
        physical_bad_row_producer_proven=False,user_databases_opened=False,provider_source_modified=False,
        conclusion='The recorded column order is incompatible with current positional inserts. Unchanged POV methods on that order write JSON into expires and reproduce the exact second-read TypeError. Original Fold row values were not collected.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('published','collected','summary','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();result=run(a.published,a.collected,a.summary)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
