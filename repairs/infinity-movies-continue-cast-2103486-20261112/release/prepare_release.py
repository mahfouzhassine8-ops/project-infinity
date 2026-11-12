"""Exact86-derived combined QA and forward recovery. No keys/registry writes."""
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
from pathlib import Path
import copy,json,os,re,shutil,subprocess,sys
import common_release as c
import patch_cast_manifest

CC='script.infinity.commandcenter';SKIN='skin.infinity.diggz'
LIB='lib/arm64-v8a/libkodi.so';LABEL='assets/experience-component-updates.properties'
SKIN_FILES=('addon.xml','infinity-skin.json','Infinity-Protected-Manifest.json','unified/VideoOSD.xml')
def scalar(raw,key,before,after):
    old=('"'+key+'": '+json.dumps(before)).encode();new=('"'+key+'": '+json.dumps(after)).encode()
    c.require(raw.count(old)==1,'EXACT_METADATA_PREIMAGE:'+key);return raw.replace(old,new,1)
def skin_files(z,kind):
    baseline={n:z.read('assets/addons/'+SKIN+'/'+n) for n in SKIN_FILES}
    number=274 if kind=='candidate' else 275;version='1.0.5.'+str(number)
    addon=baseline['addon.xml'];c.require(addon.count(b'version="1.0.5.273"')==1,'EXACT273_SKIN')
    addon=addon.replace(b'version="1.0.5.273"',('version="'+version+'"').encode(),1)
    info=baseline['infinity-skin.json']
    for key,old,new in [('candidate',273,number),('version','1.0.5.273',version),('skin_version','1.0.5.273',version)]:info=scalar(info,key,old,new)
    changed={'addon.xml':addon,'infinity-skin.json':info}
    if kind=='candidate':
        changed['unified/VideoOSD.xml']=(c.TASK/'overlay'/SKIN/'unified/VideoOSD.xml').read_bytes()
        changed['media/infinity_cast/cast.png']=(c.TASK/'overlay'/SKIN/'media/infinity_cast/cast.png').read_bytes()
    raw=baseline['Infinity-Protected-Manifest.json'];before=json.loads(raw);c.require(len(before['protected_files'])==948,'EXACT273_PROTECTED_SET')
    for name,data in changed.items():
        if name not in before['protected_files']:continue
        old=('"'+name+'": "'+before['protected_files'][name]+'"').encode();new=('"'+name+'": "'+c.digest(data)+'"').encode()
        c.require(raw.count(old)==1,'EXACT_SKIN_HASH_PREIMAGE:'+name);raw=raw.replace(old,new,1)
    if kind=='candidate':
        key='media/infinity_cast/cast.png'
        line=('"unified/VideoOSD.xml": "'+c.digest(changed['unified/VideoOSD.xml'])+'"').encode()
        c.require(raw.count(line)==1,'ONE_CAST_LAYOUT_HASH')
        raw=raw.replace(line,('"'+key+'": "'+c.digest(changed[key])+'",\n    ').encode()+line,1)
    for key,old,new in [('candidate',273,number),('skin_version','1.0.5.273',version),('candidate_version','1.0.5.273',version)]:raw=scalar(raw,key,old,new)
    after=json.loads(raw);c.require(set(after['protected_files'])-set(before['protected_files'])==({'media/infinity_cast/cast.png'} if kind=='candidate' else set()),'ONLY_CAST_ICON_ADDED')
    for name,data in changed.items():c.require(after['protected_files'][name]==c.digest(data),'SKIN_SOURCE_HASH:'+name)
    old_other=copy.deepcopy(before);new_other=copy.deepcopy(after)
    for key in ('candidate','skin_version','candidate_version','protected_files'):old_other.pop(key);new_other.pop(key)
    c.require(old_other==new_other,'UNRELATED_SKIN_METADATA_CHANGED')
    c.require(all(after['protected_files'][n]==v for n,v in before['protected_files'].items() if n not in changed),'UNRELATED_SKIN_PROTECTION_CHANGED')
    changed['Infinity-Protected-Manifest.json']=raw
    return {'assets/addons/'+SKIN+'/'+name:value for name,value in changed.items()}
def member_sha(z,name):
    with z.open(name) as stream:return __import__('hashlib').file_digest(stream,'sha256').hexdigest()
def copy_entry(source,target,name,replacement=None):
    old=source.getinfo(name);info=ZipInfo(name,old.date_time)
    info.compress_type=old.compress_type;info.external_attr=old.external_attr
    with target.open(info,'w',force_zip64=old.file_size>=2**31) as output:
        if replacement is None:
            with source.open(name) as stream:shutil.copyfileobj(stream,output,2*1024*1024)
        elif isinstance(replacement,bytes):output.write(replacement)
        else:
            with Path(replacement).open('rb') as stream:shutil.copyfileobj(stream,output,2*1024*1024)
def data_hash(value):return c.digest(value) if isinstance(value,bytes) else c.sha(value)
def compare(base,apk,replacements,added,version):
    inventory,cb,_,_,_=c.tools()
    with ZipFile(base) as old,ZipFile(apk) as new:
        names=set(inventory.validate_names(old))-inventory.SIGNATURE
        c.require(set(inventory.validate_names(new))-inventory.SIGNATURE==names|set(added),'EXACT_APK_MEMBER_VECTOR')
        rows={};unchanged=0
        for n in sorted(names|set(added)):
            after=member_sha(new,n);before=member_sha(old,n) if n in names else None
            wanted=data_hash(replacements[n]) if n in replacements else before
            c.require(after==wanted,'UNEXPECTED_APK_MEMBER:'+n)
            if before!=after:rows[n]=dict(before=before,after=after)
            else:unchanged+=1
        for n in names:
            if re.fullmatch(r'classes\d*\.dex',n):c.require(n not in rows,'ORIGINAL_FIVE_DEX_MUST_BE_BYTE_IDENTICAL')
        c.require(cb.normalize_manifest(new.read('AndroidManifest.xml'))[1]==version,'EXACT_TYPED_APK_VERSION')
    return dict(changed_members=rows,unchanged_members=unchanged,added_members=sorted(added),original_five_DEX_unchanged=True,Cobra_changed=False,shutdown_source_changed=False,databases_or_profile_changes=False)
def policy_for_new(classes,baseline):
    policy=copy.deepcopy(baseline);app='Lcom/projectinfinity/kodi/'
    for name in classes:
        if name.startswith(app):
            root=name[len(app):].split('$')[0].rstrip(';')
            c.require(policy['project_roots'].get(root,'INFINITY')=='INFINITY','EXISTING_PROJECT_OWNER_CONFLICT:'+name)
            policy['project_roots'][root]='INFINITY'
        else:
            matches=[owner for prefix,owner in policy['library_families'].items() if name.startswith(prefix)]
            c.require(not matches,'NEW_CAST_CODE_CANNOT_ENTER_EXISTING_SHARED_OR_COBRA_NAMESPACES:'+name)
            # Exact class prefixes: do not grant a broad existing namespace.
            policy['library_families'][name]='INFINITY'
    return policy
def rebuild_bundle(source,target,owner,version,replacements,new_classes,new_dex):
    inventory,cb,_,_,review=c.tools()
    with ZipFile(source) as old:
        meta=json.loads(old.read('component.json'));c.require(meta['owner']==owner,'OWNER_INPUT')
        changed={}
        for name,value in replacements.items():
            if review.member_owner(name)!=owner:continue
            digest=data_hash(value);normal=digest
            if name=='AndroidManifest.xml':normal=c.digest(cb.normalize_manifest(value)[0])
            prior=meta['members'].get(name,{})
            meta['members'][name]=dict(prior,sha256=digest,compress_type=prior.get('compress_type',ZIP_DEFLATED),external_attr=prior.get('external_attr',0o100644<<16))
            meta['payload']['member:'+name]=dict(owner=owner,sha256=normal);changed['payload/'+name]=value
        if owner=='INFINITY' and new_classes:
            for name,row in new_classes.items():
                key='class:'+name;c.require(key not in meta['payload'],'DUPLICATE_CAST_CLASS');meta['payload'][key]=dict(owner=owner,sha256=row['sha256'])
            c.require('dex/cast-private.dex' not in meta['dex'],'CAST_DEX_NOT_PREVIOUSLY_INSTALLED')
            meta['dex']['dex/cast-private.dex']=c.sha(new_dex);changed['dex/cast-private.dex']=new_dex
        meta['approved_source']=os.environ['GITHUB_SHA'];meta['version']=str(version)+'.'+owner.lower()+'.movies_cast_qa.1'
        meta['digest']=cb.component_digest(meta['payload'],owner)
        with ZipFile(target,'w',allowZip64=True) as out:
            for n in old.namelist():copy_entry(old,out,n,inventory.canonical(meta) if n=='component.json' else changed.pop(n,None))
            for n,value in changed.items():
                info=cb.record(n)
                with out.open(info,'w') as stream:
                    if isinstance(value,bytes):stream.write(value)
                    else:
                        with Path(value).open('rb') as source:shutil.copyfileobj(source,stream,2*1024*1024)
    return meta
def stage():
    c.context();r=c.load(c.HERE/'QA-RELEASE-REQUEST.json');c.require(r['operation']=='prepare-exact86-movies-home-cast-QA' and r['baseline_APK_sha256']==c.BASE,'EXACT_QA_REQUEST')
    c.require(c.sha(c.ROOT/c.WORKFLOW)==r['workflow_sha256'],'SOURCE_BOUND_PREPARATION_WORKFLOW')
    for n,wanted in r['source_bindings'].items():c.require(c.sha(c.ROOT/n)==wanted,'FROZEN_RELEASE_INPUT:'+n)
    live=c.api('git/ref/heads/'+c.CANONICAL)['object']['sha']
    c.require(live==r['registry_parent_source'],'REGISTRY_ADVANCED_RECONCILE_BEFORE_PREPARATION')
    registry=json.loads(c.git('show',live+':'+c.AUTHORITY));c.require(registry['candidate_versionCode']==2103487 and registry['generation']==72,'UNUSED88_89_AFTER_RECONCILED87')
    inputs={role:c.obtain(row,role) for role,row in r['inputs'].items()}
    base=c.unique(inputs['baseline'],'Infinity-2103486-Combined-Original-Signer.apk');c.require(c.sha(base)==c.BASE,'EXACT_SIGNED86_BASE');c.signature(base)
    owner_root=c.unique(inputs['owners'],'catalog.json').parent;catalog=c.load(owner_root/'catalog.json')
    exact86=json.loads(c.git('show','e1ef672a6f24aed6c19a14ab96d2df6fe3380460:'+c.AUTHORITY))
    c.require(catalog==exact86['bundle_catalog'],'EXACT_ACCEPTED86_OWNER_BUNDLES')
    native=c.unique(inputs['native'],'libkodi.so');c.require(c.sha(native)==c.NATIVE,'PASSED_ARM64_ENGINE')
    native_report=c.load(c.unique(inputs['native'],'CAST-ARM64.json'))
    c.require(native_report['status']=='PASS_FULL_REAL_ARM64_LINK_AND_BASELINE86_ABI' and native_report['native_sha256']==c.NATIVE,'REAL_ARM64_PROOF')
    native_sources=c.load(c.unique(inputs['native'],'CAST-SOURCE-PRESERVATION.json'))
    native_map=c.load(c.unique(inputs['native'],'NATIVE-SOURCE-MAP.json'))
    c.require(native_sources['unchanged86_native_files']==9410 and native_sources['shutdown_changed'] is False and native_sources['Cobra_changed'] is False,'EXACT_NATIVE_SCOPE')
    for p in (c.TASK/'native/overlay').rglob('*'):
        if p.is_file():c.require(c.sha(p)==native_map[p.relative_to(c.TASK/'native/overlay').as_posix()],'EXACT_COMPILED_NATIVE_SOURCE')
    component_root=c.unique(inputs['sdk'],'COMPONENT-RESULT.json').parent;component=c.load(component_root/'COMPONENT-RESULT.json')
    android=c.load(c.unique(inputs['sdk'],'ANDROID-CAST-COMPONENT.json'))
    c.require(android['pass'] is True and component['Cobra_owned_type_references']==[] and component['duplicate_classes']==[] and component['missing_baseline_APIs']==[],'PRIVATE_CAST_COMPONENT_CONTRACT')
    for n,wanted in component['feature_Java_sha256'].items():c.require(c.sha(c.TASK/'cast'/n)==wanted,'EXACT_COMPILED_CAST_JAVA:'+n)
    for n,wanted in component['build_inputs'].items():c.require(c.sha(c.TASK/n)==wanted,'EXACT_COMPILED_CAST_TOOL_OR_DEPENDENCY:'+n)
    for n,wanted in component['dex'].items():c.require(c.sha(component_root/'dex'/n)==wanted,'EXACT_COMPILED_CAST_DEX')
    c.require(len(component['dex'])==1,'ONE_APPEND_ONLY_CAST_DEX')
    inventory,cb,_,_,review=c.tools();out=c.ROOT/'movies-cast-prepared';out.mkdir(exist_ok=False)
    dex=c.unique(component_root/'dex','classes.dex');mini=out/'cast-class-fingerprint-input.zip'
    with ZipFile(mini,'w') as z:z.write(dex,'classes.dex')
    inventory.disassemble(mini,c.jars(),out/'cast-smali');classes,calls,_=inventory.parse_dex(out/'cast-smali')
    c.require(len(classes)==component['new_classes'],'ALL_ACTUAL_CAST_CLASSES_FINGERPRINTED')
    policy=json.loads(c.git('show','e1ef672a6f24aed6c19a14ab96d2df6fe3380460:repairs/dual-experience-isolation-2103420/ownership-reviewed-roots.json'))
    proposed=policy_for_new(classes,policy)
    for n,row in classes.items():c.require(review.class_owner(n,'',proposed)=='INFINITY','CAST_CLASS_OWNER')
    c.save(out/'OWNERSHIP-POLICY-PROPOSAL.json',proposed);c.save(out/'CAST-CLASSES.json',classes)
    module_root=c.unique(inputs['modules'],'ORIGINAL-SIGNATURE-VERIFICATION.json').parent
    public=c.ROOT/'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem'
    for kind,version in c.VERSIONS.items():
        dest=out/kind;dest.mkdir();owners=dest/'components';owners.mkdir();updates={};additions=set()
        with ZipFile(base) as z:
            module_path=module_root/kind/'modules'
            record=c.load(module_root/kind/'INPUTS.json')
            for p in module_path.rglob('*'):
                if p.is_file():
                    relative=p.relative_to(module_path).as_posix();name='assets/addons/'+relative
                    updates[name]=p
                    if name not in z.namelist():additions.add(name)
                    if p.name!='INFINITY-MODULES.v1.sig':c.require(c.sha(p)==record['modules'][relative],'SIGNED_MODULE_BYTES')
            for name in ('experience.py','plugin.py','service.py','default.py','cast_runtime.py'):
                if kind=='candidate':c.require((module_path/CC/name).read_bytes()==(c.TASK/'overlay'/CC/name).read_bytes(),'FROZEN_MODULE_SOURCE')
            manifest=module_path/CC/'INFINITY-MODULES.v1'
            subprocess.run(['openssl','dgst','-sha256','-verify',public,'-signature',str(manifest)+'.sig',manifest],check=True,capture_output=True)
            updates.update(skin_files(z,kind))
            updates[LABEL]=('infinity.last_updated_in='+str(version)+'\ncobra.last_updated_in=2103445\n').encode()
            raw=z.read('AndroidManifest.xml');raw=patch_cast_manifest.patch(raw) if kind=='candidate' else raw
            updates['AndroidManifest.xml']=cb.set_version(raw,version)
            if kind=='candidate':
                updates[LIB]=native;updates['classes6.dex']=dex;additions.add('classes6.dex')
                for name in ('resources.apk','RESOURCE-IDENTITY.json'):updates['assets/infinity/cast/'+name]=component_root/name
                for name,wanted in component['private_resources'].items():
                    p=component_root/'private-resources'/name;c.require(c.sha(p)==wanted,'PRIVATE_RESOURCE_BYTES');updates[name]=p
            additions|={n for n in updates if n not in z.namelist()}
            package=dest/('Infinity-'+str(version)+'-UNSIGNED-NOT-INSTALLABLE.apk')
            with ZipFile(package,'w',allowZip64=True) as target:
                for name in z.namelist():
                    if name not in inventory.SIGNATURE:copy_entry(z,target,name,updates.get(name))
                for name in sorted(additions):
                    info=cb.record(name);value=updates[name]
                    with target.open(info,'w') as stream:
                        if isinstance(value,bytes):stream.write(value)
                        else:
                            with Path(value).open('rb') as source:shutil.copyfileobj(source,stream,2*1024*1024)
        proof=compare(base,package,updates,additions,version)
        owner_updates={n:v for n,v in updates.items() if not re.fullmatch(r'classes\d*\.dex',n)}
        new_catalog=copy.deepcopy(catalog);new_catalog['source']=os.environ['GITHUB_SHA'];new_catalog['release_approved']=False
        for owner in cb.OWNED:
            row=new_catalog['bundles'][owner];src=owner_root/row['file'];target=owners/row['file']
            if owner=='COBRA':shutil.copyfile(src,target);c.require(c.sha(target)==c.sha(src),'COBRA_BUNDLE_BYTES_FROZEN')
            else:
                meta=rebuild_bundle(src,target,owner,version,owner_updates,classes if kind=='candidate' else {},dex)
                row.update(sha256=c.sha(target),**{key:meta[key] for key in ('version','digest','approved_source')})
            cb.read_bundle(target,row)
        (owners/'catalog.json').write_bytes(inventory.canonical(new_catalog))
        proof.update(status='PASS_EXACT86_APPROVED_MEMBER_LIST',source=os.environ['GITHUB_SHA'],kind=kind,versionCode=version,baseline_APK_sha256=c.BASE,unsigned_sha256=c.sha(package),Cobra_bundle_sha256=catalog['bundles']['COBRA']['sha256'],owner_acceptance='NOT_RUN',signed=False)
        c.save(dest/'PRESERVATION.json',proof)
    shutil.rmtree(out/'cast-smali');mini.unlink()
    c.save(out/'PREPARATION.json',dict(schema=1,status='PASS_BOTH_EXACT86_QA_AND_FORWARD_RECOVERY_PREPARATION',source=os.environ['GITHUB_SHA'],registry_mutated=False,original_key_used=False,inputs=r['inputs'],APK_versions_provisional=c.VERSIONS,owner_acceptance='NOT_RUN'))
    print('PASS_COMPLETE_UNSIGNED_QA_AND_FORWARD_RECOVERY; ORIGINAL_FIVE_DEX_AND_COBRA_FROZEN')
if __name__=='__main__':stage()
