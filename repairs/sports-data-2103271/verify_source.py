#!/usr/bin/env python3
from pathlib import Path
import argparse, importlib.util, json

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('sports271',HERE/'apply.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
base=a.baseline;root=a.root

base_activity=(base/'shell-kodi'/r.ACTIVITY).read_text();actual_activity=(root/'shell-kodi'/r.ACTIVITY).read_text()
assert r.sha(base_activity.encode())==r.PARENT_ACTIVITY_SHA,'Rollback is not exact 2103270 source'
assert actual_activity==r.patch_activity(base_activity),'Activity differs from bounded Sports data transformation'
for forbidden in ('mPlayer.prepare','mPlayer.release','new ExoPlayer','releaseSinglePlayer()','mChannels.clear()'):
    before=base_activity.count(forbidden);after=actual_activity.count(forbidden);assert before==after,(forbidden,before,after)
assert 'String dates=f.format(new Date(from))+"-"+f.format(new Date(to));' not in actual_activity
assert 'cobraSportsDateKeys(from,to)' in actual_activity
assert 'site.web.api.espn.com' in actual_activity
assert 'SPORTS DATA UNAVAILABLE' in actual_activity and 'NO GAMES SCHEDULED' in actual_activity

items=[];changed=[]
for f in sorted((base/'shell-kodi').rglob('*')):
    if not f.is_file():continue
    n=str(f.relative_to(base/'shell-kodi'));g=root/'shell-kodi'/n;assert g.is_file(),n
    old=r.sha(f.read_bytes());new=r.sha(g.read_bytes());items.append(dict(path=n,before=old,after=new))
    if old!=new:changed.append(n)
assert set(changed)=={r.ACTIVITY,r.GRADLE},changed

bg=(base/'shell-kodi'/r.GRADLE).read_text().replace('versionCode 2103270','versionCode 2103271').replace('versionName "1.0.9-Sports-Hub-RC1"','versionName "1.0.9-Sports-Data-RC1"')
assert (root/'shell-kodi'/r.GRADLE).read_text()==bg

bs=(base/'scripts/infinity_background_resume.py').read_text();expected=bs.replace('VERSION_CODE = 2103270','VERSION_CODE = 2103271').replace("RELEASE = '1.0.9-Sports-Hub-RC1'",f"RELEASE = '{r.RELEASE}'").replace("BASE_COMMIT = '3804ae1a680606e15b931fa33537644b0dc21e20'",f"BASE_COMMIT = '{r.PARENT_COMMIT}'").replace("BASE_APK_SHA256 = 'f71fdfad769ae30e57c2c96ab4dbaf51062fc483e54f1702114517fcf47befce'",f"BASE_APK_SHA256 = '{r.PARENT_APK}'")
assert (root/'scripts/infinity_background_resume.py').read_text()==expected,'Background script drift'

bp=(base/'scripts/package_background_resume.py').read_text();expected=bp.replace('Infinity-2103270-Sports-Hub-RC1','Infinity-2103271-Sports-Data-RC1').replace("'base_run':36741769377",f"'base_run':{r.PARENT_RUN}").replace("ROOT/'repairs/sports-hub-2103270/DEVICE-TEST.md'","ROOT/'repairs/sports-data-2103271/DEVICE-TEST.md'")
assert (root/'scripts/package_background_resume.py').read_text()==expected,'Packaging script drift'

receipt=json.loads((root/'engine/background-resume-source.json').read_text())
assert receipt['base_source_commit']==r.PARENT_COMMIT and receipt['base_apk_sha256']==r.PARENT_APK
assert receipt['version_code']==r.VERSION_CODE and receipt['release']==r.RELEASE
for key in ('sports_hub','sports_game_channel_resolver','sports_smart_multiview','sports_manual_multiview_preserved','sports_data_single_day_queries','sports_data_parallel_day_fetch','sports_data_day_cache','sports_data_host_fallback','sports_data_error_diagnostics','sports_empty_state_truthful'):
    assert receipt.get(key) is True,key
assert receipt.get('candidate_locked') is False and receipt.get('physical_device_verified') is False

a.out.mkdir(parents=True,exist_ok=True)
report=dict(base_commit=r.PARENT_COMMIT,base_apk_sha256=r.PARENT_APK,changed_shell_files=changed,protected_source_preserved=True,native_source_modified=False,infinity_skin_touched=False,player_owner_replaced=False,provider_owner_replaced=False,manual_multiview_replaced=False,sports_range_query_removed=True,sports_single_day_querying=True,sports_host_fallback=True,physical_device_verified=False,candidate_locked=False,files=items)
(a.out/'source-verification.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print('PASS: exact 2103270 source transformed only by bounded Sports data repair; playback/provider/native/skin preserved.')
