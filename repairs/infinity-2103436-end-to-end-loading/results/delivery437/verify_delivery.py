import json,hashlib,subprocess,sys,re
from pathlib import Path
from zipfile import ZipFile
repo=Path('/workspace/project-infinity');task=repo/'repairs/infinity-2103436-end-to-end-loading';sys.path.insert(0,str(task))
import release437 as r
root=Path('/tmp/infinity437-verification');signed=root/'signed437';apk=signed/'Infinity-2103437-Combined-Original-Signer.apk';base=root/'Infinity-2103436-Combined-Original-Signer.apk';prepared=Path('/tmp/infinity437-prepared');sdk=Path('/workspace/cobra-evidence/android-build-tools35/android-15')
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
        v['owner']='APK_VERSION_METADATA' if n=='AndroidManifest.xml' else authority['payload']['member:'+n]['owner']
        v['reason']='Typed install-over versionCode only' if n=='AndroidManifest.xml' else ('Truthful Infinity last-updated label only' if n==r.LABEL else 'Reviewed Infinity loading or required package/integrity metadata')
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
    r.save(out/'MATCHING-COMPONENTS.json',dict(status='PASS_EXACT_DELIVERED_APK_TO_COMPONENT_BYTES',members=checked,dex_files=len(dex),sha256={o:row['sha256'] for o,row in catalog['bundles'].items()},Cobra436_zip_byte_identical=catalog['bundles']['COBRA']==r.previous()['bundle_catalog']['bundles']['COBRA']))
print(json.dumps(dict(status='PASS_INDEPENDENT_SIGNED_DELIVERY',apk_sha256=r.file_sha(apk),changed_non_signature_members=len(report['changed_members']),changed_including_signature_members=len(full),matching_component_members=checked,native_libraries=report['native_libraries_unchanged'])))
