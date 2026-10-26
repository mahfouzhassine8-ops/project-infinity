"""Independent routing and real-receipt rejection, not a device PASS."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

import android17_candidate_probe as candidate
import android17_shutdown_probe as probe
import shutdown_request as request

ROOT=Path(__file__).resolve().parents[2]


class IndependentShutdownTests(unittest.TestCase):
    def test_exact_independent_scope_and_branch_required(self):
        head='a'*40;event=dict(ref=request.BRANCH,after=head,repository={'full_name':'mahfouzhassine8-ops/project-infinity'})
        self.assertEqual(request.validate(request.EXPECTED,event,head,[request.REQUEST])['SELECTED_CASE'],'integrated-3-close-reopen')
        for field,value in [('scenario','safe'),('candidate_apk_sha256','0'*64),('authorization',''),('request_id','unreviewed')]:
            with self.assertRaises(ValueError):request.validate(dict(request.EXPECTED,**{field:value}),event,head,[request.REQUEST])
        for changed in ([],[request.REQUEST,'unowned.cpp']):
            with self.assertRaises(ValueError):request.validate(request.EXPECTED,event,head,changed)
        with self.assertRaises(ValueError):request.validate(request.EXPECTED,dict(event,ref='refs/heads/main'),head,[request.REQUEST])

    def test_manual_shutdown_job_is_unchanged_and_candidate_has_no_dependency(self):
        before=subprocess.check_output(['git','show','efc2c51017e6ee14475a506fb1dc899c2f49e2ca:'+request.WORKFLOW],text=True)
        after=(ROOT/request.WORKFLOW).read_text()
        marker='  integrated-candidate:\n'
        prefix=after.split(marker)[0]
        prefix=prefix.replace("  push:\n    branches: [work/infinity-final-corrective-from-2103407-20261025]\n    paths: ['repairs/infinity-final-closure-2103407/SHUTDOWN-REQUEST.json']\n",'',1)
        prefix=prefix.replace("    if: github.event_name == 'workflow_dispatch'\n",'',1)
        self.assertEqual(prefix.rstrip(),before.rstrip())
        for required in ('delivery92.verify_signature','independent-shutdown-request-evidence.json',"api-level: '37.0'",'android17_shutdown_probe.py'):
            self.assertIn(required,after)
        for forbidden in ('needs:','workflow_run:','continue-on-error:'):
            self.assertNotIn(forbidden,after)
        feature=(ROOT/'.github/workflows/infinity-saved-navigation-android.yml').read_text()
        self.assertNotIn('android17_shutdown_probe',feature);self.assertNotIn('SHUTDOWN-REQUEST',feature)

    def receipt(self):
        owner={'pid':123,'owner':'e0d637de-9aa2-4f92-83fa-92d0ca2fd540'}
        names=sorted(probe.ESSENTIAL)
        native=dict(**owner,session='a3d637de-9aa2-4f92-83fa-92d0ca2fd540',phase='SAFE_TO_TERMINATE',generation=7,essential_write_generation=7,
            admission_sealed=True,inventory_complete=True,blocker_count=0,error='',
            essential_writes_sealed=True,essential_writes_durable=True,essential_write_blockers=[],
            essential_owners=names,owners=[dict(owner=n,required_writes_finished=True,dirty=False,dirty_remaining=False,
                dirty_before=True,checkpoint_generation=7,generation=2,durable_generation=2,result='COMMITTED') for n in names]+[dict(owner='python_services')])
        receipt=dict(**owner,session=native['session'],phase='COMPLETE',checkpoint_saved=True,authorization_consumed=True,
            process_death_confirmed=True,exit_policy='essential_first_process_exit_v1',coordinator_termination_authorized=True,
            engine_java_save_seal=native['session'],coordinator_java_save_seal=native['session'],
            engine_java_pending='',coordinator_java_pending='',native_receipt=native,generation=7,
            started_elapsed_ms=1,safe_elapsed_ms=2,terminate_requested_elapsed_ms=3,authorization_consumed_elapsed_ms=4,
            engine_death_elapsed_ms=5,safe_epoch_ms=100,authorization_consumed_epoch_ms=101,engine_death_epoch_ms=102)
        self.seal(receipt)
        return owner,receipt

    def seal(self,receipt):
        receipt['native_json']=json.dumps(receipt['native_receipt'])
        receipt['native_proof_sha256']=hashlib.sha256(receipt['native_json'].encode()).hexdigest()

    def test_missing_or_failed_close_and_each_proof_is_rejected(self):
        owner,receipt=self.receipt();probe.verify_receipt(receipt,owner)
        for key,value in [('phase','CHECKPOINT_FAILED'),('pid',124),('owner','stale'),('checkpoint_saved',False),
            ('authorization_consumed',False),('process_death_confirmed',False),('exit_policy','other'),
            ('coordinator_termination_authorized',False),('engine_java_save_seal',''),('coordinator_java_save_seal',''),
            ('engine_java_pending',True),('coordinator_java_pending',True),('session','stale'),('generation',6),
            ('safe_elapsed_ms',0),('authorization_consumed_elapsed_ms',2),('engine_death_elapsed_ms',3),
            ('started_elapsed_ms',None),('safe_epoch_ms',0),('native_proof_sha256','0'*64),('native_json','{}')]:
            with self.subTest(key=key),self.assertRaises(AssertionError):probe.verify_receipt(dict(receipt,**{key:value}),owner)
        with self.assertRaises(AssertionError):probe.verify_receipt({},owner)

    def test_native_owner_generation_and_shared_write_failures_are_never_waived(self):
        owner,receipt=self.receipt()
        for key,value in [('pid',124),('owner','stale'),('session','stale'),('generation',0),('essential_write_generation',6),
            ('admission_sealed',False),('inventory_complete',False),('blocker_count',1),('error','failure'),
            ('essential_writes_sealed',False),('essential_writes_durable',False),('essential_write_blockers',['unknown writer']),
            ('essential_owners',[]),('owners',[])]:
            changed=deepcopy(receipt);changed['native_receipt'][key]=value;self.seal(changed)
            with self.subTest(key=key),self.assertRaises(AssertionError):probe.verify_receipt(changed,owner)
        for key,value in [('required_writes_finished',False),('dirty_remaining',True),('result','WAITING'),
            ('checkpoint_generation',6),('durable_generation',1),('generation',-1),('dirty',True)]:
            changed=deepcopy(receipt);changed['native_receipt']['owners'][0][key]=value;self.seal(changed)
            with self.assertRaises(AssertionError):probe.verify_receipt(changed,owner)

    def test_readback_preserves_all_records_and_successful_provider_memory(self):
        before={name:{'exact-id':{'position':37,'route':'original remembered provider'}} for name in probe.BUCKETS}
        probe.verify_records(before,deepcopy(before))
        for bucket in probe.BUCKETS:
            changed=deepcopy(before);changed[bucket]['exact-id']['position']=0
            with self.assertRaises(AssertionError):probe.verify_records(before,changed)

    def test_reused_feature_setup_still_refuses_termination_and_wrong_case(self):
        import sys
        sys.path.insert(0,str(candidate.OLD))
        import android_feature_device
        with self.assertRaises(RuntimeError):android_feature_device.guard(('am','start','InfinityPowerControlActivity'))
        with self.assertRaises(ValueError):candidate.main(selected_case='unselected-case')
        body=Path(probe.__file__).read_text()
        for forbidden in ('pm clear','uninstall','force-stop','os.kill','kill -','setenforce','chmod 777'):
            self.assertNotIn(forbidden,body)
        self.assertIn('range(3)',body);self.assertIn('time.monotonic()+35',body)


if __name__=='__main__':unittest.main(verbosity=2)
