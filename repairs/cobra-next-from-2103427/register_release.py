"""Register one CI-tested Cobra vector; never promote physical acceptance."""
import argparse,copy,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1];ISO=HERE.parent/'dual-experience-isolation-2103420'
sys.path.insert(0,str(ISO))
from inventory import load,save,file_sha,canonical,digest
from component_bundles import read_bundle
from release_gate import require
from release_authority import transition,verify_evidence,launcher_icon_guard

def register(bundles,producer_run):
 scope=load(HERE/'SCOPE.json');previous=load(ISO/'release-authority.json')
 require(previous['candidate_versionCode']==2103429 and previous['generation']==14,'EXACT_PREVIOUS_AUTHORITY')
 run=json.loads(subprocess.check_output(['gh','api','repos/mahfouzhassine8-ops/project-infinity/actions/runs/'+str(producer_run)]))
 require(run['conclusion']=='success' and run['head_branch']==scope['branch'],'SUCCESSFUL_COBRA_PRODUCER');source=run['head_sha']
 bound=[HERE/'build.py',HERE/'package_owners.py',HERE/'host_tests.py',HERE/'focused_host_checks.py',HERE/'SCOPE.json',HERE/'SOURCE-BUDGET.json',*sorted((HERE/'runtime').glob('*.java')),*sorted((HERE/'tests').glob('*')),*sorted((HERE/'icon').glob('*.py')),*sorted((HERE/'icon/reference').glob('*'))]
 for path in bound:
  require(subprocess.check_output(['git','show',source+':'+str(path.relative_to(REPO))])==path.read_bytes(),'TESTED_SOURCE_CHANGED:'+path.name)
 catalog=load(bundles/'catalog.json');require(catalog['source']==source,'OWNER_PRODUCER_SOURCE');payload={};metas={}
 for owner,row in catalog['bundles'].items():
  meta=read_bundle(bundles/row['file'],row);metas[owner]=meta;payload.update(meta['payload'])
  if owner=='INFINITY':require(row==previous['bundle_catalog']['bundles'][owner],'FROZEN_OWNER:'+owner)
  else:require(meta['approved_source']==source,'EXACT_OWNER_SOURCE')
 baseline=json.loads(subprocess.check_output(['git','show',scope['baseline_source']+':repairs/dual-experience-isolation-2103420/release-authority.json']))
 old=baseline['payload'];require(set(old)<=set(payload),'REMOVED_PAYLOAD')
 changed={k for k in old if payload[k]!=old[k]}
 expected={'class:Lcom/projectinfinity/kodi/'+n+';' for n in ('InfinityLiveActivity','CobraComponent','ChooserReleaseMetadata')}
 expected.update({'member:assets/experience-component-updates.properties','member:resources.arsc'});require(changed==expected,'EXACT_CHANGED_EXISTING_PAYLOAD')
 added=set(payload)-set(old);roots={'class:Lcom/projectinfinity/kodi/'+n for n in ('CobraArrange','CobraPresentation','CobraLayoutCatalog','CobraLogoRequests')}
 new_classes={k for k in added if k.startswith('class:')};new_members=added-new_classes
 require(bool(new_classes) and all(k.split('$')[0].rstrip(';') in roots and payload[k]['owner']=='COBRA' for k in new_classes),'NARROW_NEW_CLASSES')
 guard=launcher_icon_guard();require(new_members=={'member:'+n for n in guard.NEW_PATHS},'EXACT_ICON_MEMBER_ADDITIONS')
 prior=previous['payload'];require(set(prior)<=set(payload),'NO_PREVIOUS_PAYLOAD_REMOVAL')
 require(set(payload)-set(prior)==new_members,'EXACT_PREVIOUS_PAYLOAD_PLUS_ICON_MEMBERS')
 actual_changes={k for k in prior if payload[k]!=prior[k]}
 allowed={'class:Lcom/projectinfinity/kodi/'+n+';' for n in ('InfinityLiveActivity','CobraPresentation','CobraComponent')}
 allowed.update({'member:assets/experience-component-updates.properties','member:resources.arsc'})
 require(actual_changes==allowed,'NARROW_BUTTON_AND_ICON_DELTA')
 # Preserve every earlier Cobra arrangement/logo source except the explicitly
 # scoped presentation identity helper. Packaging proves exact compiled methods.
 old_source=previous['owner_update_evidence']['producer_source']
 for name in ('CobraArrange.java','CobraLayoutCatalog.java','CobraLogoRequests.java'):
  path=HERE/'runtime'/name
  require(subprocess.check_output(['git','show',old_source+':'+str(path.relative_to(REPO))])==path.read_bytes(),'FROZEN_429_HELPER:'+name)
 proposed=copy.deepcopy(previous)
 proposed.update(generation=15,last_issued_versionCode=2103429,candidate_versionCode=2103430,update_kind='owner_update',target_owners=['COBRA','CHOOSER_SHELL','MINIMAL_ANDROID_CONTRACT'],previous_authority_sha256=digest(canonical(previous)),payload=payload,bundle_catalog=catalog,experience_version_labels={'INFINITY':2103427,'COBRA':2103430})
 proposed['launcher_icon_exception']=guard.make_exception(payload,lambda n:(REPO/n).read_bytes())
 for owner in ('COBRA','CHOOSER_SHELL','MINIMAL_ANDROID_CONTRACT'):
  proposed['components'][owner]={k:metas[owner][k] for k in ('version','settings_schema','approved_source','digest')}
  proposed['components'][owner]['revision']=previous['components'][owner]['revision']+1
  proposed['bundle_sources'][owner]=dict(run_id=producer_run,build_source=source,artifact='Cobra-Prepared-Owners-'+str(producer_run),path=owner+'.zip')
 for owner in ('INFINITY',):
  proposed['bundle_sources'][owner]=dict(run_id=40769526963,build_source=scope['baseline_source'],artifact='Infinity-Combined-Owner-Components-40769526963',path=owner+'.zip')
 proposed['source_files']={n:file_sha(REPO/n) for n in previous['source_files']}
 proposed['workflow_sha256']=file_sha(REPO/'.github/workflows/infinity-combined-release.yml')
 proposed['owner_update_evidence']=dict(owner='COBRA',changed_owners=['COBRA','CHOOSER_SHELL','MINIMAL_ANDROID_CONTRACT'],producer_source=source,producer_run=producer_run,focused_host_run=producer_run,
  chooser_change='Preserved Version wording; genuine Cobra2103430 metadata only',changed_payload=sorted(changed|added),frozen_owners=['INFINITY'],
  minimal_owner_change='Only reviewed launcher-resource table/newlighticons; all classes,DEX,existingartwork/native/manifest/persistence frozen',
  protected_contract='EXACT',shutdown_tests='NOT_RUN',physical_Fold='PENDING',accepted_pointer_updated=False,authorization='repairs/cobra-next-from-2103427/P0-2103429-PLAYER-BUTTON-ACTION-MISMATCH-20261029.md',launcher_icon_authorization='repairs/cobra-next-from-2103427/APPROVED-INFINITY-ICON-LIGHT-DARK-20261029.md',tested_source_files={str(p.relative_to(REPO)):file_sha(p) for p in bound})
 transition(previous,proposed,proposed['target_owners']);verify_evidence(proposed,lambda n:(REPO/n).read_bytes())
 save(ISO/'release-authority.json',proposed)
 save(HERE/'REGISTERED-OWNER-VECTOR.json',dict(generation=15,versionCode=2103430,producer_source=source,producer_run=producer_run,bundles=catalog['bundles'],accepted_pointer_updated=False,physical_Fold='PENDING'))
 print('Registered CI-tested Cobra owner vector; physical acceptance remains pending.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--bundles',type=Path,required=True);p.add_argument('--producer-run',type=int,required=True);register(**vars(p.parse_args()))
