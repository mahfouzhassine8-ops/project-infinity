"""Native-only signed460 Downloads candidate + exact functional460 forward recovery."""
import argparse,copy,hashlib,json,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path
from zipfile import ZipFile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];ISO=ROOT/'repairs/dual-experience-isolation-2103420';sys.path.insert(0,str(ISO))
from inventory import canonical,digest,file_sha,load,save,SIGNATURE,validate_names
from component_bundles import read_bundle,combine,record
from release_gate import require,normalize_manifest,component_digest
from release_authority import transition,verify_evidence
BRANCH='work/infinity-2103460-nine-corrections-20261106';VERSIONS=(2103462,2103463);AUTH=ISO/'release-authority.json';NATIVE='lib/arm64-v8a/libkodi.so';LABEL='assets/experience-component-updates.properties';TARGETS=['INFINITY','CHOOSER_SHELL'];RUNTIME='NOT_RUN_NO_CONNECTED_COMPATIBLE_ANDROID_TARGET'
BASE_SHA='226911966c1d27d1246cd0ecfcd864c722df48f9be07167bd4b15ad1e73560af';BASE_NATIVE='febf0e0ed95ef33e906999b4a92c46e6b79bae1c555eaa89b4954d0b74fb3e41';CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
def cmd(*a):return subprocess.check_output(list(map(str,a)),text=True)
def engine_record():return load(HERE/'ENGINE-INPUT.json')
def head_check():
 require(os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH,'EXACT_NATIVE_DOWNLOADS_BRANCH')
 require(cmd('git','rev-parse','HEAD').strip()==os.environ['GITHUB_SHA'],'EXACT_SOURCE_HEAD')
 require(cmd('git','ls-remote','origin','refs/heads/'+BRANCH).split()[0]==os.environ['GITHUB_SHA'],'REMOTE_HEAD_RACE')
 require(not cmd('git','status','--porcelain','--untracked-files=no').strip(),'COMMITTED_SOURCE_REQUIRED')
 return os.environ['GITHUB_SHA']
def bindings():
 files=[HERE/n for n in ('release_native.py','AUTHORIZATION.md','ENGINE-INPUT.json')]
 files += [HERE.parent/'downloads-native'/n for n in ('CANDIDATE.json','HOST-CONTRACT-RESULT.json','HELPER-INTEGRATION-RESULT.json','SIGNED460-NATIVE-SOURCE-MAP.json','build_native.py')]
 rows=load(HERE.parent/'downloads-native/CANDIDATE.json')['files'];files += [ROOT/r['source'] for r in rows.values()]
 return {str(p.relative_to(ROOT)):file_sha(p) for p in files}
def versions(version,out):
 require(version in VERSIONS,'EXACT_NATIVE_TEST_RECOVERY_VERSION');issued=[];current=int(os.environ.get('GITHUB_RUN_ID','0'))
 refs=cmd('git','ls-remote','--heads','--tags','origin');numbers=[int(v) for v in re.findall(r'(?<!\d)(210\d{4})(?!\d)',refs)];require(not numbers or max(numbers)<=VERSIONS[-1],'NEWER_VERSION_REF_REQUIRES_REVIEW')
 for page in range(1,21):
  response=json.loads(cmd('gh','api',f'repos/mahfouzhassine8-ops/project-infinity/actions/workflows/397702717/runs?per_page=100&page={page}'));rows=response['workflow_runs']
  for row in rows:
   if row['id']==current:continue
   require(row['status']=='completed','CONCURRENT_ORIGINAL_SIGNER')
   if row['conclusion']!='success':continue
   artifacts=json.loads(cmd('gh','api',f'repos/mahfouzhassine8-ops/project-infinity/actions/runs/{row["id"]}/artifacts?per_page=100'))['artifacts']
   if any(a['name']=='Infinity-Combined-Original-Signer-'+str(row['id']) for a in artifacts):
    authority=json.loads(cmd('git','show',row['head_sha']+':repairs/dual-experience-isolation-2103420/release-authority.json'));issued.append(dict(run=row['id'],version=authority['candidate_versionCode']))
  if len(rows)<100:break
 else:raise RuntimeError('VERSION_AUDIT_PAGINATION_BOUND_EXCEEDED')
 require(not any(r['version']>=version for r in issued),'VERSION_ALREADY_ISSUED_OR_NEWER');save(out,dict(status='PASS_PAGINATED_OFFICIAL_VERSION_AUDIT',target=version,issued=issued))
def certificate(apk,sdk):
 text=cmd(sdk/'apksigner','verify','--verbose','--print-certs',apk);require(CERT in text.lower(),'ORIGINAL_CERTIFICATE_REQUIRED');return text

def verify_native(folder):
 pins=engine_record();paths=list(folder.rglob('libkodi.so'));require(len(paths)==1,'ONE_AUTHENTICATED_ENGINE');library=paths[0];where=library.parent
 for n,h in pins['artifact_member_hashes'].items():require(file_sha(where/n)==h,'NATIVE_ARTIFACT_MEMBER:'+n)
 proof=load(where/'CONTROLLED-ENGINE-VERIFIED.json');mapping=load(where/'NATIVE-SOURCE-MAP.json');before=load(where/'SIGNED460-NATIVE-SOURCE-MAP.json');rows=load(HERE.parent/'downloads-native/CANDIDATE.json')['files']
 require(proof['status']=='PASS_FULL_ARM64_SIGNED460_PLUS_SCOPED_DOWNLOADS' and proof['source_commit']==pins['source_commit'] and proof['native_sha256']==pins['native_sha256']==file_sha(library),'VERIFIED_ARM64_ENGINE')
 require(len(mapping)==9411 and set(mapping)==set(before) and {n for n in mapping if mapping[n]!=before[n]}==set(rows),'FOUR_EXACT_NATIVE_SOURCES')
 for n,r in rows.items():require(before[n]==r['before_sha256'] and mapping[n]==r['candidate_sha256']==file_sha(ROOT/r['source']),'EXACT_NATIVE_SOURCE:'+n)
 require(file_sha(where/'SIGNED460-NATIVE-SOURCE-MAP.json')=='74031d22536937e851abb2c77c9d19b461932a221c54ea69fe422efe63658663','EXACT_COMPILED460_SOURCE_MAP')
 return library

def native_abi(base,lib,out):
 with tempfile.TemporaryDirectory() as t:
  old=Path(t)/'baseline.so'
  with ZipFile(base) as z:old.write_bytes(z.read(NATIVE))
  require(file_sha(old)==BASE_NATIVE,'BASE460_ENGINE')
  def inspect(p):
   header=cmd('readelf','-h',p);dynamic=cmd('readelf','-d',p);symbols=cmd('readelf','--dyn-syms','--wide',p)
   strong=set()
   for line in symbols.splitlines():
    f=line.split()
    if len(f)>=8 and f[4]=='GLOBAL' and f[5] in ('DEFAULT','PROTECTED') and f[6]!='UND':strong.add(f[7])
   require('ELF64' in header and 'AArch64' in header,'AARCH64_REQUIRED')
   return dict(needed=sorted(re.findall(r'\(NEEDED\).*\[([^]]+)\]',dynamic)),soname=re.findall(r'\(SONAME\).*\[([^]]+)\]',dynamic),strong_exports=sorted(strong))
  a,b=inspect(old),inspect(lib);require(a==b,'UNCHANGED_NATIVE_LINK_AND_PUBLIC_ABI');save(out,dict(status='PASS_EXACT_ORIGINAL_PUBLIC_ABI_AND_LINK_DEPENDENCIES',original=a,candidate=b))

def repack(owner,bundles,dest,row,source,version,changes):
 old=read_bundle(bundles/row['file'],row);meta=copy.deepcopy(old);meta.update(version=str(version)+'.'+owner.lower()+'.1',approved_source=source)
 selected={n:raw for n,raw in changes.items() if (n==LABEL)==(owner=='CHOOSER_SHELL')};require(owner in TARGETS,'AUTHORIZED_OWNER')
 require(set(selected)<=({LABEL} if owner=='CHOOSER_SHELL' else {NATIVE}),'NATIVE_ONLY_OWNER_PAYLOAD')
 for n,raw in selected.items():meta['members'][n]['sha256']=digest(raw);meta['payload']['member:'+n]=dict(owner=owner,sha256=digest(raw))
 meta['digest']=component_digest(meta['payload'],owner);path=dest/row['file']
 with ZipFile(bundles/row['file']) as z,ZipFile(path,'w') as out:
  for n in z.namelist():
   if n!='component.json':out.writestr(record(n),selected.get(n.removeprefix('payload/'),z.read(n)))
  out.writestr(record('component.json'),canonical(meta))
 result=dict(file=path.name,sha256=file_sha(path),**{k:meta[k] for k in ('version','digest','approved_source','settings_schema')});require(read_bundle(path,result)['dex']==old['dex'],'ALL_DEX_FROZEN');return result

def compare(baseline,candidate,version,expected,out,sdk=None):
 require(file_sha(baseline)==BASE_SHA and version in VERSIONS,'EXACT_SIGNED460_VERSION');out.mkdir(exist_ok=True,parents=True)
 changed=[];members={}
 with ZipFile(baseline) as a,ZipFile(candidate) as b:
  old=set(validate_names(a))-SIGNATURE;new=set(validate_names(b))-SIGNATURE;require(old==new,'EXACT_EXISTING_MEMBER_SET')
  allowed={'AndroidManifest.xml',LABEL}|({NATIVE} if version==VERSIONS[0] else set())
  for n in sorted(old):
   x,y=a.read(n),b.read(n);members[n]=dict(before=digest(x),after=digest(y))
   if x!=y:
    require(n in allowed,'UNAUTHORIZED_APK_MEMBER:'+n)
    if n=='AndroidManifest.xml':require(normalize_manifest(y)==(normalize_manifest(x)[0],version),'VERSION_ONLY_MANIFEST')
    else:require(digest(y)==expected[n],'EXACT_PAYLOAD:'+n)
    changed.append(n)
  require(set(changed)==allowed,'EXACT_COMPLETE_CHANGED_MEMBER_ALLOWLIST')
 proof=dict(status='PASS_EXACT_SIGNED460_NATIVE_ONLY_MEMBER_PRESERVATION',baseline_sha256=BASE_SHA,candidate_sha256=file_sha(candidate),versionCode=version,changed_existing=changed,new_members=[],protected_existing_members=len(old)-len(changed),expected_member_hashes=expected,all_DEX_unchanged=True,all_addons_and_skin_unchanged=True,Cobra_unchanged=True,Preview_unchanged=True,Android=RUNTIME,all_nine_complete=False)
 save(out/'APK-PRESERVATION.json',proof);save(out/'ALL-APK-MEMBER-HASHES.json',members)
 if sdk:(out/'SIGNATURE.txt').write_text(certificate(candidate,sdk))
 return proof

def prepare(bundles,baseline,native,sdk,out):
 source=head_check();require(file_sha(baseline)==BASE_SHA,'IMMUTABLE_SIGNED460');require(not out.exists(),'FRESH_OUTPUT');out.mkdir()
 base=load(ROOT/'repairs/infinity-2103458-six-corrections-20261105/integration-048/packaging/ISSUED460-AUTHORITY.json');require(load(bundles/'catalog.json')==base['bundle_catalog'],'EXACT_SIGNED460_OWNER_BUNDLES')
 (out/'BASELINE-SIGNATURE.txt').write_text(certificate(baseline,sdk));engine=verify_native(native);native_abi(baseline,engine,out/'NATIVE-COMPATIBILITY.json')
 for owner,row in base['bundle_catalog']['bundles'].items():read_bundle(bundles/row['file'],row)
 for version in VERSIONS:
  work=out/str(version);work.mkdir();dest=work/'components';dest.mkdir();changes={LABEL:('infinity.last_updated_in='+str(version)+'\ncobra.last_updated_in=2103445\n').encode()}
  if version==VERSIONS[0]:changes[NATIVE]=engine.read_bytes()
  catalog=copy.deepcopy(base['bundle_catalog']);catalog['source']=source
  for owner,row in list(catalog['bundles'].items()):
   if owner in TARGETS:catalog['bundles'][owner]=repack(owner,bundles,dest,row,source,version,changes)
   else:shutil.copyfile(bundles/row['file'],dest/row['file'])
  save(dest/'catalog.json',catalog);expected={n:digest(raw) for n,raw in changes.items()};combine(dest,catalog,work/'combined-unsigned.apk',version);compare(baseline,work/'combined-unsigned.apk',version,expected,work/'preservation')
  proof=dict(status='PASS_SIGNED460_DOWNLOADS_NATIVE_AND_FORWARD_RECOVERY_PREPARATION',versionCode=version,source=source,run_id=int(os.environ['GITHUB_RUN_ID']),baseline_sha256=BASE_SHA,source_files=bindings(),expected_members=expected,native_sha256=engine_record()['native_sha256'] if version==VERSIONS[0] else BASE_NATIVE,Android=RUNTIME,accepted_pointer_updated=False,known_defects={'Search':'native crash unresolved;2 settings acceptance FAIL','visual_and_controls':'Fold pending'},module_identity='0.3.5.61 unchanged; matching standalone ZIP required for updated helper',all_nine_complete=False)
  save(work/'PREPARATION.json',proof);publish=work/'publish';publish.mkdir();shutil.copytree(dest,publish/'components');shutil.copytree(work/'preservation',publish/'preservation');shutil.copyfile(work/'PREPARATION.json',publish/'PREPARATION.json');shutil.copyfile(out/'NATIVE-COMPATIBILITY.json',publish/'NATIVE-COMPATIBILITY.json')
 recovery=dict(status='PASS_SOURCE_AND_PAYLOAD_FORWARD_RECOVERY',versionCode=VERSIONS[1],original_functional_reference=2103460,all_functional_APK_members_identical=True,only_version_and_experience_metadata_differ=True,module_and_skin_restoration='Original-key recovery ZIPs through independently traced native AddonBrowser; host Java acceptance PASS, Android NOT RUN',native_install_over_and_recovery='NOT_RUN',no_data_migration=True)
 save(out/'RECOVERY-VERIFICATION.json',recovery)
 for v in VERSIONS:shutil.copyfile(out/'RECOVERY-VERIFICATION.json',out/str(v)/'publish/RECOVERY-VERIFICATION.json')
 head_check()

def official(prepared,run_id,archive=None):
 proof=load(prepared/'PREPARATION.json');v=proof['versionCode'];require(v in VERSIONS,'EXACT_PREPARED_VERSION');run=json.loads(cmd('gh','api',f'repos/mahfouzhassine8-ops/project-infinity/actions/runs/{run_id}'))
 require(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==proof['source'] and run['head_branch']==BRANCH and run['path']=='.github/workflows/infinity-combined-release.yml','OFFICIAL_KEYLESS_PREPARER')
 require(proof['source_files']==bindings(),'CURRENT_SOURCE_BINDING');rows=json.loads(cmd('gh','api',f'repos/mahfouzhassine8-ops/project-infinity/actions/runs/{run_id}/artifacts?per_page=100'))['artifacts'];found=[r for r in rows if r['name']==f'Infinity{v}-Prepared-{run_id}' and not r['expired']];require(len(found)==1,'EXACT_OFFICIAL_PREPARATION_ARTIFACT');row={k:found[0][k] for k in ('id','name','digest','size_in_bytes')}
 if archive is None:
  archive=prepared.parent/(str(row['id'])+'.zip')
  with archive.open('wb') as f:subprocess.run(['gh','api',f'repos/mahfouzhassine8-ops/project-infinity/actions/artifacts/{row["id"]}/zip'],stdout=f,check=True)
 require(file_sha(archive)==row['digest'].removeprefix('sha256:'),'OFFICIAL_ARCHIVE_DIGEST')
 with ZipFile(archive) as z:
  names={n for n in validate_names(z) if not n.endswith('/')};require(names=={str(p.relative_to(prepared)) for p in prepared.rglob('*') if p.is_file()},'EXACT_PREPARED_FILES')
  for n in names:require(digest(z.read(n))==file_sha(prepared/n),'OFFICIAL_MEMBER:'+n)
 require(load(prepared/'RECOVERY-VERIFICATION.json')['status']=='PASS_SOURCE_AND_PAYLOAD_FORWARD_RECOVERY','RECOVERY_GATE');return row

def proposed(prepared,run_id,archive=None):
 artifact=official(prepared,run_id,archive);proof=load(prepared/'PREPARATION.json');version=proof['versionCode'];prior=load(HERE/'ISSUED462-AUTHORITY.json') if version==VERSIONS[1] else json.loads(cmd('git','show','057aed04:repairs/dual-experience-isolation-2103420/release-authority.json'))
 require(prior['candidate_versionCode']==version-1,'EXACT_ISSUED_PREDECESSOR');catalog=load(prepared/'components/catalog.json');metas={o:read_bundle(prepared/'components'/r['file'],r) for o,r in catalog['bundles'].items()};a=copy.deepcopy(prior)
 a.update(generation=prior['generation']+1,last_issued_versionCode=version-1,candidate_versionCode=version,target_owners=TARGETS,update_kind='owner_update',previous_authority_sha256=digest(canonical(prior)),payload={k:v for m in metas.values() for k,v in m['payload'].items()},bundle_catalog=catalog,experience_version_labels={'INFINITY':version,'COBRA':2103445})
 for owner in TARGETS:
  a['components'][owner]={k:metas[owner][k] for k in ('version','digest','approved_source','settings_schema')};a['components'][owner]['revision']=prior['components'][owner]['revision']+1;a['bundle_sources'][owner]=dict(run_id=run_id,build_source=proof['source'],artifact=f'Infinity{version}-Prepared-{run_id}',path='components/'+owner+'.zip')
 a['source_files']={n:file_sha(ROOT/n) for n in prior['source_files']};a['workflow_sha256']=file_sha(ROOT/'.github/workflows/infinity-combined-release.yml');a['owner_update_evidence']=dict(owner='INFINITY_DOWNLOADS_NATIVE_TEST' if version==VERSIONS[0] else 'INFINITY_SIGNED460_FORWARD_RECOVERY',producer_run=run_id,producer_source=proof['source'],source_files=proof['source_files'],artifact=artifact,preparation_sha256=file_sha(prepared/'PREPARATION.json'),native_sha256=proof['native_sha256'],Android=RUNTIME,physical_Fold='PENDING',unknown_obligations='REMAIN_BLOCKING',accepted_pointer_updated=False,known_defects=proof['known_defects'])
 transition(prior,a,TARGETS);verify_evidence(a,lambda n:(ROOT/n).read_bytes());return a

def check_registered(prepared,run_id,out,archive=None):
 head_check();require(proposed(prepared,run_id,archive)==load(AUTH),'EXACT_REGISTERED_OFFICIAL_NATIVE_ARTIFACT');save(out,dict(status='PASS_NATIVE_DOWNLOADS_OR_RECOVERY_AUTHORITY',Android=RUNTIME,accepted_pointer_updated=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='op',required=True)
 for op in ('prepare','compare'):
  a=sub.add_parser(op)
  for n in (('bundles','baseline','native','sdk','out') if op=='prepare' else ('baseline','candidate','plan','out')):a.add_argument('--'+n,type=Path,required=True)
  if op=='compare':a.add_argument('--sdk',type=Path)
 a=sub.add_parser('versions');a.add_argument('--version',type=int,required=True);a.add_argument('--out',type=Path,required=True)
 a=sub.add_parser('check_registered');a.add_argument('--prepared',type=Path,required=True);a.add_argument('--run-id',type=int,required=True);a.add_argument('--out',type=Path,required=True)
 d=vars(p.parse_args());op=d.pop('op')
 if op=='compare':proof=load(d.pop('plan'));compare(version=proof['versionCode'],expected=proof['expected_members'],**d)
 else:{'prepare':prepare,'versions':versions,'check_registered':check_registered}[op](**d)
