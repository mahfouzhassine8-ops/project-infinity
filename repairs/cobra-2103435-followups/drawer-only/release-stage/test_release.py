"""Four preselected pure release contracts; no Android or shutdown execution."""
import json
from pathlib import Path
import subprocess
import unittest
import yaml
from prepare import REPO,TASK,HERE,BASE,CORRECTION,ISO

def frozen(source,path):return subprocess.check_output(['git','-C',str(REPO),'show',source+':'+path])
def workflow(path):return yaml.load(path.read_text(),Loader=yaml.BaseLoader)

class Release436ProtocolTests(unittest.TestCase):
 def test_original_key_roles_remain_guarded_and_manual(self):
    p=REPO/'.github/workflows/infinity-combined-release.yml';current=workflow(p);old=yaml.load(frozen(BASE,str(p.relative_to(REPO))),Loader=yaml.BaseLoader)
    def roles(doc):
        return [step['env'] for job in doc['jobs'].values() for step in job.get('steps',[]) if any('secrets.INFINITY_' in str(v) for v in step.get('env',{}).values())]
    self.assertEqual(roles(old),roles(current));self.assertNotIn('push',current['on'])
    job=current['jobs']['combined'];self.assertIn("github.event_name == 'workflow_dispatch'",job['if']);self.assertIn('work/cobra-only-from-2103435-20261031',job['if'])
    steps=job['steps'];key=next(i for i,s in enumerate(steps) if 'INFINITY_KEYSTORE_B64' in s.get('env',{}))
    before='\n'.join(s.get('run','') for s in steps[:key]);self.assertIn('register.py check-registered',before);self.assertIn('release_gate.py',before)
    self.assertIn('assemble.py sign',steps[key]['run']);self.assertIn('compare',steps[key+1]['run'])
    self.assertEqual(current['concurrency']['cancel-in-progress'],'false')
    feature=workflow(REPO/'.github/workflows/infinity-saved-navigation-android.yml')
    for selected in ['cobra-drawer436-prepare','cobra-drawer436-android']:self.assertIn("inputs.feature != '"+selected+"'",feature['jobs']['android17']['if'])
    for job in ['cobra-drawer436-prepare','cobra-drawer436-android']:self.assertNotIn('secrets.INFINITY_',str(feature['jobs'][job]))
 def test_two_method_correction_and_five_host_tests_remain_exact70c(self):
    names=['repairs/cobra-next-from-2103427/cards-from-2103431/runtime/CobraCardsLayout.java','repairs/cobra-2103435-followups/drawer-only/runtime/CobraCardsDrawerViewport.java','repairs/cobra-2103435-followups/drawer-only/patch.py','repairs/cobra-2103435-followups/drawer-only/compile_owner.py','repairs/cobra-2103435-followups/drawer-only/CobraDrawerCorrectionTest.java','repairs/cobra-2103435-followups/drawer-only/correction-host/JUNIT.xml']
    for n in names:self.assertEqual((REPO/n).read_bytes(),frozen(CORRECTION,n),n)
    outcome=json.loads((TASK/'correction-host/OUTCOME.json').read_text());self.assertEqual(len(outcome['selected_cases']),5);self.assertTrue(all(x['status']=='PASS' for x in outcome['selected_cases']))
 def test_only_new_helper_root_changes_owner_classification(self):
    path='repairs/dual-experience-isolation-2103420/ownership-reviewed-roots.json';old=json.loads(frozen(BASE,path));new=json.loads((REPO/path).read_text())
    old['project_roots']['CobraCardsDrawerViewport']='COBRA';self.assertEqual(new,old)
    for path in ['assemble.py','assemble_modules.py','component_bundles.py','review_ownership.py','release_authority.py','signer_policy.py','signer-policy.json']:
        relative='repairs/dual-experience-isolation-2103420/'+path;self.assertEqual((REPO/relative).read_bytes(),frozen(BASE,relative),path)
 def test_authority_branch_and435_recovery_locks_are_strict(self):
    import release_gate as gate
    self.assertEqual(gate.AUTHORITY_BRANCH,'work/cobra-only-from-2103435-20261031');self.assertEqual(gate.DRAWER_PROTECTED_COMMIT,BASE)
    self.assertEqual(gate.DRAWER_PROTECTED_REF,'refs/heads/lock/infinity-cobra-2103435-user-approved-20261031')
    text=(ISO/'release_gate.py').read_text();self.assertIn("refs.get(DRAWER_PROTECTED_REF) == DRAWER_PROTECTED_COMMIT",text)
    self.assertIn("refs.get('refs/heads/' + AUTHORITY_BRANCH) == expected_head",text)
    prior=json.loads(frozen(BASE,'repairs/dual-experience-isolation-2103420/release-authority.json'));current=json.loads((ISO/'release-authority.json').read_text())
    if current['candidate_versionCode']==2103435:self.assertEqual(current,prior)
    else:
        self.assertEqual(current['candidate_versionCode'],2103436);self.assertEqual(current['target_owners'],['COBRA','CHOOSER_SHELL']);self.assertEqual(current['protected_contract'],prior['protected_contract'])
        for owner in ['INFINITY','MINIMAL_ANDROID_CONTRACT']:
            self.assertEqual(current['components'][owner],prior['components'][owner]);self.assertEqual(current['bundle_catalog']['bundles'][owner],prior['bundle_catalog']['bundles'][owner])
    self.assertFalse(current['accepted_pointer_updated']);self.assertEqual(current['accepted_registry_sha256'],prior['accepted_registry_sha256'])

if __name__=='__main__':
 scope=json.loads((HERE/'PROTOCOL-SCOPE.json').read_text());assert scope['selected_before_execution']
 names=unittest.defaultTestLoader.getTestCaseNames(Release436ProtocolTests);assert sorted(names)==sorted(scope['tests'])
 suite=unittest.TestSuite(Release436ProtocolTests(n) for n in scope['tests']);result=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(0 if result.wasSuccessful() else 1)
