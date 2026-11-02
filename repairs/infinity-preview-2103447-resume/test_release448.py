"""Selected release/preservation negative checks; no application or shutdown suite."""
import copy,json,re,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile
import yaml
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import release448 as r
from component_bundles import set_version
class Preservation(unittest.TestCase):
 def test_original_signer_and_guards_except_new_branch_lock_are_frozen(self):
  for name in ('assemble.py','component_bundles.py','signer_policy.py','inventory.py','release_authority.py'):
   p=r.ISO/name;self.assertEqual(p.read_text(),r.cmd('git','show',r.BASE+':'+str(p.relative_to(r.REPO))))
  old=r.cmd('git','show',r.BASE+':repairs/dual-experience-isolation-2103420/release_gate.py')
  expected=old.replace("AUTHORITY_BRANCH = 'work/infinity-2103445-standalone-external-player-20261101'","PREVIEW_BASELINE_REF = 'refs/heads/lock/infinity-cobra-2103447-user-locked-20261102'\nPREVIEW_BASELINE_COMMIT = '1fe75deaebdbf71d5873dc69ba3e21c0526954f0'\nAUTHORITY_BRANCH = '"+r.BRANCH+"'")
  expected=expected.replace('ROTATION_PROTECTED_REF, EXTERNAL_BASELINE_REF)','ROTATION_PROTECTED_REF, EXTERNAL_BASELINE_REF, PREVIEW_BASELINE_REF)')
  expected=expected.replace('    require(refs.get(EXTERNAL_BASELINE_REF)',"    require(refs.get(PREVIEW_BASELINE_REF) == PREVIEW_BASELINE_COMMIT, 'PREVIEW447_APPROVED_LOCK_MOVED')\n    require(refs.get(EXTERNAL_BASELINE_REF)")
  self.assertEqual(expected,(r.ISO/'release_gate.py').read_text())
  roots=json.loads(r.cmd('git','show',r.BASE+':repairs/dual-experience-isolation-2103420/ownership-reviewed-roots.json'))
  roots['project_roots']['InfinityExternalResume']='INFINITY'
  self.assertEqual(roots,r.load(r.ISO/'ownership-reviewed-roots.json'))
 def test_sole_signer_after_all_gates_and_exact_new_branch(self):
  raw=(r.REPO/'.github/workflows/infinity-combined-release.yml').read_text();data=yaml.safe_load(raw)
  self.assertEqual(set(data['jobs']),{'prepare-resume448','combined'})
  for name,job in data['jobs'].items():
   self.assertIn(r.BRANCH,job['if']);keys=[i for i,s in enumerate(job['steps']) if 'INFINITY_KEYSTORE_B64' in s.get('env',{})]
   for step in job['steps']:
    for path in re.findall(r'python3 (repairs/[^\s\\]+\.py)',step.get('run','')):self.assertTrue((r.REPO/path).is_file(),path)
   if name!='combined':self.assertEqual(keys,[]);continue
   self.assertEqual(len(keys),1);before='\n'.join(s.get('run','') for s in job['steps'][:keys[0]])
   for guard in ('test_release448.py','signer_policy.py check','check_registered','release_gate.py'):self.assertIn(guard,before)
   self.assertIn('assemble.py sign',job['steps'][keys[0]]['run'])
  self.assertNotIn('continue-on-error',raw)
 def fixture(self,path,values):
  with ZipFile(path,'w') as z:
   for n,v in values.items():z.writestr(n,v)
 def test_exact_member_scope_rejects_every_frozen_owner(self):
  old=r.REPO/'repairs/infinity-2103445-standalone-external-player'
  sys.path.insert(0,str(old));from patch_manifest import patch as external_manifest
  manifest=external_manifest((old/'reference/AndroidManifest-2103445.xml.bin').read_bytes())
  with tempfile.TemporaryDirectory() as tmp:
   d=Path(tmp);base=d/'baseline.apk';candidate=d/'new.apk';plan=d/'plan.json'
   members={'AndroidManifest.xml':set_version(manifest,2103447),r.LABEL:b'infinity.last_updated_in=2103447\ncobra.last_updated_in=2103445\n','classes.dex':b'frozen Splash','classes2.dex':b'frozen shared','classes3.dex':b'Infinity447','classes4.dex':b'Cobra','lib/arm64-v8a/libkodi.so':b'native','assets/skin':b'skin','resources.arsc':b'icons'}
   self.fixture(base,members);changed=dict(members,**{'AndroidManifest.xml':set_version(manifest,r.VERSION),r.LABEL:b'infinity.last_updated_in=2103448\ncobra.last_updated_in=2103445\n','classes3.dex':b'Preview resume'})
   plan.write_text(json.dumps({'compiled_members':{'classes3.dex':r.digest(changed['classes3.dex'])}}))
   with patch.object(r,'APK_SHA',r.file_sha(base)):
    self.fixture(candidate,changed);self.assertEqual(r.compare(base,candidate,plan,d/'ok')['status'],'PASS_EXACT_SIGNED447_PRESERVATION')
    for n in set(members)-{'AndroidManifest.xml',r.LABEL,'classes3.dex'}:
     bad=dict(changed);bad[n]=b'tampered';self.fixture(candidate,bad)
     with self.assertRaisesRegex(Exception,'UNEXPECTED_APK_MEMBER_DELTA'):r.compare(base,candidate,plan,d/'bad')
    bad=dict(changed);bad['new/unowned']=b'added';self.fixture(candidate,bad)
    with self.assertRaisesRegex(Exception,'EXACT_APK_MEMBER_SET'):r.compare(base,candidate,plan,d/'added')
 def test_wrong_baseline_and_wrong_compiled_decoder_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'wrong.apk';p.write_bytes(b'not signed447')
   with self.assertRaisesRegex(Exception,'EXACT_SIGNED447_APK'):r.compare(p,p,p,Path(tmp))
 def test_preserved_manifest_exception_remains_exact(self):
  from release_authority import external_player_manifest_guard
  prior=r.previous();external_player_manifest_guard().verify_evidence(prior,lambda n:(r.REPO/n).read_bytes())
  self.assertNotIn('MINIMAL_ANDROID_CONTRACT',r.TARGETS)
  self.assertEqual(prior['candidate_versionCode'],2103447)
if __name__=='__main__':unittest.main(verbosity=2)
