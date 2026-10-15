#!/usr/bin/env python3
from pathlib import Path
import argparse,base64,zlib,subprocess,hashlib,json

ACTIVITY='tools/android/packaging/xbmc/src/InfinityLiveActivity.java.in'
PROUI='tools/android/packaging/xbmc/src/CobraProUi.java.in'
GRADLE='tools/android/packaging/xbmc/build.gradle.in'
PARENT_ACTIVITY_SHA='5bb21ec202221394f150ee62f7cb28d35dbc03c0cee7b47bf152ad0fd063832d'
PARENT_PROUI_SHA='2ef9662b7cf2cb6b52ba686d6b04b37da9098a893393630ff5bc0720ef66d945'
AFTER_ACTIVITY_SHA='ab7bf1619090df8aa8fb5cff77a3e16ad1b503d1e45b26736fb959000c65915c'
PARENT_APK='0f35b65e3eb8c92e1966c8116bbccb3a55d09e368d1b59db02e9c8828d15dc3f'
PARENT_COMMIT='6a89688f3e61b8f2f66d9d4cef942cc506befffd'
PARENT_RUN=36770912528
VERSION_CODE=2103274
RELEASE='1.0.9-Sports-Hub-Soccer-RC1'
PATCH_B64='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'

def sha(data): return hashlib.sha256(data).hexdigest()
def once(s,o,n):
    if s.count(o)!=1: raise AssertionError('Unexpected source preimage: '+repr(o[:120]))
    return s.replace(o,n,1)

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    shell=a.root/'shell-kodi';a.out.mkdir(parents=True,exist_ok=True)
    activity=shell/ACTIVITY;pro=shell/PROUI
    assert sha(activity.read_bytes())==PARENT_ACTIVITY_SHA,'Not exact locked 2103273 Activity'
    assert sha(pro.read_bytes())==PARENT_PROUI_SHA,'Not exact locked 2103273 Pro UI'
    patch=zlib.decompress(base64.b64decode(PATCH_B64)).decode()
    subprocess.run(['patch','-p1','--batch','--forward'],cwd=shell,input=patch,text=True,check=True)
    assert sha(activity.read_bytes())==AFTER_ACTIVITY_SHA,'Unexpected 2103274 Activity patch result'
    assert sha(pro.read_bytes())==PARENT_PROUI_SHA,'Pro UI changed in Soccer Hub visibility pass'
    gradle=shell/GRADLE;g=gradle.read_text();g=once(g,'versionCode 2103273','versionCode 2103274');g=once(g,'versionName "1.0.9-Pro-Sports-Soccer-RC1"','versionName "1.0.9-Sports-Hub-Soccer-RC1"');gradle.write_text(g)
    script=a.root/'scripts/infinity_background_resume.py';v=script.read_text();v=once(v,'VERSION_CODE = 2103273','VERSION_CODE = 2103274');v=once(v,"RELEASE = '1.0.9-Pro-Sports-Soccer-RC1'",f"RELEASE = '{RELEASE}'");v=once(v,"BASE_COMMIT = '1aea5afdfe4bf7253e3db8bb869815651a9218b4'",f"BASE_COMMIT = '{PARENT_COMMIT}'");v=once(v,"BASE_APK_SHA256 = '40de992889bda2c9f73862d2eee4937c252db10e5d9ca07777b4c4f9e37f4ad2'",f"BASE_APK_SHA256 = '{PARENT_APK}'");script.write_text(v)
    package=a.root/'scripts/package_background_resume.py';v=package.read_text();v=v.replace('Infinity-2103273-Pro-Sports-Soccer-RC1','Infinity-2103274-Sports-Hub-Soccer-RC1');v=once(v,"'base_run':36759239156",f"'base_run':{PARENT_RUN}");v=once(v,"ROOT/'repairs/pro-sports-soccer-2103273/DEVICE-TEST.md'","ROOT/'repairs/sports-hub-soccer-2103274/DEVICE-TEST.md'");package.write_text(v)
    receipt=a.root/'engine/background-resume-source.json';r=json.loads(receipt.read_text());r.update(base_source_commit=PARENT_COMMIT,base_apk_sha256=PARENT_APK,version_code=VERSION_CODE,release=RELEASE,candidate_locked=False,physical_device_verified=False,complete_product_audit=False,sports_hub_soccer_section=True,sports_hub_soccer_permanent=True,sports_hub_soccer_league_directory=True,sports_hub_soccer_aggregate_enabled_only=True,pro_sports_preserved=True,sports_repository_preserved=True,sports_channel_resolver_preserved=True,manual_multiview_preserved=True)
    for n in [ACTIVITY,PROUI,GRADLE]:r['files'].setdefault(n,{})['after']=sha((shell/n).read_bytes())
    receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    (a.out/'sports-hub-soccer.patch').write_text(patch)
    print('Applied 2103274 first-class Soccer rail to locked 2103273 Sports Hub; Pro/data/resolver/player/Multi-View owners preserved.')
if __name__=='__main__':main()
