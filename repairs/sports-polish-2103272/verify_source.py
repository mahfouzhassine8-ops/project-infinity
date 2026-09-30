#!/usr/bin/env python3
from pathlib import Path
import argparse, importlib.util, json

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('sports272',HERE/'apply.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
base=a.baseline;root=a.root

base_activity=(base/'shell-kodi'/r.ACTIVITY).read_text();actual=(root/'shell-kodi'/r.ACTIVITY).read_text()
assert r.sha(base_activity.encode())==r.PARENT_ACTIVITY_SHA,'Rollback is not exact locked 2103271 Activity'
assert actual==r.patch_activity(base_activity),'Activity differs from bounded Sports polish transformation'

restored=actual
for name in r.ALLOWED_METHODS:
    ba,bb=r.method_span(base_activity,name);restored=r.replace_method(restored,name,base_activity[ba:bb])
assert restored.count(r.HELPERS)==1
restored=restored.replace(r.HELPERS+'\n','',1)
assert restored==base_activity,'Changes escaped Sports presentation methods/helper block'

for forbidden in ('mPlayer.prepare','mPlayer.release','new ExoPlayer','releaseSinglePlayer()','mChannels.clear()','cobraSportsJson(','cobraSportsDay(','cobraSportsResolve(','cobraSportsLaunchSmartMulti('):
    assert actual.count(forbidden)==base_activity.count(forbidden),(forbidden,base_activity.count(forbidden),actual.count(forbidden))

items=[];changed=[]
for f in sorted((base/'shell-kodi').rglob('*')):
    if not f.is_file():continue
    n=str(f.relative_to(base/'shell-kodi'));g=root/'shell-kodi'/n;assert g.is_file(),n
    old=r.sha(f.read_bytes());new=r.sha(g.read_bytes());items.append(dict(path=n,before=old,after=new))
    if old!=new:changed.append(n)
assert set(changed)=={r.ACTIVITY,r.GRADLE},changed

bg=(base/'shell-kodi'/r.GRADLE).read_text().replace('versionCode 2103271','versionCode 2103272').replace('versionName "1.0.9-Sports-Data-RC1"','versionName "1.0.9-Sports-Polish-RC1"')
assert (root/'shell-kodi'/r.GRADLE).read_text()==bg

bs=(base/'scripts/infinity_background_resume.py').read_text();expected=bs.replace('VERSION_CODE = 2103271','VERSION_CODE = 2103272').replace("RELEASE = '1.0.9-Sports-Data-RC1'",f"RELEASE = '{r.RELEASE}'").replace("BASE_COMMIT = 'fe36eda6020934e538b32f754d3175040960b2cc'",f"BASE_COMMIT = '{r.PARENT_COMMIT}'").replace("BASE_APK_SHA256 = '54223cd2dcc6ebbf1b0ddddc88114ca9c95541084077a7ea03dba7c6f7ac2259'",f"BASE_APK_SHA256 = '{r.PARENT_APK}'")
assert (root/'scripts/infinity_background_resume.py').read_text()==expected,'Background script drift'

bp=(base/'scripts/package_background_resume.py').read_text();expected=bp.replace('Infinity-2103271-Sports-Data-RC1','Infinity-2103272-Sports-Polish-RC1').replace("'base_run':36755538846",f"'base_run':{r.PARENT_RUN}").replace("ROOT/'repairs/sports-data-2103271/DEVICE-TEST.md'","ROOT/'repairs/sports-polish-2103272/DEVICE-TEST.md'")
assert (root/'scripts/package_background_resume.py').read_text()==expected,'Packaging script drift'

receipt=json.loads((root/'engine/background-resume-source.json').read_text())
assert receipt['base_source_commit']==r.PARENT_COMMIT and receipt['base_apk_sha256']==r.PARENT_APK
assert receipt['version_code']==r.VERSION_CODE and receipt['release']==r.RELEASE
for key in ('sports_visual_polish','sports_compact_action_bar','sports_live_hero','sports_upcoming_scores_suppressed','sports_status_summary_local','sports_light_oled_polished','sports_data_logic_preserved','sports_channel_resolver_preserved','sports_smart_multiview_preserved'):
    assert receipt.get(key) is True,key
assert receipt.get('candidate_locked') is False and receipt.get('physical_device_verified') is False

a.out.mkdir(parents=True,exist_ok=True)
report=dict(base_commit=r.PARENT_COMMIT,base_apk_sha256=r.PARENT_APK,changed_shell_files=changed,activity_members=r.ALLOWED_METHODS,protected_source_preserved=True,sports_data_logic_preserved=True,channel_resolver_preserved=True,smart_multiview_preserved=True,native_source_modified=False,infinity_skin_touched=False,physical_device_verified=False,candidate_locked=False,files=items)
(a.out/'source-verification.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print('PASS: exact locked 2103271 transformed only by bounded Sports presentation polish; data/player/provider/Multi-View/native/skin preserved.')
