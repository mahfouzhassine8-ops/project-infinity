from pathlib import Path
import argparse,importlib.util,json
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
spec=importlib.util.spec_from_file_location('repair278',Path(__file__).parent/'apply.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
b=a.baseline/'shell-kodi';n=a.root/'shell-kodi'
assert (n/r.ACTIVITY).read_text()==r.patch_activity((b/r.ACTIVITY).read_text())
assert (n/r.AMBIENT).read_bytes()==(Path(__file__).parent/'CobraImmersiveAmbient.java.in').read_bytes()
assert (n/r.GRADLE).read_text()==(b/r.GRADLE).read_text().replace('versionCode 2103277','versionCode 2103278').replace('1.0.9-Mini-Player-Fill-RC1',r.RELEASE)
old={str(f.relative_to(b)):r.sha(f.read_bytes()) for f in b.rglob('*') if f.is_file()};new={str(f.relative_to(n)):r.sha(f.read_bytes()) for f in n.rglob('*') if f.is_file()}
assert old.keys()==new.keys();changed=[k for k in old if old[k]!=new[k]];assert set(changed)=={r.ACTIVITY,r.AMBIENT,r.GRADLE},changed
engine=(n/r.AMBIENT).read_text();assert 'if(controlsOnly||!haveFrame||getAlpha()<=0f)return;' in engine
assert 'SAMPLE_WIDTH = 144' in engine and 'FRAME_INTERVAL_MS = 83L' in engine
report=dict(parent_commit=r.BASE,changed_shell_files=changed,fullscreen_video_geometry_preserved=True,playback_ownership_preserved=True,protected_source_preserved=True,controls_only_watch_ambient=True,physical_device_verified=False,candidate_locked=False)
a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: bounded Watch-only ambient changes; every other locked shell file identical.')
