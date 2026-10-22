"""Package an internal QA candidate; preserve every payload member except engine/identity."""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile,ZIP_DEFLATED
import patch
import build

ROOT=build.ROOT
sys.path.insert(0,str(ROOT/'repairs/2103390-bugfixes/group7/finish92'))
import delivery92 as delivery
ENGINE='lib/arm64-v8a/libkodi.so'
RECORDER='lib/arm64-v8a/libinfinitycrash.so'
SIGNATURE=re.compile(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))',re.I)
PARENT='17041a44f121693ab0852c6a826b7f728a4d834a64225efec363861616b698e6'
NAME='Infinity-2103401-Universal-Persistence-RC1-NOT-ACCEPTED.apk'

def delta(parent,final,targets):
    changes=[];same=[]
    with ZipFile(parent) as old,ZipFile(final) as new:
        names=set(old.namelist())|set(new.namelist())
        for name in sorted(names):
            a=old.read(name) if name in old.namelist() else None
            b=new.read(name) if name in new.namelist() else None
            if a==b:same.append(dict(path=name,sha256=patch.sha(b)));continue
            assert name in targets or SIGNATURE.fullmatch(name),'Unexpected APK difference: '+name
            if name in targets:assert b==targets[name]
            changes.append(dict(path=name,before=patch.sha(a) if a is not None else None,after=patch.sha(b) if b is not None else None))
        assert {x['path'] for x in changes if not SIGNATURE.fullmatch(x['path'])}==set(targets)
    return dict(changed=changes,byte_identical_members=same,signing_block='Verified separately outside ZIP members')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('parent','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();parent=a.parent/'Infinity-2103401-Fold-Corrective-EXPERIMENTAL.apk'
    assert patch.sha(parent.read_bytes())==PARENT
    assert all(os.environ.get(k) for k in delivery.KEYS),'Permanent signing secrets required; no fallback'
    expected=json.loads((build.OUT/'NATIVE-SOURCE-MAP.json').read_text())
    build.checked_sources(ROOT/'kodi',expected,allow_generated=True)
    proof=json.loads((build.OUT/'ENGINE-PROOF.json').read_text())
    assert proof['source_commit']==os.environ['GITHUB_SHA'] and proof['complete_native_engine_compiled']
    engine=(build.OUT/'libkodi.so').read_bytes();assert patch.sha(engine)==proof['native_sha256']
    for name in ('UNIVERSAL-TESTS.json','EXISTING-REGRESSIONS.json'):
        assert json.loads((build.OUT/name).read_text())['passed'],name
    tools=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
    parent_signature=delivery.verify_signature(parent,tools)
    _,_,signer=delivery.adapters()
    out=a.out.resolve();assert not out.exists();out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='universal-package-',dir=out.parent) as tmp:
        tmp=Path(tmp);unsigned=tmp/'unsigned.apk';signed=tmp/NAME
        with ZipFile(parent) as old:
            abi=signer.native_export_compatibility(old.read(ENGINE),engine)
            recorder=old.read(RECORDER)
            rebound=delivery.replace_recorder_field(recorder,patch.sha(old.read(ENGINE)),patch.sha(engine),signer.nativeidentity.elf_sections(recorder))
            targets={ENGINE:engine,RECORDER:rebound}
            with ZipFile(unsigned,'w',allowZip64=True) as new:
                for info in old.infolist():
                    if not SIGNATURE.fullmatch(info.filename):new.writestr(copy.copy(info),targets.get(info.filename,old.read(info)))
        delta(parent,unsigned,targets)
        subprocess.run(['bash',str(ROOT/'scripts/sign-infinity71.sh'),str(unsigned),str(signed)],check=True)
        signature=delivery.verify_signature(signed,tools)
        report=delta(parent,signed,targets)
        badging=delivery.command([tools/'aapt','dump','badging',signed])
        assert "package: name='com.projectinfinity.kodi' versionCode='2103401'" in badging
        assert 'application-debuggable' not in badging
        receipt=dict(source_commit=os.environ['GITHUB_SHA'],build_run=os.environ['GITHUB_RUN_ID'],
            protected_baseline=2103400,parent_sha256=PARENT,apk_sha256=patch.sha(signed.read_bytes()),
            native_sha256=proof['native_sha256'],native_abi=abi,same_version_install_over=True,
            permanent_certificate_sha256=delivery.CERT,signature_schemes_verified=[1,2,3],
            changed_payload_members=sorted(targets),all_dex_assets_manifest_other_libraries_byte_identical=True,
            provider_code_changed=False,user_profile_changed=False,android_validated=False,
            physical_fold_verified=False,final_lock=False,distribution='INTERNAL QA ONLY; not accepted')
        for name,value in [('APK-DELTA.json',report),('CANDIDATE.json',receipt)]:build.save(tmp/name,value)
        for name in ('SOURCE-DELTA.json','NATIVE-SOURCE-MAP.json','ENGINE-PROOF.json','UNIVERSAL-TESTS.json','EXISTING-REGRESSIONS.json'):
            shutil.copyfile(build.OUT/name,tmp/name)
        (tmp/'PARENT-SIGNATURE.txt').write_text(parent_signature)
        (tmp/'FINAL-SIGNATURE.txt').write_text(signature);(tmp/'APK-BADGING.txt').write_text(badging)
        with ZipFile(tmp/'Infinity-Universal-Source-and-Evidence.zip','w',ZIP_DEFLATED,compresslevel=9) as z:
            for name in expected:z.write(ROOT/'kodi'/name,'native/'+name)
            for file in build.HERE.rglob('*'):
                if file.is_file() and '__pycache__' not in file.parts:z.write(file,'repair/'+file.relative_to(build.HERE).as_posix())
            for file in tmp.iterdir():
                if file.suffix in ('.json','.txt'):z.write(file,'receipts/'+file.name)
        unsigned.unlink()
        (tmp/'SHA256SUMS').write_text(''.join(patch.sha(f.read_bytes())+'  '+f.name+'\n' for f in sorted(tmp.iterdir()) if f.is_file()))
        os.rename(tmp,out)
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
