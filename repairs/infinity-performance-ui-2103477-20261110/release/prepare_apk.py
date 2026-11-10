"""Performance owner-bundle adapter using the unchanged original assembler.

No signing, registry writes, native compilation, or Android tests. All payload
bytes originate in exact signed77 except reviewed modules and version metadata.
"""
from pathlib import Path
import argparse
import copy
import json
import re
import shutil
import subprocess
from zipfile import ZipFile
import prepare_modules as prep

SKIN='skin.infinity.diggz'
NATIVE='lib/arm64-v8a/libkodi.so'
ENGINE='ee3be7c7a95b86f8357539001fcd50bedbd80217b02f130d649f7f57e6075794'
LABELS='assets/experience-component-updates.properties'
CANONICAL='bd46fa73c713ed869f75822fab1b0821a7d2d11b'
MODULE_SOURCE='7b84194eed8f0a6d5d07739e2f6ba041e816a79a'
MODULE_ARCHIVE='cfd616ddf63c43c25d6400b228af8ff8090ba5c40820de7adb5de5eff34e20ad'
TARGETS=('INFINITY','CHOOSER_SHELL')

def load(path):return json.loads(path.read_bytes())
def authority():return json.loads(subprocess.check_output(['git','show',CANONICAL+':repairs/dual-experience-isolation-2103420/release-authority.json'],cwd=prep.ROOT))
def allowed(recovery):
    cc='assets/addons/'+prep.CC+'/';skin='assets/addons/'+SKIN+'/'
    return {'AndroidManifest.xml',LABELS,*(cc+n for n in ('addon.xml','INFINITY-MODULES.v1','INFINITY-MODULES.v1.sig')),*(skin+n for n in ('addon.xml','infinity-skin.json','Infinity-Protected-Manifest.json'))}|(set() if recovery else {cc+'common.py',cc+'service.py'})

def scalar(raw,key,before,after):
    old=('"'+key+'": '+json.dumps(before)).encode();new=('"'+key+'": '+json.dumps(after)).encode()
    assert raw.count(old)==1,('EXACT_METADATA_PREIMAGE',key)
    return raw.replace(old,new,1)

def skin_metadata(original,version):
    baseline={n:original.read('assets/addons/'+SKIN+'/'+n) for n in ('addon.xml','infinity-skin.json','Infinity-Protected-Manifest.json')}
    addon=baseline['addon.xml'];assert addon.count(b'version="1.0.5.270"')==1
    addon=addon.replace(b'version="1.0.5.270"',('version="'+version+'"').encode(),1)
    skin=baseline['infinity-skin.json'];number=int(version.rsplit('.',1)[1])
    for key,old,new in [('candidate',270,number),('skin_version','1.0.5.270',version),('version','1.0.5.270',version)]:skin=scalar(skin,key,old,new)
    raw=baseline['Infinity-Protected-Manifest.json'];before=json.loads(raw);assert len(before['protected_files'])==948
    updated={'addon.xml':addon,'infinity-skin.json':skin}
    for name,value in updated.items():
        old=('"'+name+'": "'+before['protected_files'][name]+'"').encode();new=('"'+name+'": "'+prep.sha(value)+'"').encode();assert raw.count(old)==1;raw=raw.replace(old,new,1)
    for key,old,new in [('candidate',270,number),('skin_version','1.0.5.270',version),('candidate_version','1.0.5.270',version)]:raw=scalar(raw,key,old,new)
    after=json.loads(raw);assert set(after['protected_files'])==set(before['protected_files'])
    assert {n for n in before['protected_files'] if before['protected_files'][n]!=after['protected_files'][n]}==set(updated)
    for name,wanted in after['protected_files'].items():
        value=updated[name] if name in updated else original.read('assets/addons/'+SKIN+'/'+name)
        assert prep.sha(value)==wanted,name
    updated['Infinity-Protected-Manifest.json']=raw
    return updated

def compare(baseline,candidate,proof):
    t=prep.tools();assert prep.sha(baseline.read_bytes())==prep.BASE_APK
    with ZipFile(baseline) as a,ZipFile(candidate) as b:
        old=set(t.validate_names(a))-t.SIGNATURE;new=set(t.validate_names(b))-t.SIGNATURE
        assert new==old,'NO_PAYLOAD_MEMBER_ADDITION_OR_REMOVAL'
        differences={}
        for name in sorted(new):
            after=b.read(name)
            if a.read(name)!=after:
                assert name in allowed(proof['recovery']),name
                assert prep.sha(after)==proof['changed_members'][name],name
                differences[name]=prep.sha(after)
            if name=='AndroidManifest.xml':assert t.normalize_manifest(after)==(t.normalize_manifest(a.read(name))[0],proof['versionCode'])
        assert differences==proof['changed_members'] and set(differences)==allowed(proof['recovery'])
        assert prep.sha(b.read(NATIVE))==ENGINE
        dex={n:prep.sha(b.read(n)) for n in new if re.fullmatch(r'classes\d*\.dex',n)}
        assert dex=={n:prep.sha(a.read(n)) for n in dex}
    return dict(status='PASS_EXACT77_TWO_FILE_PERFORMANCE_OR_FORWARD_RECOVERY',baseline_sha256=prep.BASE_APK,candidate_sha256=prep.sha(candidate.read_bytes()),changed_members=differences,added_members=[],all_DEX_unchanged=dex,all_native_unchanged=True,all_layout_provider_Cobra_members_unchanged=True,APK_signing='NOT_VERIFIED_BY_COMPARISON',Android='NOT_RUN_BY_PREPARATION',physical_Fold='PENDING')

def prepare(apk,module_fixture,components,out,candidate_version,recovery_version):
    assert not out.exists() and candidate_version>2103479 and recovery_version>candidate_version
    assert prep.sha(apk.read_bytes())==prep.BASE_APK
    assert prep.sha((module_fixture.parent/'artifact.zip').read_bytes())==MODULE_ARCHIVE
    t=prep.tools();previous=authority();catalog=load(components/'catalog.json')
    historical=json.loads(subprocess.check_output(['git','show','dfee7205dd88abe81db5e263c368f67ece43df02:repairs/dual-experience-isolation-2103420/release-authority.json'],cwd=prep.ROOT))
    assert catalog==historical['bundle_catalog'],'ORIGINAL_OFFICIAL75_OWNERSHIP_CATALOG'
    metas={o:t.read_bundle(components/row['file'],row) for o,row in catalog['bundles'].items()}
    for owner in ('COBRA','MINIMAL_ANDROID_CONTRACT'):assert catalog['bundles'][owner]==previous['bundle_catalog']['bundles'][owner]
    prepared=module_fixture/'performance-module-prepared';stage=load(prepared/'PREPARATION.json')
    audit_path=module_fixture/'performance-module-audit/MODULE-UPGRADE-RECOVERY.json';audit=load(audit_path)
    assert audit['status']=='PASS_FOUR_AFFECTED_ORIGINAL_INSTALLER_CASES' and audit['original_installer_changed'] is False
    assert stage['source_commit']==MODULE_SOURCE and stage['networking_inputs'] is False
    expected=load(prep.HERE/'MODULE-PREPARE-REQUEST.json')['expected_outputs']
    source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=prep.ROOT,text=True).strip();records={}
    with ZipFile(apk) as original:
        baseline_names=set(t.validate_names(original))-t.SIGNATURE
        member_names={n for m in metas.values() for n in m['members']}
        order=sorted(((o,n) for o,m in metas.items() for n in m['dex']),key=lambda x:(('CHOOSER_SHELL','MINIMAL_ANDROID_CONTRACT','INFINITY','COBRA').index(x[0]),x[1]))
        dex_names=['classes'+(str(i) if i>1 else '')+'.dex' for i in range(1,len(order)+1)]
        assert baseline_names==member_names|set(dex_names)
        for (owner,name),actual in zip(order,dex_names):assert prep.sha(original.read(actual))==metas[owner]['dex'][name]
        for owner in ('COBRA','MINIMAL_ANDROID_CONTRACT'):
            with ZipFile(components/catalog['bundles'][owner]['file']) as z:
                for name in metas[owner]['members']:
                    before,actual=z.read('payload/'+name),original.read(name)
                    assert (t.normalize_manifest(before)[0]==t.normalize_manifest(actual)[0] if name=='AndroidManifest.xml' else before==actual),name
        for (label,cc_version),version,skin_version in zip(prep.PAIRS,(candidate_version,recovery_version),('1.0.5.273','1.0.5.274')):
            work=out/str(version);bundles=work/'components';bundles.mkdir(parents=True)
            pins=load(prepared/label/'INPUTS.json');assert prep.sha((prepared/label/'INPUTS.json').read_bytes())==stage['inputs'][label]
            for key,wanted in expected[label].items():assert pins[key]==wanted,key
            modules=prepared/label/'modules';current=prep.hashes(modules)
            assert {n:v for n,v in current.items() if n!=prep.CC+'/INFINITY-MODULES.v1.sig'}==pins['modules']
            manifest,files=t.module_bundle.build(modules);assert len(files)==80 and prep.sha(manifest)==pins['manifest_sha256']
            assert manifest==(modules/prep.CC/'INFINITY-MODULES.v1').read_bytes()
            subprocess.run(['openssl','dgst','-sha256','-verify',str(prep.ROOT/'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem'),'-signature',str(modules/prep.CC/'INFINITY-MODULES.v1.sig'),str(modules/prep.CC/'INFINITY-MODULES.v1')],check=True,capture_output=True)
            replacements={'assets/addons/'+n:(modules/n).read_bytes() for n in current}
            replacements.update({'assets/addons/'+SKIN+'/'+n:raw for n,raw in skin_metadata(original,skin_version).items()})
            replacements[LABELS]=('infinity.last_updated_in='+str(version)+'\ncobra.last_updated_in=2103445\n').encode()
            changes={n:prep.sha(raw) for n,raw in replacements.items() if original.read(n)!=raw}
            changes['AndroidManifest.xml']=prep.sha(t.set_version(original.read('AndroidManifest.xml'),version))
            assert set(changes)==allowed(label=='recovery')
            new_catalog=copy.deepcopy(catalog);new_catalog.update(source=source,release_approved=False)
            for owner,old in metas.items():
                if owner not in TARGETS:
                    shutil.copyfile(components/catalog['bundles'][owner]['file'],bundles/catalog['bundles'][owner]['file']);continue
                meta=copy.deepcopy(old);meta.update(version=f'{version}.{owner.lower()}.performance.1',approved_source=source)
                path=bundles/(owner+'.zip')
                with ZipFile(path,'w') as target,ZipFile(components/catalog['bundles'][owner]['file']) as previous_bundle:
                    for name in sorted(meta['dex']):target.writestr(t.record(name),previous_bundle.read(name))
                    for name in sorted(meta['members']):
                        raw=replacements[name] if name in replacements else original.read(name);info=original.getinfo(name)
                        meta['members'][name]=dict(sha256=prep.sha(raw),compress_type=info.compress_type,external_attr=info.external_attr)
                        normalized=t.normalize_manifest(raw)[0] if name=='AndroidManifest.xml' else raw
                        meta['payload']['member:'+name]=dict(owner=owner,sha256=prep.sha(normalized))
                        target.writestr(t.record('payload/'+name),raw)
                    meta['digest']=t.component_digest(meta['payload'],owner);target.writestr(t.record('component.json'),t.canonical(meta))
                row={k:meta[k] for k in ('version','digest','approved_source','settings_schema')};row.update(file=path.name,sha256=prep.sha(path.read_bytes()));new_catalog['bundles'][owner]=row
            prep.save(bundles/'catalog.json',new_catalog);unsigned=work/'combined-unsigned.apk';assembly=t.combine(bundles,new_catalog,unsigned,version)
            proof=dict(versionCode=version,source_commit=source,baseline_versionCode=2103477,baseline_sha256=prep.BASE_APK,native_sha256=ENGINE,CC=cc_version,skin=skin_version,recovery=label=='recovery',changed_members=changes,source_files_added=[],original_module_audit_sha256=prep.sha(audit_path.read_bytes()),module_manifest_sha256=pins['manifest_sha256'],module_count=80,unsigned_sha256=assembly['unsigned_apk_sha256'],version_reserved=False,networking_inputs=False,public_release=False,Android='PENDING_SIGNED_APK_CHECK',physical_Fold='PENDING',original_APK_signing='PENDING_REGISTERED_ORIGINAL_SIGNER')
            prep.save(work/'PREPARATION.json',proof);prep.save(work/'APK-PRESERVATION.json',compare(apk,unsigned,proof));shutil.copyfile(audit_path,work/'MODULE-UPGRADE-RECOVERY.json')
            records[str(version)]=dict(preparation=prep.sha((work/'PREPARATION.json').read_bytes()),preservation=prep.sha((work/'APK-PRESERVATION.json').read_bytes()),catalog=prep.sha((bundles/'catalog.json').read_bytes()))
    prep.save(out/'PAIR-PREPARATION.json',dict(status='UNSIGNED_SOURCE_BOUND_77_PERFORMANCE_FORWARD_PAIR',baseline=2103477,prior_canonical=CANONICAL,source=source,preparations=records,registry_mutation=False,APK_signing=False,Android='PENDING',owner_delivery_cleared=False))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('apk','module-fixture','components','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--candidate-version',type=int,required=True);p.add_argument('--recovery-version',type=int,required=True)
    prepare(**vars(p.parse_args()))
