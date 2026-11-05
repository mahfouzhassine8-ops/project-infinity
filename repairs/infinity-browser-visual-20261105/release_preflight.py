"""Read-only check of existing release authority; never uses keys/builds an APK."""
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'repairs/infinity-master-testing-20261105'))
import release_controlled as r

out={'status':'BLOCKED_EXISTING_EXACT_RELEASE_AUTHORITY','APK_built':False,'keys_used':False,
     'phone_installed_version':'UNVERIFIED','Android':'NOT_RUN','physical_Fold':'NOT_RUN'}
authority=json.loads((r.ISO/'release-authority.json').read_bytes())
out['registered_candidate_versionCode']=authority['candidate_versionCode']
out['registered_owner']=authority['owner_update_evidence']['owner']
out['authorized_versions']=list(r.VERSIONS)
out['authority_branch']=r.BRANCH
out['working_branch']=subprocess.check_output(['git','branch','--show-current'],text=True,cwd=ROOT).strip()
try:r.generate(Path('NOT_OPENED'),2103458,Path('NOT_WRITTEN'))
except ValueError as error:out['next_version_rejection']=str(error)
else:raise RuntimeError('Expected exact existing version guard to refuse')
out['source_guard']={'required_checkpoint':r.SOURCE,'required_completed_members':12,
    'actual_candidate_changed_members':['assets/addons/script.infinity.commandcenter/default.py',
    'assets/addons/script.infinity.commandcenter/library_navigation.py',
    'assets/addons/skin.infinity.diggz/unified/Custom_1198_InfinityNav.xml',
    'assets/addons/skin.infinity.diggz/unified/Includes_InfinityMediaLists.xml',
    'assets/addons/skin.infinity.diggz/unified/MyVideoNav.xml',
    'assets/addons/skin.infinity.diggz/unified/Variables.xml']}
out['required_next_release_action']='Review/register a distinct exact successor source/member/version authority and higher-version recovery through the sole original-key workflow. The existing 456/457 authority must not be reused or weakened.'
out['security_sources_unchanged']={str(p.relative_to(ROOT)):
    p.read_bytes()==subprocess.check_output(['git','show','2b5fcc73:'+str(p.relative_to(ROOT))],cwd=ROOT)
    for p in [r.ISO/'release_gate.py',r.ISO/'release-authority.json',r.ISO/'signer-policy.json',ROOT/'.github/workflows/infinity-combined-release.yml']}
assert all(out['security_sources_unchanged'].values())
(HERE/'results/RELEASE-PREFLIGHT.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
