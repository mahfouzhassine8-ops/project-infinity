"""Selected separate-package Android Cast probe. No Kodi launch/shutdown/reset."""
from pathlib import Path
import json,re,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'cast504-android-work';OUT=ROOT/'cast504-android-results';OUT.mkdir(exist_ok=True)
def adb(*args,timeout=30):return subprocess.check_output(['adb',*map(str,args)],text=True,stderr=subprocess.STDOUT,timeout=timeout)
result=None;stage='installation'
try:
 abis=adb('shell','getprop','ro.product.cpu.abilist').strip();assert 'arm64-v8a' in abis,'ARM64_NATIVE_BRIDGE_REQUIRED'
 # APK extraction and multi-DEX verification are not connection/encoder timeouts.
 adb('install',WORK/'CI-ONLY.apk',timeout=180)
 stage='launch'
 (OUT/'LAUNCH.txt').write_text(adb('shell','am','start','-W','-n','com.projectinfinity.castqa/com.projectinfinity.kodi.InfinityCastProbeActivity'))
 stage='probe_execution'
 deadline=time.monotonic()+180;next_update=0
 while time.monotonic()<deadline:
  raw=adb('logcat','-d','-v','brief','InfinityCastProbe:I','*:S')
  for line in raw.splitlines():
   found=re.search(r'InfinityCastProbe[^:]*:\s*(\{.*\})',line)
   if found:result=json.loads(found[1])
  if result is not None:break
  if time.monotonic()>next_update:print('Waiting for selected JNI/relay probe outcome',flush=True);next_update=time.monotonic()+15
  time.sleep(1)
 assert result is not None,'SELECTED_PROBE_DID_NOT_REPORT'
 result['emulator_ABIs']=abis;result['scope']='Actual ARM64 binary under Android native translation, original504 engine and DEX; separate CI package; no physical receiver claim'
 assert result['pass'],result
 def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-show_packets','-show_data_hash','sha256','-of','json',str(p)]))
 rows=[]
 for name in ('transients51','44100-odd','32000','main10-eac3'):
  target=OUT/(name+'.mp4');adb('pull','/sdcard/Android/data/com.projectinfinity.castqa/files/'+name+'.mp4',target)
  a,b=probe(WORK/'fixtures'/str(name+'.mkv')),probe(target)
  ap=[p for p in a['packets'] if p['codec_type']=='video'];bp=[p for p in b['packets'] if p['codec_type']=='video']
  assert [p['data_hash'] for p in ap]==[p['data_hash'] for p in bp],name+' video changed'
  offset=10-float(a['format']['start_time'])
  assert all(abs(float(x['pts_time'])+offset-float(y['pts_time']))<.000002 for x,y in zip(ap,bp)),name+' video PTS'
  assert all(abs(float(x['dts_time'])+offset-float(y['dts_time']))<.000002 for x,y in zip(ap,bp) if 'dts_time' in x),name+' video DTS'
  audio=next(s for s in b['streams'] if s['codec_type']=='audio');assert audio['codec_name']=='aac' and audio['profile']=='LC' and audio['channels']==2
  for kind in ('video','audio'):
   packets=[p for p in b['packets'] if p['codec_type']==kind];dts=[p['dts'] for p in packets]
   assert all(y>x for x,y in zip(dts,dts[1:])),name+' monotonic '+kind
   if kind=='audio':assert all('K' in p['flags'] for p in packets),name+' AAC sync flags'
  rows.append({'case':name,'video_packets':len(ap),'video_byte_exact':True,'video_PTS_DTS_preserved':True,'AAC_LC_stereo':True,'monotonic_DTS':True})
 result.update(status='PASS_ACTUAL_ARM64_ANDROID_AAC_JNI_RELAY',output_proof=rows,physical_TV='NOT_TESTED',owner_data='NOT_ACCESSED',shutdown='NOT_SELECTED')
except BaseException as error:
 if result is None:result={'pass':False}
 result['pass']=False
 result.update(status='FAIL_SELECTED_ANDROID_CAST_AUDIO',wrapper_failure=str(error),wrapper_stage=stage)
 if stage=='installation':result['native_encoder_execution']='NOT_RUN'
 if isinstance(error,subprocess.CalledProcessError):result['command_output']=str(error.output)[-2048:];raise
finally:
 try:(OUT/'LOGCAT.txt').write_text(adb('logcat','-d','-v','threadtime'))
 except Exception as error:(OUT/'LOGCAT-ERROR.txt').write_text(str(error))
 (OUT/'ANDROID-CAST-AUDIO.json').write_text(json.dumps(result,indent=2)+'\n')
 if (WORK/'BUILD.json').exists():(OUT/'BUILD.json').write_bytes((WORK/'BUILD.json').read_bytes())
 print(json.dumps(result,indent=2))
