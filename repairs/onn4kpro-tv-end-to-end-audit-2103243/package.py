#!/usr/bin/env python3
"""Package the audited Android layer only. Never rebuild Kodi/native or certify physical playback."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,re,shutil,zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
VERSION=2103243;RELEASE='1.0.9-Cobra-Onn4KPro-TV-End-To-End-Audit-RC23'
PACKAGE='com.projectinfinity.kodi'
BASE_SHA='2e0480ae719a319125ad9482840439e3e8406fe47c8181424469a719b44b9754'
ENGINE_SHA='670eb63be5c42a82224229215a7cb38b9e0d9ab393e394247f199d2bacc8c105'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
BASE_COMMIT='f95e84676932470ec6093bf6408a920d40239702'
DEX=re.compile(r'classes\d*\.dex$')
SIGNATURE=re.compile(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))$',re.I)
def sha(data):return hashlib.sha256(data).hexdigest()
def require(value,message):
 if not value:raise RuntimeError(message)
def load(path):return json.loads(path.read_text())
def write(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--base-apk',type=Path,required=True);p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 source,base,build,out=[v.resolve() for v in (a.source,a.base_apk,a.build_dir,a.out)];out.mkdir(parents=True,exist_ok=True)
 require(sha(base.read_bytes())==BASE_SHA,'Not exact locked RC22 APK')
 tests=load(ROOT/'audit243/candidate-android/android-test-summary.json')
 require(tests['mode']=='rc23-candidate' and tests['tests']==20 and tests['passed']==20 and not tests['unexpected_failures'],'Mandatory Android regression gate failed')
 preservation=load(ROOT/'audit243/source/source-preservation.json')
 require(preservation['baseline_commit']==BASE_COMMIT and len(preservation['changed_declarations'])==29 and not preservation['removed_declarations'],'Declaration preservation gate missing')
 spec=importlib.util.spec_from_file_location('locked_pack',ROOT/'repairs/onn4kpro-tv-final-product-audit-2103242/package.py');pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
 pack.VERSION=VERSION;pack.RELEASE=RELEASE;pack.BASE_APK_SHA256=BASE_SHA
 # Reuse only audited staging/JNI/merge machinery. RC23 explicitly supersedes two old policy
 # claims: the blanket 120ms edge cooldown and automatic non-user-pause recovery.
 def source_preservation(folder):
  receipt=load(ROOT/'engine/background-resume-source.json')
  require(receipt['version_code']==VERSION and receipt['version_name']==RELEASE,'Wrong candidate receipt')
  require(receipt['tv_remote_edge_guard_ms'] is None and receipt['tv_unexpected_non_user_pause_recovery'] is False,'Obsolete policy receipt was not superseded')
  require(receipt['tv_target_abi']=='armeabi-v7a' and receipt['native_engine_rebuilt'] is False,'TV/native boundary changed')
  for name,row in receipt['files'].items():require(sha((folder/name).read_bytes())==row['after'],'Source receipt drift: '+name)
  for name,digest in load(ROOT/'audit243/source/source-file-hashes-after.json').items():require(sha((folder/name).read_bytes())==digest,'Source changed after audit: '+name)
 pack.source_preservation=source_preservation
 ids=pack.prepare(source,base,build,out)
 env=dict(os.environ,KODI_ANDROID_KEY_ALIAS='androiddebugkey',KODI_ANDROID_KEY_PASSWORD='android',KODI_ANDROID_STORE_PASSWORD='android',KODI_ANDROID_STORE_FILE=str(Path.home()/'.android/debug.keystore'))
 pack.run('./gradlew','--no-daemon','--console=plain',':xbmc:assembleRelease',cwd=build,env=env)
 donor=build/'xbmc/build/outputs/apk/release/xbmc-release.apk';require(donor.is_file(),'Android donor missing')
 bt=Path(os.environ['ANDROID_HOME'])/'build-tools/34.0.0'
 require(ids==pack.resource_ids(bt/'aapt2',donor,out/'compiled-resources.txt'),'Pinned resource IDs changed')
 unsigned=out/'RC23-unsigned.apk';natives,core=pack.merge(base,donor,unsigned)
 old_manifest=pack.run(bt/'aapt','dump','xmltree',base,'AndroidManifest.xml',output=out/'base-manifest.txt')
 new_manifest=pack.run(bt/'aapt','dump','xmltree',unsigned,'AndroidManifest.xml',output=out/'manifest.txt')
 pack.verify_manifest_pair(old_manifest,new_manifest)
 for key in ('INFINITY_KEYSTORE_B64','INFINITY_STORE_PASSWORD','INFINITY_KEY_PASSWORD','INFINITY_KEY_ALIAS'):require(bool(os.environ.get(key)),'Missing permanent signing input '+key)
 final=out/'Infinity-1.0.9-Cobra-Onn4KPro-TV-End-To-End-Audit-RC23.apk'
 pack.run('bash',ROOT/'scripts/sign-infinity71.sh',unsigned,final)
 cert=pack.run(bt/'apksigner','verify','--verbose','--print-certs',final,output=out/'signing-verification.txt')
 require(CERT in cert.lower(),'Permanent signer changed')
 pack.run(bt/'zipalign','-c','-p','4',final,output=out/'zipalign-verification.txt')
 badging=pack.run(bt/'aapt','dump','badging',final,output=out/'badging.txt')
 require(f"package: name='{PACKAGE}' versionCode='{VERSION}' versionName='{RELEASE}'" in badging,'APK identity mismatch')
 require("native-code: 'armeabi-v7a'" in badging and "application-label:'Infinity'" in badging and 'application-debuggable' not in badging,'APK ABI/label/debug mismatch')
 with zipfile.ZipFile(base) as old,zipfile.ZipFile(final) as new:
  an,bn=set(old.namelist()),set(new.namelist())
  require(len(an)==len(old.namelist()) and len(bn)==len(new.namelist()),'Duplicate APK entries')
  require(new.testzip() is None,'APK CRC failure')
  kept={n for n in an if n!='AndroidManifest.xml' and not DEX.fullmatch(n) and not SIGNATURE.fullmatch(n)}
  require(bn==kept|{'AndroidManifest.xml'}|{n for n in bn if DEX.fullmatch(n) or SIGNATURE.fullmatch(n)},'Unexpected payload inventory')
  for name in sorted(kept):require(old.read(name)==new.read(name),'Protected APK payload changed: '+name)
  require(sha(new.read('lib/armeabi-v7a/libkodi.so'))==ENGINE_SHA,'Native engine changed')
  require(pack.dex_contract(old)[0]==pack.dex_contract(new)[0],'JNI descriptors changed')
  joined=b''.join(new.read(n) for n in bn if DEX.fullmatch(n))
  for token in (b'cobra_tv_movies_landing_search_2103240',b'cobra_tv_shows_landing_search_2103240',b'cobraTvRecordConsumedKey',b'cobraTvFocusTargetCurrent',b'non-user-pause-observed',b'no_auto_resume=true',b'cobraTvWireLinearFocus',b'cobra_power_switch_infinity',b'cobra_power_exit',b'cobra_power_cancel',b'CobraTvPlayingDot',b'NORMAL_PULSE_MS',b'CINEMA_PULSE_MS',b'buffer_observed_no_restart',b'Type a title or narrow by genre',b'Return to Multi-View'):
   require(token in joined,'Compiled audit marker missing: '+repr(token))
  for token in (b'experience-settings-infinity',b'experience-settings-cobra',b'On-screen keyboard',b'unexpected-pause-recovery'):
   require(token not in joined,'Obsolete behavior/UI marker remained: '+repr(token))
  native_count=sum(n.startswith('lib/') and not n.endswith('/') for n in kept);asset_count=sum(n.startswith('assets/') and not n.endswith('/') for n in kept)
 digest=sha(final.read_bytes());(out/'Infinity-TV-RC23.sha256').write_text(digest+'  '+final.name+'\n')
 report={'version_code':VERSION,'version_name':RELEASE,'package':PACKAGE,'target_abi':'armeabi-v7a','baseline_commit':BASE_COMMIT,'baseline_apk_sha256':BASE_SHA,
  'apk':final.name,'apk_sha256':digest,'signer_certificate_sha256':CERT,'native_engine_sha256':ENGINE_SHA,
  'native_files_byte_identical':native_count,'asset_files_byte_identical':asset_count,'android_resources_byte_identical':True,
  'protected_payload_entries':len(kept),'resource_id_map_verified':len(ids),'jni_declarations_preserved':natives,'native_facing_java_classes_preserved':core,
  'android_view_regressions_executed':20,'android_view_regressions_passed':20,'source_preservation':preservation,
  'native_engine_rebuilt':False,'phone_fold_branch_modified':False,'zipalign_verified':True,'permanent_signer_verified':True,
  'physical_onn_device_tested':False,'real_provider_decoder_tested':False,'shipping_certified':False,'candidate_locked':False}
 write(out/'RC23-VERIFICATION.json',report)
 shutil.copy2(ROOT/'audit243/candidate-android/android-test-summary.json',out/'android-test-summary.json')
 for name in ('AUDIT.md','DEVICE-TEST.md','ROLLBACK.md'):
  require((HERE/name).is_file(),'Missing deliverable '+name);shutil.copy2(HERE/name,out/name)
 shutil.copy2(ROOT/'audit243/source/source-preservation.json',out/'source-preservation.json')
 unsigned.unlink()
 print('PASS: signed RC23 candidate; 20 Android-view tests passed; native/assets/resources preserved. Physical TV acceptance pending.')
 print('APK SHA256',digest)
if __name__=='__main__':main()
