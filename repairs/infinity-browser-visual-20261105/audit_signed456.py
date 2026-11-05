"""Inspect actual original-signed APK bytes, not a mocked helper or source plan."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
APK='Infinity-2103456-Combined-Original-Signer.apk'
EXPECTED='81aed468bcdf4031f3186fa7c5aa73e396a38f27837581fbcc54f56cbbc94696'
WRAPPER='bf51d707e7596fa78b09b210a02dd0e9165918d380f3e8c98597c1885f9ac3ac'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'


def digest(stream):
    h=hashlib.sha256()
    while chunk:=stream.read(1024*1024):h.update(chunk)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--artifact',type=Path,required=True);a=p.parse_args()
    with a.artifact.open('rb') as f:assert digest(f)==WRAPPER
    out=HERE/'results/signed456';out.mkdir(parents=True,exist_ok=True)
    payload=Path('/tmp/infinity-signed456-payload-audit')
    payload.mkdir(parents=True,exist_ok=True)
    with ZipFile(a.artifact) as outer:
        assert CERT in outer.read('SIGNATURE.txt').decode()
        with outer.open(APK) as stream:assert digest(stream)==EXPECTED
        with outer.open(APK) as stream,ZipFile(stream) as apk:
            names=apk.namelist()
            def selected(name):
                if name.startswith('assets/addons/skin.infinity.diggz/'):
                    return '/unified/' in name or name.endswith(('.json','/addon.xml','/infinity_library_navigation.py'))
                if name.startswith('assets/addons/script.infinity.commandcenter/'):
                    return name.endswith(('.py','.xml','.json')) or '/INFINITY-MODULES.v1' in name
                if name.startswith(('assets/addons/plugin.video.umbrella/','assets/addons/plugin.video.sporthdme/')):
                    return name.endswith(('.py','/addon.xml'))
                return False
            entries=sorted((apk.getinfo(n) for n in names if selected(n)),key=lambda i:i.header_offset)
            record={}
            for info in entries:
                raw=apk.read(info);path=payload/info.filename
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
                record[info.filename]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
            drawer='assets/addons/skin.infinity.diggz/unified/Custom_1198_InfinityNav.xml'
            helper='assets/addons/skin.infinity.diggz/resources/lib/infinity_library_navigation.py'
            assert drawer in record and helper in record
            # Bind extracted code to the actual signed preservation map as well.
            inventory=json.loads(outer.read('preservation/ALL-APK-MEMBER-HASHES.json'))
            assert all(inventory[n]['after']==r['sha256'] for n,r in record.items())
            receipt={'status':'PASS_ACTUAL_SIGNED456_SHA_AND_TARGETED_PAYLOAD_EXTRACTION',
                'APK_sha256':EXPECTED,'artifact_sha256':WRAPPER,'certificate_sha256':CERT,
                'download_artifact':13397163155,'run':41988386798,
                'source_commit':'9c77703eb847d3482441091da94bdbee272a2ee3',
                'extracted_members':record,'native_libraries':len([n for n in names if n.startswith('lib/') and n.endswith('.so')]),
                'DEX_members':[n for n in names if n.endswith('.dex')],
                'Android':'NOT_RUN','phone_installed_version':'UNVERIFIED','functional_acceptance':'NOT_ACCEPTED'}
    (out/'ACTUAL-PAYLOAD-AUDIT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='extracted_members'},indent=2))
    print('Actual signed source members extracted:',len(record))


if __name__=='__main__':main()
