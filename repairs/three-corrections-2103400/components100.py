"""Exactly three corrective overlays on the user-locked, signed 2103399."""
from pathlib import Path
from zipfile import ZipFile
import ast,hashlib,json,sys,xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'consolidated-2103398'))
import components98 as prior
require,once,sha,digest,xml=prior.require,prior.once,prior.sha,prior.digest,prior.xml
CC,UI,WB,SKIN,HEALTH,LATEST=prior.CC,prior.UI,prior.WB,prior.SKIN,prior.HEALTH,prior.LATEST
PARENT='e549c4caed7093b93cd18cca99d7a3ae7c197a2c4d38297fc0a3db2eeb5ccf4d'
COMMIT='e4bb09dbb951173bf99d868b2391aeafac89c03f'
VERSIONS={CC:'0.3.5.28',UI:'0.1.11',WB:'1.0.9',SKIN:'1.0.5.237',HEALTH:'2.5.26',LATEST:'0.1.1','script.infinity.rails':'0.2.7'}
OLD={CC:'0.3.5.27',UI:'0.1.10',WB:'1.0.8',SKIN:'1.0.5.236',HEALTH:'2.5.25',LATEST:'0.1.0','script.infinity.rails':'0.2.7'}
def read_parent(apk):
 require(digest(apk)==PARENT,'exact signed locked 2103399 required')
 with ZipFile(apk) as z:
  require(z.testzip() is None and len(z.namelist())==len(set(z.namelist())),'invalid protected APK')
  return {n[14:]:z.read(n) for n in z.namelist() if n.startswith('assets/addons/') and not n.endswith('/') and n.split('/')[2] in VERSIONS}
def components(before):
 after=dict(before)
 for p in sorted((HERE/'overlay').rglob('*')):
  if p.is_file():
   n=p.relative_to(HERE/'overlay').as_posix();require(n in before,'overlay unexpectedly adds a file '+n);after[n]=p.read_bytes()
 after[UI+'/latest_identity.py']=after[LATEST+'/identity.py']
 headings=0
 for n,b in before.items():
  if n.startswith(SKIN+'/') and n.endswith('/Home.xml'):
   count=b.count(b'Umbrella - Latest Releases')
   require(count==2,'both exact Home labels required '+n)
   after[n]=b.replace(b'Umbrella - Latest Releases','Infinity \u2013 Latest Releases'.encode());headings+=count
 require(headings==28,'all fourteen retained Home profile copies required')
 # Bump only components that contain corrections or exact controller bindings.
 for a,v in VERSIONS.items():
  if OLD[a]!=v:after[a+'/addon.xml']=once(before[a+'/addon.xml'],('version="'+OLD[a]+'"').encode(),('version="'+v+'"').encode())
 after[CC+'/checkpoint_runtime.py']=once(before[CC+'/checkpoint_runtime.py'],b'ADDON_VERSION = "0.3.5.27"',b'ADDON_VERSION = "0.3.5.28"')
 for leaf in ('khc_contracts.py','khc_diagnostics.py','khc_doctor.py'):
  key=HEALTH+'/'+leaf
  after[key]=once(before[key],b"VERSION = '2.5.25'",b"VERSION = '2.5.26'")
 after[WB+'/controller.py']=once(before[WB+'/controller.py'],b'"0.3.5.27"',b'"0.3.5.28"')
 pins={n.split('/',1)[1]:sha(b) for n,b in after.items() if n.startswith(CC+'/') and (n.endswith('.py') or n.endswith('/addon.xml') or n==CC+'/resources/settings.xml')}
 require(len(pins)==17,'controller source inventory changed')
 for addon in (UI,WB):after[addon+'/CONTROLLER-PREIMAGES.json']=(json.dumps(pins,indent=2,sort_keys=True)+'\n').encode()
 for leaf in ('infinity-skin.json','Infinity-Protected-Manifest.json'):
  key=SKIN+'/'+leaf;data=json.loads(before[key]);data.update(candidate=237,skin_version=VERSIONS[SKIN],candidate_locked=False)
  for k in ('version','candidate_version'):
   if k in data:data[k]=VERSIONS[SKIN]
  if 'protected_files' in data:data['protected_files']={p:sha(after[SKIN+'/'+p]) for p in data['protected_files']}
  after[key]=(json.dumps(data,indent=2,sort_keys=True)+'\n').encode()
 for n,b in after.items():
  if b!=before[n]:
   if n.endswith('.py'):ast.parse(b,filename=n)
   if n.endswith('.xml'):ET.fromstring(b)
   require('cobra' not in n.lower() and not n.startswith('script.infinity.rails/'),'forbidden component change')
 return after

def reason(n):
 if n.startswith(LATEST+'/') or n.endswith('/latest_identity.py'):return ('1','Admit actual reviewed play_Item producer route; retain bounded checksummed identities and emit ownership receipts')
 if n.endswith('/Home.xml'):return ('1','Change only the two Infinity-owned Latest Releases headings; preserve all XML geometry and bindings')
 if n.endswith('/home_option_b.py'):return ('1','Validate the complete bounded path without truncating security-relevant suffixes')
 if n.startswith(HEALTH+'/') and n.endswith('khc_android.py'):return ('2','Replace Android-rejected O_TMPFILE probe with exclusive named temporary capture; keep observer safeguards')
 if n.startswith(CC+'/') and n.endswith(('experience.py','service.py','plugin.py')):return ('3','Capture actual native provider invocation, verify producer and exact media identity, preserve progress and fresh resolver route')
 return ('binding','Advance changed-component versions, integrity manifests and exact controller ownership pins')
def ledger(before,after):
 changed={}
 for n,b in after.items():
  if before[n]!=b:
   group,why=reason(n);changed[n]=dict(original_sha256=sha(before[n]),new_sha256=sha(b),workstream=group,corrective_reason=why,affected_runtime_behavior=why,regression_result='PENDING')
 return dict(protected_commit=COMMIT,protected_apk_sha256=PARENT,versions=VERSIONS,changed=changed,removed=[],cobra_changed=False,rails_changed=False,physical_fold_verified=False,final_lock=False)
def evidence_manifest(after):return prior.evidence_manifest(after)
def stage(apk,out):
 before=read_parent(apk);after=components(before);require(not out.exists(),'stage exists')
 for n,b in after.items():p=out/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 return ledger(before,after)
if __name__=='__main__':print(json.dumps(stage(Path(sys.argv[1]),Path(sys.argv[2])),indent=2,sort_keys=True))
