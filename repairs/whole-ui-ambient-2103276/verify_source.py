from pathlib import Path
import argparse,importlib.util,json,hashlib
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
here=Path(__file__).parent;spec=importlib.util.spec_from_file_location('repair276',here/'apply.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
b=a.baseline/'shell-kodi';n=a.root/'shell-kodi';changed=[]
assert r.sha((b/r.ACTIVITY).read_bytes())=='0ed5f50992bf637bd31ff7c4c299fc4837f5ae0ed3169a687511eec8ed07643c'
assert (n/r.ACTIVITY).read_text()==r.patch_activity((b/r.ACTIVITY).read_text())
assert (n/r.AMBIENT).read_bytes()==(here/'CobraImmersiveAmbient.java.in').read_bytes()
assert (n/r.GRADLE).read_text()==(b/r.GRADLE).read_text().replace('versionCode 2103275','versionCode 2103276').replace('1.0.9-Immersive-Edge-Ambient-RC1',r.RELEASE)
old={str(f.relative_to(b)):r.sha(f.read_bytes()) for f in b.rglob('*') if f.is_file()};new={str(f.relative_to(n)):r.sha(f.read_bytes()) for f in n.rglob('*') if f.is_file()}
assert old.keys()==new.keys()
changed=[k for k in old if old[k]!=new[k]];assert set(changed)=={r.ACTIVITY,r.AMBIENT,r.GRADLE},changed
s=(n/r.AMBIENT).read_text();assert 'drawBitmap(smoothed, null' not in s and 'FRAME_INTERVAL_MS = 83L' in s and 'SAMPLE_WIDTH = 144' in s
assert 'new Canvas(smoothed)' not in s[s.index('private boolean captureInternal'):s.index('private void updateSourceRect')]
report=dict(parent_commit=r.BASE,changed_shell_files=changed,protected_source_preserved=True,off_subtle_engine_byte_equivalent=True,native_source_modified=False,infinity_skin_touched=False,physical_device_verified=False,candidate_locked=False)
a.out.mkdir(parents=True,exist_ok=True);(a.out/'source-verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: bounded 2103276 changes; all other locked shell files identical.')
