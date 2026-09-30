#!/usr/bin/env python3
from pathlib import Path
import argparse,importlib.util,json,re

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('hub274',HERE/'apply.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
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
assert r.sha(ba.encode())==r.PARENT_ACTIVITY_SHA and r.sha(bp.encode())==r.PARENT_PROUI_SHA,'Rollback is not exact locked 2103273'
assert r.sha(aa.encode())==r.AFTER_ACTIVITY_SHA,'Forward Activity does not match bounded 2103274 payload'
assert r.sha(ap.encode())==r.PARENT_PROUI_SHA,'CobraProUi changed in 2103274'

for name in ('playChannel','startSinglePlayer','cobraSportsResolve','cobraSportsWatch','cobraSportsOpenSmartMultiView','cobraSportsJson','cobraSportsDay','cobraSportsRecord','cobraRenderFocusMode','cobraRenderProSports'):
    assert method(aa,name)==method(ba,name),'Protected owner changed: '+name
for name in ('cobraSportsAddLeagueSection','showCobraSportsLeague','cobraSportsGameCard'):
    assert method(aa,name)==method(ba,name),'Existing Sports behavior changed: '+name

for token in ('cobra_sports_soccer_section','cobra_sports_soccer_heading','cobra_sports_soccer_leagues','cobra_sports_soccer_rail','cobra_sports_soccer_empty','COBRA • SPORTS • SOCCER','SOCCER LEAGUES','!"soccer".equals(spec.sport)'):
    assert token in aa,token

items=[];changed=[]
for f in sorted((base/'shell-kodi').rglob('*')):
    if not f.is_file():continue
    n=str(f.relative_to(base/'shell-kodi'));g=root/'shell-kodi'/n;assert g.is_file(),n
    old=r.sha(f.read_bytes());new=r.sha(g.read_bytes());items.append(dict(path=n,before=old,after=new))
    if old!=new:changed.append(n)
assert set(changed)=={r.ACTIVITY,r.GRADLE},changed

bg=(base/'shell-kodi'/r.GRADLE).read_text().replace('versionCode 2103273','versionCode 2103274').replace('versionName "1.0.9-Pro-Sports-Soccer-RC1"','versionName "1.0.9-Sports-Hub-Soccer-RC1"')
assert (root/'shell-kodi'/r.GRADLE).read_text()==bg

bs=(base/'scripts/infinity_background_resume.py').read_text();expected=bs.replace('VERSION_CODE = 2103273','VERSION_CODE = 2103274').replace("RELEASE = '1.0.9-Pro-Sports-Soccer-RC1'",f"RELEASE = '{r.RELEASE}'").replace("BASE_COMMIT = '1aea5afdfe4bf7253e3db8bb869815651a9218b4'",f"BASE_COMMIT = '{r.PARENT_COMMIT}'").replace("BASE_APK_SHA256 = '40de992889bda2c9f73862d2eee4937c252db10e5d9ca07777b4c4f9e37f4ad2'",f"BASE_APK_SHA256 = '{r.PARENT_APK}'")
assert (root/'scripts/infinity_background_resume.py').read_text()==expected,'Background script drift'
bpkg=(base/'scripts/package_background_resume.py').read_text();expected=bpkg.replace('Infinity-2103273-Pro-Sports-Soccer-RC1','Infinity-2103274-Sports-Hub-Soccer-RC1').replace("'base_run':36759239156",f"'base_run':{r.PARENT_RUN}").replace("ROOT/'repairs/pro-sports-soccer-2103273/DEVICE-TEST.md'","ROOT/'repairs/sports-hub-soccer-2103274/DEVICE-TEST.md'")
assert (root/'scripts/package_background_resume.py').read_text()==expected,'Packaging script drift'

receipt=json.loads((root/'engine/background-resume-source.json').read_text())
assert receipt['base_source_commit']==r.PARENT_COMMIT and receipt['base_apk_sha256']==r.PARENT_APK
for key in ('sports_hub_soccer_section','sports_hub_soccer_permanent','sports_hub_soccer_league_directory','sports_hub_soccer_aggregate_enabled_only','pro_sports_preserved','sports_repository_preserved','sports_channel_resolver_preserved','manual_multiview_preserved'):assert receipt.get(key) is True,key
assert receipt.get('candidate_locked') is False and receipt.get('physical_device_verified') is False

a.out.mkdir(parents=True,exist_ok=True)
report=dict(base_commit=r.PARENT_COMMIT,base_apk_sha256=r.PARENT_APK,changed_shell_files=changed,protected_source_preserved=True,pro_sports_preserved=True,sports_repository_preserved=True,channel_resolver_preserved=True,manual_multiview_preserved=True,native_source_modified=False,infinity_skin_touched=False,physical_device_verified=False,candidate_locked=False,files=items)
(a.out/'source-verification.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print('PASS: locked 2103273 changed only for main Sports Hub Soccer visibility + version metadata; Pro/data/resolver/player/Multi-View/native/skin preserved.')
