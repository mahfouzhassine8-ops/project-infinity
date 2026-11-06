"""Independently verify actual downloaded signed quick-update payloads.

Input is the real CI artifact, not a locally prepared unsigned tree.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import padding

ROOT=Path(__file__).resolve().parents[3]
FIRST=ROOT/'repairs/infinity-final-closure-2103407'
CC='script.infinity.commandcenter';SKIN='skin.infinity.diggz'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
OLD={CC:'3f9887d18d82d8bdba066e449e7ce25dbe57a59742a7da6d491d72a86be9dea2',SKIN:'02b4b8bf09ecbd56d9f68f4939e0f9216c01334c4e7ff60e677ab77509265f60'}

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def members(path):
    with ZipFile(path) as z:
        assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
        return {n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if not n.endswith('/')}

def main(delivery,previous,out):
    out.mkdir(parents=True,exist_ok=False)
    pem=(FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem').read_bytes()
    assert (delivery/'ORIGINAL-INFINITY-PUBLIC-KEY.pem').read_bytes()==pem
    key=serialization.load_pem_public_key(pem)
    envelope=(delivery/'INFINITY-QUICK-UPDATE.v1').read_bytes()
    key.verify((delivery/'INFINITY-QUICK-UPDATE.v1.sig').read_bytes(),envelope,padding.PKCS1v15(),hashes.SHA256())
    lines=envelope.decode('ascii').splitlines()
    assert lines[:4]==['INFINITY-QUICK-UPDATE/1','base\t2103460','commandcenter\t0.3.5.61','skin\t1.0.5.266']
    bound={row.split('\t')[2]:row.split('\t')[1] for row in lines[4:]}
    assert len(bound)==4
    proof=json.loads((delivery/'BUILD-RECEIPT.json').read_text())
    assert proof['certificate_sha256']==CERT and proof['artifacts']==bound
    assert proof['device_APK']==2103462 and proof['native_changed'] is False
    recovery=json.loads((delivery/'RECOVERY-VERIFIED.json').read_text())
    assert recovery['status']=='PASS_SIX_HOST_INSTALLER_AND_RECOVERY_CASES' and len(recovery['tests'])==6
    baseline={}
    for aid,version in ((CC,'0.3.5.61'),(SKIN,'1.0.5.262')):
        p=previous/(aid+'-'+version+'-2103460-corrective.zip')
        assert sha(p)==OLD[aid]
        baseline[aid]=members(p)
    reports=[]
    for filename,digest in bound.items():
        path=delivery/filename;assert sha(path)==digest
        aid=SKIN if filename.startswith(SKIN+'-') else CC
        recover=filename.endswith('-recovery.zip')
        actual=members(path)
        assert set(actual)==set(baseline[aid]),'NO_EXTRA_MISSING_OR_PROFILE_FILES'
        changed={n for n in actual if actual[n]!=baseline[aid][n]}
        expected=({SKIN+'/'+n for n in ('addon.xml','infinity-skin.json','Infinity-Protected-Manifest.json')} if recover and aid==SKIN
                  else set() if recover else {n for n in proof['changes'] if n.startswith(aid+'/')}|({CC+'/INFINITY-MODULES.v1.sig'} if aid==CC else set()))
        assert changed==expected,(filename,changed^expected)
        with ZipFile(path) as z:
            version=ET.fromstring(z.read(aid+'/addon.xml')).get('version')
            expected_version=('1.0.5.267' if recover else '1.0.5.266') if aid==SKIN else '0.3.5.61'
            assert version==expected_version
            if aid==SKIN:
                protected=json.loads(z.read(aid+'/Infinity-Protected-Manifest.json'))['protected_files']
                assert len(protected)==948
                for rel,want in protected.items():assert actual[aid+'/'+rel]==want,rel
            else:
                key.verify(z.read(CC+'/INFINITY-MODULES.v1.sig'),z.read(CC+'/INFINITY-MODULES.v1'),padding.PKCS1v15(),hashes.SHA256())
                # Execute the unchanged real C++ module verifier with this actual
                # signed generation and original unchanged extension-point shims.
                with tempfile.TemporaryDirectory(dir=out) as temp:
                    stage=Path(temp)
                    original=Path('/dev/shm/infinity2103460-native-original-modules')
                    for owner in (CC,'script.infinity.rails','script.infinity.uirepair','script.infinity.watchedbridge'):
                        shutil.copytree(original/owner,stage/owner)
                    for n in actual:
                        p=stage/n;assert '..' not in p.parts;p.write_bytes(z.read(n))
                    result=subprocess.run(['/dev/shm/infinity2103460-quick-verifier',str(stage.resolve()),str((FIRST/'ORIGINAL-INFINITY-PUBLIC-KEY.pem').resolve())],text=True,capture_output=True)
                    assert result.returncode==0,result.stderr
                    (out/(('recovery' if recover else 'corrective')+'-NATIVE-MODULE-VERIFICATION.txt')).write_text(result.stdout+result.stderr)
        reports.append(dict(file=filename,sha256=digest,addon=aid,version=version,member_count=len(actual),
            protected_unchanged=len(actual)-len(changed),changed=sorted(changed),
            original_key_module_signature='PASS' if aid==CC else 'covered by original-key outer envelope',
            exact262_functional_recovery=recover))
    report=dict(status='PASS_ACTUAL_DOWNLOADED_ORIGINAL_KEY_QUICK_INSTALLERS',artifacts=reports,
                module_RSA_and_native_verifier='PASS',outer_RSA='PASS',skin_948_hashes='PASS',
                physical_Android='NOT_RUN',APK2103462_unchanged=True,Cobra_changed=False,Preview_changed=False,
                all_requested_repairs_complete=False,known_open=['Search All settings-write rejection','reported heading regression Android attribution','native repeated-search stability'])
    (out/'VERIFIED-DOWNLOAD.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'artifacts':len(reports),'Android':'NOT_RUN'}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--delivery',type=Path,required=True);p.add_argument('--previous',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();main(a.delivery,a.previous,a.out)
