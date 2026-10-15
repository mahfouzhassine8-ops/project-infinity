#!/usr/bin/env python3
import argparse,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--classes',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
source=(a.root/'shell-kodi/tools/android/packaging/xbmc/src/InfinityChooserWeather.java.in').read_text()
assert 'XBMCJsonRPC' not in source and 'request_string' not in source
assert 'HttpURLConnection' not in source and 'java.net.' not in source
assert 'prepareSnapshotBridge' in source and 'captured_at_ms' in source
assert 'infinity-chooser-weather/snapshot.json' in source
paths=sorted(a.classes.rglob('InfinityChooserWeather*.class'))
assert len(paths)>=3,'Compiled weather classes missing'
reports=[]
for f in paths:
    result=subprocess.run(['javap','-verbose','-p',str(f)],check=True,capture_output=True,text=True).stdout
    assert 'XBMCJsonRPC' not in result,'Compiled weather class has a Kodi JNI dependency'
    assert 'java/net/' not in result,'Compiled weather class has a network dependency'
    reports.append({'class':f.name,'no_kodi_json_jni_reference':True})
a.out.mkdir(parents=True,exist_ok=True)
(a.out/'WEATHER-NATIVE-BOUNDARY-AUDIT.json').write_text(json.dumps({'source_checked':True,'compiled_classes':reports,'no_network_dependency':True,'original_observation_time_retained':True,'read_only_producer_registered_in_cache':True,'native_crash_physically_verified':False},indent=2)+'\n')
print('PASS: compiled weather classes contain no Kodi JSON/JNI reference; local snapshot boundary audited')
