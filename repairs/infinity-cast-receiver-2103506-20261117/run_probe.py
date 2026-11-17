from pathlib import Path
import json,subprocess,time,re
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'cast506-hardware-work';OUT=ROOT/'cast506-hardware-results';OUT.mkdir();result=None
def adb(*args,timeout=30):return subprocess.check_output(['adb',*map(str,args)],text=True,stderr=subprocess.STDOUT,timeout=timeout)
try:
 abis=adb('shell','getprop','ro.product.cpu.abilist').strip();assert 'arm64-v8a' in abis
 assert adb('shell','getprop','ro.kernel.qemu').strip()=='1'
 adb('install',WORK/'CI-ONLY.apk',timeout=180);adb('shell','am','start','-W','-n','com.projectinfinity.castqa.receiver/com.projectinfinity.castqa.ReceiverHardwareProbe')
 end=time.monotonic()+75
 while time.monotonic()<end:
  raw=adb('logcat','-d','-v','brief','InfinityReceiverProbe:I','*:S')
  for line in raw.splitlines():
   m=re.search(r'InfinityReceiverProbe[^:]*:\s*(\{.*\})',line)
   if m:result=json.loads(m[1])
  if result is not None:break
  time.sleep(1)
 assert result is not None,'NO_ACTUAL_PROBE_OUTCOME'
 result['scope']='API36 emulator, actual original506 ARM64 engine under native translation; codec inventory only, not physical hardware qualification';result['emulator_ABIs']=abis
 assert result['pass'] is True and result['status']=='PASS_SELECTED_CODEC_INVENTORY' and result['owned_codecs_after_close']==0,result
except BaseException as e:
 if result is None:result={'pass':False}
 result.update(pass_=False,wrapper_failure=str(e));result['pass']=False;raise
finally:
 (OUT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
 if (WORK/'BUILD.json').exists():(OUT/'BUILD.json').write_bytes((WORK/'BUILD.json').read_bytes())
 (OUT/'LOGCAT.txt').write_text(adb('logcat','-d','-v','threadtime'));print(json.dumps(result,indent=2))
