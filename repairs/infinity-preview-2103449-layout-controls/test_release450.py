"""Selected release/preservation negative checks; no application or shutdown suite."""
import copy,hashlib,json,re,shutil,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile
import yaml
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import release450 as r
from component_bundles import set_version
class Preservation(unittest.TestCase):
 def test_original_signer_and_guards_except_new_branch_lock_are_frozen(self):
  for name in ('assemble.py','component_bundles.py','signer_policy.py','inventory.py','release_authority.py'):
   p=r.ISO/name;self.assertEqual(p.read_text(),r.cmd('git','show',r.BASE+':'+str(p.relative_to(r.REPO))))
  old=r.cmd('git','show',r.BASE+':repairs/dual-experience-isolation-2103420/release_gate.py')
  expected=old
  self.assertEqual(expected,(r.ISO/'release_gate.py').read_text())
  roots=json.loads(r.cmd('git','show',r.BASE+':repairs/dual-experience-isolation-2103420/ownership-reviewed-roots.json'))
  roots['project_roots']['InfinityPreviewChrome']='INFINITY'
  self.assertEqual(roots,r.load(r.ISO/'ownership-reviewed-roots.json'))
 def test_sole_signer_after_all_gates_and_exact_new_branch(self):
  raw=(r.REPO/'.github/workflows/infinity-combined-release.yml').read_text();data=yaml.safe_load(raw)
  self.assertNotIn("sys.path.insert(0,'repairs/infinity-preview-2103447-resume')",raw)
  self.assertEqual(set(data['jobs']),{'prepare-preview450','combined'})
  for name,job in data['jobs'].items():
   self.assertIn(r.BRANCH,job['if']);keys=[i for i,s in enumerate(job['steps']) if 'INFINITY_KEYSTORE_B64' in s.get('env',{})]
   for step in job['steps']:
    for path in re.findall(r'python3 (repairs/[^\s\\]+\.py)',step.get('run','')):self.assertTrue((r.REPO/path).is_file(),path)
   if name!='combined':self.assertEqual(keys,[]);continue
   self.assertEqual(len(keys),1);before='\n'.join(s.get('run','') for s in job['steps'][:keys[0]])
   for guard in ('test_release450.py','signer_policy.py check','check_registered','release_gate.py'):self.assertIn(guard,before)
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
   members={'AndroidManifest.xml':set_version(manifest,2103449),r.LABEL:b'infinity.last_updated_in=2103449\ncobra.last_updated_in=2103445\n','classes.dex':b'frozen Splash','classes2.dex':b'frozen shared','classes3.dex':b'Infinity449','classes4.dex':b'Cobra','lib/arm64-v8a/libkodi.so':b'native','assets/skin':b'skin','resources.arsc':b'icons'}
   self.fixture(base,members);changed=dict(members,**{'AndroidManifest.xml':set_version(manifest,r.VERSION),r.LABEL:b'infinity.last_updated_in=2103450\ncobra.last_updated_in=2103445\n','classes3.dex':b'Preview resume'})
   plan.write_text(json.dumps({'compiled_members':{'classes3.dex':r.digest(changed['classes3.dex'])}}))
   with patch.object(r,'APK_SHA',r.file_sha(base)):
    self.fixture(candidate,changed);self.assertEqual(r.compare(base,candidate,plan,d/'ok')['status'],'PASS_EXACT_SIGNED449_PRESERVATION')
    for n in set(members)-{'AndroidManifest.xml',r.LABEL,'classes3.dex'}:
     bad=dict(changed);bad[n]=b'tampered';self.fixture(candidate,bad)
     with self.assertRaisesRegex(Exception,'UNEXPECTED_APK_MEMBER_DELTA'):r.compare(base,candidate,plan,d/'bad')
    bad=dict(changed);bad['classes3.dex']=b'not the Android-tested decoder';self.fixture(candidate,bad)
    with self.assertRaisesRegex(Exception,'EXACT_ANDROID_TESTED_DEX'):r.compare(base,candidate,plan,d/'wrong-dex')
    bad=dict(changed);bad['AndroidManifest.xml']=set_version(manifest,r.VERSION+1);self.fixture(candidate,bad)
    with self.assertRaisesRegex(Exception,'EXACT_AUTHORIZED_MANIFEST_AND_VERSION'):r.compare(base,candidate,plan,d/'wrong-version')
    bad=dict(changed);bad['new/unowned']=b'added';self.fixture(candidate,bad)
    with self.assertRaisesRegex(Exception,'EXACT_APK_MEMBER_SET'):r.compare(base,candidate,plan,d/'added')
 def test_wrong_baseline_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'wrong.apk';p.write_bytes(b'not signed449')
   with self.assertRaisesRegex(Exception,'EXACT_SIGNED449_APK'):r.compare(p,p,p,Path(tmp))
 def test_preserved_manifest_exception_remains_exact(self):
  from release_authority import external_player_manifest_guard
  prior=r.previous();external_player_manifest_guard().verify_evidence(prior,lambda n:(r.REPO/n).read_bytes())
  self.assertNotIn('MINIMAL_ANDROID_CONTRACT',r.TARGETS)
  self.assertEqual(prior['candidate_versionCode'],2103449)
 def test_runtime_requires_completed_bound_selected_checks(self):
  from runtime_evidence import summarize
  self.assertEqual(summarize()['status'],'PASS_SELECTED_PREVIEW_LAYOUT_CHECKS')
  with tempfile.TemporaryDirectory() as tmp:
   d=Path(tmp);(d/'final-evidence').mkdir();(d/'runtime-attempts/second').mkdir(parents=True);shutil.copyfile(H/'runtime-attempts/second/RESULT.json',d/'runtime-attempts/second/RESULT.json')
   raw=json.loads((H/'final-evidence/ANDROID-RAW.json').read_text());binding=json.loads((H/'final-evidence/RUNTIME-BINDING.json').read_text())
   for failure in ('status','missing'):
    bad=copy.deepcopy(raw)
    if failure=='status':bad['status']='FAIL'
    else:bad['checks']=[x for x in bad['checks'] if x['check']!='real_rotation_selected_state']
    p=d/'final-evidence/ANDROID-RAW.json';p.write_text(json.dumps(bad));binding['result_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();(d/'final-evidence/RUNTIME-BINDING.json').write_text(json.dumps(binding))
    with self.assertRaises(RuntimeError):summarize(d)
if __name__=='__main__':unittest.main(verbosity=2)
