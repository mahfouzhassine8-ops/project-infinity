"""Original397 QA input/preservation gate. The unchanged assembler signs."""
from pathlib import Path
from zipfile import ZipFile
import copy,json,os,re,subprocess,sys
import common_release as c
import prepare_release as p
import release_guard

OWNERS=['INFINITY','CHOOSER_SHELL','MINIMAL_ANDROID_CONTRACT']
LOCK='e1ef672a6f24aed6c19a14ab96d2df6fe3380460'
def request(canonical=True):
    c.context(canonical);r=c.load(c.HERE/'QA-RELEASE-REQUEST.json')
    c.require(r['operation']=='prepare-exact86-movies-home-cast-QA' and r['baseline_APK_sha256']==c.BASE and
              r['owner_acceptance_after_signing'] is True and r['accepted_pointer_updated'] is False,'EXACT_OWNER_QA_SCOPE')
    for n,wanted in r['source_bindings'].items():c.require(c.sha(c.ROOT/n)==wanted,'FROZEN_REVIEWED_SOURCE:'+n)
    c.require(c.sha(c.ROOT/c.WORKFLOW)==r['workflow_sha256'],'EXACT_ORIGINAL_WORKFLOW_SOURCE')
    for name in ('assemble.py','component_bundles.py','release_gate.py','inventory.py','review_ownership.py','signer_policy.py'):
        path='repairs/dual-experience-isolation-2103420/'+name
        c.require((c.ROOT/path).read_bytes()==c.git('show',LOCK+':'+path),'ORIGINAL_SIGNER_OR_GUARD_CHANGED:'+name)
    return r
def prepared(r):
    root=c.obtain(r['prepared_producer'],'prepared')
    receipt=c.load(c.unique(root,'PREPARATION.json'));c.require(receipt['source']==r['prepared_producer']['source'] and receipt['status']=='PASS_BOTH_EXACT86_QA_AND_FORWARD_RECOVERY_PREPARATION' and receipt['inputs']==r['inputs'],'EXACT_PREPARED_PAIR')
    return c.unique(root,'PREPARATION.json').parent
def expected_apk(r,kind):
    inventory,cb,_,_,_=c.tools()
    base=c.unique(c.obtain(r['inputs']['baseline'],'baseline'),'Infinity-2103486-Combined-Original-Signer.apk')
    c.require(c.sha(base)==c.BASE,'EXACT_ACCEPTED86_APK');c.signature(base)
    modules=c.unique(c.obtain(r['inputs']['modules'],'modules'),'ORIGINAL-SIGNATURE-VERIFICATION.json').parent/kind/'modules'
    component=c.unique(c.obtain(r['inputs']['sdk'],'sdk'),'COMPONENT-RESULT.json').parent
    sdk=c.load(component/'COMPONENT-RESULT.json')
    c.require(sdk['duplicate_classes']==[] and sdk['Cobra_owned_type_references']==[] and sdk['missing_baseline_APIs']==[],'EXACT_PRIVATE_CAST_CODE')
    for n,h in sdk['feature_Java_sha256'].items():c.require(c.sha(c.TASK/'cast'/n)==h,'COMPILED_CAST_SOURCE:'+n)
    updates={};added=set()
    with ZipFile(base) as z:
        before=set(inventory.validate_names(z))-inventory.SIGNATURE
        for file in modules.rglob('*'):
            if file.is_file():updates['assets/addons/'+file.relative_to(modules).as_posix()]=file
        if kind=='candidate':
            for name in p.CHANGED if hasattr(p,'CHANGED') else ('experience.py','plugin.py','service.py','default.py','cast_runtime.py'):
                c.require((modules/p.CC/name).read_bytes()==(c.TASK/'overlay'/p.CC/name).read_bytes(),'EXACT_NEW_MODULE_SOURCE')
        public=c.ROOT/'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem'
        manifest=modules/p.CC/'INFINITY-MODULES.v1'
        subprocess.run(['openssl','dgst','-sha256','-verify',public,'-signature',str(manifest)+'.sig',manifest],capture_output=True,check=True)
        updates.update(p.skin_files(z,kind))
        version=c.VERSIONS[kind]
        updates[p.LABEL]=('infinity.last_updated_in='+str(version)+'\ncobra.last_updated_in=2103445\n').encode()
        raw=z.read('AndroidManifest.xml')
        if kind=='candidate':raw=p.patch_cast_manifest.patch(raw)
        updates['AndroidManifest.xml']=cb.set_version(raw,version)
        if kind=='candidate':
            for name in ('resources.apk','RESOURCE-IDENTITY.json'):updates['assets/infinity/cast/'+name]=component/name
            for name,wanted in sdk['private_resources'].items():
                file=component/'private-resources'/name;c.require(c.sha(file)==wanted,'PRIVATE_RESOURCE_HASH');updates[name]=file
            updates['classes6.dex']=component/'dex/classes.dex'
        added=set(updates)-before
    wanted={n:p.data_hash(value) for n,value in updates.items()}
    if kind=='candidate':wanted[p.LIB]=c.NATIVE
    return base,wanted,added
def verify_apk(r,kind,apk):
    inventory,cb,_,_,_=c.tools();base,wanted,added=expected_apk(r,kind)
    with ZipFile(base) as old,ZipFile(apk) as new:
        names=set(inventory.validate_names(old))-inventory.SIGNATURE
        c.require(set(inventory.validate_names(new))-inventory.SIGNATURE==names|added,'EXACT_BASE86_PLUS_APPROVED_ADDITIONS')
        changed={};unchanged=0
        for name in sorted(names|added):
            a=p.member_sha(old,name) if name in names else None;b=p.member_sha(new,name)
            c.require(b==wanted.get(name,a),'OUT_OF_SCOPE_APK_MEMBER:'+name)
            if a!=b:changed[name]=dict(before=a,after=b)
            else:unchanged+=1
        c.require(all(name not in changed for name in names if re.fullmatch(r'classes\d*\.dex',name)),'ORIGINAL_DEX_CHANGED')
        c.require(cb.normalize_manifest(new.read('AndroidManifest.xml'))[1]==c.VERSIONS[kind],'EXACT_TYPED_APK_VERSION')
        # Any original addon/module outside the complete approved source set is
        # covered by the same whole-member equality above, never an exemption.
    return dict(status='PASS_ORIGINAL_SIGNED86_EXACT_APPROVED_MEMBER_VECTOR',baseline_APK_sha256=c.BASE,
        kind=kind,versionCode=c.VERSIONS[kind],changed_members=changed,added_members=sorted(added),
        unchanged_payload_members=unchanged,original_five_DEX_unchanged=True,Cobra_changed=False,
        shutdown_source_changed=False,Python_startup_changed=False,provider_implementations_changed=False,
        existing_profile_or_databases_accessed=False,owner_acceptance='PENDING_ONE_COMBINED_FOLD_SESSION')
def propose():
    r=request();kind=r['active_kind'];c.require(kind in c.VERSIONS,'EXACT_RELEASE_KIND')
    root=prepared(r);package=root/kind/('Infinity-'+str(c.VERSIONS[kind])+'-UNSIGNED-NOT-INSTALLABLE.apk')
    proof=verify_apk(r,kind,package);inventory,cb,ra,_,_=c.tools()
    current=c.load(c.ROOT/c.AUTHORITY)
    c.require(c.sha(c.ROOT/c.AUTHORITY)==r['parent_authority_sha256'] and
              current['generation']==c.GENERATIONS[kind]-1 and current['candidate_versionCode']==c.VERSIONS[kind]-1,'EXACT_RECONCILED_PARENT')
    c.require(c.api('git/ref/heads/'+c.CANONICAL)['object']['sha']==os.environ['GITHUB_SHA'],'CURRENT_CANONICAL_HEAD')
    policy=c.load(c.CORE/'ownership-reviewed-roots.json');proposal=c.load(root/'OWNERSHIP-POLICY-PROPOSAL.json')
    c.require(policy==proposal,'EXACT_REVIEWED_PRIVATE_CAST_OWNER_ADDITIONS')
    old_policy=json.loads(c.git('show',LOCK+':repairs/dual-experience-isolation-2103420/ownership-reviewed-roots.json'))
    for key,value in old_policy.items():
        if isinstance(value,dict):c.require(all(policy[key].get(n)==v for n,v in value.items()),'NO_EXISTING_OWNER_RELABEL')
        else:c.require(policy[key]==value,'OLD_POLICY_FIELD_FROZEN')
    catalog=c.load(root/kind/'components/catalog.json')
    meta={o:cb.read_bundle(root/kind/'components'/catalog['bundles'][o]['file'],catalog['bundles'][o]) for o in cb.OWNED}
    payload={n:v for m in meta.values() for n,v in m['payload'].items()}
    result=copy.deepcopy(current)
    result.update(generation=c.GENERATIONS[kind],candidate_versionCode=c.VERSIONS[kind],
        last_issued_versionCode=max(current['candidate_versionCode'],current['last_issued_versionCode']),
        previous_authority_sha256=inventory.digest(inventory.canonical(current)),target_owners=OWNERS,
        update_kind='owner_update',payload=payload,bundle_catalog=catalog,
        experience_version_labels={'INFINITY':c.VERSIONS[kind],'COBRA':2103445},
        workflow_sha256=c.sha(c.ROOT/c.WORKFLOW))
    for owner in OWNERS:
        result['components'][owner]={key:meta[owner][key] for key in ('version','digest','approved_source','settings_schema')}
        result['components'][owner]['revision']=current['components'][owner]['revision']+1
        result['bundle_sources'][owner]=dict(run_id=r['prepared_producer']['run'],build_source=r['prepared_producer']['source'],artifact=r['prepared_producer']['name'],path=kind+'/components/'+owner+'.zip')
    for name in result['source_files']:result['source_files'][name]=c.sha(c.ROOT/name)
    result['cast_manifest_exception']=dict(schema=1,mode=kind,baseline_APK_sha256=c.BASE,
        reference=release_guard.REFERENCE,reference_sha256=release_guard.REFERENCE_SHA,
        baseline_normalized_sha256=release_guard.NORMALIZED,candidate_manifest_sha256=release_guard.expected(kind),
        source_inputs={name:c.sha(c.ROOT/name) for name in release_guard.SOURCE_NAMES})
    result['owner_update_evidence']=dict(owner='INFINITY_MOVIES_CONTINUE_CAST_QA_'+kind.upper(),
        producer_run=r['prepared_producer']['run'],producer_source=r['prepared_producer']['source'],
        artifact={key:r['prepared_producer'][key] for key in ('id','name','digest','size_in_bytes')},
        source_files=dict(r['source_bindings'],**{(c.HERE/'QA-RELEASE-REQUEST.json').relative_to(c.ROOT).as_posix():c.sha(c.HERE/'QA-RELEASE-REQUEST.json')}),
        baseline_APK_sha256=c.BASE,preparation_sha256=c.sha(root/kind/'PRESERVATION.json'),
        Fold='OWNER_ACCEPTANCE_AFTER_SIGNING',Cast_receiver='OWNER_ACCEPTANCE_AFTER_SIGNING',
        original_five_DEX_unchanged=True,Cobra_changed=False,shutdown_source_changed=False,
        accepted_pointer_updated=False,publication=False,public_release=False,owner_delivery_cleared=False,
        verification_toolchain=current['owner_update_evidence']['verification_toolchain'])
    ra.transition(current,result,OWNERS);ra.verify_evidence(result,lambda n:(c.ROOT/n).read_bytes())
    ra.verify(result,{n:v['sha256'] for n,v in payload.items()},c.VERSIONS[kind],c.GENERATIONS[kind])
    out=c.ROOT/'movies-cast-authority';out.mkdir(exist_ok=False)
    (out/'AUTHORITY-PROPOSAL.json').write_bytes(inventory.canonical(result));c.save(out/'PRESERVATION.json',proof)
    print('PASS_EXACT_SOURCE_BOUND_AUTHORITY_PROPOSAL; NO_KEY_ACCESS_OR_ACCEPTANCE')
def admit():
    r=request();kind=r['active_kind'];a=c.load(c.ROOT/c.AUTHORITY)
    c.require(a['generation']==c.GENERATIONS[kind] and a['candidate_versionCode']==c.VERSIONS[kind] and
              a['owner_update_evidence']['owner']=='INFINITY_MOVIES_CONTINUE_CAST_QA_'+kind.upper(),'EXACT_REGISTERED_QA_OWNER')
    inventory,cb,ra,gate,_=c.tools()
    ra.validate(a);ra.verify_evidence(a,lambda n:(c.ROOT/n).read_bytes())
    root=prepared(r);apk=root/kind/('Infinity-'+str(c.VERSIONS[kind])+'-UNSIGNED-NOT-INSTALLABLE.apk')
    c.require(c.sha(apk)==c.load(root/kind/'PRESERVATION.json')['unsigned_sha256'],'FROZEN_UNSIGNED_APK')
    verify_apk(r,kind,apk)
    return r,apk
def inputs():
    r,apk=admit()
    with Path(os.environ['GITHUB_OUTPUT']).open('a') as output:output.write('apk='+str(apk.relative_to(c.ROOT))+'\ngeneration='+str(c.GENERATIONS[r['active_kind']])+'\n')
    c.jars()
def post():
    r=request();kind=r['active_kind'];folder=c.ROOT/'movies-cast-original-signed'
    apk=folder/('Infinity-'+str(c.VERSIONS[kind])+'-Combined-Original-Signer.apk')
    receipt=c.load(folder/'BUILD-RECEIPT.json')
    c.require(receipt['signed_apk_sha256']==c.sha(apk) and receipt['certificate_sha256']==c.CERT,'ACTUAL_SIGNED_RECEIPT')
    text=c.signature(apk);proof=verify_apk(r,kind,apk);proof.update(APK_sha256=c.sha(apk),certificate_sha256=c.CERT,source=os.environ['GITHUB_SHA'],original_signer_workflow=397702717)
    c.save(folder/'PRESERVATION.json',proof);(folder/'SIGNATURE.txt').write_text(text)
    (folder/'SHA256SUMS').write_text(c.sha(apk)+'  '+apk.name+'\n')
if __name__=='__main__':
    c.require(len(sys.argv)==2,'EXACT_GATE_OPERATION')
    {'propose':propose,'admit':admit,'inputs':inputs,'post':post}[sys.argv[1]]()
