"""Exact signed77 performance module staging; no keys, APK or registry writes."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
TASK=HERE.parent
ROOT=TASK.parents[1]
CC='script.infinity.commandcenter'
BASE_APK='93eb081cd6a86ff9cf1cb9aa75bc6d9087cd9c982fb46e0a9baa12c12aa9af22'
BASE_MANIFEST='63110023bf70f4ec32b0ab4750b3c1293a4976aa58cdfd1afbcd55027758b371'
PAIRS=[('candidate','0.3.5.78'),('recovery','0.3.5.79')]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def hashes(root):return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def tools():
    path=ROOT/'repairs/infinity-tracking-integration-2103469-20261108/prepare_tracking_release.py'
    assert sha(path.read_bytes())=='49c4d49bd679b2dd2ae2819ab45b8a673d4b362f80fc30090223553d3abc9e0b'
    spec=importlib.util.spec_from_file_location('retained_original_release_tools',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.load_tools()

def stage(apk,out):
    assert not out.exists(),'FRESH_STAGING_ONLY'
    assert sha(apk.read_bytes())==BASE_APK,'EXACT_SIGNED77_INPUT'
    t=tools();source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    proof=json.loads((TASK/'HOST-SOURCE-VERIFICATION.json').read_text())
    assert proof['status']=='PASS_SOURCE_PRESERVATION_AND_FULL948_HOST_PARITY'
    baseline=out/'baseline-modules'
    with ZipFile(apk) as z:
        t.validate_names(z)
        for name in z.namelist():
            if any(name.startswith('assets/addons/'+aid+'/') for aid in t.module_bundle.IDS) and not name.endswith('/'):
                relative=name[len('assets/addons/'):];assert t.module_bundle.safe(relative)
                dest=baseline/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
    raw,before=t.module_bundle.build(baseline)
    assert len(before)==80 and sha(raw)==BASE_MANIFEST
    assert raw==(baseline/CC/t.module_bundle.MANIFEST).read_bytes()
    subprocess.run(['openssl','dgst','-sha256','-verify',str(ROOT/'repairs/infinity-final-closure-2103407/ORIGINAL-INFINITY-PUBLIC-KEY.pem'),'-signature',str(baseline/CC/(t.module_bundle.MANIFEST+'.sig')),str(baseline/CC/t.module_bundle.MANIFEST)],check=True,capture_output=True)
    records={}
    for label,version in PAIRS:
        work=out/label;modules=work/'modules';shutil.copytree(baseline,modules)
        if label=='candidate':
            for name in ('common.py','service.py'):
                assert sha((baseline/CC/name).read_bytes())==proof['files'][name]['before_sha256']
                candidate=(TASK/'overlay'/CC/name).read_bytes()
                assert sha(candidate)==proof['files'][name]['after_sha256']
                (modules/CC/name).write_bytes(candidate)
        addon=modules/CC/'addon.xml';raw=addon.read_bytes();assert raw.count(b'version="0.3.5.75"')==1
        addon.write_bytes(raw.replace(b'version="0.3.5.75"',('version="'+version+'"').encode(),1))
        (modules/CC/(t.module_bundle.MANIFEST+'.sig')).unlink()
        payload,files=t.module_bundle.build(modules)
        expected={CC+'/addon.xml'}|({CC+'/common.py',CC+'/service.py'} if label=='candidate' else set())
        assert len(files)==80 and set(files)==set(before)
        assert {n for n in before if before[n]!=files[n]}==expected
        (modules/CC/t.module_bundle.MANIFEST).write_bytes(payload)
        record=dict(label=label,baseline=2103477,baseline_APK_sha256=BASE_APK,source_commit=source,CC=version,authenticated_source_count=80,modules=hashes(modules),manifest_sha256=sha(payload),functional_recovery_to_2103477=label=='recovery',Cobra_changes=False,APK=False,APK_version_reserved=False,signature='PENDING_ORIGINAL_SIGNER')
        save(work/'INPUTS.json',record);records[label]=sha((work/'INPUTS.json').read_bytes())
    save(out/'PREPARATION.json',dict(baseline=2103477,source_commit=source,inputs=records,original_tools=t.pins,original_signer='UNCHANGED_SignInfinityModules.java',APK=False,registry_mutated=False,Cobra_changes=False,networking_inputs=False,Android='PENDING'))
    print('PASS exact signed77; two authorized files; complete80 manifests; no APK or registry mutation')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--apk',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();stage(a.apk,a.out)
