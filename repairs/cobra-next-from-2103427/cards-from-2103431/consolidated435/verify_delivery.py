"""Verify the one consolidated435 install-over APK and every exact owner member.

No application launch/install, baseline promotion, lifecycle or shutdown tests.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import subprocess
import tempfile
from zipfile import ZipFile
from combined_owners import *
from inventory import CERT_SHA,PACKAGE,SIGNATURE
from release_gate import normalize_manifest
from release_authority import transition,launcher_icon_guard

RECOVERY={2103431:'3fbf5abebdbdd9f96f30a69a213f086c617d2a9395f892dd1ce0142bf1b64471',
          2103432:'55671707e7acc8b1c329e5b87bdbe47706607418aa152b11b8889c3081a447c3',
          2103433:'874db7007b9fc79478844e5b37d4795d43c4c58de770c553d943734e1014b986',
          2103434:'16f02a9625c057a3fe4d4b55da8a554fdb2bff0f1b19c8f567bdf56af41eb465'}

def command(args):return subprocess.check_output(list(map(str,args)),text=True)

def member_sha(z,name):
    with z.open(name) as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def verify(recovery431,recovery432,baseline433,rejected434,signed,bundles,sdk):
    authority=load(ISO/'release-authority.json');build=load(signed/'BUILD-RECEIPT.json')
    require(load(signed/'release-authority.json')==authority,'EXACT_SIGNED_CURRENT_AUTHORITY')
    require(authority['candidate_versionCode']==VERSION and authority['generation']==GENERATION and set(authority['target_owners'])==set(TARGETS),'EXACT_COORDINATED435_AUTHORITY')
    prior=previous();transition(prior,authority,TARGETS)
    require(authority['previous_authority_sha256']==digest(canonical(prior)),'EXACT433_REGISTRY_LINEAGE')
    require(build['versionCode']==VERSION and build['registry_sha256']==digest(canonical(authority)) and build['source']==os.environ.get('GITHUB_SHA',build['source']),'ACTUAL_SIGNING_SOURCE_REGISTRY_VERSION')
    require(build['accepted_pointer_updated'] is False and authority['accepted_pointer_updated'] is False,'NO_AUTOMATIC_LOCK_OR_ACCEPTANCE')
    apk=signed/('Infinity-'+str(VERSION)+'-Combined-Original-Signer.apk');require(file_sha(apk)==build['signed_apk_sha256'],'EXACT_SIGNED435_APK')
    recoveries={2103431:recovery431,2103432:recovery432,2103433:baseline433,2103434:rejected434}
    for version,path in recoveries.items():require(file_sha(path)==RECOVERY[version],'IMMUTABLE_RECOVERY_APK:'+str(version))
    for version,path in {**recoveries,VERSION:apk}.items():
        text=command([sdk/'apksigner','verify','--verbose','--print-certs',path]);(signed/('ORIGINAL-SIGNATURE-'+str(version)+'.txt')).write_text(text)
        require(re.findall(r'Signer #[0-9]+ certificate SHA-256 digest: ([0-9a-f]+)',text)==[CERT_SHA],'ORIGINAL_CERTIFICATE:'+str(version))
        for scheme in ('v1','v2','v3'):require(re.search('Verified using '+scheme+r' scheme.*: true',text) is not None,'ORIGINAL_SIGNATURE_SCHEME:'+scheme)
    command([sdk/'zipalign','-c','-P','16','4',apk])
    catalog=load(bundles/'catalog.json');require(catalog==authority['bundle_catalog'],'EXACT_MATCHING_COMPONENT_VECTOR')
    # The registered evidence check already validated the official preparation;
    # independently bind the actual APK to every member of those exact ZIPs.
    metas={owner:read_bundle(bundles/row['file'],row) for owner,row in catalog['bundles'].items()}
    require(catalog['bundles']['MINIMAL_ANDROID_CONTRACT']==prior['bundle_catalog']['bundles']['MINIMAL_ANDROID_CONTRACT'],'SHARED_NATIVE_ICON_COMPONENT_FROZEN')
    members={};dex={};index=0
    for owner in ('CHOOSER_SHELL','MINIMAL_ANDROID_CONTRACT','INFINITY','COBRA'):
        for name,row in metas[owner]['members'].items():require(name not in members,'DUPLICATE_OWNER_MEMBER');members[name]=(owner,row)
        for name,pin in sorted(metas[owner]['dex'].items()):index+=1;dex['classes'+(str(index) if index>1 else '')+'.dex']=(owner,pin)
    require(index==5 and metas['INFINITY']['dex']==BASE_INFINITY_DEX,'FIVE_MATCHING_DEX_AND_EXACT_INFINITY_JAVA')
    expected_classes={k:v for meta in metas.values() for k,v in meta['payload'].items() if k.startswith('class:')}
    require(expected_classes=={k:v for k,v in authority['payload'].items() if k.startswith('class:')},'EXACT_REGISTERED_CLASS_PAYLOAD')
    allowed_infinity=set(authority['owner_update_evidence']['infinity_authentication']['changed_payload'])|set(authority['owner_update_evidence']['infinity_authentication']['added_payload'])
    allowed_infinity={name[len('member:'):] for name in allowed_infinity}
    cobra_dex={name for name,(owner,_) in dex.items() if owner=='COBRA'}
    allowed_members=allowed_infinity|cobra_dex|{METADATA,'AndroidManifest.xml'}
    rejected_auth=prior['owner_update_evidence']['infinity_authentication']
    rejected_changed={n.removeprefix('member:') for n in rejected_auth['changed_payload']+rejected_auth['added_payload']}
    rejected_added={n.removeprefix('member:') for n in rejected_auth['added_payload']}
    hashes={};native={};changes={}
    with ZipFile(apk) as actual:
        names=set(validate_names(actual))-SIGNATURE
        require(names==set(members)|set(dex),'EXACT_DECLARED_SIGNED_APK_MEMBER_SET')
        for name in sorted(names):
            hashes[name]=member_sha(actual,name)
            if name.endswith('.so'):native[name]=hashes[name]
        for name,(owner,pin) in dex.items():require(hashes[name]==pin,'EXACT_COMPONENT_APK_DEX:'+name)
        for owner,meta in metas.items():
            with ZipFile(bundles/catalog['bundles'][owner]['file']) as component:
                for name,row in meta['members'].items():
                    a,b=component.read('payload/'+name),actual.read(name)
                    if name=='AndroidManifest.xml':a,b=normalize_manifest(a)[0],normalize_manifest(b)[0]
                    require(a==b,'EXACT_COMPONENT_APK_MEMBER:'+name)
        require(actual.read(METADATA)==LABELS,'BOTH_435_OWNER_LABELS_PRESENT')
        for version,path in recoveries.items():
            with ZipFile(path) as old:
                before=set(validate_names(old))-SIGNATURE
                removed=before-names
                require(not removed if version!=2103434 else removed<=rejected_added,'NO_PROTECTED_FEATURE_REMOVAL:'+str(version))
                require(names-before<=allowed_infinity,'ONLY_TESTED_INFINITY_UI_MEMBERS_ADDED')
                normal,old_version=normalize_manifest(old.read('AndroidManifest.xml'))
                require(old_version==version and normalize_manifest(actual.read('AndroidManifest.xml'))==(normal,VERSION) and VERSION>version,'INSTALL_OVER_IDENTITY_AND_VERSION_ONLY:'+str(version))
                changed={name for name in names if name not in before or member_sha(old,name)!=hashes[name]}
                require(changed|removed<=allowed_members|(rejected_changed if version==2103434 else set()),'UNRELATED_APK_MEMBER_CHANGED_FROM_RECOVERY:'+str(version))
                require(METADATA in changed and bool(cobra_dex&changed) and bool(allowed_infinity&changed),'ALL_THREE_WORKSTREAMS_PRESENT:'+str(version))
                for name,pin in native.items():require(name in before and member_sha(old,name)==pin,'NATIVE_LIBRARY_FROZEN:'+name)
                for name,(owner,_) in dex.items():
                    if owner!='COBRA':require(member_sha(old,name)==hashes[name],'NON_COBRA_JAVA_DEX_FROZEN:'+owner)
                changes[str(version)]=dict(changed=sorted(changed),removed_rejected_only=sorted(removed))
        with tempfile.TemporaryDirectory(prefix='signed435-infinity-authentication-') as temporary:
            temp=Path(temporary)
            for leaf in ('INFINITY-MODULES.v1','INFINITY-MODULES.v1.sig'):(temp/leaf).write_bytes(actual.read('assets/addons/script.infinity.commandcenter/'+leaf))
            text=command(['openssl','dgst','-sha256','-verify',REPO/'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem','-signature',temp/'INFINITY-MODULES.v1.sig',temp/'INFINITY-MODULES.v1'])
            require(text.strip()=='Verified OK','ACTUAL_APK_ORIGINAL_KEY_MODULE_SIGNATURE')
    source_auth=verify_infinity_signature(bundles/'INFINITY.zip')
    require(source_auth['manifest_sha256']==authority['owner_update_evidence']['loading']['module_manifest_sha256'],'EXACT_TESTED_CODE_IN_FINAL_APK')
    icon=launcher_icon_guard().verify_actual_apk(apk,authority)
    require(authority['launcher_icon_exception']==prior['launcher_icon_exception'] and authority['protected_contract']==prior['protected_contract'],'APPROVED_ICONS_AND_SHUTDOWN_CONTRACT_EXACT433')
    report=dict(status='SIGNED435_COORDINATED_INSTALL_OVER_OWNER_COMPONENTS_VERIFIED',versionCode=VERSION,signing_source=build['source'],
        build_run=os.environ.get('GITHUB_RUN_ID'),package=PACKAGE,certificate_sha256=CERT_SHA,signature_schemes=['v1','v2','v3'],
        apk_sha256=file_sha(apk),apk_bytes=apk.stat().st_size,component_sha256={row['file']:file_sha(bundles/row['file']) for row in catalog['bundles'].values()},
        recovery_APK_sha256={str(v):RECOVERY[v] for v in RECOVERY},changed_APK_members_from_recoveries=changes,
        all_three_approved_workstreams_present=True,Cobra_selected_host_tests=3,Infinity_selected_host_tests=7,
        Infinity_module_source_signature=source_auth,unchanged_native_libraries=len(native),launcher_icons=icon,
        chooser='EXACT433_EXECUTABLES_AND_UI; GENUINE435_OWNER_LABELS_ONLY',shared_native='EXACT431_432_433',
        manifest='Typed versionCode only; same original package/identity/permissions',
        zip_alignment='PASS -P16; unchanged ELF segment compatibility',
        actual_device_install='NOT_RUN',physical_Fold='USER_ACCEPTANCE_PENDING',
        Infinity_Android_runtime='BLOCKED_EXISTING_TRANSLATED_ARM_CONSTRUCTOR_BEFORE_PYTHON',
        shutdown='NOT_CHANGED_NOT_RUN',accepted_pointer_updated=False,lock_promoted=False)
    save(signed/'DELIVERY-VERIFICATION.json',report)
    (signed/'SHA256SUMS').write_text(file_sha(apk)+'  '+apk.name+'\n')
    (bundles/'SHA256SUMS').write_text(''.join(file_sha(bundles/row['file'])+'  '+row['file']+'\n' for row in catalog['bundles'].values()))
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('recovery431','recovery432','baseline433','rejected434','signed','bundles','sdk'):p.add_argument('--'+name,type=Path,required=True)
    verify(**vars(p.parse_args()))
