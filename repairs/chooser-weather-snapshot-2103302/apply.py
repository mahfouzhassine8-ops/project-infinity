#!/usr/bin/env python3
import argparse,hashlib,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
PARENT='f95f844463acfde03e0865cb64d0eed55583fda1b752a573db5d19c83e876c42'
COMMIT='1591beee377948ed812fb25ac7576b016aab8a3c'
RELEASE='1.0.9-Chooser-Weather-Snapshot-RC1'
H=lambda b:hashlib.sha256(b).hexdigest()
def once(s,old,new):
    assert s.count(old)==1,(old[:100],s.count(old));return s.replace(old,new,1)
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    assert H(a.parent.read_bytes())==PARENT
    root=a.root.resolve();shell=root/'shell-kodi';out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    receipt_path=root/'engine/background-resume-source.json';receipt=json.loads(receipt_path.read_text());assert receipt['version_code']==2103301
    for k,row in receipt['files'].items():assert H((shell/k).read_bytes())==row['after'],k
    before={str(f.relative_to(shell)):H(f.read_bytes()) for f in shell.rglob('*') if f.is_file()}
    java=shell/'tools/android/packaging/xbmc/src';weather=java/'InfinityChooserWeather.java.in';shutil.copy2(HERE/weather.name,weather)
    prep=java/'InfinityStartupPreparation.java.in';s=prep.read_text();s=once(s,'    trace.event("powerRoutes.begin");','''    trace.event("weatherSnapshot.prepare.begin");
    try { InfinityChooserWeather.prepareSnapshotBridge(app, home); trace.event("weatherSnapshot.prepare.ready"); }
    catch(Exception unavailable) { trace.event("weatherSnapshot.prepare.unavailable."+unavailable.getClass().getSimpleName()); }
    trace.event("powerRoutes.begin");''');prep.write_text(s)
    main=java/'Main.java.in';main.write_text(once(main.read_text(),'main.weather.loopbackOnly','main.weather.snapshotOnly'))
    gradle=shell/'tools/android/packaging/xbmc/build.gradle.in';s=once(gradle.read_text(),'versionCode 2103301','versionCode 2103302');s=once(s,'1.0.9-Weather-Native-Isolation-RC1',RELEASE);gradle.write_text(s)
    after={str(f.relative_to(shell)):H(f.read_bytes()) for f in shell.rglob('*') if f.is_file()};assert before.keys()==after.keys()
    changed={k for k in before if before[k]!=after[k]};allowed={str(f.relative_to(shell)) for f in (weather,prep,main,gradle)};assert changed==allowed,changed^allowed
    for k in changed:receipt['files'][k]={'before':before[k],'after':after[k]}
    receipt.update(version_code=2103302,release=RELEASE,base_apk_sha256=PARENT,base_source_commit=COMMIT);receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    producer=root/'scripts/infinity_background_resume.py';s=producer.read_text();s=once(s,'VERSION_CODE = 2103301','VERSION_CODE = 2103302');s=once(s,"RELEASE = '1.0.9-Weather-Native-Isolation-RC1'",f"RELEASE = '{RELEASE}'");s=once(s,"BASE_COMMIT = 'ee2f338baf86304bd5d585a1f76bcafaec904b3e'",f"BASE_COMMIT = '{COMMIT}'");s=once(s,"BASE_APK_SHA256 = '2dc49a92bf2299118bc30001678d4949bfac7dfd5db4a91fe2bfb1c26f848dcc'",f"BASE_APK_SHA256 = '{PARENT}'");producer.write_text(s)
    packager=root/'scripts/package_background_resume.py';s=packager.read_text().replace('2103301','2103302').replace('1.0.9-Weather-Native-Isolation-RC1',RELEASE).replace('37123017872','37143916577').replace('repairs/weather-native-isolation-2103302/','repairs/chooser-weather-snapshot-2103302/').replace('exact 2103300','exact 2103301');packager.write_text(s)
    dest=root/'repairs/chooser-weather-snapshot-2103302';dest.mkdir(parents=True,exist_ok=True);shutil.copy2(HERE/'DEVICE-TEST.txt',dest/'DEVICE-TEST.txt')
    rows=[{'path':k,'before_2103301':before[k],'after_2103302':after[k],'status':'changed' if k in changed else 'unchanged'} for k in sorted(before)]
    (out/'SOURCE-BYTE-MANIFEST-2103302.json').write_text(json.dumps(rows,indent=2)+'\n');(out/'SOURCE-CHANGES-2103302.json').write_text(json.dumps([r for r in rows if r['status']=='changed'],indent=2)+'\n')
    (out/'REPAIR-SCOPE-2103302.json').write_text(json.dumps({'version_code':2103302,'release':RELEASE,'direct_parent_sha256':PARENT,'direct_parent_source_commit':COMMIT,'change':'Chooser consumes original-time local Kodi weather snapshots; optional read-only producer prepared in extracted APK cache. No JNI or web-service dependency.','protected_source_files_unchanged':len(rows)-len(changed),'native_recompiled':False,'packaged_assets_resources_or_skin_modified':False,'chooser_layout_or_motion_modified':False,'exit_or_playback_policy_modified':False,'existing_user_addons_provider_settings_or_databases_written_by_android':False,'runtime_cache_addon_manifest_change':'one optional registration for owned chooser snapshot producer','new_weather_provider_or_network_api':False,'physical_device_verified':False,'locked':False},indent=2)+'\n')
    print('PASS: only weather bridge, preparation hook, diagnostic breadcrumb and version changed')
if __name__=='__main__':main()
