"""Five selected release/preservation tests; no application or shutdown execution."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile
import yaml

H=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(H))
import release446 as r
import release_gate

class ReleaseTests(unittest.TestCase):
    def test_authority_route_preserves_all_existing_guards(self):
        old=r.cmd('git','show',r.BASE+':repairs/dual-experience-isolation-2103420/release_gate.py')
        expected=old.replace("AUTHORITY_BRANCH = 'work/cobra-2103444-rotation-audio-preserved-20261101'",
            "AUTHORITY_BRANCH = '"+r.BRANCH+"'\nEXTERNAL_PROTECTED_REF = 'refs/heads/lock/infinity-cobra-2103445-user-approved-20261101'\nEXTERNAL_PROTECTED_COMMIT = '"+r.BASE+"'")
        expected=expected.replace('QUALITY_PROTECTED_REF, ROTATION_PROTECTED_REF)','QUALITY_PROTECTED_REF, ROTATION_PROTECTED_REF, EXTERNAL_PROTECTED_REF)')
        expected=expected.replace("    require(refs.get(ROTATION_PROTECTED_REF)","    require(refs.get(EXTERNAL_PROTECTED_REF) == EXTERNAL_PROTECTED_COMMIT, 'EXTERNAL445_APPROVED_LOCK_MOVED')\n    require(refs.get(ROTATION_PROTECTED_REF)")
        self.assertEqual((r.ISO/'release_gate.py').read_text(),expected)
        self.assertEqual(release_gate.AUTHORITY_BRANCH,r.BRANCH)
        roots=json.loads(r.cmd('git','show',r.BASE+':repairs/dual-experience-isolation-2103420/ownership-reviewed-roots.json'))
        roots['project_roots']['InfinityExternalVideoIntents']='INFINITY'
        self.assertEqual(r.load(r.ISO/'ownership-reviewed-roots.json'),roots)
        for leaf in ('assemble.py','release_authority.py','component_bundles.py','signer_policy.py','accepted-combined-release.json'):
            self.assertEqual((r.ISO/leaf).read_bytes(),__import__('subprocess').check_output(['git','show',r.BASE+':'+str((r.ISO/leaf).relative_to(r.REPO))]))
        policy=r.load(r.ISO/'signer-policy.json');prior=json.loads(r.cmd('git','show',r.BASE+':repairs/dual-experience-isolation-2103420/signer-policy.json'))
        self.assertEqual(policy['retired_original_key_workflows'],prior['retired_original_key_workflows'])
        self.assertEqual(policy['sole_original_key_workflow_id'],prior['sole_original_key_workflow_id'])
        self.assertEqual(set(policy['reviewed_workflow_ids'])-set(prior['reviewed_workflow_ids']),{404063472})
        self.assertTrue(set(prior['reviewed_workflow_ids'])<=set(policy['reviewed_workflow_ids']))
        qa=(r.REPO/'.github/workflows/infinity-external-video-live-qa.yml').read_text()
        self.assertNotIn('secrets.',qa)
        self.assertEqual(qa,r.cmd('git','show','b2db7578264fb1151d9258a7fd833b500a8e41ed:.github/workflows/infinity-external-video-live-qa.yml'))

    def test_original_signer_after_exact_payload_gates(self):
        path=r.REPO/r.WORKFLOW;raw=path.read_text();data=yaml.safe_load(raw)
        self.assertEqual(data['name'],'Infinity combined release | owner gate before original signing')
        self.assertEqual(data['concurrency']['group'],'infinity-combined-original-key-release')
        self.assertFalse(data['concurrency']['cancel-in-progress'])
        key_count=0
        for name,job in data['jobs'].items():
            self.assertIn(r.BRANCH,job['if'])
            keys=[i for i,s in enumerate(job['steps']) if 'INFINITY_KEYSTORE_B64' in s.get('env',{})]
            key_count+=len(keys)
            if name!='combined':self.assertFalse(keys);continue
            self.assertEqual(len(keys),1);i=keys[0]
            before='\n'.join(s.get('run','') for s in job['steps'][:i])
            for guard in ('test_release446.py','signer_policy.py check','check_registered','release_gate.py','EXACT_VERIFIED_UNSIGNED_APK'):
                self.assertIn(guard,before)
            self.assertIn('assemble.py sign',job['steps'][i]['run'])
            self.assertIn('--expected-generation 33',job['steps'][i]['run'])
        self.assertEqual(key_count,1)
        for forbidden in ('continue-on-error','INFINITY_KEYSTORE_B64: ${{ github','live_external_qa.py','android-emulator-runner'):
            self.assertNotIn(forbidden,raw)
        self.assertIn('--version 2103446',raw)
        self.assertIn("a['candidate_versionCode']==2103446 and a['generation']==33",raw)

    def fixture(self,d):
        base=d/'baseline.apk';candidate=d/'candidate.apk';plan=d/'plan.json'
        old={'AndroidManifest.xml':b'445',r.LABEL:b'445','classes3.dex':b'old Infinity',
            'classes4.dex':b'frozen Cobra','classes.dex':b'frozen chooser','lib/arm64-v8a/libkodi.so':b'frozen native','assets/skin':b'frozen skin'}
        new=dict(old);new.update({'AndroidManifest.xml':b'446',r.LABEL:b'infinity.last_updated_in=2103446\ncobra.last_updated_in=2103445\n','classes3.dex':b'new Infinity'})
        def write(p,m):
            with ZipFile(p,'w') as z:
                for k,v in m.items():z.writestr(k,v)
        write(base,old);write(candidate,new)
        plan.write_text(json.dumps({'changed_members':['classes3.dex'],'candidate_dex_sha256':r.digest(b'new Infinity')}))
        return base,candidate,plan,new,write

    def test_exact_member_delta_rejects_unrelated_changes(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);base,cand,plan,new,write=self.fixture(d)
            with patch.object(r,'APK_SHA',r.file_sha(base)),patch.object(r,'DEX_SHA',r.digest(b'new Infinity')),patch.object(r,'normalize_manifest',side_effect=lambda x:(b'same manifest',2103445 if x==b'445' else 2103446)):
                report=r.compare(base,cand,plan,d/'ok')
                self.assertEqual(set(report['changed_members']),{'classes3.dex',r.LABEL,'AndroidManifest.xml'})
                for protected in ('classes4.dex','classes.dex','lib/arm64-v8a/libkodi.so','assets/skin'):
                    bad=dict(new);bad[protected]+=b'not authorized';write(cand,bad)
                    with self.assertRaisesRegex(Exception,'EXACT_APK_DELTA'):r.compare(base,cand,plan,d/'bad')

    def test_original_baseline_and_member_set_required(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);base,cand,plan,new,write=self.fixture(d)
            with self.assertRaisesRegex(Exception,'EXACT_SIGNED445_APK'):r.compare(base,cand,plan,d/'wrong')
            new['assets/unapproved']=b'new';write(cand,new)
            with patch.object(r,'APK_SHA',r.file_sha(base)),patch.object(r,'DEX_SHA',r.digest(b'new Infinity')):
                with self.assertRaisesRegex(Exception,'EXACT_APK_MEMBER_SET'):r.compare(base,cand,plan,d/'added')

    def test_reused_host_receipts_and_production_sources(self):
        receipt=r.reused_receipts()
        self.assertEqual(receipt['onResume_onPause_onStop_onDestroy_other_methods'],'EXACT')
        self.assertEqual(len(receipt['changed_methods']),2)
        self.assertEqual(sum(map(len,receipt['changed_methods'].values())),3)
        for name,pin in receipt['sources'].items():
            self.assertEqual(r.file_sha(r.REPO/name),pin)
            original=__import__('subprocess').check_output(['git','show','1a7cfc89ef3695ae9ee85b963666f9a154005c5c:'+name])
            self.assertEqual(r.digest(original),pin)
        self.assertEqual(r.load(H/'RELEASE-SCOPE.json')['new_application_tests'],[])
        allowed={r.WORKFLOW,'.github/workflows/infinity-external-video-live-qa.yml',
            *['repairs/dual-experience-isolation-2103420/'+n for n in ('release_gate.py','release-authority.json','ownership-reviewed-roots.json','signer-policy.json')]}
        changed=r.cmd('git','diff','--name-only',r.BASE).splitlines()
        self.assertTrue(all(n.startswith('repairs/infinity-2103445-external-video-lifecycle/') or n in allowed for n in changed),changed)

if __name__=='__main__':
    selected=r.load(H/'RELEASE-SCOPE.json')['selected_release_tests']
    if sorted(selected)!=unittest.defaultTestLoader.getTestCaseNames(ReleaseTests):raise RuntimeError('Release test selection drift')
    result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(ReleaseTests(n) for n in selected))
    raise SystemExit(not result.wasSuccessful())
