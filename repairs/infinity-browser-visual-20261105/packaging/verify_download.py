"""Independent original artifact/payload hashing; no APK extraction/install."""
import argparse,hashlib,json,sys
from pathlib import Path
from zipfile import ZipFile
H=Path(__file__).resolve().parent;R=H.parents[2]
sys.path.insert(0,str(R/'repairs/dual-experience-isolation-2103420'))
from inventory import SIGNATURE
from release_gate import normalize_manifest
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
FROZEN=Path('/tmp/kodi451-signed-baseline/Infinity-2103451-Combined-Original-Signer.apk')

def sha(f):return hashlib.file_digest(f,'sha256').hexdigest()
def signed(path,digest,version,out):
    with path.open('rb') as f:assert sha(f)==digest
    out.mkdir(parents=True,exist_ok=True)
    with ZipFile(path) as outer:
        assert outer.testzip() is None
        names=outer.namelist();apks=[n for n in names if n.endswith('.apk')];assert len(apks)==1
        apk=apks[0];receipt=json.loads(outer.read('BUILD-RECEIPT.json'))
        with outer.open(apk) as f:actual=sha(f)
        assert actual==receipt['signed_apk_sha256'] and receipt['versionCode']==version
        assert receipt['certificate_sha256']==CERT and receipt['accepted_pointer_updated'] is False
        signature=outer.read('SIGNATURE.txt').decode()
        assert 'Number of signers: 1' in signature and CERT in signature and signature.startswith('Verifies\n')
        for scheme in ('v1','v2','v3'):assert any(line.startswith('Verified using '+scheme+' scheme') and line.endswith(': true') for line in signature.splitlines())
        mapping=json.loads(outer.read('preservation/ALL-APK-MEMBER-HASHES.json'))
        with outer.open(apk) as f,ZipFile(f) as z:
            assert len(z.namelist())==len(set(z.namelist()))
            payload=set(z.namelist())-SIGNATURE;assert payload==set(mapping)
            for n in sorted(payload,key=lambda n:z.getinfo(n).header_offset):
                with z.open(n) as entry:assert sha(entry)==mapping[n]['after'],n
            with ZipFile(FROZEN) as old:
                assert normalize_manifest(z.read('AndroidManifest.xml'))==(normalize_manifest(old.read('AndroidManifest.xml'))[0],version)
        for n in names:
            if n.endswith(('.json','.txt')) and not n.endswith('/'):
                p=out/n;assert '..' not in p.relative_to(out).parts;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(outer.read(n))
    proof={'status':'PASS_DOWNLOADED_ACTUAL_APK_ALL_PAYLOAD_HASHES_AND_ORIGINAL_SIGNATURE_BINDING',
        'versionCode':version,'APK':apk,'APK_sha256':actual,'artifact_sha256':digest,'all_payload_members_verified':len(mapping),
        'original_certificate_sha256':CERT,'single_signer':True,'v1_v2_v3':True,'source':receipt['source'],
        'manifest_identical_except_versionCode':True,'Android':'NOT_RUN','installed_version':'UNVERIFIED','physical_acceptance':'PENDING',
        'signature_verification':'Original workflow apksigner evidence bound to the exact independently downloaded APK SHA; no local APK installation.'}
    (out/'DOWNLOADED-VERIFIED.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))

def components(path,digest,out):
    with path.open('rb') as f:assert sha(f)==digest
    with ZipFile(path) as z:
        assert z.testzip() is None
        catalogs=[n for n in z.namelist() if n.endswith('catalog.json')];assert len(catalogs)==1
        cat=json.loads(z.read(catalogs[0]));base=str(Path(catalogs[0]).parent)
        rows={}
        for owner,r in cat['bundles'].items():
            n=(base+'/' if base!='.' else '')+r['file']
            with z.open(n) as f:assert sha(f)==r['sha256']
            rows[owner]=dict(file=r['file'],sha256=r['sha256'],version=r['version'])
        assert rows['COBRA']['sha256']=='f63d4c1e491dc94591c5623bf02be90d4f9c187b91a0511b36398ee96745f8a8'
        assert rows['MINIMAL_ANDROID_CONTRACT']['sha256']=='1c4a2890ef5ca8665b86b148dd293c06a56d76ec846de1e0c9c037a3b0151a25'
        out.mkdir(parents=True,exist_ok=True);(out/'catalog.json').write_text(json.dumps(cat,indent=2)+'\n')
    proof={'status':'PASS_DOWNLOADED_COMPONENT_ARCHIVE_CRC_AND_ALL_COMPONENT_HASHES','artifact_sha256':digest,'components':rows,
           'matching_signed_APK_catalog_required':True,'Cobra_and_minimal_components_byte_identical':True}
    (out/'DOWNLOADED-COMPONENTS-VERIFIED.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['signed','components']);p.add_argument('--archive',type=Path,required=True);p.add_argument('--sha256',required=True);p.add_argument('--version',type=int);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.kind=='signed':signed(a.archive,a.sha256,a.version,a.out)
    else:components(a.archive,a.sha256,a.out)
