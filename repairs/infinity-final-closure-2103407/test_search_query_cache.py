"""Exact signed-source contract; no invented Android/provider speed result."""
import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from zipfile import ZipFile
import patch_search_query_cache as patcher

APK=Path(os.environ.get('INFINITY_CACHE_PARENT_APK','/tmp/infinity-7aaf-artifacts/candidate417/fast-home-candidate/Infinity-2103417-Continue-Watching-Corrective-VERIFICATION.apk'))


def actual_source():
    with ZipFile(APK) as z:return z.read('assets/addons/script.infinity.commandcenter/infinity_search.py')


class QueryCacheTests(unittest.TestCase):
    def setup_code(self,revised=True):
        raw=actual_source();raw=patcher.patch('infinity_search.py',raw) if revised else raw
        tree=ast.parse(raw);selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in
            ('_query_cache_entries','_remember_query_answer','_provider_result')]
        self.clock=[100.0];self.props={};self.leases=[];self.routes=[];self.profile=['/profile/one'];self.reject=[False]
        self.cancel=SimpleNamespace(iscanceled=lambda:False)
        self.home=SimpleNamespace(getProperty=lambda key:self.props.get(key,''),setProperty=lambda key,value:self.props.__setitem__(key,value))
        def route(provider,query):
            self.routes.append((provider['id'],query))
            if self.reject[0]:raise RuntimeError('Actual source changed')
            return 'plugin://'+provider['id']+'/?q='+query
        def leased(path,home,progress):
            self.leases.append(path)
            return 'completed',{'result':{'files':[{'label':path,'file':path}]}}
        self.env=dict(json=json,hashlib=hashlib,time=SimpleNamespace(monotonic=lambda:self.clock[0]),
            xbmcvfs=SimpleNamespace(translatePath=lambda path:self.profile[0]),route=route,
            _leased_directory=leased,_VisibleCancellation=lambda cancel,progress:cancel)
        exec(compile(ast.Module(body=selected,type_ignores=[]),'actual-signed-Search.py','exec'),self.env)
        self.provider=dict(id='plugin.video.umbrella',contract=dict(pins={'main.py':'a'*64}))
        self.run_query=lambda query:self.env['_provider_result'](self.provider,query,self.home,self.cancel)
        return self.env

    def test_two_recent_queries_avoid_actual_source_lease_calls_without_renewing_age(self):
        calls=[]
        for revised in (False,True):
            self.setup_code(revised)
            for query in ('first','second','first','second'):
                result=self.run_query(query);self.assertEqual(result[1],'completed')
            calls.append(len(self.leases))
            if revised:
                before=deepcopy(self.props);self.clock[0]=200;self.run_query('first')
                self.assertEqual(self.props,before);self.assertEqual(len(self.routes),10)
        self.assertEqual(calls,[4,2])

    def test_expiry_future_nonfinite_bool_and_invalid_schema_cannot_supply_cached_answers(self):
        env=self.setup_code();read=env['_query_cache_entries'];row=dict(signature='a'*64,at=100,answer={'result':{'files':[]}})
        self.assertEqual(len(read(json.dumps(row),399.999)),1)
        self.assertFalse(read(json.dumps(row),400));self.assertFalse(read(json.dumps(row),99))
        for stamp in (True,float('nan'),float('inf'),'100'):
            self.assertFalse(read(json.dumps(dict(row,at=stamp)),101))
        for value in ({'schema':99,'entries':[row]},{'schema':2,'entries':[row]*2},[],{'schema':2,'entries':[row]*5}):
            self.assertFalse(read(json.dumps(value),101))
        self.assertFalse(read('x'*300000,101));self.assertFalse(read('é',101))

    def test_at_most_four_entries_and_same_strict_byte_budget_oversize_keeps_other_queries(self):
        env=self.setup_code();remember=env['_remember_query_answer'];read=env['_query_cache_entries']
        for i in range(6):
            entries=read(self.props.get('cache',''),100)
            self.assertTrue(remember(self.home,'cache',entries,format(i,'064x'),{'result':{'files':[]}},100))
        entries=read(self.props['cache'],100);self.assertEqual(len(entries),4)
        self.assertEqual([r['signature'] for r in entries],[format(i,'064x') for i in (5,4,3,2)])
        before=self.props['cache']
        self.assertFalse(remember(self.home,'cache',entries,'f'*64,{'result':{'files':[]},'plot':'x'*300000},100))
        self.assertEqual(self.props['cache'],before)
        remember(self.home,'cache',entries,'f'*64,{'result':{'files':[]},'plot':'字'*30000},100)
        self.assertLess(len(self.props['cache'].encode()),300000);self.assertLessEqual(len(read(self.props['cache'],100)),4)

    def test_legacy_valid_answer_is_preserved_on_new_query_and_source_profile_identity_isolated(self):
        env=self.setup_code();self.run_query('first');raw=json.loads(next(iter(self.props.values())))
        key=next(iter(self.props));self.props[key]=json.dumps(raw['entries'][0])
        self.run_query('first');self.assertEqual(len(self.leases),1)
        self.run_query('second');self.assertEqual(len(json.loads(self.props[key])['entries']),2)
        self.profile[0]='/profile/two';self.run_query('first');self.assertEqual(len(self.leases),3)
        self.provider['contract']['pins']['main.py']='b'*64;self.run_query('first');self.assertEqual(len(self.leases),4)
        self.reject[0]=True;self.assertEqual(self.run_query('first')[1],'unavailable');self.assertEqual(len(self.leases),4)

    def test_source_race_after_cache_hit_is_rejected_and_failed_or_cancelled_work_never_cached(self):
        env=self.setup_code();self.run_query('first');before=deepcopy(self.props);calls=[0]
        original=env['route']
        def raced(provider,query):
            calls[0]+=1
            if calls[0]==2:raise RuntimeError('Provider updated after cache lookup')
            return original(provider,query)
        env['route']=raced
        self.assertEqual(self.run_query('first')[1],'unavailable');self.assertEqual(len(self.leases),1)
        self.assertEqual(self.props,before)
        for outcome in ('timeout','busy','cancelled','completed'):
            env=self.setup_code();env['_leased_directory']=lambda *args:(outcome,{'error':{'message':'actual failure'}})
            self.run_query('first');self.assertFalse(self.props)
        env=self.setup_code()
        def cancelled(*args):
            self.cancel.iscanceled=lambda:True
            return 'completed',{'result':{'files':[]}}
        env['_leased_directory']=cancelled
        self.assertEqual(self.run_query('first')[1],'cancelled');self.assertFalse(self.props)

    def test_exact_inverse_keeps_route_admission_cancellation_and_original_writer_boundaries(self):
        before=actual_source();after=patcher.patch('infinity_search.py',before)
        a=ast.parse(before);b=ast.parse(after)
        functions=lambda t:{n.name:ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,ast.FunctionDef)}
        old,new=functions(a),functions(b)
        self.assertEqual(set(new)-set(old),{'_query_cache_entries','_remember_query_answer'})
        self.assertEqual([name for name in old if old[name]!=new[name]],['_provider_result'])
        self.assertEqual(after.count(b'route(provider,query)'),before.count(b'route(provider,query)'))
        with self.assertRaises(ValueError):patcher.patch('infinity_search.py',before+b'\n')


if __name__=='__main__':unittest.main(verbosity=2)
