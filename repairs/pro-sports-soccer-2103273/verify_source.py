#!/usr/bin/env python3
from pathlib import Path
import argparse,importlib.util,json,hashlib,re

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pro273',HERE/'apply.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
base=a.baseline;root=a.root

def method(text,name):
    m=re.search(r'(?m)^\s+private [^\n{]*\b'+re.escape(name)+r'\s*\(',text)
    if not m: raise AssertionError('Missing method '+name)
    brace=text.find('{',m.end()-1);depth=0
    for i in range(brace,len(text)):
        if text[i]=='{':depth+=1
        elif text[i]=='}':
            depth-=1
            if depth==0:return text[m.start():i+1]
    raise AssertionError('Unclosed method '+name)

ba=(base/'shell-kodi'/r.ACTIVITY).read_text();bp=(base/'shell-kodi'/r.PROUI).read_text()
aa=(root/'shell-kodi'/r.ACTIVITY).read_text();ap=(root/'shell-kodi'/r.PROUI).read_text()
assert r.sha(ba.encode())==r.PARENT_ACTIVITY_SHA and r.sha(bp.encode())==r.PARENT_PROUI_SHA,'Rollback is not exact locked 2103271'
assert r.sha(aa.encode())==r.AFTER_ACTIVITY_SHA and r.sha(ap.encode())==r.AFTER_PROUI_SHA,'Forward Java does not match approved patch payload'

for name in ('playChannel','startSinglePlayer','cobraSportsResolve','cobraSportsWatch','cobraSportsOpenSmartMultiView','cobraSportsJson','cobraSportsDay','cobraSportsRecord'):
    assert method(aa,name)==method(ba,name),'Protected owner changed: '+name

for token in (
    'static final String[] LABELS={"All Channels","Favorites","Recents","Groups","Sports","Search"}',
    'setTag("pro_six_action_row")','setTag("pro_sports_tabs")','setTag("pro_sports_game_list")',
    'this.source="LIVE SPORTS"','pro_sports_watch','pro_sports_stats','pro_sports_multiview',
    'new CobraSportsLeagueSpec("epl","soccer","eng.1","Premier League")',
    'new CobraSportsLeagueSpec("ucl","soccer","uefa.champions","Champions League")',
    'new CobraSportsLeagueSpec("mls","soccer","usa.1","MLS")',
    'new CobraSportsLeagueSpec("laliga","soccer","esp.1","La Liga")',
    'new CobraSportsLeagueSpec("bundesliga","soccer","ger.1","Bundesliga")',
    'new CobraSportsLeagueSpec("seriea","soccer","ita.1","Serie A")',
    'new CobraSportsLeagueSpec("ligue1","soccer","fra.1","Ligue 1")',
    'new CobraSportsLeagueSpec("uel","soccer","uefa.europa","Europa League")'):
    assert token in aa or token in ap,token
assert 'java.util.Arrays.asList("nfl","nba","mlb","nhl","ncaaf","ncaam","epl","ucl","mls")' in aa

items=[];changed=[]
for f in sorted((base/'shell-kodi').rglob('*')):
    if not f.is_file():continue
    n=str(f.relative_to(base/'shell-kodi'));g=root/'shell-kodi'/n;assert g.is_file(),n
    old=r.sha(f.read_bytes());new=r.sha(g.read_bytes());items.append(dict(path=n,before=old,after=new))
    if old!=new:changed.append(n)
assert set(changed)=={r.ACTIVITY,r.PROUI,r.GRADLE},changed

bg=(base/'shell-kodi'/r.GRADLE).read_text().replace('versionCode 2103271','versionCode 2103273').replace('versionName "1.0.9-Sports-Data-RC1"','versionName "1.0.9-Pro-Sports-Soccer-RC1"')
assert (root/'shell-kodi'/r.GRADLE).read_text()==bg

bs=(base/'scripts/infinity_background_resume.py').read_text();expected=bs.replace('VERSION_CODE = 2103271','VERSION_CODE = 2103273').replace("RELEASE = '1.0.9-Sports-Data-RC1'",f"RELEASE = '{r.RELEASE}'").replace("BASE_COMMIT = 'fe36eda6020934e538b32f754d3175040960b2cc'",f"BASE_COMMIT = '{r.PARENT_COMMIT}'").replace("BASE_APK_SHA256 = '54223cd2dcc6ebbf1b0ddddc88114ca9c95541084077a7ea03dba7c6f7ac2259'",f"BASE_APK_SHA256 = '{r.PARENT_APK}'")
assert (root/'scripts/infinity_background_resume.py').read_text()==expected,'Background script drift'
bpkg=(base/'scripts/package_background_resume.py').read_text();expected=bpkg.replace('Infinity-2103271-Sports-Data-RC1','Infinity-2103273-Pro-Sports-Soccer-RC1').replace("'base_run':36755538846",f"'base_run':{r.PARENT_RUN}").replace("ROOT/'repairs/sports-data-2103271/DEVICE-TEST.md'","ROOT/'repairs/pro-sports-soccer-2103273/DEVICE-TEST.md'")
assert (root/'scripts/package_background_resume.py').read_text()==expected,'Packaging script drift'

receipt=json.loads((root/'engine/background-resume-source.json').read_text())
assert receipt['base_source_commit']==r.PARENT_COMMIT and receipt['base_apk_sha256']==r.PARENT_APK
assert receipt['version_code']==r.VERSION_CODE and receipt['release']==r.RELEASE
for key in ('pro_sports_tab','pro_six_tabs','pro_live_sports_hero_source','pro_sports_live_now','pro_sports_my_teams','pro_sports_upcoming','pro_sports_leagues','pro_sports_watch_live','pro_sports_stats','pro_sports_multiview','soccer_enabled_by_default','soccer_premier_league','soccer_champions_league','soccer_mls','soccer_extended_leagues','sports_repository_preserved','sports_channel_resolver_preserved','manual_multiview_preserved'):
    assert receipt.get(key) is True,key
assert receipt.get('candidate_locked') is False and receipt.get('physical_device_verified') is False

a.out.mkdir(parents=True,exist_ok=True)
report=dict(base_commit=r.PARENT_COMMIT,base_apk_sha256=r.PARENT_APK,changed_shell_files=changed,protected_owner_methods=['playChannel','startSinglePlayer','cobraSportsResolve','cobraSportsWatch','cobraSportsOpenSmartMultiView','cobraSportsJson','cobraSportsDay','cobraSportsRecord'],protected_source_preserved=True,sports_repository_preserved=True,channel_resolver_preserved=True,manual_multiview_preserved=True,native_source_modified=False,infinity_skin_touched=False,physical_device_verified=False,candidate_locked=False,files=items)
(a.out/'source-verification.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print('PASS: exact locked 2103271 transformed only for Pro Sports/Soccer presentation + league enablement; player/provider/resolver/native/skin owners preserved.')
