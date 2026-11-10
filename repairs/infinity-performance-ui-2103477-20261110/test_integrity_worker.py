"""Selected actual-source worker/checksum contracts; no application execution."""
import ast
import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import types
import unittest

HERE = Path(__file__).parent
BASE = Path('/workspace/scratch/infinity-performance-77/baseline/assets/addons/script.infinity.commandcenter')
OVERLAY = HERE/'overlay/script.infinity.commandcenter'


def functions(path, names, namespace):
    tree=ast.parse(path.read_text())
    selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    if {n.name for n in selected} != set(names):raise AssertionError('Exact function selection')
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),'exec'),namespace)
    return namespace


class IntegrityContracts(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.file=self.root/'unified/Home.xml';self.file.parent.mkdir();self.file.write_bytes(b'a'*200000)
        self.manifest={'candidate':270,'skin_version':'1.0.5.270','protected_files':{
            'unified/Home.xml':hashlib.sha256(self.file.read_bytes()).hexdigest()}}
        self.manifest_path=self.root/'Infinity-Protected-Manifest.json';self.write_manifest()
        namespace=dict(Path=Path,hashlib=hashlib,os=os,xbmcvfs=types.SimpleNamespace(translatePath=lambda _:str(self.root)),
                       read_json=lambda path,default:json.loads(Path(path).read_text()) if Path(path).exists() else default)
        self.old=functions(BASE/'common.py',['skin_baseline_integrity'],dict(namespace))
        self.new=functions(OVERLAY/'common.py',['skin_baseline_integrity','_scan_skin_integrity','_skin_digest_cancellable'],dict(namespace))
        self.gate=types.SimpleNamespace(value=True);self.gate.visible=lambda:self.gate.value
        self.monitor=types.SimpleNamespace(value=False);self.monitor.abortRequested=lambda:self.monitor.value
        self.calls=[];self.releases=[]
        self.contract=types.SimpleNamespace(identity=types.SimpleNamespace(manifest_sha256='test-generation'),current=lambda:self.calls.append('current'))
        self.ns=dict(Path=Path,time=time,threading=threading,os=os,json=json,
            xbmc=types.SimpleNamespace(getSkinDir=lambda:'skin.infinity.diggz'),
            xbmcvfs=types.SimpleNamespace(translatePath=lambda _:str(self.root)),
            _skin_root=lambda:self.root,read_json=namespace['read_json'],
            _scan_skin_integrity=self.new['_scan_skin_integrity'],_infinity_contract=self.contract,
            log=lambda message:self.calls.append(message),_integrity_cache=None,_integrity_signature=None,
            _integrity_checked_at=0.0,_integrity_job=None,_integrity_job_lock=threading.Lock(),
            _integrity_retry_after=0.0,_integrity_monitor=self.monitor,_integrity_foreground=self.gate)
        functions(OVERLAY/'service.py',['_integrity_pending','_cancel_integrity','_skin_integrity_signature','_read_integrity_manifest',
            '_run_skin_integrity','_background_integrity'],self.ns)

    def tearDown(self):
        for event in self.releases:event.set()
        job=self.ns.get('_integrity_job')
        if job:
            job['cancel'].set();job['thread'].join(timeout=2)
            self.assertFalse(job['thread'].is_alive(),'Owned host worker must retire')
        self.temp.cleanup()

    def write_manifest(self):self.manifest_path.write_text(json.dumps(self.manifest,sort_keys=True))

    def finish(self):
        job=self.ns['_integrity_job'];self.assertIsNotNone(job)
        job['thread'].join(timeout=2);self.assertFalse(job['thread'].is_alive())

    def blocking_checker(self):
        begun=threading.Event();release=threading.Event();self.releases.append(release)
        def checker(root,manifest,canceled):
            begun.set();release.wait(timeout=2)
            return {'status':'ok','checked':1,'mismatches':[],'candidate':270,'skin_version':'1.0.5.270'}
        self.ns['_scan_skin_integrity']=checker
        return begun,release

    def test_manual_and_full_worker_results_match_signed77(self):
        for mutation in ('healthy','changed','missing','empty'):
            with self.subTest(mutation=mutation):
                if mutation=='changed':self.file.write_bytes(b'changed')
                elif mutation=='missing':self.file.unlink()
                elif mutation=='empty':self.manifest['protected_files']={};self.write_manifest()
                expected=self.old['skin_baseline_integrity']()
                self.assertEqual(self.new['skin_baseline_integrity'](),expected)
                self.assertEqual(self.new['_scan_skin_integrity'](self.root,self.manifest,lambda:False),expected)

    def test_mismatch_limit_and_sorted_order_preserved(self):
        self.manifest['protected_files']={str(n)+'.xml':'0'*64 for n in range(45)};self.write_manifest()
        expected=self.old['skin_baseline_integrity']()
        self.assertEqual(expected['checked'],45);self.assertEqual(len(expected['mismatches']),40)
        self.assertEqual(self.new['_scan_skin_integrity'](self.root,self.manifest,lambda:False),expected)

    def test_cancel_closes_all_descriptors_and_does_not_follow_outside_links(self):
        before=len(os.listdir('/proc/self/fd'))
        for _ in range(10):
            count=[0]
            def canceled():count[0]+=1;return count[0]>=4
            status,digest=self.new['_skin_digest_cancellable'](self.root,'unified/Home.xml',canceled)
            self.assertEqual(status,'canceled');self.assertIsNone(digest)
        self.assertEqual(len(os.listdir('/proc/self/fd')),before)
        outside=self.root/'outside.txt';outside.write_text('private fixture')
        (self.file.parent/'link.xml').symlink_to(outside)
        for name in ['../outside.txt','unified/link.xml']:
            self.assertEqual(self.new['_skin_digest_cancellable'](self.root,name,lambda:False)[0],'unreadable')
        self.assertEqual(len(os.listdir('/proc/self/fd')),before)

    def test_one_worker_and_no_healthy_result_for_changed_generation(self):
        begun,release=self.blocking_checker()
        self.assertEqual(self.ns['_background_integrity']()['status'],'checking');self.assertTrue(begun.wait(1))
        first=self.ns['_integrity_job']
        self.assertFalse(first['thread'].daemon)
        self.manifest['candidate']='changed-generation';self.write_manifest()
        for _ in range(5):
            self.assertEqual(self.ns['_background_integrity']()['status'],'checking')
            self.assertIs(self.ns['_integrity_job'],first)
            self.assertEqual(sum(t.name=='InfinitySkinIntegrity' for t in threading.enumerate()),1)
        self.assertTrue(first['cancel'].is_set())
        release.set();self.finish();self.ns['_background_integrity']()
        self.assertIsNone(self.ns['_integrity_cache'])

    def test_complete_current_result_and_cache_cadence(self):
        self.assertEqual(self.ns['_background_integrity']()['status'],'checking');self.finish()
        expected=self.old['skin_baseline_integrity']()
        self.assertEqual(self.ns['_background_integrity'](),expected)
        self.assertIsNone(self.ns['_integrity_job'])
        self.assertEqual(self.ns['_background_integrity'](),expected)
        self.assertIsNone(self.ns['_integrity_job'])

    def test_background_and_abort_cancel_without_publishing_partial(self):
        for mode in ('background','abort'):
            with self.subTest(mode=mode):
                self.gate.value=True;self.monitor.value=False;self.ns['_integrity_retry_after']=0
                begun,release=self.blocking_checker();self.ns['_background_integrity']();self.assertTrue(begun.wait(1))
                if mode=='background':self.gate.value=False
                else:self.monitor.value=True
                self.assertEqual(self.ns['_background_integrity']()['status'],'checking')
                release.set();self.finish();self.assertEqual(self.ns['_integrity_job']['result']['status'],'canceled')
                self.gate.value=True;self.monitor.value=False
                self.ns['_background_integrity']();self.assertIsNone(self.ns['_integrity_cache'])

    def test_failure_is_unavailable_and_does_not_restart_each_tick(self):
        def failed(*_):raise OSError('controlled fixture failure')
        self.ns['_scan_skin_integrity']=failed;self.ns['_background_integrity']();self.finish()
        self.assertEqual(self.ns['_background_integrity']()['status'],'unavailable')
        for _ in range(5):self.assertEqual(self.ns['_background_integrity']()['status'],'unavailable')
        self.assertIsNone(self.ns['_integrity_job'])

    def test_no_work_before_existing_monitor_or_outside_infinity_skin(self):
        self.ns['_integrity_monitor']=None
        self.assertEqual(self.ns['_background_integrity']()['status'],'checking')
        self.assertIsNone(self.ns['_integrity_job'])
        self.ns['_integrity_monitor']=self.monitor
        self.ns['xbmc'].getSkinDir=lambda:'other.skin'
        self.assertEqual(self.ns['_background_integrity']()['status'],'checking')
        self.assertIsNone(self.ns['_integrity_job']);self.assertEqual(self.calls,[])

    def test_file_mutation_during_stream_is_not_healthy(self):
        changed=[False]
        def canceled():
            if not changed[0]:
                for name in os.listdir('/proc/self/fd'):
                    try:
                        if os.readlink('/proc/self/fd/'+name)==str(self.file) and os.lseek(int(name),0,os.SEEK_CUR)>=65536:
                            self.file.write_bytes(b'b'*200000);changed[0]=True;break
                    except OSError:pass
            return False
        status,digest=self.new['_skin_digest_cancellable'](self.root,'unified/Home.xml',canceled)
        self.assertTrue(changed[0]);self.assertEqual(status,'changed');self.assertIsNone(digest)

    def test_module_generation_result_is_discarded(self):
        begun,release=self.blocking_checker();self.ns['_background_integrity']();self.assertTrue(begun.wait(1))
        self.contract.identity.manifest_sha256='replacement-generation'
        release.set();self.finish()
        self.assertEqual(self.ns['_background_integrity']()['status'],'checking')
        self.assertIsNone(self.ns['_integrity_cache'])

    def test_authentication_failure_before_publication_stays_fail_closed(self):
        self.ns['_background_integrity']();self.finish()
        class Rejected(RuntimeError):pass
        def reject():raise Rejected('controlled signature rejection')
        self.contract.current=reject
        with self.assertRaises(Rejected):self.ns['_background_integrity']()
        self.assertIsNone(self.ns['_integrity_cache'])

    def test_thread_start_failure_reports_unavailable_without_retry_storm(self):
        starts=[]
        class FailedThread:
            def __init__(self,**kwargs):starts.append(kwargs)
            def start(self):raise RuntimeError('controlled thread admission failure')
        self.ns['threading']=types.SimpleNamespace(Thread=FailedThread,Event=threading.Event)
        self.assertEqual(self.ns['_background_integrity']()['status'],'unavailable')
        for _ in range(5):self.assertEqual(self.ns['_background_integrity']()['status'],'unavailable')
        self.assertEqual(len(starts),1);self.assertFalse(starts[0]['daemon'])
        self.assertIsNone(self.ns['_integrity_job'])

    def test_growing_file_reads_only_captured_size(self):
        initial=self.file.stat().st_size
        class CountOS:
            total=0
            def __getattr__(self,name):return getattr(os,name)
            def read(self,descriptor,size):
                block=os.read(descriptor,size);self.total+=len(block);return block
        counted=CountOS();self.new['os']=counted
        def canceled():
            if counted.total:
                with self.file.open('ab') as stream:stream.write(b'x'*65536)
            return counted.total>initial+65536  # A broken unbounded implementation must fail, not hang this test.
        status,digest=self.new['_skin_digest_cancellable'](self.root,'unified/Home.xml',canceled)
        self.assertEqual(status,'changed');self.assertIsNone(digest);self.assertEqual(counted.total,initial)

    def test_private_work_limits_never_report_healthy(self):
        with self.file.open('r+b') as stream:stream.truncate(64*1024*1024+1)
        result=self.new['_scan_skin_integrity'](self.root,self.manifest,lambda:False)
        self.assertEqual(result['status'],'unavailable');self.assertEqual(result['reason'],'file-size-budget')
        many={'protected_files':{str(n):'0'*64 for n in range(4097)}}
        result=self.new['_scan_skin_integrity'](self.root,many,lambda:False)
        self.assertEqual(result['status'],'unavailable');self.assertEqual(result['reason'],'file-count-budget')

    def test_cooperative_budget_and_completion_backoff(self):
        clock=[1.0];self.ns['time']=types.SimpleNamespace(monotonic=lambda:clock[0])
        def timeout(root,manifest,canceled):clock[0]=32.0;canceled()
        self.ns['_scan_skin_integrity']=timeout
        self.ns['_background_integrity']();self.finish()
        self.assertEqual(self.ns['_background_integrity']()['status'],'unavailable')
        self.assertEqual(self.ns['_integrity_checked_at'],32.0)
        clock[0]=33.0
        self.assertEqual(self.ns['_background_integrity']()['status'],'unavailable')
        self.assertIsNone(self.ns['_integrity_job'])

    def test_oversized_manifest_is_not_parsed_or_scheduled(self):
        self.manifest_path.write_bytes(b' '*(1024*1024+1))
        self.ns['read_json']=lambda *_:self.fail('Oversized background manifest must not be parsed')
        result=self.ns['_background_integrity']()
        self.assertEqual(result['status'],'unavailable');self.assertEqual(result['reason'],'manifest-size-budget')
        self.assertIsNone(self.ns['_integrity_job'])

    def test_growing_manifest_has_actual_bounded_read_and_no_fd_leak(self):
        signature=self.ns['_skin_integrity_signature'](self.root)
        path=self.manifest_path
        class GrowOS:
            total=0
            grew=False
            def __getattr__(self,name):return getattr(os,name)
            def read(self,descriptor,size):
                block=os.read(descriptor,size);self.total+=len(block)
                if block and not self.grew:
                    self.grew=True
                    with path.open('ab') as stream:stream.write(b' '*(2*1024*1024))
                return block
        proxy=GrowOS();self.ns['os']=proxy
        before=len(os.listdir('/proc/self/fd'))
        manifest,reason=self.ns['_read_integrity_manifest'](self.root,signature)
        self.assertIsNone(manifest);self.assertEqual(reason,'manifest-size-budget')
        self.assertLessEqual(proxy.total,1024*1024+1)
        self.assertEqual(len(os.listdir('/proc/self/fd')),before)

    def test_replaced_manifest_is_rejected_before_content_read(self):
        signature=self.ns['_skin_integrity_signature'](self.root)
        replacement=self.root/'replacement.json';replacement.write_text('{}');replacement.replace(self.manifest_path)
        manifest,reason=self.ns['_read_integrity_manifest'](self.root,signature)
        self.assertIsNone(manifest);self.assertEqual(reason,'manifest-changed')


if __name__=='__main__':unittest.main()
