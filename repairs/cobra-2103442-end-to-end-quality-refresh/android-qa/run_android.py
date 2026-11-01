"""One exact signed442 baseline; optional original-key higher candidate install-over."""
import argparse,hashlib,json,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2]
sys.path.insert(0,str(R/'repairs/cobra-2103435-followups/drawer-only/android-qa'))
import android_probe435 as probe
APK_SHA='88f968c53eb3d306db57de72419744f427554f7146f4f86e147b192f4f5e0bf5'
CERT='d7adeb68e9341596a02bd3262b737a0f45fc6e771ed7e60285437e833b58c6d7'
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def run(baseline,driver,sdk,out):
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
 except Exception as error:report['status']='FAILED_OR_BLOCKED_NOT_A_PASS';report['error']=str(error);raise
 finally:
  for name,args in [('logcat',('logcat','-d','-v','threadtime')),('activities',('shell','dumpsys','activity','activities')),('memory',('shell','dumpsys','meminfo',probe.PACKAGE))]:
   (out/(name+'.txt')).write_text(probe.adb(*args,check=False))
  save(out/'OUTCOME.json',report)
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for name in ['baseline','driver','sdk','out']:p.add_argument('--'+name,type=Path,required=True)
 run(**vars(p.parse_args()))
