"""Independent downloaded-artifact, original-signature and exact component proof.

Keep the protected APK archive intact; use anonymous memory files to avoid
redundant 779 MB disk copies in the constrained engineering workspace.
"""
import argparse,hashlib,io,json,os,shutil
from pathlib import Path
from zipfile import ZipFile
import release451 as r
from inventory import manifest_tree
p=argparse.ArgumentParser()
for n in ('baseline_archive','archive','components','plan','out','sdk'):p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
for n in ('digest','components_digest'):p.add_argument('--'+n.replace('_','-'),required=True)
a=p.parse_args();a.out.mkdir(parents=True)
assert r.file_sha(a.baseline_archive)=='c2631df3b5adf2008a0fbde566913aa0670a993b171c59fc71f0aa00a93e391c'
assert r.file_sha(a.archive)==a.digest and r.file_sha(a.components)==a.components_digest
fds=[]
def apk(archive,name):
    assert archive.testzip() is None
    fd=os.memfd_create('Preview-verified-artifact',0);fds.append(fd)
    with archive.open(name) as source,os.fdopen(os.dup(fd),'wb') as dest:shutil.copyfileobj(source,dest,1024*1024)
    return Path('/proc')/str(os.getpid())/'fd'/str(fd)
try:
 with ZipFile(a.baseline_archive) as old_archive,ZipFile(a.archive) as new_archive,ZipFile(a.components) as components:
    assert [n for n in new_archive.namelist() if n.endswith('.apk')]==['Infinity-2103451-Combined-Original-Signer.apk']
    baseline=apk(old_archive,'Infinity-2103450-Combined-Original-Signer.apk')
    candidate=apk(new_archive,'Infinity-2103451-Combined-Original-Signer.apk')
    report=r.compare(baseline,candidate,a.plan,a.out,a.sdk)
    assert components.testzip() is None;catalog=json.loads(components.read('catalog.json'))
    with ZipFile(baseline) as before,ZipFile(candidate) as after:
        changed={}
        for name in sorted(set(before.namelist())|set(after.namelist())):
            x=r.digest(before.read(name)) if name in before.namelist() else None
            y=r.digest(after.read(name)) if name in after.namelist() else None
            if x!=y:changed[name]=dict(before=x,after=y,signature_metadata=name in r.SIGNATURE)
        identity=manifest_tree(after.read('AndroidManifest.xml'))['attributes']
        assert identity['package']['value']=='com.projectinfinity.kodi'
        matches={};mapping={'CHOOSER_SHELL':['classes.dex'],'MINIMAL_ANDROID_CONTRACT':['classes2.dex'],'INFINITY':['classes3.dex'],'COBRA':['classes4.dex','classes5.dex']}
        for owner,row in catalog['bundles'].items():
            raw=components.read(row['file']);assert r.digest(raw)==row['sha256']
            if owner in ('COBRA','MINIMAL_ANDROID_CONTRACT'):assert row==r.previous()['bundle_catalog']['bundles'][owner]
            with ZipFile(io.BytesIO(raw)) as bundle:
                meta=json.loads(bundle.read('component.json'));count=0
                for name in bundle.namelist():
                    if not name.startswith('payload/'):continue
                    member=name[8:];expected=bundle.read(name);actual=after.read(member)
                    if member=='AndroidManifest.xml':
                        assert r.normalize_manifest(expected)[0]==r.normalize_manifest(actual)[0]
                    else:assert expected==actual,member
                    count+=1
                for part,member in zip(sorted(meta['dex']),mapping[owner]):
                    assert r.digest(bundle.read(part))==meta['dex'][part]==r.digest(after.read(member))
                assert len(meta['dex'])==len(mapping[owner])
                matches[owner]=dict(zip_sha256=row['sha256'],payload_members=count,dex_members=mapping[owner])
    report.update(published_artifact_sha256=a.digest,published_apk_bytes=candidate.stat().st_size,
        all_changed_members_including_signatures=changed,
        package_identity={k:v for k,v in identity.items() if k.endswith(('package','versionCode','versionName'))})
    r.save(a.out/'PUBLISHED-VERIFICATION.json',report)
    r.save(a.out/'PUBLISHED-COMPONENT-MATCH.json',dict(status='PASS_ALL_PUBLISHED_COMPONENT_PAYLOADS_MATCH_SIGNED_APK',artifact_sha256=a.components_digest,components=matches,manifest_exception='app versionCode only; normalized shared component is exact'))
    for name in ('SIGNATURE.txt','SHA256SUMS','RELEASE.json','BUILD-RECEIPT.json','SIGNING-DECISION.json','REGISTERED451-CHECK.json','SIGNER-ROUTES.json'):
        if name in new_archive.namelist():(a.out/name).write_bytes(new_archive.read(name))
    print(json.dumps(dict(status=report['status'],apk_sha256=report['candidate_sha256'],certificate=report['certificate_sha256'],unchanged_members=report['unchanged_members'],changed_members=list(changed),components=matches),indent=2))
finally:
 for fd in fds:os.close(fd)
