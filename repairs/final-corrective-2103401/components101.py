"""Four approved corrections; preserve every other protected 2103400 member."""
from pathlib import Path
from zipfile import ZipFile
import ast,hashlib,json,sys,xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'three-corrections-2103400'))
import components100 as prior
require,once,sha,digest,xml=prior.require,prior.once,prior.sha,prior.digest,prior.xml
CC,UI,WB,SKIN,HEALTH,LATEST=prior.CC,prior.UI,prior.WB,prior.SKIN,prior.HEALTH,prior.LATEST
PARENT='e1334ce46bc96edce76a8b7af2d3ebb9871ac7c351526ac2cc6cc58820da009a'
COMMIT='b514b21a50a7109cd2f79c22fbfa0e61e687d622'
OLD=prior.VERSIONS
VERSIONS=dict(OLD,**{CC:'0.3.5.29',UI:'0.1.12',WB:'1.0.10',SKIN:'1.0.5.238'})
HEADER='INFINITY [COLOR $VAR[InfinityPaletteAccent]]∞[/COLOR]'.encode()
def read_parent(apk):
 require(digest(apk)==PARENT,'exact signed protected 2103400 required')
 with ZipFile(apk) as z:
  require(z.testzip() is None and len(z.namelist())==len(set(z.namelist())),'invalid protected APK')
  return {n[14:]:z.read(n) for n in z.namelist() if n.startswith('assets/addons/') and not n.endswith('/') and n.split('/')[2] in VERSIONS}
def components(before):
 after=dict(before)
 for p in sorted((HERE/'overlay').rglob('*')):
  if p.is_file():
   n=p.relative_to(HERE/'overlay').as_posix()
   require(n in before or n==CC+'/resources/skins/Default/1080i/InfinityTraktNotice.xml','unexpected overlay addition '+n)
   after[n]=p.read_bytes()
 headings=0
 for n,b in before.items():
  if n.startswith(SKIN+'/') and n.endswith('/Home.xml'):
   require(b.count(b'INFINITY 1.0.5')==1,'exact approved header absent '+n)
   after[n]=b.replace(b'INFINITY 1.0.5',HEADER);headings+=1
 require(headings==14,'all fourteen header layout copies required')
 after[SKIN+'/unified/InfinityHomeOptionB.xml']=after[UI+'/resources/skins/Default/1080i/InfinityHomeOptionB.xml']
 after[SKIN+'/unified/InfinityTraktNotice.xml']=after[CC+'/resources/skins/Default/1080i/InfinityTraktNotice.xml']
 for a,v in VERSIONS.items():
  if OLD[a]!=v:after[a+'/addon.xml']=once(before[a+'/addon.xml'],('version="'+OLD[a]+'"').encode(),('version="'+v+'"').encode())
 after[CC+'/checkpoint_runtime.py']=once(before[CC+'/checkpoint_runtime.py'],b'ADDON_VERSION = "0.3.5.28"',b'ADDON_VERSION = "0.3.5.29"')
 after[WB+'/controller.py']=once(before[WB+'/controller.py'],b'"0.3.5.28"',b'"0.3.5.29"')
 bridge={n.split('/',1)[1]:sha(b) for n,b in after.items() if n.startswith(WB+'/') and (n.endswith('.py') or n.endswith('/addon.xml') or n.endswith('/PROVIDER-CONTRACTS.json'))}
 require(bridge and 'controller.py' in bridge and 'context.py' in bridge,'bridge executable pins required')
 after[CC+'/infinity_trakt.py']=once(after[CC+'/infinity_trakt.py'],b'BRIDGE_PINS = {}',('BRIDGE_PINS = '+repr(dict(sorted(bridge.items())))).encode())
 pins={n.split('/',1)[1]:sha(b) for n,b in after.items() if n.startswith(CC+'/') and (n.endswith('.py') or n.endswith('/addon.xml') or n==CC+'/resources/settings.xml')}
 require(len(pins)==17,'controller source inventory changed')
 for addon in (UI,WB):after[addon+'/CONTROLLER-PREIMAGES.json']=(json.dumps(pins,indent=2,sort_keys=True)+'\n').encode()
 for leaf in ('infinity-skin.json','Infinity-Protected-Manifest.json'):
  key=SKIN+'/'+leaf;data=json.loads(before[key]);data.update(candidate=238,skin_version=VERSIONS[SKIN],candidate_locked=False)
  for k in ('version','candidate_version'):
   if k in data:data[k]=VERSIONS[SKIN]
  if 'protected_files' in data:
   data['protected_files']={p:sha(after[SKIN+'/'+p]) for p in data['protected_files']}
   data['protected_files']['unified/InfinityTraktNotice.xml']=sha(after[SKIN+'/unified/InfinityTraktNotice.xml'])
  after[key]=(json.dumps(data,indent=2,sort_keys=True)+'\n').encode()
 for n,b in after.items():
  if b!=before.get(n):
   if n.endswith('.py'):ast.parse(b,filename=n)
   if n.endswith('.xml'):ET.fromstring(b)
   require('cobra' not in n.lower() and not n.startswith(('script.infinity.rails/',HEALTH+'/',LATEST+'/')),'forbidden component change')
 return after
def reason(n):
 if n.endswith('/infinity_trakt.py') or n.endswith('/InfinityTraktNotice.xml'):return ('1','Verify exact installed and loaded tracking components; bound the compatibility notice')
 if n.endswith('/home_option_b.py') or n.endswith('/InfinityHomeOptionB.xml'):return ('2','Replace unsupported Python scrollbar access, bind captured metadata, restore same-popup Back and compact empty state')
 if n.endswith('/infinity_search.py'):return ('3','Verified supplied-query provider dispatch, lossless Seren encoding, isolated shared search history')
 if n.endswith('/Home.xml'):return ('4','Replace only visible version label with theme-aware INFINITY infinity branding')
 return ('binding','Necessary component versions, exact controller pins and protected-resource manifests')
def ledger(before,after):
 changed={}
 for n,b in after.items():
  if before.get(n)!=b:
   group,why=reason(n);changed[n]=dict(original_sha256=sha(before[n]) if n in before else None,new_sha256=sha(b),workstream=group,corrective_reason=why,affected_runtime_behavior=why,regression_result='PENDING')
 return dict(protected_commit=COMMIT,protected_apk_sha256=PARENT,versions=VERSIONS,changed=changed,removed=[],cobra_changed=False,rails_changed=False,physical_fold_verified=False,final_lock=False)
def evidence_manifest(after):return prior.evidence_manifest(after)
def stage(apk,out):
 before=read_parent(apk);after=components(before);require(not out.exists(),'stage exists')
 for n,b in after.items():p=out/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 return ledger(before,after)
if __name__=='__main__':print(json.dumps(stage(Path(sys.argv[1]),Path(sys.argv[2])),indent=2,sort_keys=True))
