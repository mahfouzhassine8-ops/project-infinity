#!/usr/bin/env python3
from pathlib import Path
import argparse,importlib.util,json

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('amb275',HERE/'apply.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
base=a.baseline;root=a.root

ba=(base/'shell-kodi'/r.ACTIVITY).read_text();br=(base/'shell-kodi'/r.RENDERER).read_text();bp=(base/'shell-kodi'/r.PROUI).read_text();bc=(base/'shell-kodi'/r.CMAKE).read_text()
aa=(root/'shell-kodi'/r.ACTIVITY).read_text();ar=(root/'shell-kodi'/r.RENDERER).read_text();ap=(root/'shell-kodi'/r.PROUI).read_text();ac=(root/'shell-kodi'/r.CMAKE).read_text()
assert r.sha(ba.encode())==r.PARENT_ACTIVITY_SHA and r.sha(br.encode())==r.PARENT_RENDERER_SHA and r.sha(bp.encode())==r.PARENT_PROUI_SHA and r.sha(bc.encode())==r.PARENT_CMAKE_SHA,'Rollback is not exact locked 2103274'
assert aa==r.patch_activity(ba),'Activity differs from bounded 2103275 transformation'
assert ar==r.patch_renderer(br),'Visual renderer differs from bounded 2103275 transformation'
assert ap==bp,'Pro Sports UI changed in ambient-only pass'
assert r.sha(ac.encode())==r.AFTER_CMAKE_SHA,'Android CMake registration differs from bounded 2103275 result'
assert 'src/CobraImmersiveAmbient.java' in ac and 'CobraImmersiveAmbient.java.in' in ac
assert r.sha(aa.encode())==r.AFTER_ACTIVITY_SHA and r.sha(ar.encode())==r.AFTER_RENDERER_SHA
immersive=(root/'shell-kodi'/r.IMMERSIVE);assert immersive.is_file() and r.sha(immersive.read_bytes())==r.AFTER_IMMERSIVE_SHA
assert 'SAMPLE_WIDTH = 144' in immersive.read_text() and 'FRAME_INTERVAL_MS = 83L' in immersive.read_text()
assert 'RAY_STEPS = 48' in immersive.read_text() and 'SATURATION = 1.65f' in immersive.read_text()
assert 'x-ambient project by mmnga' in immersive.read_text()
assert 'mPlayerOverlay!=null' in aa and 'mMultiOverlay!=null' in aa and 'mCobraMiniBackgroundActive||mBackgroundStopped' in aa
assert 'Live mini-player edge colours • suspended in fullscreen, PiP and background' in aa
assert (root/'shell-kodi'/r.LICENSE).read_text()==r.MIT,'MIT attribution payload changed'

items=[];changed=[];base_names=set()
for f in sorted((base/'shell-kodi').rglob('*')):
    if not f.is_file():continue
    n=str(f.relative_to(base/'shell-kodi'));base_names.add(n);g=root/'shell-kodi'/n;assert g.is_file(),n
    old=r.sha(f.read_bytes());new=r.sha(g.read_bytes());items.append(dict(path=n,before=old,after=new))
    if old!=new:changed.append(n)
current_names={str(f.relative_to(root/'shell-kodi')) for f in (root/'shell-kodi').rglob('*') if f.is_file()}
added=sorted(current_names-base_names)
assert set(changed)=={r.ACTIVITY,r.RENDERER,r.GRADLE,r.CMAKE},changed
assert set(added)=={r.IMMERSIVE,r.LICENSE},added

bg=(base/'shell-kodi'/r.GRADLE).read_text().replace('versionCode 2103274','versionCode 2103275').replace('versionName "1.0.9-Sports-Hub-Soccer-RC1"','versionName "1.0.9-Immersive-Edge-Ambient-RC1"')
assert (root/'shell-kodi'/r.GRADLE).read_text()==bg

bs=(base/'scripts/infinity_background_resume.py').read_text();expected=bs.replace('VERSION_CODE = 2103274','VERSION_CODE = 2103275').replace("RELEASE = '1.0.9-Sports-Hub-Soccer-RC1'",f"RELEASE = '{r.RELEASE}'").replace("BASE_COMMIT = '6a89688f3e61b8f2f66d9d4cef942cc506befffd'",f"BASE_COMMIT = '{r.PARENT_COMMIT}'").replace("BASE_APK_SHA256 = '0f35b65e3eb8c92e1966c8116bbccb3a55d09e368d1b59db02e9c8828d15dc3f'",f"BASE_APK_SHA256 = '{r.PARENT_APK}'")
assert (root/'scripts/infinity_background_resume.py').read_text()==expected,'Background script drift'

bpkg=(base/'scripts/package_background_resume.py').read_text();expected=bpkg.replace('Infinity-2103274-Sports-Hub-Soccer-RC1','Infinity-2103275-Immersive-Edge-Ambient-RC1').replace("'base_run':36770912528",f"'base_run':{r.PARENT_RUN}").replace("ROOT/'repairs/sports-hub-soccer-2103274/DEVICE-TEST.md'","ROOT/'repairs/immersive-edge-ambient-2103275/DEVICE-TEST.md'")
assert (root/'scripts/package_background_resume.py').read_text()==expected,'Packaging script drift'

receipt=json.loads((root/'engine/background-resume-source.json').read_text())
assert receipt['base_source_commit']==r.PARENT_COMMIT and receipt['base_apk_sha256']==r.PARENT_APK
for key in ('cobra_immersive_edge_ambient','cobra_immersive_directional_edges','cobra_immersive_all_view_modes','cobra_immersive_fullscreen_suspended','cobra_immersive_pip_suspended','cobra_immersive_background_suspended','cobra_off_preserved','cobra_subtle_preserved','x_ambient_mit_attribution','pro_sports_preserved','sports_repository_preserved','sports_channel_resolver_preserved','manual_multiview_preserved'):
    assert receipt.get(key) is True,key
assert receipt.get('cobra_immersive_sample_width')==144 and receipt.get('cobra_immersive_frame_interval_ms')==83
assert receipt.get('candidate_locked') is False and receipt.get('physical_device_verified') is False

a.out.mkdir(parents=True,exist_ok=True)
report=dict(base_commit=r.PARENT_COMMIT,base_apk_sha256=r.PARENT_APK,changed_shell_files=changed,added_shell_files=added,protected_source_preserved=True,pro_sports_preserved=True,sports_repository_preserved=True,channel_resolver_preserved=True,manual_multiview_preserved=True,native_source_modified=False,infinity_skin_touched=False,immersive_sample_width=144,immersive_frame_interval_ms=83,immersive_ray_steps=48,fullscreen_suspended=True,pip_suspended=True,background_suspended=True,physical_device_verified=False,candidate_locked=False,files=items)
(a.out/'source-verification.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print('PASS: exact locked 2103274 transformed only by bounded Cobra mini-player immersive edge projection + MIT notice; playback/data/Pro owners preserved.')
