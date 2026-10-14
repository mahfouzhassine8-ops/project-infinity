#!/usr/bin/env python3
"""Merge tested Java and fully compiled native corrections, preserve locked payload."""
from pathlib import Path
import argparse
import copy
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'repairs/mobile-regressions-2103304'))
import package_candidate as factory
from packaging_checks import require,sha,run,resource_ids,manifest_tree
PARENT_SHA='8e8e139929592daedb63e0e41040258d655f132fd025b236de7dee1e88b47649'
SIGNER='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'

def exports(text):
    return {parts[-1].split('@',1)[0] for row in text.splitlines()
            if len(parts:=row.split())>=8 and parts[4:6]==['GLOBAL','DEFAULT'] and parts[6]!='UND'}

def verify_manifest(old_text,new_text):
    old,new=manifest_tree(old_text),manifest_tree(new_text)
    found=[]
    def visit(node):
        for child in node['children']:
            if child['tag']=='meta-data' and 'android.app.func_name' in child['attrs'].get('android:name',''):
                found.append((node,child))
            visit(child)
    visit(new)
    require(len(found)==1,'Missing or duplicate native entry metadata')
    owner,child=found[0]
    require(owner['tag']=='activity' and '.Main' in owner['attrs'].get('android:name',''),'Native entry attached to wrong activity')
    require(set(child['attrs'])=={'android:name','android:value'} and
            'InfinityNativeActivity_onCreate' in child['attrs']['android:value'] and not child['children'],
            'Unapproved native entry metadata')
    owner['children'].remove(child)
    for tree in (old,new):
        for key in ('android:versionCode','android:versionName'):tree['attrs'].pop(key,None)
    require(old==new,'Manifest differs outside version identity and saved native-entry metadata')

def package(args):
    require(sha(args.parent.read_bytes())==PARENT_SHA,'Wrong locked APK')
    for name in ('INFINITY_KEYSTORE_B64','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS'):
        require(bool(os.environ.get(name)),'Original permanent signing configuration missing: '+name)
    native=args.native/'checkpoint-build'
    if not native.exists():native=args.native
    android=args.android
    proof=json.loads((native/'ENGINE-PROOF.json').read_text())
    tests=json.loads((android/'ANDROID-VERIFICATION.json').read_text())
    preservation=json.loads((native/'FINAL-SHUTDOWN-SOURCE-PRESERVATION.json').read_text())
    native_commit=os.environ.get('INFINITY_NATIVE_SOURCE_COMMIT',os.environ['GITHUB_SHA'])
    require(proof['source_commit']==native_commit,'Native source commit mismatch')
    if native_commit!=os.environ['GITHUB_SHA']:
        subprocess.run(['git','merge-base','--is-ancestor',native_commit,os.environ['GITHUB_SHA']],check=True)
        delta=set(subprocess.check_output(['git','diff','--name-only',native_commit,os.environ['GITHUB_SHA']],text=True).splitlines())
        allowed={'repairs/shutdown-final-2103377/package.py','.github/workflows/infinity-2103377-final-shutdown-package.yml'}
        require(delta<=allowed,'Verified native/Java source changed before packaging')
    reuse_path=android/'ANDROID-REUSE-PROOF.json'
    if tests['source_commit']!=os.environ['GITHUB_SHA']:
        require(reuse_path.is_file(),'Earlier tested Java has no exact current source-replay proof')
        reuse=json.loads(reuse_path.read_text())
        require(reuse['source_commit'] in (os.environ['GITHUB_SHA'],native_commit) and reuse['tested_source_commit']==tests['source_commit']
                and reuse['runtime_source_byte_identical'] and reuse['fresh_test_results_preserved']
                and reuse['donor_sha256']==sha(args.donor.read_bytes()),'Java/native pairing proof failed')
    require(proof['complete_native_engine_compiled'] and proof['final_shutdown_corrections_compiled'],
            'Complete repaired native engine proof missing')
    require(proof['native_entry_matches_saved_274_java'] and proof['original_save_and_termination_authority_preserved'],
            'Lifecycle pairing or save authority missing')
    require(preservation['save_and_termination_authority_byte_identical'] and not preservation['in_process_threads_forcibly_killed'],
            'Unsafe persistence/termination delta')
    require(tests['totals']==dict(tests=274,failures=0,errors=0,skipped=0),'274 fresh Android tests did not all pass')
    for key in ('previous_234_case_names_preserved','previous_234_test_sources_unchanged',
                'runtime_source_matches_candidate','compiled_java_inputs_match_candidate','new_test_matches'):
        require(tests[key],'Android preservation failed: '+key)
    latch=json.loads((native/'COOPERATIVE-ABORT-TESTS.json').read_text())
    waits=json.loads((native/'STARTUP-WAIT-VERIFICATION.json').read_text())
    require(latch['passed'] and latch['corrected_cases']==9 and waits['passed'] and waits['actual_function_scenarios']==20,
            'Targeted shutdown regressions missing')
    require(not proof['unknown_writers_abandoned'] and not proof['shutdown_timeout_changed'],'Unknown work or deadline safety changed')
    require(proof.get('rc2_optional_queued_prune_compiled') is True,
            'RC2 pruning must be present in the fully compiled native engine')
    rc2=json.loads((native/'RC2-OPTIONAL-QUEUE-PRUNE.json').read_text())
    require(rc2['only_verified_optional_no_callback_queued'] and
            not rc2['required_or_unknown_jobs_abandoned'] and
            not rc2['checkpoint_save_or_termination_authority_changed'],
            'RC2 optional job safety contract missing')
    native_cases=json.loads((native/'RC2-PRUNE-HOST-TESTS.json').read_text())
    require(native_cases['tests'] >= 8 and native_cases['tests']==native_cases['passed'],
            'RC2 native test cases missing')
    args.out.mkdir(parents=True,exist_ok=True)
    engine=native/'libkodi.so'
    require(sha(engine.read_bytes())==proof['native_sha256'],'Native bytes differ from full-build proof')
    packaged=args.out/'libkodi.so';shutil.copyfile(engine,packaged)
    ndk=Path(os.environ['ANDROID_HOME'])/'ndk'/os.environ['NDK_VER']/'toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip'
    run(ndk,'--strip-unneeded',packaged)
    bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
    with zipfile.ZipFile(args.parent) as z:
        old_engine=args.out/'parent-libkodi.so';old_engine.write_bytes(z.read(factory.ENGINE))
    before_exports=exports(run('readelf','--dyn-syms','--wide',old_engine,
                               output=args.out/'parent-dynamic-symbols.txt'))
    after_exports=exports(run('readelf','--dyn-syms','--wide',packaged,
                              output=args.out/'candidate-dynamic-symbols.txt'))
    require(not before_exports-after_exports and 'InfinityNativeActivity_onCreate' in after_exports,'Native export contract failed')
    needed=lambda file:sorted(re.findall(r'\(NEEDED\).*?\[(.*?)\]',run('readelf','-d','-W',file,
                              output=args.out/(file.stem+'-dependencies.txt'))))
    require(needed(old_engine)==needed(packaged),'Native companion dependency contract changed')
    factory.BASE_APK_SHA256=PARENT_SHA
    factory.BASE_ENGINE_SHA256=sha(old_engine.read_bytes())
    factory.JNI_ADDITIONS=set()
    ids=resource_ids(bt/'aapt2',args.parent,args.out/'base-resources.txt')
    require(ids==resource_ids(bt/'aapt2',args.donor,args.out/'donor-resources.txt'),'Android resource IDs changed')
    unsigned=args.out/'final-shutdown-unsigned.apk'
    natives,core=factory.merge(args.parent,args.donor,packaged,unsigned)
    old_manifest=run(bt/'aapt','dump','xmltree',args.parent,'AndroidManifest.xml',output=args.out/'base-manifest.txt')
    new_manifest=run(bt/'aapt','dump','xmltree',unsigned,'AndroidManifest.xml',output=args.out/'candidate-manifest.txt')
    verify_manifest(old_manifest,new_manifest)
    final=args.out/'Infinity-2103377-Shutdown-Drain-RC2.apk'
    run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
    cert=run(bt/'apksigner','verify','--verbose','--print-certs',final,output=args.out/'signing-verification.txt')
    require(SIGNER in cert.lower(),'Permanent signing identity changed')
    for version in (2,3):require(re.search(r'Verified using v'+str(version)+r' scheme[^\n]+true',cert),'Signing scheme missing')
    run(bt/'zipalign','-c','-p','4',final,output=args.out/'alignment.txt')
    badging=run(bt/'aapt','dump','badging',final,output=args.out/'badging.txt')
    require("package: name='com.projectinfinity.kodi' versionCode='2103377'" in badging,'Package/version changed')
    require("application-label:'Infinity'" in badging and 'application-debuggable' not in badging,'Branding/debug mode changed')
    preserved=factory.verify_bytes(args.parent,final,packaged)
    report=dict(schema=1,source_commit=os.environ['GITHUB_SHA'],native_source_commit=native_commit,file=final.name,
                apk_sha256=sha(final.read_bytes()),bytes=final.stat().st_size,
                parent_sha256=PARENT_SHA,unstripped_native_sha256=proof['native_sha256'],
                packaged_native_sha256=sha(packaged.read_bytes()),signer_certificate_sha256=SIGNER,
                fresh_android_tests=274,android_tested_source_commit=tests['source_commit'],
                android_current_source_byte_identical=True,targeted_abort_cases=9,targeted_startup_wait_cases=20,
                complete_native_engine_compiled=True,matched_lifecycle_integrated=True,
                existing_jni_declarations_preserved=natives,core_java_classes_preserved=core,
                native_exports_preserved=True,native_dependencies_preserved=True,
                locked_skin='1.0.5.211',playlist_browser_changed=False,
                rc2_optional_pruning=True,rc2_host_tests=native_cases['passed'],
                unknown_writes_abandoned=False,physical_shutdown_verified=False,
                device_accepted=False,locked=False,**preserved)
    (args.out/'FINAL-APK-VERIFICATION.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    for path in (unsigned,packaged,old_engine):path.unlink()
    print('PASS: RC2 optional job pruning compiled, permanently signed test APK, protected native/Android payload preserved. Fully loaded device shutdown still unverified.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('parent','donor','native','android','out'):parser.add_argument('--'+name,type=Path,required=True)
    package(parser.parse_args())
