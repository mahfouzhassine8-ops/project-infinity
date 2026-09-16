#!/usr/bin/env python3
"""Additional RC2 -> RC3 differential gate; retains original run40 packager gates."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile
from package_background_resume import dex_contract, manifest_tree, DEX, SIGNATURE
from infinity_async_lifecycle_repair import RC2_APK_SHA, RELEASE, VERSION_CODE

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--base',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True)
p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(a.base.read_bytes())==RC2_APK_SHA,'Wrong predecessor APK'
with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(a.candidate) as new:
    assert len(new.namelist())==len(set(new.namelist())) and not new.testzip()
    kept=lambda z:{n for n in z.namelist() if n!='AndroidManifest.xml' and not DEX.fullmatch(n) and not SIGNATURE.fullmatch(n)}
    assert kept(old)==kept(new),'Payload inventory changed'
    for n in sorted(kept(old)):assert old.read(n)==new.read(n),'Protected RC2 payload changed: '+n
    assert dex_contract(old)[0]==dex_contract(new)[0],'JNI declarations changed'
    dex=b''.join(new.read(n) for n in new.namelist() if DEX.fullmatch(n))
    for token in (b'submitCobraIo',b'postCobraUi',b'postCobraDelayed',b'stopCobraAsync',b'mAsyncDestroyed',b'BACKGROUND_MODE_NORMAL',b'BACKGROUND_MODE_EXTENDED'):
        assert token in dex,'Missing lifecycle/bridge method: '+repr(token)
    engine=sha(new.read('lib/arm64-v8a/libkodi.so'))
    assert engine=='9783527356ec108fb3bdd61213dc6c7af9b227da3b81051163aa893a9fa358d0'
    preserved=len(kept(new))
bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
def manifest(apk,path):
    text=subprocess.check_output([str(bt/'aapt'),'dump','xmltree',str(apk),'AndroidManifest.xml'],text=True)
    path.write_text(text);tree=manifest_tree(text)
    for key in ('android:versionCode','android:versionName'):tree['attrs'].pop(key,None)
    return tree
assert manifest(a.base,a.out/'rc2-manifest.txt')==manifest(a.candidate,a.out/'rc3-manifest.txt'),'Manifest drift beyond version'
cert=subprocess.check_output([str(bt/'apksigner'),'verify','--verbose','--print-certs',str(a.candidate)],text=True)
assert 'd7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7' in cert.lower()
(a.out/'rc3-signer.txt').write_text(cert)
badging=subprocess.check_output([str(bt/'aapt'),'dump','badging',str(a.candidate)],text=True)
assert f"versionCode='{VERSION_CODE}' versionName='{RELEASE}'" in badging
report={'status':'PASS','predecessor_apk_sha256':RC2_APK_SHA,'apk_sha256':sha(a.candidate.read_bytes()),
        'native_engine_sha256':engine,'rc2_payload_entries_byte_identical':preserved,
        'manifest_unchanged_except_version':True,'jni_unchanged':True,'signer_matches_rc2':True,
        'skin_update_required':False,'skin_lock':'1.0.5.139','native_rebuilt':False,
        'android_device_tested':False,'version_code':VERSION_CODE,'version_name':RELEASE}
(a.out/'rc2-to-rc3-payload-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: RC2 -> RC3 payload, manifest, JNI and permanent signer preserved')
