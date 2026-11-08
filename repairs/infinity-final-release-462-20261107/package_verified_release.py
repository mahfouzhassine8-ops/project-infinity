"""Package unchanged signed files only after actual execution and visual gates.

No APK signing, data migration, provider edits or acceptance-pointer update.
Publication is a separate explicit workflow operation after this succeeds.
"""
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
import argparse,hashlib,json,os,re,shutil,subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'repairs/dual-experience-isolation-2103420'))
from inventory import file_sha,load,save
from release_gate import require
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
PINS={2103464:'eb4ea5594d18d83c5638d10c0c1b22b2124e6c61c303d41908108dcd02b6ae54',2103465:'bec094103bca08abce081038669428ce9babf0aab1d99ca4cb0ec09ca1a729e9'}
SCREENS=['front-yes-home.png','front-no-home.png','inner-yes-home.png','inner-no-home.png','Info-Play.png','Info-Trailer.png','Downloads-Files.png']
CASES=['authenticated_current_external61_268_before_exact462_update','actual_462_to464_install_over_and78_signed_module_files',*['real_native_Search_cycle_'+str(i) for i in range(1,9)],'actual_watched_and_unwatched_popup_callbacks','actual_Info_Play_control','actual_Info_Trailer_control','native_Downloads_Files_observation','actual_464_to465_forward_recovery78_files_and_data_preservation']

def copy_verified(source,target,expected):
    require(file_sha(source)==expected,'EXACT_SIGNED_SOURCE')
    with source.open('rb') as src,target.open('wb') as dst:
        while block:=src.read(1024*1024):require(dst.write(block)==len(block),'COMPLETE_COPY')
        dst.flush();os.fsync(dst.fileno())
    require(file_sha(target)==expected,'UNCHANGED_SIGNED_COPY')

def package(candidate,recovery,android,review,sdk,out):
    require(not out.exists(),'FRESH_RELEASE_OUTPUT')
    report=load(android/'ANDROID-VERIFICATION.json');manual=load(review)
    require(report['status']=='PASS_SELECTED_ANDROID_EXECUTION_VISUAL_REVIEW_PENDING','ACTUAL_ANDROID_EXECUTION_MUST_PASS')
    cases={r['case']:r for r in report['cases']}
    require(all(cases.get(n,{}).get('status')=='PASS' for n in CASES),'ALL_SELECTED_RUNTIME_CASES_REQUIRED')
    require(manual['status']=='PASS_SELECTED_ENGINEERING_RELEASE_GATES' and manual['APK_sha256']=={str(k):v for k,v in PINS.items()},'EXACT_MANUAL_ENGINEERING_REVIEW')
    require(manual['ANDROID_VERIFICATION_sha256']==file_sha(android/'ANDROID-VERIFICATION.json'),'ACTUAL_REPORT_BOUND_TO_REVIEW')
    require(manual['VERIFICATION_md_sha256']==file_sha(HERE/'VERIFICATION.md'),'FINAL_CONCISE_REPORT_BOUND_TO_REVIEW')
    require(manual['physical_Fold']=='PENDING_ONE_FINAL_USER_TEST' and manual['accepted_pointer_updated'] is False,'NO_FOLD_ACCEPTANCE_CLAIM')
    require(manual['Downloads_Files_entries_reviewed'] is True and manual['white_line_review_completed'] is True,'MANDATORY_FILES_AND_WHITE_LINE_REVIEW')
    require(set(manual['screenshots'])==set(SCREENS),'ALL_SELECTED_SURFACES_REQUIRE_REVIEW')
    for name in SCREENS:
        row=manual['screenshots'][name]
        require(row['sha256']==file_sha(android/name) and row['status']=='PASS_SELECTED_CI_VISUAL_REVIEW','SOURCE_BOUND_VISUAL_REVIEW:'+name)
    scope=load(HERE/'ANDROID-SCOPE.json')
    require(scope['operation']=='verify-signed464465','EXACT_TEST_SCOPE')
    for version,path in [(2103464,candidate),(2103465,recovery)]:
        require(file_sha(path)==PINS[version],'EXACT_SIGNED_RELEASE_APK')
        receipt=load(path.parent/'BUILD-RECEIPT.json')
        require(receipt['source']==scope['signed_APKs'][str(version)]['source'] and receipt['signed_apk_sha256']==PINS[version] and receipt['versionCode']==version,'EXACT_SIGNED_SOURCE_RECEIPT')
        signature=subprocess.check_output([str(sdk/'apksigner'),'verify','--verbose','--print-certs',str(path)],text=True)
        require(re.findall(r'certificate SHA-256 digest: ([0-9a-f]+)',signature)==[CERT],'ONE_ORIGINAL_PERMANENT_CERTIFICATE')
        for scheme in ('v1','v2','v3'):require(re.search(r'Verified using '+scheme+r' scheme .*: true',signature),'SIGNATURE_SCHEME:'+scheme)
    out.mkdir(parents=True)
    primary=out/'Infinity-2103464-Combined-Original-Signer.apk'
    copy_verified(candidate,primary,PINS[2103464])
    recovery_zip=out/'Infinity-2103465-Matching-Forward-Recovery.zip'
    files={
        'Infinity-2103465-Combined-Original-Signer.apk':recovery,
        'README.md':HERE/'RECOVERY-README.md',
        'BUILD-RECEIPT.json':recovery.parent/'BUILD-RECEIPT.json',
        'SIGNATURE.txt':recovery.parent/'SIGNATURE.txt',
        'RECOVERY-CLARIFICATION.json':HERE/'RECOVERY-CLARIFICATION.json',
        'APK-PRESERVATION.json':recovery.parent/'preservation/APK-PRESERVATION.json',
    }
    with ZipFile(recovery_zip,'w',compression=ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for name,path in sorted(files.items()):
            info=ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=ZIP_DEFLATED;info.external_attr=0o100644<<16;info.file_size=path.stat().st_size
            with path.open('rb') as src,z.open(info,'w') as dst:
                while block:=src.read(1024*1024):dst.write(block)
        info=ZipInfo('SHA256SUMS',(1980,1,1,0,0,0));info.compress_type=ZIP_DEFLATED;info.external_attr=0o100644<<16
        z.writestr(info,PINS[2103465]+'  Infinity-2103465-Combined-Original-Signer.apk\n')
    with recovery_zip.open('rb') as stream:os.fsync(stream.fileno())
    with ZipFile(recovery_zip) as z:
        with z.open('Infinity-2103465-Combined-Original-Signer.apk') as stream:
            require(hashlib.file_digest(stream,'sha256').hexdigest()==PINS[2103465],'EXACT_RECOVERY_APK_INSIDE_PACKAGE')
    shutil.copyfile(HERE/'VERIFICATION.md',out/'VERIFICATION.md')
    shutil.copyfile(review,out/'ENGINEERING-REVIEW.json')
    shutil.copyfile(android/'ANDROID-VERIFICATION.json',out/'ANDROID-VERIFICATION.json')
    save(out/'PUBLICATION-GATE.json',dict(status='PASS_ONE_COMBINED_APK_AND_MATCHING_FORWARD_RECOVERY_READY',candidate_sha256=PINS[2103464],recovery_apk_sha256=PINS[2103465],recovery_package_sha256=file_sha(recovery_zip),original_certificate_sha256=CERT,Android=report['status'],manual_review_sha256=file_sha(review),physical_Fold='PENDING_ONE_FINAL_USER_TEST',accepted_pointer_updated=False,APK_bytes_changed_by_packaging=False,public_release_created=False))
    sums=''.join(file_sha(p)+'  '+p.name+'\n' for p in sorted(out.iterdir()) if p.is_file())
    (out/'SHA256SUMS').write_text(sums)
    print('PASS exact signed combined APK and matching recovery; publication remains separate')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('candidate','recovery','android','review','sdk','out'):p.add_argument('--'+n,type=Path,required=True)
    package(**vars(p.parse_args()))
