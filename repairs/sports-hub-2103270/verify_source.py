#!/usr/bin/env python3
from pathlib import Path
import argparse, importlib.util, json, hashlib

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('sports270',HERE/'apply.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
base=a.baseline;root=a.root
fragment=r.fragment_text()
for forbidden in ('mPlayer.prepare','mPlayer.release','new ExoPlayer','releaseSinglePlayer()','mChannels.clear()'):
    assert forbidden not in fragment, 'Sports fragment must not take player/provider ownership: '+forbidden

base_activity=(base/'shell-kodi'/r.ACTIVITY).read_text();actual_activity=(root/'shell-kodi'/r.ACTIVITY).read_text()
assert r.sha(base_activity.encode())==r.PARENT_ACTIVITY_SHA,'Rollback is not exact locked 2103269 Activity'
assert actual_activity==r.patch_activity(base_activity,fragment),'Activity differs from exact Sports-only transformation'
assert actual_activity.count('// 2103270 — Cobra Sports Hub')==1

items=[];changed=[]
for f in sorted((base/'shell-kodi').rglob('*')):
    if not f.is_file():continue
    n=str(f.relative_to(base/'shell-kodi'));g=root/'shell-kodi'/n;assert g.is_file(),n
    old=r.sha(f.read_bytes());new=r.sha(g.read_bytes());items.append(dict(path=n,before=old,after=new))
    if old!=new:changed.append(n)
assert set(changed)=={r.ACTIVITY,r.GRADLE},changed

bg=(base/'shell-kodi'/r.GRADLE).read_text().replace('versionCode 2103269','versionCode 2103270').replace('versionName "1.0.9-Responsive-Window-RC1"','versionName "1.0.9-Sports-Hub-RC1"')
assert (root/'shell-kodi'/r.GRADLE).read_text()==bg

bs=(base/'scripts/infinity_background_resume.py').read_text();expected=bs.replace('VERSION_CODE = 2103269','VERSION_CODE = 2103270').replace("RELEASE = '1.0.9-Responsive-Window-RC1'",f"RELEASE = '{r.RELEASE}'").replace("BASE_COMMIT = '46de646cc8a87c4dfafe2e7bf9b1776c011cadeb'",f"BASE_COMMIT = '{r.PARENT_COMMIT}'").replace("BASE_APK_SHA256 = 'de03a34643a4693162c2cd46912b826b4a77aaafbb4491ce46d1d33bf1f6d4e8'",f"BASE_APK_SHA256 = '{r.PARENT_APK}'")
assert (root/'scripts/infinity_background_resume.py').read_text()==expected,'Background script drift'

bp=(base/'scripts/package_background_resume.py').read_text();expected=bp.replace('Infinity-2103269-Responsive-Window-RC1','Infinity-2103270-Sports-Hub-RC1').replace("'base_run':36699564793",f"'base_run':{r.PARENT_RUN}").replace("ROOT/'repairs/responsive-window-2103269/DEVICE-TEST.md'","ROOT/'repairs/sports-hub-2103270/DEVICE-TEST.md'")
assert (root/'scripts/package_background_resume.py').read_text()==expected,'Packaging script drift'

receipt=json.loads((root/'engine/background-resume-source.json').read_text())
assert receipt['base_source_commit']==r.PARENT_COMMIT and receipt['base_apk_sha256']==r.PARENT_APK
assert receipt['version_code']==r.VERSION_CODE and receipt['release']==r.RELEASE
for key in ('sports_hub','sports_data_repository_abstraction','sports_live_scoreboard','sports_favorite_teams','sports_hide_scores','sports_game_channel_resolver','sports_smart_multiview','sports_manual_multiview_preserved','sports_stats','sports_standings','sports_recording_handoff','sports_failure_isolated_from_live_tv','sports_actual_window_responsive'):
    assert receipt.get(key) is True,key
assert receipt.get('candidate_locked') is False and receipt.get('physical_device_verified') is False

a.out.mkdir(parents=True,exist_ok=True)
report=dict(base_commit=r.PARENT_COMMIT,base_apk_sha256=r.PARENT_APK,changed_shell_files=changed,sports_fragment_sha256=r.sha(fragment.encode()),protected_source_preserved=True,native_source_modified=False,infinity_skin_touched=False,player_owner_replaced=False,provider_owner_replaced=False,manual_multiview_replaced=False,physical_device_verified=False,candidate_locked=False,files=items)
(a.out/'source-verification.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print('PASS: exact locked 2103269 source transformed only by bounded Sports Hub Activity/version delta; native/player/provider/skin preserved.')
