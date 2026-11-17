from pathlib import Path
import json,subprocess,time,re
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'cast510-dual-work';OUT=ROOT/'cast510-dual-results';OUT.mkdir();result=None
def adb(*args,timeout=30):return subprocess.check_output(['adb',*map(str,args)],text=True,stderr=subprocess.STDOUT,timeout=timeout)
try:
 abis=adb('shell','getprop','ro.product.cpu.abilist').strip();assert 'arm64-v8a' in abis and adb('shell','getprop','ro.kernel.qemu').strip()=='1'
 adb('shell','setprop','debug.checkjni','1')
 assert adb('shell','getprop','debug.checkjni').strip()=='1'
 adb('install',WORK/'CI-ONLY.apk',timeout=180);adb('shell','am','start','-W','-n','com.projectinfinity.castqa.pipeline/com.projectinfinity.kodi.InfinityCastProbeActivity')
 end=time.monotonic()+300
 while time.monotonic()<end:
  raw=adb('logcat','-d','-v','brief','InfinityPipelineProbe:I','AndroidRuntime:E','*:S')
  assert 'Process: com.projectinfinity.castqa.pipeline,' not in raw,'CI_PACKAGE_RUNTIME_CRASH; inspect retained logcat'
  saved=subprocess.run(['adb','shell','cat','/sdcard/Android/data/com.projectinfinity.castqa.pipeline/files/RESULT.json'],capture_output=True,text=True,timeout=15)
  if saved.returncode==0 and saved.stdout.strip():result=json.loads(saved.stdout)
  if result is not None:break
  time.sleep(1)
 assert result is not None,'NO_ACTUAL_PIPELINE_OUTCOME'
 result['emulator_ABIs']=abis;result['scope']='actual original510 ARM64 FFmpeg/JNI, directMain10HTTP/rangesandcodec_inventory; genuineMain8RADL realMediaCodec720p/AAC inbandCSD/cache; privateCIsoftwarebackend, notFoldhardwareorTVqualification'
 assert result['pass'] is True and result['status']=='PASS_ACTUAL_ARM64_DUAL_CAST_CORRECTIONS' and result['owned_native_after_close']==0,result
except BaseException as e:
 if result is None:result={'pass':False}
 result['wrapper_failure']=str(e);result['pass']=False
 if isinstance(e,subprocess.CalledProcessError):result['command_output']=str(e.output)[-4096:]
 raise
finally:
 (OUT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'LOGCAT.txt').write_text(adb('logcat','-d','-v','threadtime'))
 try:adb('pull','/sdcard/Android/data/com.projectinfinity.castqa.pipeline/files',OUT/'media',timeout=45)
 except Exception:pass
 print(json.dumps(result,indent=2))
