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
NATIVE_PIN='645b0e8b15c45d4c170a8b664073a87cb848b831'
JAVA_PIN='5a1a427cb5bdcc248b0e2a7887f9d6682ca53877'
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
    require(proof['source_commit']==NATIVE_PIN,'RC3 native source not the verified engine')
    require(tests['source_commit']==JAVA_PIN,'RC3 Android source not the newly tested 274-case build')
    require(proof['complete_native_engine_compiled'] and
            proof.get('rc3_early_local_snapshot_compiled') is True and
            proof.get('rc3_owner_specific_http_read_cancellation_compiled') is True and
            proof.get('rc3_python_stop_at_native_request_compiled') is True and
            proof.get('rc3_curl_cancel_semantic_error_compiled') is True and
            proof.get('rc3_sleep_and_monitor_original_implementation_verified') is True and
            proof.get('rc3_final_save_authority_unchanged') is True,
            'RC4 inherited native engine not verified')
    require(preservation.get('final_termination_authorization_byte_identical') is True and
            preservation.get('final_required_save_and_database_seal_stages_byte_identical') is True and
            preservation.get('unknown_writes_abandoned') is False,
            'Original required final-save or termination authority changed')
    require(tests['totals']==dict(tests=274,failures=0,errors=0,skipped=0),
            'RC3 original Android 274 tests are not all green')
    for key in ('previous_234_case_names_preserved','previous_234_test_sources_unchanged',
                'runtime_source_matches_candidate','compiled_java_inputs_match_candidate','new_test_matches'):
        require(tests[key],'RC3 Android preservation failed: '+key)
    require(proof.get('rc2_optional_queued_prune_compiled') is True,
            'Saved RC2 source correction was lost')
    rc2=json.loads((native/'RC2-OPTIONAL-QUEUE-PRUNE.json').read_text())
    require(rc2['only_verified_optional_no_callback_queued'] and
            not rc2['required_or_unknown_jobs_abandoned'] and
            not rc2['checkpoint_save_or_termination_authority_changed'],
            'RC2 optional job source preservation failed')
    rc2_cases=json.loads((native/'RC2-PRUNE-HOST-TESTS.json').read_text())
    require(rc2_cases['tests']==rc2_cases['passed']==9,'RC2 nine tests missing')
    latch=json.loads((native/'COOPERATIVE-ABORT-TESTS.json').read_text())
    waits=json.loads((native/'STARTUP-WAIT-VERIFICATION.json').read_text())
    require(latch['passed'] and latch['corrected_cases']==9 and waits['passed'] and
            waits['actual_function_scenarios']==20,'Original 2103377 fixes regressed')
    native_cases=json.loads((native/'RC3-HOST-VERIFICATION.json').read_text())
    require(native_cases['passed']==native_cases['total']==10,'RC3 immediate abort and Curl failure host tests not green')
    java_cases=json.loads((android/'RC3-ANDROID-VERIFICATION.json').read_text())
    require(java_cases['verified_unmodified_274_cases']==274 and
            java_cases['tests_freshly_executed'] and
            java_cases['rc3_two_java_templates_only'] and
            java_cases['grace_ms']==6500 and java_cases.get('rc4_live_pending_writers') is True and
            java_cases['no_automatic_force_close'] and
            java_cases['donor_sha256']==sha(args.donor.read_bytes()),
            'RC4 targeted recovery UI, tests or donor were not verified')
    rc5=json.loads((native/'RC5-OPTIONAL-STOP-DELTA.json').read_text())
    optional_cases=json.loads((native/'RC5-OPTIONAL-HOST-TESTS.json').read_text())
    require(optional_cases['passed']==optional_cases['total'] and optional_cases['passed']>=12
            and optional_cases['checks']['real_cpp_classifier_compiles_executes']
            and optional_cases['checks']['real_cpp_begin_checkpoint_compiles_executes']
            and optional_cases['checks']['seventeen_native_required_owners_preserved'],
            'RC5 optional Trakt and Continuity compiled host methods were not proven')
    require(proof.get('rc5_trakt_stop_only_compiled') is True and
            proof.get('rc5_continuity_stop_only_compiled') is True and
            proof.get('rc5_17_required_save_owners_unchanged') is True and
            proof.get('rc5_unclassified_script_save_gate_unchanged') is True,
            'Native engine does not contain proven RC5 optional-service stop-only')
    require(rc5['trakt_enabled_and_files_unchanged'] is True and
            rc5['trakt_updates_not_source_pinned'] is True and
            rc5['trakt_not_required_save_owner'] is True and
            rc5['trakt_receipt_fabricated'] is False and
            rc5['continuity_exact_source_pinned'] and
            rc5['other_foreign_writers_still_require_durability'] is True and
            rc5['all_17_required_owner_gates_unchanged'] is True,
            'Trakt cloud is optional but unknown Python save writers must remain protected')
    require(proof.get('rc5_full_loaded_fold_verified') is False and not proof['physical_shutdown_verified'],
            'Host-only RC5 cannot claim physical Fold success')
    gate=json.loads((native/'RC3-CURL-OWNER-CANCEL-DELTA.json').read_text())
    retirement=json.loads((native/'RC3-EARLY-PYTHON-ABORT-DELTA.json').read_text())
    sleep_audit=json.loads((native/'RC3-SLEEP-AND-FIVE-SERVICE-GATE.json').read_text())
    require(retirement['first_stop_before_playback_checkpoint'] and
            retirement['idempotent_reentry'] and
            not retirement['required_writer_retirement_waived'] and
            not sleep_audit['five_service_retirement_measured_on_fold'] and
            sleep_audit['native_monitor_wait_interruptible'],
            'Native Request stop timing, monitor wake or physical-proof boundary invalid')
    require(gate['required_saves_waived'] is False and
            gate['unverified_addon_writes_abandoned'] is False and
            gate['ordinary_running_unchanged'] is True,
            'Unsafe RC3 Curl cancellation scope')
    require(not proof['unknown_writers_abandoned'] and not proof['shutdown_timeout_changed'],
            'RC3 bypasses unknown writers or changes timeout')
    subprocess.run(['git','merge-base','--is-ancestor',NATIVE_PIN,os.environ['GITHUB_SHA']],check=True)
    subprocess.run(['git','merge-base','--is-ancestor',JAVA_PIN,os.environ['GITHUB_SHA']],check=True)
    # Native follow-up was intentionally authored after the 274-test Java
    # build; require its original Android production sources unchanged.
    java_delta=set(subprocess.check_output(
        ['git','diff','--name-only',JAVA_PIN,os.environ['GITHUB_SHA']],text=True).splitlines())
    java_protected={
       'repairs/shutdown-rc3-2103377/early_blocker_ui.py',
       'repairs/shutdown-rc3-2103377/android_stage.py',
       '.github/workflows/infinity-2103377-rc3-android.yml',
    }
    require(not (java_delta & java_protected) and
            not any(path.startswith('repairs/android-checkpoint-shutdown/runtime/android/')
                    for path in java_delta),
            'Approved 274-tested Java sources changed after verification')
    # The native owner/saver inputs may not change after the green native SHA.
    native_delta=set(subprocess.check_output(
        ['git','diff','--name-only',NATIVE_PIN,os.environ['GITHUB_SHA']],text=True).splitlines())
    # RC4 adds only source-controlled UI packaging and add-on overlay evidence.
    # Forbid modifying the native RC3 repair input scripts or any source overlay,
    # rather than assuming all new docs/tests belong to the frozen RC3 whitelist.
    native_locked={
       'repairs/shutdown-rc3-2103377/early_retirement.py',
       'repairs/shutdown-rc3-2103377/early_local_snapshot.py',
       'repairs/shutdown-rc3-2103377/cancel_owned_curl.py',
       'repairs/shutdown-rc3-2103377/native_ci.py',
       'repairs/shutdown-final-2103377/native_ci.py',
    }
    require(not (native_delta & native_locked) and
            not any(path.startswith('repairs/android-checkpoint-shutdown/runtime/native/')
                    for path in native_delta),
            'Verified RC3 native correction source changed after native build')
    require(sha((native/'libkodi.so').read_bytes())==proof['native_sha256'],
            'RC3 compiled native artifact hash does not match build proof')
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
    final=args.out/'Infinity-2103377-RC5-Optional-Shutdown-Signed-Test.apk'
    run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
    cert=run(bt/'apksigner','verify','--verbose','--print-certs',final,output=args.out/'signing-verification.txt')
    require(SIGNER in cert.lower(),'Permanent signing identity changed')
    for version in (2,3):require(re.search(r'Verified using v'+str(version)+r' scheme[^\n]+true',cert),'Signing scheme missing')
    run(bt/'zipalign','-c','-p','4',final,output=args.out/'alignment.txt')
    badging=run(bt/'aapt','dump','badging',final,output=args.out/'badging.txt')
    require("package: name='com.projectinfinity.kodi' versionCode='2103377'" in badging,'Package/version changed')
    require("application-label:'Infinity'" in badging and 'application-debuggable' not in badging,'Branding/debug mode changed')
    preserved=factory.verify_bytes(args.parent,final,packaged)
    report=dict(schema=1,source_commit=os.environ['GITHUB_SHA'],native_source_commit=NATIVE_PIN,
                android_source_commit=JAVA_PIN,rc3_host_tests=10,rc3_grace_ms=2500,rc4_grace_ms=6500,rc4_dynamic_pending=True,
                rc5_optional_host_tests=optional_cases['passed'],
                rc5_trakt_cloud_entry_stop_only=True,rc5_continuity_diagnostic_stop_only=True,
                rc5_trakt_provider_source_modified=False,
                rc5_nonoptional_writers_still_required=True,
                rc5_skin_update_required=False,
                rc3_python_abort_at_request=True,rc3_cancelled_curl_uses_io_failure=True,
                rc3_five_services_physically_confirmed=False,
                rc3_curl_read_cancel_compiled=True,rc3_early_provisional_saves=True,
                rc3_automated_quit_when_unverified_writer_pending=False,file=final.name,
                apk_sha256=sha(final.read_bytes()),bytes=final.stat().st_size,
                parent_sha256=PARENT_SHA,unstripped_native_sha256=proof['native_sha256'],
                packaged_native_sha256=sha(packaged.read_bytes()),signer_certificate_sha256=SIGNER,
                fresh_android_tests=274,android_tested_source_commit=tests['source_commit'],
                android_current_source_byte_identical=True,targeted_abort_cases=9,targeted_startup_wait_cases=20,
                complete_native_engine_compiled=True,matched_lifecycle_integrated=True,
                existing_jni_declarations_preserved=natives,core_java_classes_preserved=core,
                native_exports_preserved=True,native_dependencies_preserved=True,
                locked_skin='1.0.5.211',playlist_browser_changed=False,
                rc2_optional_pruning=True,rc2_host_tests=rc2_cases['passed'],
                rc3_native_compiled_at_run=38498786704,
                rc3_android_compiled_at_run=38495506871,
                unknown_writes_abandoned=False,physical_shutdown_verified=False,
                device_accepted=False,locked=False,**preserved)
    (args.out/'FINAL-APK-VERIFICATION.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    for path in (unsigned,packaged,old_engine):path.unlink()
    print('PASS RC5 PACKAGE: original signed baseline + fully compiled RC5 native optional stop + freshly verified 274 Android tests; physical Fold shutdown still NOT verified.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('parent','donor','native','android','out'):parser.add_argument('--'+name,type=Path,required=True)
    package(parser.parse_args())
