"""One exact signed442 baseline; optional original-key higher candidate install-over."""
import argparse,hashlib,json,subprocess,sys,time,zipfile,math
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2]
sys.path.insert(0,str(R/'repairs/cobra-2103435-followups/drawer-only/android-qa'))
import android_probe435 as probe
APK_SHA='88f968c53eb3d306db57de72419744f427554f7146f4f86e147b192f4f5e0bf5'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def run(baseline,driver,sdk,out,candidate_dir):
 out.mkdir(parents=True,exist_ok=False)
 signature=subprocess.check_output([str(sdk/'apksigner'),'verify','--verbose','--print-certs',str(baseline)],text=True)
 assert 'Signer #1 certificate SHA-256 digest: '+CERT in signature
 (out/'SIGNATURE.txt').write_text(signature)
 report=dict(phase='SIGNED442_BASELINE',physical_Fold='NOT_RUN',Infinity='NOT_LAUNCHED',shutdown='NOT_RUN')
 try:
  probe.probe(baseline,out/'first-screen',APK_SHA)
  jar=driver/'CobraQualityDriver.jar';build=json.loads((driver/'BUILD.json').read_text());pin=hashlib.sha256(jar.read_bytes()).hexdigest();assert pin==build['jar_sha256']
  for name,want in build['sources'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==want
  probe.adb('push',str(jar),'/data/local/tmp/CobraQualityDriver.jar');assert probe.adb('shell','sha256sum','/data/local/tmp/CobraQualityDriver.jar').split()[0]==pin
  remote='/sdcard/cobra-quality-baseline-'+str(time.monotonic_ns())
  result=subprocess.run(['adb','shell','CLASSPATH=/system/framework/android.test.runner.jar:/system/framework/uiautomator.jar:/data/local/tmp/CobraQualityDriver.jar','ANDROID_DATA=/data/local/tmp','/system/bin/app_process','/system/bin','qa.CobraQualityDriver','baseline',remote,pin],capture_output=True,text=True,timeout=600)
  (out/'stdout.txt').write_text(result.stdout);(out/'stderr.txt').write_text(result.stderr);probe.adb('pull',remote,str(out/'native'),check=False,timeout=90)
  assert result.returncode==0,'Public input journey failed; inspect preserved evidence before another run'
  report['status']='PASS_SELECTED_BASELINE_JOURNEY'
  probe.adb('shell','input','keyevent','KEYCODE_HOME')
  warm=probe.adb('shell','am','start','-W','-n',probe.PACKAGE+'/.InfinityLiveActivity');(out/'baseline-warm-launch.txt').write_text(warm)
  with zipfile.ZipFile(baseline) as z:native={n for n in z.namelist() if n.startswith('lib/arm64-v8a/') and n.endswith('.so')}
  report['baseline_warm_notice']=probe.acknowledge_known_notice_after_launch(warm,out/'baseline-warm-notice',native)
  if candidate_dir.is_dir():
   apk=candidate_dir/'Infinity-2103443-Combined-Original-Signer.apk';receipt=json.loads((candidate_dir/'BUILD-RECEIPT.json').read_text());expected=hashlib.file_digest(apk.open('rb'),'sha256').hexdigest()
   assert receipt['versionCode']==2103443 and receipt['signed_apk_sha256']==expected
   signature=subprocess.check_output([str(sdk/'apksigner'),'verify','--verbose','--print-certs',str(apk)],text=True)
   assert 'Signer #1 certificate SHA-256 digest: '+CERT in signature;(out/'CANDIDATE-SIGNATURE.txt').write_text(signature)
   uid=probe.adb('shell','pm','list','packages','-U',probe.PACKAGE).strip()
   budget=min(120,max(30,math.ceil(apk.stat().st_size/(10*1024*1024))+45));started=time.monotonic()
   try:report['install_client']=probe.adb('install','--no-incremental','-r',str(apk),timeout=budget)
   except subprocess.TimeoutExpired:report['install_client']='CLIENT_TIMEOUT; EXACT_INSTALLED_BYTES_REQUIRED'
   report['candidate_install']=probe.confirm_installed_apk(expected,budget);report['install_seconds']=time.monotonic()-started
   assert probe.adb('shell','pm','list','packages','-U',probe.PACKAGE).strip()==uid,'Update must preserve application UID'
   launched=probe.adb('shell','am','start','-W','-n',probe.PACKAGE+'/.InfinityLiveActivity');(out/'candidate-launch.txt').write_text(launched)
   report['candidate_notice']=probe.acknowledge_known_notice_after_launch(launched,out/'candidate-launch-notice',native)
   remote='/sdcard/cobra-quality-candidate-'+str(time.monotonic_ns())
   result=subprocess.run(['adb','shell','CLASSPATH=/system/framework/android.test.runner.jar:/system/framework/uiautomator.jar:/data/local/tmp/CobraQualityDriver.jar','ANDROID_DATA=/data/local/tmp','/system/bin/app_process','/system/bin','qa.CobraQualityDriver','candidate',remote,pin],capture_output=True,text=True,timeout=600)
   (out/'candidate-stdout.txt').write_text(result.stdout);(out/'candidate-stderr.txt').write_text(result.stderr);probe.adb('pull',remote,str(out/'candidate-native'),check=False,timeout=90)
   assert result.returncode==0,'Candidate public-input journey failed; do not retry unchanged'
   probe.adb('shell','input','keyevent','KEYCODE_HOME');warm=probe.adb('shell','am','start','-W','-n',probe.PACKAGE+'/.InfinityLiveActivity');(out/'candidate-warm-launch.txt').write_text(warm)
   report['candidate_warm_notice']=probe.acknowledge_known_notice_after_launch(warm,out/'candidate-warm-notice',native)
   report['status']='PASS_ORIGINAL_KEY_INSTALL_OVER_AND_SELECTED_PUBLIC_INPUT_MATRIX'
 except Exception as error:report['status']='FAILED_OR_BLOCKED_NOT_A_PASS';report['error']=str(error);raise
 finally:
  for name,args in [('logcat',('logcat','-d','-v','threadtime')),('activities',('shell','dumpsys','activity','activities')),('memory',('shell','dumpsys','meminfo',probe.PACKAGE))]:
   (out/(name+'.txt')).write_text(probe.adb(*args,check=False))
  save(out/'OUTCOME.json',report)
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for name in ['baseline','driver','sdk','out','candidate-dir']:p.add_argument('--'+name,type=Path,required=True)
 run(**vars(p.parse_args()))
