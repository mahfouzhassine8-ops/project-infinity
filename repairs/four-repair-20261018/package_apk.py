"""Same signer, exact 2103384 parent, only version fields and verified UI engine."""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
CODE = 2103385
PARENT_SHA = 'b571676731bb9bdccb25134c557be613e15cc9adaf77d6675dabc8e0586e54af'
PARENT_ENGINE = 'f47c6f3473a45438a533ecfa57dd196bac6d794227b16c4fb7888636e8f4408d'
PARENT_NAME = '1.0.9-Optional-VFS-SaveFix-TEST1'
NAME = '1.0.9-UI-Restoration-Fold-TEST01'
ENGINE = 'lib/arm64-v8a/libkodi.so'

def load(path, name):
    spec=importlib.util.spec_from_file_location(name,path); obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj); return obj

old = load(ROOT/'repairs/full-system-20261017/package_2103384_vfs.py', 'ui_signer_utilities')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def package(parent, native, dest):
    assert len(NAME) == len(PARENT_NAME) and sha(parent) == PARENT_SHA
    for key in ('INFINITY_KEYSTORE_B64','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS'):
        assert os.environ.get(key), 'Permanent signing secret unavailable: ' + key
    proof=json.loads((native/'ENGINE-PROOF.json').read_text())
    delta=json.loads((native/'FOUR-REPAIR-INPUT-DELTA.json').read_text())
    locked=json.loads((native/'LOCKED-2103384-SOURCE-MAP.json').read_text())
    final=json.loads((native/'FINAL-SHUTDOWN-SOURCE-PRESERVATION.json').read_text())['after']
    assert len(locked)==9404 and final==dict(locked,**delta['after'])
    post=json.loads((native/'POST-BUILD-SOURCE-INVENTORY.json').read_text())
    assert post['reviewed_file_count']==9404 and post['changed_or_missing_reviewed']==[]
    assert all(post['actual'].get(name)==digest for name,digest in final.items())
    assert post['build_generated_additions']=={name:digest for name,digest in post['actual'].items() if name not in final}
    assert set(delta['changed'])=={'xbmc/input/InputManager.cpp','xbmc/guilib/GUIBaseContainer.cpp','xbmc/guilib/GUIBaseContainer.h'}
    assert delta['before']=={p:locked[p] for p in delta['changed']}
    assert proof['source_commit']==delta['source_commit']==os.environ['GITHUB_SHA']
    assert proof['ui_input_contract_compiled'] and proof['complete_native_engine_compiled']
    assert proof['shutdown_policy']=='essential_first_process_exit_v1' and not proof['crash_fixed']
    assert sha(native/'libkodi.so')==proof['native_sha256']
    bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
    ndk=Path(os.environ['ANDROID_HOME'])/'ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin'
    old.verify_signed(parent,bt)
    dest.mkdir(parents=True,exist_ok=True)
    compiled=dest/'new-engine.so'; compiled.write_bytes((native/'libkodi.so').read_bytes())
    old.output(ndk/'llvm-strip','--strip-unneeded',compiled)
    manifest=load(ROOT/'repairs/critical-preview-2103376/manifest_patch.py','ui_manifest_patch')
    manifest.PARENT_CODE=2103384;manifest.CODE=CODE;manifest.PARENT_NAME=PARENT_NAME
    reports=[]
    with zipfile.ZipFile(parent) as src:
        assert hashlib.sha256(src.read(ENGINE)).hexdigest()==PARENT_ENGINE
        original=dest/'old-engine.so';original.write_bytes(src.read(ENGINE))
        assert not old.library_exports(original)-old.library_exports(compiled)
        assert old.needed(original)==old.needed(compiled)
        for restore in (False,True):
            filename='Infinity-2103385-2103384-Compatibility-Return.apk' if restore else 'Infinity-2103385-UI-Restoration-TEST1.apk'
            manifest.NAME=PARENT_NAME if restore else NAME
            xml,edits=manifest.patch(src.read('AndroidManifest.xml'))
            assert {e['field'] for e in edits}=={'versionCode','versionName'}
            unsigned=dest/('unsigned-'+filename)
            with zipfile.ZipFile(unsigned,'w') as z:
                for info in src.infolist():
                    if old.SIGNATURE.fullmatch(info.filename):continue
                    payload=xml if info.filename=='AndroidManifest.xml' else compiled.read_bytes() if info.filename==ENGINE and not restore else src.read(info)
                    z.writestr(copy.copy(info),payload)
            signed=dest/filename
            subprocess.run(['bash',str(ROOT/'scripts/sign-infinity71.sh'),str(unsigned),str(signed)],check=True)
            old.verify_signed(signed,bt);old.output(bt/'zipalign','-c','-p','4',signed)
            badge=old.output(bt/'aapt','dump','badging',signed)
            assert "package: name='com.projectinfinity.kodi' versionCode='2103385'" in badge
            assert 'application-debuggable' not in badge
            with zipfile.ZipFile(signed) as z:
                assert z.testzip() is None and set(z.namelist())==set(src.namelist())
                changes=sorted(n for n in src.namelist() if not old.SIGNATURE.fullmatch(n) and src.read(n)!=z.read(n))
                assert changes==(['AndroidManifest.xml'] if restore else ['AndroidManifest.xml',ENGINE])
            reports.append(dict(file=filename,sha256=sha(signed),native_restored_2103384=restore,changed_unsigned_payload=changes))
            unsigned.unlink()
        original.unlink();compiled.unlink()
    (dest/'SHA256SUMS').write_text(''.join(r['sha256']+'  '+r['file']+'\n' for r in reports))
    (dest/'SIGNED-2103385.json').write_text(json.dumps(dict(source_commit=os.environ['GITHUB_SHA'],
        parent_sha256=PARENT_SHA,artifacts=reports,signer_sha256=old.CERT,
        only_input_native_delta=True,crash_fixed=False,android_verified=False,physical_fold_verified=False,locked=False),indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('parent','native','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();package(a.parent,a.native,a.out)
