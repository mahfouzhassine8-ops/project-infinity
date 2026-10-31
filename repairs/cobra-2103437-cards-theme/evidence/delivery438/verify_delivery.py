import json,hashlib,subprocess,sys,re
from pathlib import Path
from zipfile import ZipFile
repo=Path('/workspace/project-infinity');task=repo/'repairs/cobra-2103437-cards-theme';sys.path.insert(0,str(task))
import release438 as r
root=Path('/tmp/cards438');signed=root/'signed438';apk=signed/'Infinity-2103438-Combined-Original-Signer.apk';base=Path('/tmp/infinity437-verification/signed437/Infinity-2103437-Combined-Original-Signer.apk');prepared=Path('/tmp/cards438/prepared');sdk=Path('/workspace/cobra-evidence/android-build-tools35/android-15')
out=root/'independent';out.mkdir(exist_ok=True)
report=r.compare(base,apk,prepared/'PREPARATION.json',out,sdk)
original_report=json.loads((signed/'preservation/APK-PRESERVATION.json').read_text());assert report==original_report
with ZipFile(base) as a,ZipFile(apk) as b:
    assert set(a.namelist())==set(b.namelist())
    signatures={n:dict(before=r.digest(a.read(n)),after=r.digest(b.read(n)),owner='ORIGINAL_APK_SIGNER',reason='Required regenerated original-key APK v1 signature metadata') for n in r.SIGNATURE}
    full=dict(report['changed_members']);full.update({n:v for n,v in signatures.items() if v['before']!=v['after']})
    authority=r.load(r.AUTH);source=r.cmd('git','rev-parse','HEAD').strip()
    for n,v in full.items():
        if n in r.SIGNATURE:continue
        v['owner']='APK_VERSION_METADATA' if n=='AndroidManifest.xml' else ('COBRA' if n in ('classes4.dex','classes5.dex') else authority['payload']['member:'+n]['owner'])
        v['reason']='Typed install-over versionCode only' if n=='AndroidManifest.xml' else ('Truthful Cobra last-updated label only' if n==r.LABEL else 'Reviewed Cards theme DEX or mandatory version metadata')
    r.save(out/'COMPLETE-APK-DELTA.json',dict(status='PASS_INDEPENDENT_ALL_MEMBERS_INCLUDING_SIGNATURES',changes=full,added=[],removed=[],signing_block='Original-key APK signing block is outside ZIP members; apksigner v1/v2/v3 verification passed',baseline_sha256=r.APK_SHA,candidate_sha256=r.file_sha(apk)))
    catalog=r.load(prepared/'components/catalog.json');dex=[];checked=0
    for owner,row in catalog['bundles'].items():
        meta=r.read_bundle(prepared/'components'/row['file'],row)
        with ZipFile(prepared/'components'/row['file']) as z:
            for n in meta['members']:
                x=z.read('payload/'+n);y=b.read(n)
                if n=='AndroidManifest.xml':assert r.normalize_manifest(x)[0]==r.normalize_manifest(y)[0]
                else:assert x==y,n
                checked+=1
            dex.extend((owner,n,z.read(n)) for n in sorted(meta['dex']))
    order={o:i for i,o in enumerate(('CHOOSER_SHELL','MINIMAL_ANDROID_CONTRACT','INFINITY','COBRA'))};dex.sort(key=lambda x:(order[x[0]],x[1]))
    for i,(owner,n,raw) in enumerate(dex,1):assert b.read('classes'+(str(i) if i>1 else '')+'.dex')==raw
    r.save(out/'MATCHING-COMPONENTS.json',dict(status='PASS_EXACT_DELIVERED_APK_TO_COMPONENT_BYTES',members=checked,dex_files=len(dex),sha256={o:row['sha256'] for o,row in catalog['bundles'].items()},Infinity437_zip_byte_identical=catalog['bundles']['INFINITY']==r.previous()['bundle_catalog']['bundles']['INFINITY']))
print(json.dumps(dict(status='PASS_INDEPENDENT_SIGNED_DELIVERY',apk_sha256=r.file_sha(apk),changed_non_signature_members=len(report['changed_members']),changed_including_signature_members=len(full),matching_component_members=checked,native_libraries=report['native_libraries_unchanged'])))

old=r.previous()['payload'];new=r.load(r.AUTH)['payload']
changed={n:dict(before=old[n],after=new[n]) for n in old if n.startswith('class:') and old[n]!=new[n]}
allowed={'class:'+n for n in r.load(task/'METHOD-ALLOWLIST.json')}
assert set(changed)==allowed
added=sorted(set(new)-set(old));assert added==['class:Lcom/projectinfinity/kodi/CobraCardsTheme$Colors;','class:Lcom/projectinfinity/kodi/CobraCardsTheme;']
assert all(new[n]['owner']=='COBRA' for n in added)
assert all(old[n]==new[n] for n in old if old[n]['owner']!='COBRA' and n!='member:'+r.LABEL)
r.save(out/'CLASS-PRESERVATION.json',dict(status='PASS_EXACT_REVIEWED_CLASS_DELTA',changed=changed,added=added,removed=[],unchanged_Cobra_classes=sum(n.startswith('class:') and old[n]['owner']=='COBRA' and old[n]==new[n] for n in old),all_other_owners_unchanged_except_truthful_label=True,method_allowlist=r.load(task/'METHOD-ALLOWLIST.json'),physical_Fold='PENDING'))
