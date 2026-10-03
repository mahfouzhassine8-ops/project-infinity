#!/usr/bin/env python3
"""Isolate chooser weather from JNI over the exact unlocked 2103300 parent."""
import argparse, hashlib, json, shutil
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARENT='2dc49a92bf2299118bc30001678d4949bfac7dfd5db4a91fe2bfb1c26f848dcc'
COMMIT='ee2f338baf86304bd5d585a1f76bcafaec904b3e'
RELEASE='1.0.9-Weather-Native-Isolation-RC1'
H=lambda b:hashlib.sha256(b).hexdigest()
def once(s,old,new):
    if s.count(old)!=1:raise RuntimeError('Unexpected preimage: '+old[:100])
    return s.replace(old,new,1)
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    assert H(a.parent.read_bytes())==PARENT,'Not the exact 2103300 parent'
    root=a.root.resolve();shell=root/'shell-kodi';out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    receipt_path=root/'engine/background-resume-source.json';receipt=json.loads(receipt_path.read_text())
    assert receipt['version_code']==2103300 and receipt['release']=='1.0.9-Clean-Task-Relaunch-RC1'
    for name,row in receipt['files'].items():assert H((shell/name).read_bytes())==row['after'],name
    paths={str(f.relative_to(shell)):H(f.read_bytes()) for f in shell.rglob('*') if f.is_file()}
    java=shell/'tools/android/packaging/xbmc/src'
    weather=java/'InfinityChooserWeather.java.in'
    assert 'new XBMCJsonRPC().request_string(REQUEST)' in weather.read_text()
    shutil.copy2(HERE/weather.name,weather)
    main=java/'Main.java.in';s=main.read_text()
    s=once(s,'      mInfinityWeatherCapture = new InfinityChooserWeather(this, null);',
        '      InfinityExitDiagnostics.breadcrumb(getApplicationContext(), "main.weather.loopbackOnly");\n      mInfinityWeatherCapture = new InfinityChooserWeather(this, null);')
    main.write_text(s)
    gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';s=gradle.read_text()
    s=once(s,'versionCode 2103300','versionCode 2103301');s=once(s,'1.0.9-Clean-Task-Relaunch-RC1',RELEASE);gradle.write_text(s)
    after={str(f.relative_to(shell)):H(f.read_bytes()) for f in shell.rglob('*') if f.is_file()}
    assert paths.keys()==after.keys()
    changed={k for k in paths if paths[k]!=after[k]}
    allowed={str(f.relative_to(shell)) for f in (weather,main,gradle)}
    assert changed==allowed,changed^allowed
    for k in changed:receipt['files'][k]={'before':paths[k],'after':after[k]}
    receipt.update(version_code=2103301,release=RELEASE,base_apk_sha256=PARENT,base_source_commit=COMMIT)
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    producer=root/'scripts/infinity_background_resume.py';s=producer.read_text()
    s=once(s,'VERSION_CODE = 2103300','VERSION_CODE = 2103301')
    s=once(s,"RELEASE = '1.0.9-Clean-Task-Relaunch-RC1'",f"RELEASE = '{RELEASE}'")
    s=once(s,"BASE_COMMIT = '56a9ec9ed5fc6a2cd02a4d64975d7fb6b77f93aa'",f"BASE_COMMIT = '{COMMIT}'")
    s=once(s,"BASE_APK_SHA256 = 'e46f1745668d6cd6b3df05ae12785e8a3a952e94c9e14cec70a2901ed0bd9dc5'",f"BASE_APK_SHA256 = '{PARENT}'")
    producer.write_text(s)
    packager=root/'scripts/package_background_resume.py';s=packager.read_text()
    s=s.replace('2103300','2103301').replace('1.0.9-Clean-Task-Relaunch-RC1',RELEASE)
    s=s.replace('37117015142','37123017872').replace('repairs/stale-main-task-2103301/','repairs/weather-native-isolation-2103301/')
    s=s.replace('over exact signed 2103298','over exact signed 2103300').replace('over exact signed 2103299','over exact signed 2103300')
    # Older local reconstruction retains the 3299 manifest exception. The direct
    # 3300 parent already includes that bridge; require an identical manifest here.
    start=s.index('def verify_manifest_pair(');end=s.index('\n\ndef ',start+10)
    body=s[start:end]
    if 'app=next(' in body:
        pos=body.index('    app=next(')
        body=body[:pos]+"    require(old==new,'Compiled manifest drift from exact 2103300 base outside version identity')\n"
        s=s[:start]+body+s[end:]
    else:s=s.replace('exact 2103299 base','exact 2103300 base')
    packager.write_text(s)
    dest=root/'repairs/weather-native-isolation-2103301';dest.mkdir(parents=True,exist_ok=True)
    shutil.copy2(HERE/'DEVICE-TEST.txt',dest/'DEVICE-TEST.txt')
    rows=[{'path':k,'before_2103300':paths[k],'after_2103301':after[k],'status':'changed' if k in changed else 'unchanged'} for k in sorted(paths)]
    (out/'SOURCE-BYTE-MANIFEST-2103301.json').write_text(json.dumps(rows,indent=2)+'\n')
    (out/'SOURCE-CHANGES-2103301.json').write_text(json.dumps([r for r in rows if r['status']=='changed'],indent=2)+'\n')
    (out/'REPAIR-SCOPE-2103301.json').write_text(json.dumps({
        'version_code':2103301,'version_name':RELEASE,'direct_parent_sha256':PARENT,'direct_parent_source_commit':COMMIT,
        'change':'Weather JNI request removed completely. Bounded cancellable loopback HTTP read uses only an existing enabled Kodi web service and existing authentication. Cached readings preserved.',
        'protected_source_files_unchanged':len(rows)-len(changed),'native_recompiled':False,'skin_assets_resources_or_xml_modified':False,
        'chooser_animation_or_layout_modified':False,'normal_or_force_exit_policy_modified':False,'fresh_or_live_handoff_flags_modified':False,
        'runtime_user_settings_written':False,'web_service_or_weather_provider_enabled':False,'external_network_used':False,
        'stale_task_cause_claim_retracted':'2103300 did not resolve the crashes. Its stale-task explanation was a hypothesis, not an established root cause.',
        'physical_device_verified':False,'locked':False},indent=2)+'\n')
    print('PASS: only Main weather breadcrumb, weather transport, and version changed; all other source bytes identical')
if __name__=='__main__':main()
