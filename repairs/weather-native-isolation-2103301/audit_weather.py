#!/usr/bin/env python3
import argparse,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--classes',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
source=(a.root/'shell-kodi/tools/android/packaging/xbmc/src/InfinityChooserWeather.java.in').read_text()
assert 'XBMCJsonRPC' not in source and 'request_string' not in source
assert '127.0.0.1:' in source and 'Proxy.NO_PROXY' in source
assert 'setInstanceFollowRedirects(false)' in source
assert 'setConnectTimeout(1500)' in source and 'setReadTimeout(1500)' in source
paths=sorted((a.classes/'com/projectinfinity/kodi').glob('InfinityChooserWeather*.class'))
assert len(paths)>=4,'Compiled weather classes missing'
reports=[]
for f in paths:
    result=subprocess.run(['javap','-verbose','-p',str(f)],check=True,capture_output=True,text=True).stdout
    assert 'XBMCJsonRPC' not in result,'Compiled weather class has a Kodi JNI dependency'
    reports.append({'class':f.name,'no_kodi_json_jni_reference':True})
a.out.mkdir(parents=True,exist_ok=True)
(a.out/'WEATHER-NATIVE-BOUNDARY-AUDIT.json').write_text(json.dumps({'source_checked':True,'compiled_classes':reports,'redirects_disabled':True,'loopback_only':True,'finite_timeouts':True,'native_crash_physically_verified':False},indent=2)+'\n')
print('PASS: compiled weather classes contain no Kodi JSON/JNI reference; loopback boundary audited')
