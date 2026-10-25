"""Deterministic overload/cancellation tests against real signed Search source.

No Kodi or provider network calls: only the native JSON-RPC boundary is stubbed.
Verifies the old runtime weakness, the patched cross-invoker admission gate,
source route preservation, and absence of unowned post-cancel threads.
"""
import ast
import hashlib
import os
from pathlib import Path
import threading
import time
import types
import unittest
import uuid

ROOT=Path(__file__).resolve().parent
BASE=Path(os.environ['SIGNED_SEARCH'])
FIXED=Path(os.environ['PATCHED_SEARCH'])
MODULE_NAMES={'_leased_directory','_native_search_admission','_bounded_results','_Cancellation','_VisibleCancellation'}

def methods(path, rpc, monitor=None):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in MODULE_NAMES]
    scope={'threading':threading,'hashlib':hashlib,'uuid':uuid,
           'xbmc':types.SimpleNamespace(Monitor=monitor or (lambda:types.SimpleNamespace(abortRequested=lambda:False))),
           'rpc':rpc,'MAX_RESULTS':40,'PROPERTIES':['title']}
    exec(compile(ast.fix_missing_locations(ast.Module(nodes,type_ignores=[])),str(path),'exec'),scope)
    return scope

class Home:
    def __init__(self):self.props={};self.lock=threading.Lock();self.cancel_writes=0
    def setProperty(self,key,val):
        with self.lock:
            self.props[key]=val
            if '.Cancel.' in key:self.cancel_writes+=1
    def getProperty(self,key):
        with self.lock:
            return 'completed' if '.Result.' in key else self.props.get(key,'')
    def clearProperty(self,key):
        with self.lock:self.props.pop(key,None)

class Progress:
    def __init__(self):self.canceled=False
    def iscanceled(self):return self.canceled

class FakeRPC:
    def __init__(self):
        self.release=threading.Event()
        self.called=threading.Event()
        self.lock=threading.Lock()
        self.inflight=0
        self.peak=0
        self.count=0
    def __call__(self,method,params):
        assert method=='Files.GetDirectory'
        with self.lock:
            self.inflight+=1;self.count+=1;self.peak=max(self.peak,self.inflight);self.called.set()
        if not self.release.wait(3):raise RuntimeError('test worker timed out')
        with self.lock:self.inflight-=1
        return {'result':{'files':[]}}

class SearchPressureTests(unittest.TestCase):
    def call_parallel(self,source,n=2):
        stub=FakeRPC();home=Home();scope=methods(source,stub)
        results=[]
        threads=[threading.Thread(target=lambda k=k:results.append((k,scope['_leased_directory'](
                'plugin://plugin.video.seren/?q='+str(k),home,Progress())))) for k in range(n)]
        for t in threads:t.start()
        self.assertTrue(stub.called.wait(2))
        try:
            time.sleep(.13)
            return stub,home,threads,results
        except BaseException:
            stub.release.set()
            for t in threads:t.join(2)
            raise
    def finish(self,stub,threads):
        stub.release.set()
        for t in threads:t.join(2)
        self.assertTrue(all(not t.is_alive() for t in threads),'Unretired test worker')
    def test_signed_baseline_reproduces_multiple_active_rpcs(self):
        self.assertEqual(hashlib.sha256(BASE.read_bytes()).hexdigest(),
          'a5640a725d07440e914fd5f8d83a29196ea9cbb1104686f1929b5140040b2c44')
        stub,home,threads,results=self.call_parallel(BASE)
        try:
            self.assertEqual(stub.peak,2,'Signed Search did not reproduce cross-invoker overload')
            self.assertEqual(sum(t.is_alive() for t in threads),2)
        finally:self.finish(stub,threads)
        self.assertEqual(home.props,{})
    def test_process_wide_guard_rejects_second_rpc_without_launching_a_worker(self):
        stub,home,threads,results=self.call_parallel(FIXED,n=2)
        try:
            self.assertEqual(stub.peak,1)
            self.assertEqual(stub.count,1)
            self.assertEqual(len(results),1,'Rejected extra session must return promptly')
            self.assertEqual(results[0][1][0],'busy')
            self.assertIn('previous Infinity Search',results[0][1][1]['error']['message'])
        finally:self.finish(stub,threads)
        self.assertEqual(len(results),2)
        self.assertEqual(home.props,{})
    def test_admission_auto_releases_after_worker_completion(self):
        stub=FakeRPC();stub.release.set();scope=methods(FIXED,stub);home=Home()
        for k in range(4):
            status,result=scope['_leased_directory']('plugin://plugin.video.seren/?q='+str(k),home,Progress())
            self.assertEqual(status,'completed')
        self.assertEqual(stub.count,4)
        self.assertEqual(home.props,{})
    def test_cancel_repeatedly_writes_only_one_signal_and_never_abandons_worker(self):
        stub=FakeRPC();scope=methods(FIXED,stub);home=Home();prog=Progress()
        result=[]
        t=threading.Thread(target=lambda:result.append(scope['_leased_directory'](
            'plugin://plugin.video.seren/?q=1',home,prog)))
        t.start();self.assertTrue(stub.called.wait(2))
        try:
            prog.canceled=True
            time.sleep(.28)
            self.assertEqual(home.cancel_writes,1)
            self.assertTrue(t.is_alive(),'Original invoker must remain owned until it retires')
            other=scope['_leased_directory']('plugin://plugin.video.seren/?q=2',home,Progress())
            self.assertEqual(other[0],'busy')
        finally:stub.release.set();t.join(2)
        self.assertFalse(t.is_alive());self.assertEqual(home.props,{})
        self.assertEqual(stub.count,1)
    def test_probe_path_keeps_original_capability_handshake(self):
        stub=FakeRPC();stub.release.set();scope=methods(FIXED,stub);home=Home()
        status,_=scope['_leased_directory']('plugin://script.infinity.commandcenter/?action=search-probe',home)
        self.assertEqual(status,'completed')
        self.assertEqual(stub.count,1)
        self.assertEqual(home.props,{})
    def test_only_search_affected_and_no_disk_lock(self):
        src=FIXED.read_text()
        self.assertIn("path.startswith('plugin://plugin.video.')",src)
        block=src[src.index('def _native_search_admission'):src.index('def _leased_directory')]
        self.assertIn('socket.AF_UNIX',block)
        self.assertIn("'\\0infinity-search-native-rpc-v1-' + str(os.getpid())",block)
        self.assertNotIn('open(',block)
        self.assertNotIn('os.mkdir',block)
        self.assertNotIn('atomic_json',block)
        self.assertNotIn('StopScript',src)
        self.assertNotIn('kill(',block)
    def test_second_results_session_is_not_queued_across_other_providers(self):
        src=FIXED.read_text()
        self.assertIn("if result[1] == 'busy':",src)
        self.assertIn('break  # Never hammer other providers',src)

if __name__=='__main__':unittest.main(verbosity=2)
