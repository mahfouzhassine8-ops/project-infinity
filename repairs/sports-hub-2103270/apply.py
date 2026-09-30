#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, difflib

ACTIVITY='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
GRADLE='tools/android/packaging/xbmc/build.gradle.in'
PARENT_ACTIVITY_SHA='2e18fe0f01b9ab8fc3e3b273174ffaa69d7733141a5a9df045dc90a8f9ac5729'
PARENT_APK='f71fdfad769ae30e57c2c96ab4dbaf51062fc483e54f1702114517fcf47befce'
PARENT_COMMIT='3804ae1a680606e15b931fa33537644b0dc21e20'
PARENT_RUN=36741769377
VERSION_CODE=2103270
RELEASE='1.0.9-Sports-Hub-RC1'

def sha(data): return hashlib.sha256(data).hexdigest()
def fragment_text():
    here=Path(__file__).parent
    parts=sorted(here.glob('SportsHub.fragment.*.java.part'))
    if parts:return ''.join(x.read_text() for x in parts)
    return (here/'SportsHub.fragment.java').read_text()
def once(s, old, new):
    count=s.count(old)
    if count!=1: raise AssertionError(f'Expected one anchor, found {count}: {old[:120]!r}')
    return s.replace(old,new,1)

def patch_activity(s, fragment):
    s=once(s,
      '    cobraDrawerDestination(library,"play","Live TV","TV",()->cobraOpenLiveTv());\n    cobraDrawerDestination(library,"film","Movies","MOVIES",()->{stopCobraPreview();mCobraInternalScreen="internal";showMovies();});',
      '    cobraDrawerDestination(library,"play","Live TV","TV",()->cobraOpenLiveTv());\n    cobraDrawerDestination(library,"play","Sports","SPORTS",()->{stopCobraPreview();mCobraInternalScreen="internal";showCobraSportsHub();});\n    cobraDrawerDestination(library,"film","Movies","MOVIES",()->{stopCobraPreview();mCobraInternalScreen="internal";showMovies();});')
    s=once(s,
      '    if(upper.contains("MOVIES")){showMovies();return;}\n    if(upper.contains("SHOWS")){showSeries();return;}',
      '    if(upper.contains("SPORTS")){showCobraSportsHub();return;}\n    if(upper.contains("MOVIES")){showMovies();return;}\n    if(upper.contains("SHOWS")){showSeries();return;}')
    s=once(s,
      '    if(COBRA_OWNER_MOVIES.equals(owner)){stopCobraPreview();mCobraInternalScreen="internal";showMovies();return;}\n    if(COBRA_OWNER_SHOWS.equals(owner)){stopCobraPreview();mCobraInternalScreen="internal";showSeries();return;}',
      '    if(COBRA_OWNER_SPORTS.equals(owner)){stopCobraPreview();mCobraInternalScreen="internal";showCobraSportsHub();return;}\n    if(COBRA_OWNER_MOVIES.equals(owner)){stopCobraPreview();mCobraInternalScreen="internal";showMovies();return;}\n    if(COBRA_OWNER_SHOWS.equals(owner)){stopCobraPreview();mCobraInternalScreen="internal";showSeries();return;}')
    s=once(s,
      '          !COBRA_OWNER_RECORDINGS.equals(stored)&&!COBRA_OWNER_MY_LIST.equals(stored)&&\n          !COBRA_OWNER_LIVE.equals(stored))stored=COBRA_OWNER_LIVE;',
      '          !COBRA_OWNER_RECORDINGS.equals(stored)&&!COBRA_OWNER_MY_LIST.equals(stored)&&\n          !COBRA_OWNER_SPORTS.equals(stored)&&!COBRA_OWNER_LIVE.equals(stored))stored=COBRA_OWNER_LIVE;')
    s=once(s,
      '    if("TV".equals(destination))owner=COBRA_OWNER_LIVE;\n    else if("MOVIES".equals(destination))owner=COBRA_OWNER_MOVIES;',
      '    if("TV".equals(destination))owner=COBRA_OWNER_LIVE;\n    else if("SPORTS".equals(destination))owner=COBRA_OWNER_SPORTS;\n    else if("MOVIES".equals(destination))owner=COBRA_OWNER_MOVIES;')
    s=once(s,
      '    if(COBRA_OWNER_MOVIES.equals(owner))\n      return "COBRA • MOVIES".equals(title)||(mCobraVodDetailReturnCaptured&&!mCobraVodDetailReturnSeries)||(mCobraVodReturnCaptured&&!mCobraVodReturnSeries);',
      '    if(COBRA_OWNER_SPORTS.equals(owner))return title.startsWith("COBRA • SPORTS");\n    if(COBRA_OWNER_MOVIES.equals(owner))\n      return "COBRA • MOVIES".equals(title)||(mCobraVodDetailReturnCaptured&&!mCobraVodDetailReturnSeries)||(mCobraVodReturnCaptured&&!mCobraVodReturnSeries);')
    s=once(s,
      '    if(COBRA_OWNER_LIVE.equals(owner))return false;\n    if(COBRA_OWNER_MOVIES.equals(owner)){',
      '    if(COBRA_OWNER_LIVE.equals(owner))return false;\n    if(COBRA_OWNER_SPORTS.equals(owner)){\n      if("COBRA • SPORTS".equals(title)){moveTaskToBack(true);return true;}\n      showCobraSportsHub();return true;\n    }\n    if(COBRA_OWNER_MOVIES.equals(owner)){')
    s=once(s,
      '      if ("livetv".equals(id)) id = "live";\n      return mDestinations.contains(id);',
      '      if ("livetv".equals(id)) id = "live";\n      if ("sports".equals(id)) return true;\n      return mDestinations.contains(id);')
    s=once(s,
      '    Button liveRewind = action("LIVE TV REWIND  •  " + cobraLiveRewindLabel());\n    liveRewind.setTag("cobra_live_rewind");\n    liveRewind.setOnClickListener(v -> showCobraLiveRewindPicker());',
      '    Button liveRewind = action("LIVE TV REWIND  •  " + cobraLiveRewindLabel());\n    liveRewind.setTag("cobra_live_rewind");\n    liveRewind.setOnClickListener(v -> showCobraLiveRewindPicker());\n\n    Button sportsSettings = action("SPORTS HUB  •  TEAMS, LEAGUES & SPOILERS");\n    sportsSettings.setTag("cobra_sports_settings");\n    sportsSettings.setOnClickListener(v -> showCobraSportsSettings());')
    s=once(s,
      '    list.addView(liveRewind, new LinearLayout.LayoutParams(-1, dp(56)));\n    list.addView(cobraSettingsSection("SYSTEM & SOURCES"), new LinearLayout.LayoutParams(-1, dp(38)));',
      '    list.addView(liveRewind, new LinearLayout.LayoutParams(-1, dp(56)));\n    list.addView(cobraSettingsSection("SPORTS"), new LinearLayout.LayoutParams(-1, dp(38)));\n    list.addView(sportsSettings, new LinearLayout.LayoutParams(-1, dp(58)));\n    list.addView(cobraSettingsSection("SYSTEM & SOURCES"), new LinearLayout.LayoutParams(-1, dp(38)));')
    if not s.endswith('\n}\n'): raise AssertionError('Unexpected Activity ending')
    return s[:-2]+fragment+'\n}\n'

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    shell=a.root/'shell-kodi';a.out.mkdir(parents=True,exist_ok=True)
    activity=shell/ACTIVITY;before=activity.read_text();assert sha(activity.read_bytes())==PARENT_ACTIVITY_SHA,'Not exact locked 2103269 Activity'
    fragment=fragment_text();after=patch_activity(before,fragment);activity.write_text(after)
    gradle=shell/GRADLE;g=gradle.read_text();g=once(g,'versionCode 2103269','versionCode 2103270');g=once(g,'versionName "1.0.9-Responsive-Window-RC1"','versionName "1.0.9-Sports-Hub-RC1"');gradle.write_text(g)
    script=a.root/'scripts/infinity_background_resume.py';v=script.read_text();v=once(v,'VERSION_CODE = 2103269','VERSION_CODE = 2103270');v=once(v,"RELEASE = '1.0.9-Responsive-Window-RC1'",f"RELEASE = '{RELEASE}'");v=once(v,"BASE_COMMIT = '46de646cc8a87c4dfafe2e7bf9b1776c011cadeb'",f"BASE_COMMIT = '{PARENT_COMMIT}'");v=once(v,"BASE_APK_SHA256 = 'de03a34643a4693162c2cd46912b826b4a77aaafbb4491ce46d1d33bf1f6d4e8'",f"BASE_APK_SHA256 = '{PARENT_APK}'");script.write_text(v)
    package=a.root/'scripts/package_background_resume.py';v=package.read_text();v=v.replace('Infinity-2103269-Responsive-Window-RC1','Infinity-2103270-Sports-Hub-RC1');v=once(v,"'base_run':36699564793",f"'base_run':{PARENT_RUN}");v=once(v,"ROOT/'repairs/responsive-window-2103269/DEVICE-TEST.md'","ROOT/'repairs/sports-hub-2103270/DEVICE-TEST.md'");package.write_text(v)
    receipt=a.root/'engine/background-resume-source.json';r=json.loads(receipt.read_text());r.update(base_source_commit=PARENT_COMMIT,base_apk_sha256=PARENT_APK,version_code=VERSION_CODE,release=RELEASE,candidate_locked=False,physical_device_verified=False,complete_product_audit=False,sports_hub=True,sports_data_repository_abstraction=True,sports_live_scoreboard=True,sports_favorite_teams=True,sports_hide_scores=True,sports_game_channel_resolver=True,sports_smart_multiview=True,sports_manual_multiview_preserved=True,sports_stats=True,sports_standings=True,sports_recording_handoff=True,sports_failure_isolated_from_live_tv=True,sports_actual_window_responsive=True)
    for n in [ACTIVITY,GRADLE]:r['files'].setdefault(n,{})['after']=sha((shell/n).read_bytes())
    receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    (a.out/'sports-hub.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='locked2103269/'+ACTIVITY,tofile='candidate2103270/'+ACTIVITY)))
    print('Applied Cobra Sports Hub 2103270 on exact locked 2103269 shell. Existing player/provider/native owners remain untouched.')
if __name__=='__main__':main()
