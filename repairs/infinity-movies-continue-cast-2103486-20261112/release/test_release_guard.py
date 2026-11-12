"""Focused new Cast manifest admission checks; no application tests or signing."""
import copy,hashlib,json,sys,unittest,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'repairs/dual-experience-isolation-2103420'))
sys.path.insert(0,str(HERE))
import release_guard as guard

class CastGuard(unittest.TestCase):
 def setUp(self):
  self.before=json.loads(subprocess.check_output(['git','show','87d65d642f9054ddd8390038ade3de72168c1695:repairs/dual-experience-isolation-2103420/release-authority.json'],cwd=ROOT))
  self.after=copy.deepcopy(self.before);self.after['candidate_versionCode']=2103488
  self.proof=dict(schema=1,mode='candidate',baseline_APK_sha256=guard.APK,reference=guard.REFERENCE,
   reference_sha256=guard.REFERENCE_SHA,baseline_normalized_sha256=guard.NORMALIZED,
   candidate_manifest_sha256=guard.expected('candidate'),source_inputs={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in guard.SOURCE_NAMES})
  self.after['cast_manifest_exception']=self.proof
  self.after['payload']['member:AndroidManifest.xml']=dict(owner=guard.OWNER,sha256=self.proof['candidate_manifest_sha256'])
  self.owners={'INFINITY','CHOOSER_SHELL',guard.OWNER}
 def test_exact_metadata_and_historical_proof_are_both_required(self):
  guard.transition(self.before,self.after,self.owners)
  original=copy.deepcopy(self.after);historical=guard.historical(self.after)
  self.assertEqual(original,self.after);self.assertEqual(guard.NORMALIZED,historical['payload']['member:AndroidManifest.xml']['sha256'])
  self.assertNotEqual(guard.NORMALIZED,self.after['payload']['member:AndroidManifest.xml']['sha256'])
  guard.verify_evidence(self.after,lambda n:(ROOT/n).read_bytes())
 def test_only_exact_new_owner_scope_can_reuse_known_cast_metadata_at90(self):
  before=json.loads(subprocess.check_output(['git','show','ab5f3e41721291091e5fe177787156408193c0fa:repairs/dual-experience-isolation-2103420/release-authority.json'],cwd=ROOT))
  after=copy.deepcopy(before);after['candidate_versionCode']=2103490
  after['cast_manifest_exception']=copy.deepcopy(self.proof)
  after['payload']['member:AndroidManifest.xml']=dict(owner=guard.OWNER,sha256=self.proof['candidate_manifest_sha256'])
  with self.assertRaises(ValueError):guard.transition(before,after,self.owners)
  after['owner_update_evidence']=dict(owner='INFINITY_CAST_FINAL_CANDIDATE',baseline_APK_sha256='4217b217bca06084121572bbde71164abe67d05ef49741c78d4f83c5c5d4a566',original_five_DEX_unchanged=True,Cobra_changed=False,source_files={'repairs/infinity-cast-final-2103488-20261112/SCOPE.json':'bound-by-outer-original-evidence-verifier'})
  guard.transition(before,after,self.owners)
 def test_any_other_shared_class_or_resource_change_is_rejected(self):
  key=next(k for k,v in self.after['payload'].items() if v['owner']==guard.OWNER and k!='member:AndroidManifest.xml')
  self.after['payload'][key]['sha256']='0'*64
  with self.assertRaises(ValueError):guard.transition(self.before,self.after,self.owners)
 def test_cobra_or_wrong_version_or_unbound_source_is_rejected(self):
  with self.assertRaises(ValueError):guard.transition(self.before,self.after,self.owners|{'COBRA'})
  self.after['candidate_versionCode']=2103489
  with self.assertRaises(ValueError):guard.transition(self.before,self.after,self.owners)
  self.proof['source_inputs']['arbitrary.py']='0'*64
  with self.assertRaises(ValueError):guard.validate(self.after)
 def test_arbitrary_manifest_and_old_proof_changes_are_rejected(self):
  self.after['payload']['member:AndroidManifest.xml']['sha256']='0'*64
  with self.assertRaises(ValueError):guard.validate(self.after)
  self.after['payload']['member:AndroidManifest.xml']['sha256']=self.proof['candidate_manifest_sha256']
  self.after['external_player_manifest_exception']['candidate_manifest_sha256']='0'*64
  with self.assertRaises(ValueError):guard.validate(self.after)
 def test_forward_recovery_restores_exact86_and_cannot_go_backward(self):
  recovery=copy.deepcopy(self.after);recovery['candidate_versionCode']=2103489
  recovery['cast_manifest_exception']['mode']='recovery';recovery['cast_manifest_exception']['candidate_manifest_sha256']=guard.NORMALIZED
  recovery['payload']['member:AndroidManifest.xml']['sha256']=guard.NORMALIZED
  guard.transition(self.after,recovery,self.owners)
  recovery['candidate_versionCode']=2103486
  with self.assertRaises(ValueError):guard.transition(self.after,recovery,self.owners)
if __name__=='__main__':unittest.main(verbosity=2)
