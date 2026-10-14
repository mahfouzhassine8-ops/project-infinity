#!/usr/bin/env python3
"""Sign a native-only test derivative; preserve every other parent APK payload byte."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
NATIVE_COMMIT='fc3d6ebbb1bbef43bf01273004608e1c40358a3c'
ENGINE='lib/arm64-v8a/libkodi.so'
SIGNATURE=re.compile(r'^META-INF/(?:MANIFEST.MF|[^/]+\.(?:SF|RSA|DSA|EC))$',re.I)

def sha(data):return hashlib.sha256(data).hexdigest()
def run(*args):return subprocess.check_output([str(a) for a in args],text=True,stderr=subprocess.STDOUT)
def load(p):return json.loads(p.read_text())

def package(args):
    native=args.native/'checkpoint-build'
    proof=load(native/'ENGINE-PROOF.json');delta=load(native/'RAILS-NATIVE-DELTA.json')
    parent_receipt=load(args.receipts/'FINAL-APK-VERIFICATION.json')
    assert proof['rails_source_commit']==NATIVE_COMMIT
    assert proof['complete_native_engine_compiled'] and proof['rails_native_hold_compiled']
    assert proof['rc5_17_required_save_owners_unchanged'] and not proof['locked']
    assert delta['exact_three_file_delta_verified'] and len(delta['changed'])==3
    assert load(native/'RAILS-NATIVE-HOST.json')['passed']
    assert sha((native/'libkodi.so').read_bytes())==proof['native_sha256']
    assert sha(args.parent.read_bytes())==parent_receipt['apk_sha256']
    assert parent_receipt['source_commit']=='eafaab0d21c1cb20646b08dfe28fea7f769d56e9'
    assert parent_receipt['signer_certificate_sha256']==CERT
    assert parent_receipt['fresh_android_tests']==274
    smoke_files=list(args.smoke.rglob('rail-smoke-result.json'))
    assert len(smoke_files)==1,smoke_files
    smoke=load(smoke_files[0])
    assert smoke['passed'] and smoke['back_dismisses_and_clears_guard'] and smoke['open_action_runs_real_plugin']
    args.out.mkdir(parents=True,exist_ok=True)
    ndk=Path(os.environ['ANDROID_HOME'])/'ndk'/os.environ['NDK_VER']/'toolchains/llvm/prebuilt/linux-x86_64/bin'
    bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
    engine=args.out/'libkodi.so';shutil.copyfile(native/'libkodi.so',engine)
    run(ndk/'llvm-strip','--strip-unneeded',engine)
    module_path=ROOT/'repairs/critical-preview-2103376/manifest_patch.py'
    spec=importlib.util.spec_from_file_location('rails_manifest',module_path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    # Same versionCode permits a normal in-place reinstall of the protected
    # original APK for rollback, without uninstalling or deleting user data.
    mod.PARENT_CODE=mod.CODE=2103377
    mod.PARENT_NAME='1.0.9-RC5-Optional-Shutdown-Test'
    mod.NAME='1.0.9-Rails-Hold-Correction-RC02'
    unsigned=args.out/'rails-unsigned.apk'
    with zipfile.ZipFile(args.parent) as src, zipfile.ZipFile(unsigned,'w') as dst:
        assert len(src.namelist())==len(set(src.namelist()))
        parent_engine=args.out/'parent-libkodi.so';parent_engine.write_bytes(src.read(ENGINE))
        for info in src.infolist():
            if SIGNATURE.match(info.filename):continue
            data=src.read(info.filename)
            if info.filename==ENGINE:data=engine.read_bytes()
            elif info.filename=='AndroidManifest.xml':data,edits=mod.patch(data)
            dst.writestr(info,data)
    def exports(file):
        return {parts[-1].split('@')[0] for line in run('readelf','--dyn-syms','--wide',file).splitlines()
                if len(parts:=line.split())>=8 and parts[4:6]==['GLOBAL','DEFAULT'] and parts[6]!='UND'}
    assert not exports(parent_engine)-exports(engine)
    needed=lambda p:sorted(re.findall(r'\(NEEDED\).*?\[(.*?)\]',run('readelf','-d','-W',p)))
    assert needed(parent_engine)==needed(engine)
    final=args.out/'Infinity-2103377-Rails-Hold-Native-RC2-TEST.apk'
    subprocess.run(['bash',str(ROOT/'scripts/sign-infinity71.sh'),str(unsigned),str(final)],check=True)
    cert=run(bt/'apksigner','verify','--verbose','--print-certs',final)
    assert CERT in cert.lower()
    for version in (2,3):assert re.search(r'Verified using v'+str(version)+r' scheme[^\n]+true',cert)
    run(bt/'zipalign','-c','-p','4',final)
    badging=run(bt/'aapt','dump','badging',final)
    assert "versionCode='2103377'" in badging and mod.NAME in badging
    assert "package: name='com.projectinfinity.kodi'" in badging
    changed=[]
    with zipfile.ZipFile(args.parent) as old,zipfile.ZipFile(final) as new:
        a={n for n in old.namelist() if not SIGNATURE.match(n)}
        b={n for n in new.namelist() if not SIGNATURE.match(n)}
        assert a==b
        changed=sorted(n for n in a if old.read(n)!=new.read(n))
        assert changed==['AndroidManifest.xml',ENGINE],changed
        assert new.read(ENGINE)==engine.read_bytes()
        assert new.read('AndroidManifest.xml')==mod.patch(old.read('AndroidManifest.xml'))[0]
    result=dict(source_commit=os.environ['GITHUB_SHA'],native_source_commit=NATIVE_COMMIT,
       filename=final.name,sha256=sha(final.read_bytes()),parent_sha256=parent_receipt['apk_sha256'],
       native_sha256=proof['native_sha256'],packaged_native_sha256=sha(engine.read_bytes()),
       signer_sha256=CERT,changed_payload=changed,all_dex_resources_assets_other_libraries_byte_identical=True,
       preserved_android_cases=274,fresh_android_cases=0,complete_native_build=True,
       real_kodi_helper_smoke=smoke,physical_fold_accepted=False,locked=False,
       version_code=2103377,version_name=mod.NAME,
       rollback='Reinstall the original permanently signed 2103377 RC5 APK over this same-code test; never uninstall or clear data.')
    (args.out/'RAILS-APK-VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    (args.out/'signing-verification.txt').write_text(cert)
    (args.out/'SHA256SUMS').write_text(result['sha256']+'  '+final.name+'\n')
    for p in [unsigned,engine,parent_engine]:p.unlink()

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ['native','parent','receipts','smoke','out']:p.add_argument('--'+name,type=Path,required=True)
    package(p.parse_args())
