#!/usr/bin/env python3
"""Associate the green checkpoint engine with its shell; never certify device acceptance."""
import argparse, copy, hashlib, importlib.util, json, os, re, shutil, subprocess, sys, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / 'repairs/android-checkpoint-shutdown'
sys.path[:0] = [str(RUNTIME), str(ROOT/'repairs/mobile-regressions-2103304')]
import android_ci, runtime_delta, participant_asset
from packaging_checks import DEX, SIGNATURE, dex_contract, require, resource_ids, run, sha, verify_manifest_pair
VERSION = 2103345
RELEASE = '1.0.9-Checkpoint-Raw-IO-Settings-Fix-RC1'
ENGINE = 'lib/arm64-v8a/libkodi.so'
GREEN_SHA = os.environ.get('INFINITY_ENGINE_SOURCE_COMMIT', os.environ.get('GITHUB_SHA', ''))

def verify_class_coverage(old_classes, new_classes):
    # The reviewed source rewrite may remove old anonymous/nested classes.
    # Top-level owners and every class outside those exact Java files stay required.
    manifest = json.loads((RUNTIME/'runtime/android/manifest.json').read_text())
    changed_owners = {
        'Lcom/projectinfinity/kodi/' + Path(name).name.removesuffix('.java.in')
        for name in manifest['changed'] if name.endswith('.java.in')
    }
    removed = old_classes-new_classes
    unexpected = sorted(name for name in removed
                        if '$' not in name or name.split('$', 1)[0] not in changed_owners)
    require(not unexpected, 'Protected DEX classes removed: '+repr(unexpected))
    return sorted(removed)

def stage(args):
    sys.argv = ['android_ci', '--source', str(args.source), '--base', str(args.base), '--build', str(args.build), '--out', str(args.out)]
    android_ci.main()
    for relative in ('xbmc/build.gradle', 'xbmc/AndroidManifest.xml'):
        path = args.build / relative
        text = path.read_text()
        require('2103335' in text and '1.0.9-Checkpoint-Work-Compile-Only' in text, 'Unexpected donor version preimage')
        path.write_text(text.replace('2103335', str(VERSION)).replace('1.0.9-Checkpoint-Work-Compile-Only', RELEASE))

def associated_native(args):
    proof = json.loads((args.engine/'ENGINE-PROOF.json').read_text())
    require(proof['source_commit'] == GREEN_SHA, 'Wrong compiled engine source')
    require(proof['all_reviewed_inputs_preserved'] is True, 'Native preservation gate missing')
    require(proof['source_manifest_sha256'] == sha((RUNTIME/'runtime/native/manifest.json').read_bytes()), 'Native overlay changed since green build')
    native = args.engine/'libkodi.so'
    require(sha(native.read_bytes()) == proof['native_sha256'], 'Native artifact/proof mismatch')
    android_ci.factory.elf_identity(native, args.out/'native-elf.txt')
    target = args.out/'libkodi.so'
    shutil.copyfile(native, target)
    strip = Path(os.environ['ANDROID_HOME'])/'ndk'/os.environ['NDK_VER']/'toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip'
    run(strip, '--strip-unneeded', target)
    android_ci.factory.elf_identity(target, args.out/'packaged-elf.txt')
    return target, proof

def merge(base, donor, native, output, replacements):
    with zipfile.ZipFile(base) as a, zipfile.ZipFile(donor) as b:
        require(a.testzip() is None and b.testzip() is None, 'Corrupt APK input')
        require(len(a.namelist()) == len(set(a.namelist())) and len(b.namelist()) == len(set(b.namelist())), 'Duplicate APK entries')
        actual_assets = {n for n in b.namelist() if n.startswith('assets/') and not n.endswith('/')}
        require(actual_assets == set(replacements), 'Unreviewed donor asset')
        for n, expected in replacements.items():
            require(sha(b.read(n)) == expected, 'Donor asset mismatch: '+n)
        require(not any(n.startswith('lib/') and not n.endswith('/') for n in b.namelist()), 'Unexpected donor native libraries')
        old_jni, old_classes = dex_contract(a)
        new_jni, new_classes = dex_contract(b)
        require(old_jni <= new_jni, 'Existing JNI declaration removed: '+repr(sorted(old_jni-new_jni)))
        removed = verify_class_coverage(old_classes, new_classes)
        (output.parent/'DEX-CLASS-COVERAGE.json').write_text(json.dumps({
            'removed_reviewed_nested_classes': removed,
            'existing_top_level_and_unrelated_classes_preserved': True,
            'existing_jni_declarations_preserved': True,
        }, indent=2)+'\n')
        allowed = {
            ('Lcom/projectinfinity/kodi/Main;', 'infinityRegisterCheckpointOwner', '(Ljava/lang/String;ILjava/lang/String;)Z'),
            ('Lcom/projectinfinity/kodi/Main;', 'infinityRequestPersistenceCheckpoint', '(Ljava/lang/String;Ljava/lang/String;I)Z'),
            ('Lcom/projectinfinity/kodi/Main;', 'infinityPersistenceCheckpointStatus', '(Ljava/lang/String;Ljava/lang/String;I)Ljava/lang/String;'),
            ('Lcom/projectinfinity/kodi/Main;', 'infinityAuthorizeCheckpointTermination', '(Ljava/lang/String;Ljava/lang/String;I)Z'),
        }
        require(new_jni-old_jni == allowed, 'Unexpected checkpoint JNI declaration changes: '+repr(new_jni-old_jni))
        with zipfile.ZipFile(output, 'w') as z:
            for info in a.infolist():
                n=info.filename
                if n in ('AndroidManifest.xml', ENGINE) or n in replacements or DEX.fullmatch(n) or SIGNATURE.fullmatch(n): continue
                z.writestr(copy.copy(info), a.read(n))
            for info in b.infolist():
                n=info.filename
                if n=='AndroidManifest.xml' or DEX.fullmatch(n) or n in replacements: z.writestr(copy.copy(info), b.read(n))
            z.write(native, ENGINE, compress_type=zipfile.ZIP_STORED)

def finish(args):
    parent = json.loads((RUNTIME/'PARENT.json').read_text())
    require(sha(args.base.read_bytes()) == parent['parent_apk_sha256'], 'Wrong parent APK')
    runtime_delta.verify(args.source, json.loads((RUNTIME/'runtime/android/manifest.json').read_text())['after'])
    native, proof = associated_native(args)
    receipt=json.loads((args.out/'COMPAT-ASSET-ASSOCIATION.json').read_text())
    replacements={n:v['after'] for n,v in receipt['staged_assets'].items()}
    replacements['assets/infinity/checkpoint-controller.zip']=sha(participant_asset.build())
    replacements.update({'assets/infinity/'+name: sha(android_ci.installed_build.build(addon)) for addon,name in [('script.infinity.commandcenter','checkpoint-controller-20.zip'),('service.infinity.compat','checkpoint-compat-82.zip')]})
    donor=args.build/'xbmc/build/outputs/apk/release/xbmc-release.apk'
    bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
    require(resource_ids(bt/'aapt2',args.base,args.out/'base-resources.txt') == resource_ids(bt/'aapt2',donor,args.out/'donor-resources.txt'), 'Resource ID drift')
    unsigned=args.out/'checkpoint-unsigned.apk'
    merge(args.base, donor, native, unsigned, replacements)
    verify_manifest_pair(run(bt/'aapt','dump','xmltree',args.base,'AndroidManifest.xml',output=args.out/'base-manifest.txt'), run(bt/'aapt','dump','xmltree',unsigned,'AndroidManifest.xml',output=args.out/'manifest.txt'))
    for key in ('INFINITY_KEYSTORE_B64','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS'):
        require(bool(os.environ.get(key)), 'Missing permanent signer: '+key)
    final=args.out/f'Infinity-{VERSION}-Checkpoint-Raw-IO-Settings-Fix-RC1.apk'
    run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
    for label,path in [('base',args.base),('final',final)]:
        certificate=run(bt/'apksigner','verify','--verbose','--print-certs',path,output=args.out/(label+'-signer.txt'))
        require(parent['signer_certificate_sha256'] in certificate.lower(), 'Permanent signer mismatch')
    badging=run(bt/'aapt','dump','badging',final,output=args.out/'badging.txt')
    require(f"package: name='com.projectinfinity.kodi' versionCode='{VERSION}' versionName='{RELEASE}'" in badging, 'Wrong candidate identity')
    require('application-debuggable' not in badging, 'Debuggable candidate')
    with zipfile.ZipFile(args.base) as a, zipfile.ZipFile(final) as b:
        changed={'AndroidManifest.xml',ENGINE}|set(replacements)
        kept={n for n in a.namelist() if n not in changed and not DEX.fullmatch(n) and not SIGNATURE.fullmatch(n)}
        expected=kept|changed|{n for n in b.namelist() if DEX.fullmatch(n) or SIGNATURE.fullmatch(n)}
        require(set(b.namelist())==expected and len(b.namelist())==len(expected), 'Unexpected packaged payload')
        require(b.testzip() is None, 'Final APK integrity failure')
        for n in kept: require(a.read(n)==b.read(n),'Protected entry changed: '+n)
        for n,h in replacements.items(): require(sha(b.read(n))==h,'Final asset changed: '+n)
        require(b.read(ENGINE)==native.read_bytes(), 'Packaged native mismatch')
    (args.out/'DELIVERY.json').write_text(json.dumps({
        'file':final.name,'size':final.stat().st_size,'sha256':sha(final.read_bytes()),
        'candidate':VERSION,'source_commit':os.environ['GITHUB_SHA'],
        'native_source_commit':GREEN_SHA,'native_validation_run':int(os.environ['INFINITY_NATIVE_RUN_ID']),
        'android_validation_run':int(os.environ.get('INFINITY_ANDROID_RUN_ID',os.environ['GITHUB_RUN_ID'])),
        'native_unstripped_sha256':proof['native_sha256'],'native_packaged_sha256':sha(native.read_bytes()),
        'parent_apk_sha256':parent['parent_apk_sha256'],'protected_entries':len(kept),
        'signer_certificate_sha256':parent['signer_certificate_sha256'],
        'native_recompiled':True,'device_accepted':False,'locked':False,
        'installed_owner_audit_complete':False,'unknown_writers_block_normal_close':True,
        'purpose':'Fold test candidate; unresolved saves must block termination'
    },indent=2)+'\n')
    unsigned.unlink(); native.unlink()

def main():
    p=argparse.ArgumentParser(); p.add_argument('mode',choices=['stage','package'])
    for n in ['source','base','build','out','engine']:p.add_argument('--'+n,type=Path,required=True)
    args=p.parse_args()
    for n in ['source','base','build','out','engine']:setattr(args,n,getattr(args,n).resolve())
    args.out.mkdir(exist_ok=True,parents=True)
    (stage if args.mode=='stage' else finish)(args)
if __name__=='__main__':main()
