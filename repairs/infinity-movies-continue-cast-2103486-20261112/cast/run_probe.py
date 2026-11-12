"""Execute only the disposable Cast component probe. No Infinity shutdown."""
from pathlib import Path
import json,re,subprocess,sys,time
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
def adb(*args):return subprocess.check_output(['adb',*args],text=True,stderr=subprocess.STDOUT)
adb('logcat','-c')
adb('install',str(Path(sys.argv[2]).resolve()))
launch=adb('shell','am','start','-W','-n','com.projectinfinity.castqa/com.projectinfinity.kodi.InfinityCastProbeActivity')
(out/'launch.txt').write_text(launch)
deadline=time.monotonic()+35;result=None
while time.monotonic()<deadline:
 logs=adb('logcat','-d','-v','brief','InfinityCastProbe:I','*:S')
 for line in logs.splitlines():
  match=re.search(r'InfinityCastProbe[^:]*:\s*(\{.*\})',line)
  if match:result=json.loads(match[1])
 if result is not None:break
 time.sleep(.5)
(out/'component.logcat.txt').write_text(adb('logcat','-d','-v','threadtime'))
if result is None:result=dict(schema=1,**{'pass':False},reason='Probe result not emitted within 35 seconds')
result.update(scope='Cast SDK/resource/UI-thread, private isolated HTTP relay/resource and explicit-selection guard; no real receiver or Infinity playback',
              original_APK_modified=False,owner_device='NOT_TESTED',shutdown='NOT_SELECTED')
(out/'ANDROID-CAST-COMPONENT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
assert result['pass'],result
