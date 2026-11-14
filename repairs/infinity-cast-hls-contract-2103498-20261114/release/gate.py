"""Exact signed498 one-library Dolby correction and original-signer checks.

No key handling or replacement signer. The unchanged original assembler signs.
"""
from pathlib import Path
from zipfile import ZipFile
import copy,hashlib,importlib.util,json,os,re,shutil,stat,subprocess,sys
HERE=Path(__file__).resolve().parent;TASK=HERE.parent;ROOT=TASK.parents[1]
OLD=ROOT/'repairs/infinity-movies-continue-cast-2103486-20261112';sys.path.insert(0,str(OLD/'release'))
import common_release as c
import prepare_release as old
import release_guard
c.BRANCH='work/infinity-cast-root-cause-from-2103496-20261114'
c.BASE='2fd158bbdd26d47f4204c8c474f15c9ca69cfef00fcecdb62c866b42559d3004'
VERSIONS={'candidate':2103500,'recovery':2103501};GENERATIONS={'candidate':85,'recovery':86}
LABEL='assets/experience-component-updates.properties';LIB='lib/arm64-v8a/libkodi.so';DEX='classes6.dex'
REMUX_LIB='lib/arm64-v8a/libinfinitycastremux.so'
PREFIX='repairs/infinity-cast-hls-contract-2103498-20261114/'
SCOPE='repairs/infinity-cast-hls-contract-2103498-20261114/SCOPE.json'
BASE_SOURCE='80aef0a13b2390076d263435b4a98ee497ecf0d4'
RECOVERY_SOURCE=BASE_SOURCE
RECOVERY_SHA=c.BASE

def request(canonical=False):
 c.context(canonical);r=c.load(HERE/'REQUEST.json')
 c.require(r['baseline_APK_sha256']==c.BASE and r['accepted_pointer_updated'] is False and r['owner_acceptance_after_signing'] is True,'EXACT_CAST_ONLY_OWNER_SCOPE')
 for n,h in r['source_bindings'].items():c.require(c.sha(ROOT/n)==h,'EXACT_FROZEN_CAST_RELEASE_SOURCE:'+n)
 c.require(c.sha(ROOT/c.WORKFLOW)==r['workflow_sha256'],'SOURCE_BOUND_ORIGINAL_WORKFLOW')
 c.tools();return r


def source_scope():
 scope=c.load(ROOT/SCOPE);baseline=scope['baseline_source_snapshot'];permitted=set(scope['production_allowlist'])
 tools={c.WORKFLOW,'.github/workflows/infinity-saved-navigation-android.yml',c.AUTHORITY}
 changed=c.git('diff','--name-only',baseline,'HEAD').decode().splitlines()
 for name in changed:c.require(name in permitted or name in tools or name.startswith(PREFIX),'OUT_OF_CAST_SOURCE_SCOPE:'+name)
 c.require(c.git('show',BASE_SOURCE+':'+str((c.CORE/'ownership-reviewed-roots.json').relative_to(ROOT)))==(c.CORE/'ownership-reviewed-roots.json').read_bytes(),'NO_CAST_CLASS_OR_COBRA_OWNER_POLICY_CHANGE')
 for name in c.git('ls-tree','-r','--name-only',BASE_SOURCE,'--',str(OLD.relative_to(ROOT))+'/cast/java').decode().splitlines():
  if name not in permitted:c.require((ROOT/name).read_bytes()==c.git('show',BASE_SOURCE+':'+name),'OUTSIDE_TWO_CAST_JAVA_FILES:'+name)
 return dict(status='PASS_THREE_CAST_SOURCE_FILES_ONLY',baseline=baseline,baseline_signing_source=BASE_SOURCE,changed_files=changed,production_allowlist=scope['production_allowlist'],Command_Center_changed=False,skin_changed=False,Cobra_changed=False,shutdown_changed=False)

def owners(row,kind):
 c.producer(row);folder=ROOT/'cast-final-owner-input';folder.mkdir(exist_ok=True);archive=folder/'authenticated.zip'
 if not archive.exists():
  with archive.open('xb') as out:subprocess.run(['gh','api','repos/'+c.REPO+'/actions/artifacts/'+str(row['id'])+'/zip'],stdout=out,check=True,timeout=900)
 c.require('sha256:'+c.sha(archive)==row['digest'] and archive.stat().st_size==row['size_in_bytes'],'EXACT_SIGNED496_OWNER_ARCHIVE')
 dest=folder/'selected';dest.mkdir(exist_ok=True)
 with ZipFile(archive) as z:
  c.require(len(z.namelist())==len(set(z.namelist())) and sum(x.file_size for x in z.infolist())<8*1024**3,'SAFE_COMPLETE_OWNER_ARCHIVE')
  for item in z.infolist():
   p=Path(item.filename);c.require(not p.is_absolute() and '..' not in p.parts and '\\' not in item.filename and not stat.S_ISLNK(item.external_attr>>16),'SAFE_OWNER_MEMBER')
   if not item.is_dir() and item.filename.startswith(kind+'/components/'):
    target=dest/p;target.parent.mkdir(parents=True,exist_ok=True)
    with z.open(item) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst,1024*1024)
 root=dest/kind/'components';catalog=c.load(root/'catalog.json');a=json.loads(c.git('show',(BASE_SOURCE if kind=='candidate' else RECOVERY_SOURCE)+':'+c.AUTHORITY))
 c.require(catalog==a['bundle_catalog'],'EXACT_SIGNED496_APPROVED_OWNER_CATALOG');return root,catalog


def compiled(r):
 sdk_root=c.obtain(r['inputs']['android'],'dolby-android');component=c.unique(sdk_root,'COMPONENT-RESULT.json').parent;proof=c.load(component/'COMPONENT-RESULT.json');android=c.load(c.unique(sdk_root,'ANDROID-CAST-COMPONENT.json'))
 c.require(proof['baseline_APK_sha256']==c.BASE and not proof['duplicate_classes'] and not proof['Cobra_owned_type_references'] and not proof['missing_baseline_APIs'],'PRIVATE_CAST_ABI_AND_COBRA_ISOLATION')
 c.require(android['pass'] is True and android['existing_original_engine'] is True and android['new_ARM64_JNI'] is True and android['real_Dolby_configuration'] is True and android['Dolby_header_and_media_delivery'] is True and android['stream_copy_not_transcode'] is True and android['exact_packet_quality_timing'] is True and android['authenticated_ranges'] is True and android['random_segment_seeking'] is True and android['cancellation'] is True and android['native_contexts_after_close']==0,'ACTUAL_ANDROID_DOLBY_HEADER_PACKET_CLOCK_AND_NATIVE_RETIREMENT')
 if android['EAC3_decoder_available']:c.require(android['HLS']['actual_Android_HLS_playback'] is True,'PRESENT_ANDROID_DOLBY_DECODER_MUST_PLAY')
 native=c.unique(sdk_root,'libinfinitycastremux.so');receipt=c.load(native.parent/'CAST-HLS-NATIVE.json');mpl=c.load(c.unique(sdk_root,'GOOGLE-MPL-CONTRACT.json'))
 c.require(android['explicit_master_codecs'] is True and android['converted_HTTP_complete_range_type_CORS'] is True and android['actual_fMP4_bytes_identical_to_498'] is True,'EXPLICIT_CODEC_MASTER_COMPLETE_HTTP_AND_UNCHANGED498_MEDIA')
 c.require(mpl['status']=='PASS_ACTUAL_GOOGLE_MPL_BEFORE_AFTER_CODEC_CONTRACT' and mpl['expected_actual_native_codecs']=='hev1.1.6.L30.90,ec-3','ACTUAL_PUBLIC_GOOGLE_MPL_MISCLASSIFICATION_CORRECTED')
 c.require(receipt['status']=='PASS_REAL_ARM64_HLS_CODEC_METADATA_EXACT498_ORIGINAL_ENGINE' and receipt['baseline_APK_sha256']==c.BASE and receipt['existing_engine_sha256']=='3caccc96c23336e220b791118989f3a850b73fa8804267fb7beb2aad3b3afc75' and not receipt['engine_changed'] and c.sha(native)==receipt['new_library_sha256'],'EXACT_SCOPED_CAST_METADATA_LIBRARY_ORIGINAL_ENGINE')
 for name,sha in receipt['source_hashes'].items():c.require(c.sha(ROOT/name)==sha,'EXACT_COMPILED_CAST_METADATA_SOURCE:'+name)
 for name,sha in proof['feature_Java_sha256'].items():c.require(c.sha(OLD/'cast'/name)==sha,'EXACT_SCOPED_CAST_JAVA:'+name)
 c.require(list(proof['dex'])==['classes.dex'],'ONE_EXISTING_CAST_DEX');dex=component/'dex/classes.dex';c.require(c.sha(dex)==proof['dex']['classes.dex'],'EXACT_COMPILED_CAST_DEX');return native,component,dex,proof


def updates(base,kind,native,dex,version):
 _,cb,_,_,_=c.tools()
 with ZipFile(base) as z:changes={'AndroidManifest.xml':cb.set_version(z.read('AndroidManifest.xml'),version),LABEL:('infinity.last_updated_in='+str(version)+'\ncobra.last_updated_in=2103445\n').encode()}
 if kind=='candidate':changes.update({REMUX_LIB:native.read_bytes(),DEX:dex.read_bytes()})
 return changes


def preservation(base,apk,kind,changes):
 inventory,cb,_,_,_=c.tools();rows={};same=0
 with ZipFile(base) as a,ZipFile(apk) as b:
  names=set(inventory.validate_names(a))-inventory.SIGNATURE;c.require(set(inventory.validate_names(b))-inventory.SIGNATURE==names,'EXACT496_MEMBER_SET_NO_ADDITIONS_OR_REMOVALS')
  for name in sorted(names):
   before=old.member_sha(a,name);after=old.member_sha(b,name);wanted=old.data_hash(changes[name]) if name in changes else before;c.require(after==wanted,'OUT_OF_CAST_SCOPE_APK_MEMBER:'+name)
   if before!=after:rows[name]=dict(before=before,after=after)
   else:same+=1
  c.require(set(rows)==({'AndroidManifest.xml',LABEL,REMUX_LIB,DEX} if kind=='candidate' else {'AndroidManifest.xml',LABEL}),'EXACT_DOLBY_ONLY_MEMBER_VECTOR')
  c.require(cb.normalize_manifest(a.read('AndroidManifest.xml'))[0]==cb.normalize_manifest(b.read('AndroidManifest.xml'))[0],'NO_MANIFEST_CHANGE_EXCEPT_VERSION')
  c.require(old.member_sha(a,LIB)==old.member_sha(b,LIB)=='3caccc96c23336e220b791118989f3a850b73fa8804267fb7beb2aad3b3afc75','NO_KODI_ENGINE_REPLACEMENT')
  if kind=='recovery':c.require(old.member_sha(a,DEX)==old.member_sha(b,DEX)=='5f2bf19c979904856c0300ae819bf584599255b12623b309c2f984c0cc0f2944','EXACT498_RECOVERY_CAST_DEX')
 return dict(status='PASS_EXACT_SIGNED498_SCOPED_CAST_METADATA_AND_PLAYLISTS',baseline_APK_sha256=c.BASE,protected_recovery_functional_baseline=2103498,versionCode=VERSIONS[kind],kind=kind,changed_members=rows,unchanged_payload_members=same,added_members=[],removed_members=[],original_five_DEX_unchanged=True,all_original_native_libraries_except_Cast_bridge_unchanged=True,Cobra_changed=False,Command_Center_or_movie_or_tracking_changed=False,skin_changed=False,providers_or_Search_changed=False,shutdown_or_persistence_guards_changed=False,Python_startup_changed=False,profiles_or_databases_read_or_changed=False,Fold_acceptance='PENDING_OWNER_ONE_SESSION')

def class_rows(dex,out,label):
 inventory,_,_,_,_=c.tools();mini=out/(label+'.zip');folder=out/(label+'-smali')
 with ZipFile(mini,'w') as z:z.write(dex,'classes.dex')
 inventory.disassemble(mini,c.jars(),folder);rows,_,_=inventory.parse_dex(folder);shutil.rmtree(folder);mini.unlink();return rows

def bundle(src,dst,owner,version,changes,new_classes=None,old_classes=None,dex=None,preserve_identity=False):
 inventory,cb,_,_,review=c.tools()
 with ZipFile(src) as z:
  meta=json.loads(z.read('component.json'));replacements={}
  for name,value in changes.items():
   if re.fullmatch(r'classes\d*\.dex',name) or review.member_owner(name)!=owner:continue
   raw_hash=old.data_hash(value);normal=c.digest(cb.normalize_manifest(value)[0]) if name=='AndroidManifest.xml' else raw_hash
   meta['payload']['member:'+name]=dict(owner=owner,sha256=normal);meta['members'][name]=dict(meta['members'].get(name,dict(compress_type=0,external_attr=0o100644<<16)),sha256=raw_hash);replacements['payload/'+name]=value
  if owner=='INFINITY' and new_classes is not None:
   for name,row in old_classes.items():c.require(meta['payload'].pop('class:'+name)==dict(owner='INFINITY',sha256=row['sha256']),'OLD_CAST_DEX_OWNER_AND_BYTES')
   for name,row in new_classes.items():
    c.require('class:'+name not in meta['payload'],'CAST_CANNOT_REPLACE_AN_ORIGINAL_FIVE_DEX_CLASS');meta['payload']['class:'+name]=dict(owner='INFINITY',sha256=row['sha256'])
   c.require('dex/cast-private.dex' in meta['dex'],'EXACT_EXISTING_CAST_DEX');meta['dex']['dex/cast-private.dex']=c.sha(dex);replacements['dex/cast-private.dex']=dex
  if not preserve_identity:meta['version']=str(version)+'.'+owner.lower()+'.cast_hls498.1';meta['approved_source']=os.environ['GITHUB_SHA']
  meta['digest']=cb.component_digest(meta['payload'],owner)
  with ZipFile(dst,'w',allowZip64=True) as target:
   for n in z.namelist():old.copy_entry(z,target,n,inventory.canonical(meta) if n=='component.json' else replacements.get(n))
   for n,value in replacements.items():
    if n not in z.namelist():target.writestr(cb.record(n,False),value.read_bytes() if isinstance(value,Path) else value)
 return meta


def prepare():
 r=request();source_proof=source_scope();parent=c.api('git/ref/heads/'+c.CANONICAL)['object']['sha'];c.require(parent==r['registry_parent_source'],'RECONCILE_REGISTRY_RACE')
 a=json.loads(c.git('show',parent+':'+c.AUTHORITY));c.require((a['generation'],a['candidate_versionCode'])==(84,2103499),'UNUSED_NEXT98_99_FROM_ACTUAL_REGISTRY')
 base=c.unique(c.obtain(r['inputs']['baseline'],'dolby-base'),'Infinity-2103498-Combined-Original-Signer.apk');c.require(c.sha(base)==c.BASE,'EXACT_SIGNED496_STARTING_APK');c.signature(base)
 owner_root,catalog=owners(r['inputs']['owners'],'candidate');native,component,dex,proof=compiled(r);inventory,cb,_,_,_=c.tools();out=ROOT/'cast-final-prepared';out.mkdir(exist_ok=False);c.save(out/'SOURCE-PRESERVATION.json',source_proof)
 with ZipFile(base) as z:c.require(old.member_sha(z,REMUX_LIB)=='39d571773f536271320f270a7f0c26c68849285ca29ed7555fbd5d96c83bed64','ORIGINAL496_CAST_BRIDGE_IDENTITY')
 olddex=out/'baseline-cast.dex'
 with ZipFile(base) as z:olddex.write_bytes(z.read(DEX))
 old_classes=class_rows(olddex,out,'old-cast');new_classes=class_rows(dex,out,'new-cast');olddex.unlink()
 c.require(set(old_classes)==set(new_classes) and len(old_classes)==1033,'NO_CAST_OR_SDK_CLASS_ADDITIONS_OR_REMOVALS')
 changed_classes=[n for n in old_classes if old_classes[n]['sha256']!=new_classes[n]['sha256']]
 for n in changed_classes:c.require(any(n==root+';' or n.startswith(root+'$') for root in ['Lcom/projectinfinity/kodi/InfinityCastRemux','Lcom/projectinfinity/kodi/InfinityCastRelay']),'OUTSIDE_TWO_CAST_SOURCE_CLASSES:'+n)
 c.save(out/'CLASS-PRESERVATION.json',dict(status='PASS_TWO_CAST_SOURCE_ROOTS_ONLY',changed=changed_classes,unchanged=len(old_classes)-len(changed_classes),total=1033))
 with ZipFile(base) as z:c.require(z.read('assets/infinity/cast/RESOURCE-IDENTITY.json')==(component/'RESOURCE-IDENTITY.json').read_bytes() and old.member_sha(z,'assets/infinity/cast/resources.apk')==c.sha(component/'resources.apk'),'CAST_UI_AND_SDK_RESOURCES_FROZEN')
 for kind,version in VERSIONS.items():
  dest=out/kind;dest.mkdir();components=dest/'components';components.mkdir();changes=updates(base,kind,native,dex,version);apk=dest/('Infinity-'+str(version)+'-UNSIGNED-NOT-INSTALLABLE.apk')
  with ZipFile(base) as src,ZipFile(apk,'w',allowZip64=True) as target:
   for name in src.namelist():
    if name not in inventory.SIGNATURE:old.copy_entry(src,target,name,changes.get(name))
  check=preservation(base,apk,kind,changes);check.update(unsigned_sha256=c.sha(apk),source=os.environ['GITHUB_SHA']);c.save(dest/'PRESERVATION.json',check)
  cat=copy.deepcopy(catalog);cat['source']=os.environ['GITHUB_SHA'];cat['release_approved']=False
  for owner in cb.OWNED:
   row=cat['bundles'][owner];source=owner_root/row['file'];target=components/row['file']
   if owner=='COBRA':shutil.copyfile(source,target)
   else:
    if owner=='MINIMAL_ANDROID_CONTRACT':
     before=cb.read_bundle(source,row);meta=bundle(source,target,owner,version,changes,preserve_identity=True);c.require(all(meta[k]==before[k] for k in ('version','digest','approved_source','settings_schema','payload')),'UNCHANGED_MINIMAL_OWNER_IDENTITY')
    else:meta=bundle(source,target,owner,version,changes,new_classes if kind=='candidate' and owner=='INFINITY' else None,old_classes,dex)
    row.update(sha256=c.sha(target),**{k:meta[k] for k in ('version','digest','approved_source')})
   cb.read_bundle(target,row)
  (components/'catalog.json').write_bytes(inventory.canonical(cat))
 c.save(out/'PREPARATION.json',dict(status='PASS_CAST_ONLY_COMPLETE_PAIR_PREPARATION',source=os.environ['GITHUB_SHA'],baseline_APK_sha256=c.BASE,inputs=r['inputs'],new_Cast_library_sha256=c.sha(native),original_five_DEX_unchanged=True,registry_changed=False,signed=False,owner_acceptance='NOT_RUN'));print('PASS_EXACT_SIGNED496_DOLBY_ONLY_QA_AND_FORWARD_RECOVERY')

def prepared(r):
 root=c.obtain(r['prepared_producer'],'cast-final-prepared');p=c.unique(root,'PREPARATION.json');receipt=c.load(p)
 c.require(receipt['status']=='PASS_CAST_ONLY_COMPLETE_PAIR_PREPARATION' and receipt['inputs']==r['inputs'] and receipt['source']==r['prepared_producer']['source'],'EXACT_PREPARED_CAST_PAIR');return p.parent

def verify(r,kind,apk):
 role='baseline';version=2103498;expected=c.BASE
 base=c.unique(c.obtain(r['inputs'][role],'final-verify-'+kind),'Infinity-'+str(version)+'-Combined-Original-Signer.apk');c.require(c.sha(base)==expected,'EXACT_APPROVED_STARTING_APK');native,component,dex,proof=compiled(r)
 return preservation(base,apk,kind,updates(base,kind,native,dex,VERSIONS[kind]))

def propose():
 r=request(True);kind=r['active_kind'];root=prepared(r);apk=root/kind/('Infinity-'+str(VERSIONS[kind])+'-UNSIGNED-NOT-INSTALLABLE.apk');proof=verify(r,kind,apk)
 inventory,cb,ra,_,_=c.tools();current=c.load(ROOT/c.AUTHORITY)
 c.require(c.sha(ROOT/c.AUTHORITY)==r['parent_authority_sha256'] and current['generation']==GENERATIONS[kind]-1 and current['candidate_versionCode']==VERSIONS[kind]-1,'EXACT_CURRENT_VERSION_REGISTRY')
 c.require(c.api('git/ref/heads/'+c.CANONICAL)['object']['sha']==os.environ['GITHUB_SHA'],'CURRENT_ORIGINAL_SIGNER_HEAD')
 c.require((c.CORE/'ownership-reviewed-roots.json').read_bytes()==c.git('show',BASE_SOURCE+':repairs/dual-experience-isolation-2103420/ownership-reviewed-roots.json'),'NO_CLASS_POLICY_CHANGE')
 catalog=c.load(root/kind/'components/catalog.json');meta={o:cb.read_bundle(root/kind/'components'/row['file'],row) for o,row in catalog['bundles'].items()}
 targets=['INFINITY','CHOOSER_SHELL']
 result=copy.deepcopy(current);result.update(generation=GENERATIONS[kind],candidate_versionCode=VERSIONS[kind],last_issued_versionCode=current['candidate_versionCode'],previous_authority_sha256=inventory.digest(inventory.canonical(current)),target_owners=targets,update_kind='owner_update',payload={n:v for m in meta.values() for n,v in m['payload'].items()},bundle_catalog=catalog,experience_version_labels=dict(INFINITY=VERSIONS[kind],COBRA=2103445),workflow_sha256=c.sha(ROOT/c.WORKFLOW))
 for owner in targets:
  result['components'][owner]={k:meta[owner][k] for k in ('version','digest','approved_source','settings_schema')};result['components'][owner]['revision']=current['components'][owner]['revision']+1
  result['bundle_sources'][owner]=dict(run_id=r['prepared_producer']['run'],build_source=r['prepared_producer']['source'],artifact=r['prepared_producer']['name'],path=kind+'/components/'+owner+'.zip')
 for n in result['source_files']:result['source_files'][n]=c.sha(ROOT/n)
 c.require(result['cast_manifest_exception']==current['cast_manifest_exception'],'UNCHANGED_SHARED_MANIFEST_AUTHORITY')
 result['owner_update_evidence']=dict(owner='INFINITY_CAST_HLS498_'+kind.upper(),producer_run=r['prepared_producer']['run'],producer_source=r['prepared_producer']['source'],artifact={k:r['prepared_producer'][k] for k in ('id','name','digest','size_in_bytes')},source_files=dict(r['source_bindings'],**{str((HERE/'REQUEST.json').relative_to(ROOT)):c.sha(HERE/'REQUEST.json')}),baseline_APK_sha256=c.BASE,protected_recovery_baseline_APK_sha256=c.BASE,preparation_sha256=c.sha(root/kind/'PRESERVATION.json'),Fold='OWNER_ACCEPTANCE_AFTER_SIGNING',Cast_receiver='OWNER_ACCEPTANCE_AFTER_SIGNING',original_five_DEX_unchanged=True,Cobra_changed=False,shutdown_source_changed=False,accepted_pointer_updated=False,publication=False,public_release=False,owner_delivery_cleared=False,verification_toolchain=current['owner_update_evidence']['verification_toolchain'])
 ra.transition(current,result,targets);ra.verify_evidence(result,lambda n:(ROOT/n).read_bytes());ra.verify(result,{n:v['sha256'] for n,v in result['payload'].items()},VERSIONS[kind],GENERATIONS[kind])
 out=ROOT/'cast-final-authority';out.mkdir(exist_ok=False);(out/'AUTHORITY-PROPOSAL.json').write_bytes(inventory.canonical(result));c.save(out/'PRESERVATION.json',proof);print('PASS_CAST_ONLY_AUTHORITY_PROPOSAL_NO_KEY_ACCESS')

def inputs():
 r=request(True);kind=r['active_kind'];a=c.load(ROOT/c.AUTHORITY);_,_,ra,_,_=c.tools();c.require(a['generation']==GENERATIONS[kind] and a['candidate_versionCode']==VERSIONS[kind] and a['owner_update_evidence']['owner']=='INFINITY_CAST_HLS498_'+kind.upper(),'EXACT_REGISTERED_CAST_ONLY_QA')
 ra.verify_evidence(a,lambda n:(ROOT/n).read_bytes());root=prepared(r);apk=root/kind/('Infinity-'+str(VERSIONS[kind])+'-UNSIGNED-NOT-INSTALLABLE.apk');c.require(c.sha(apk)==c.load(root/kind/'PRESERVATION.json')['unsigned_sha256'],'EXACT_FROZEN_UNSIGNED_APK');verify(r,kind,apk)
 with Path(os.environ['GITHUB_OUTPUT']).open('a') as out:out.write('apk='+str(apk.relative_to(ROOT))+'\ngeneration='+str(GENERATIONS[kind])+'\n')
 c.jars()

def post():
 r=request(True);kind=r['active_kind'];folder=ROOT/'cast-final-original-signed';apk=folder/('Infinity-'+str(VERSIONS[kind])+'-Combined-Original-Signer.apk');receipt=c.load(folder/'BUILD-RECEIPT.json')
 c.require(receipt['signed_apk_sha256']==c.sha(apk) and receipt['certificate_sha256']==c.CERT,'ACTUAL_ORIGINAL_SIGNER_RECEIPT');signature=c.signature(apk);proof=verify(r,kind,apk);proof.update(APK_sha256=c.sha(apk),source=os.environ['GITHUB_SHA'],certificate_sha256=c.CERT);c.save(folder/'PRESERVATION.json',proof);(folder/'SIGNATURE.txt').write_text(signature);(folder/'SHA256SUMS').write_text(c.sha(apk)+'  '+apk.name+'\n')
if __name__=='__main__':
 c.require(len(sys.argv)==2,'EXACT_CAST_RELEASE_OPERATION');{'prepare':prepare,'propose':propose,'inputs':inputs,'post':post}[sys.argv[1]]()
